from __future__ import annotations

from pathlib import Path
from typing import Any, BinaryIO

import httpx

DEFAULT_BASE_URL = "https://chat.wokey.pro/_keychat"


class KeyChatError(RuntimeError):
    def __init__(self, status: int, body: Any):
        super().__init__(f"Key Chat API error: {status}")
        self.status = status
        self.body = body


class KeyChatBot:
    """Key Chat Bot Runtime API client initialized with a bot token."""

    def __init__(self, token: str, *, base_url: str = DEFAULT_BASE_URL, timeout: float = 30):
        if not token:
            raise ValueError("Key Chat bot token is required")
        self.token = token
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )

    def __enter__(self) -> "KeyChatBot":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = self._client.request(method, path, **kwargs)
        try:
            body = response.json()
        except ValueError:
            body = None
        if response.is_error:
            raise KeyChatError(response.status_code, body)
        return body

    def send_message(
        self,
        chat_id: str,
        content: dict[str, Any],
        *,
        idempotency_key: str | None = None,
        reply_to_event_id: str | None = None,
        replace_event_id: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "content": content}
        for key, value in {
            "idempotency_key": idempotency_key,
            "reply_to_event_id": reply_to_event_id,
            "replace_event_id": replace_event_id,
        }.items():
            if value is not None:
                payload[key] = value
        return self._request("POST", "/v1/bot/messages", json=payload)

    def edit_message(self, chat_id: str, event_id: str, content: dict[str, Any], *, idempotency_key: str | None = None) -> dict[str, Any]:
        return self.send_message(chat_id, content, replace_event_id=event_id, idempotency_key=idempotency_key)

    def reply(self, chat_id: str, event_id: str, content: dict[str, Any], *, idempotency_key: str | None = None) -> dict[str, Any]:
        return self.send_message(chat_id, content, reply_to_event_id=event_id, idempotency_key=idempotency_key)

    def upload_media(self, source: str | Path | BinaryIO, *, filename: str | None = None, mime_type: str = "application/octet-stream") -> dict[str, Any]:
        if isinstance(source, (str, Path)):
            path = Path(source)
            with path.open("rb") as stream:
                return self.upload_media(stream, filename=filename or path.name, mime_type=mime_type)
        name = filename or getattr(source, "name", "attachment")
        return self._request("POST", "/v1/bot/media", files={"file": (str(name), source, mime_type)})


def command_button(command: str, **options: Any) -> dict[str, Any]:
    return {**options, "command": command}


def callback_button(button_id: str, text: str, data: str | None = None, **options: Any) -> dict[str, Any]:
    return {**options, "id": button_id, "text": text, "action": {"type": "callback", "data": data}}


def message_button(text: str, message: str, **options: Any) -> dict[str, Any]:
    return {**options, "text": text, "action": {"type": "send_message", "text": message}}


def url_button(text: str, url: str, **options: Any) -> dict[str, Any]:
    return {**options, "text": text, "action": {"type": "open_url", "url": url}}
