from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import Callable, Mapping
from typing import Any


class WebhookError(ValueError):
    pass


def verify_webhook(raw_body: bytes, headers: Mapping[str, str], secret: str, *, tolerance_seconds: int = 300) -> dict[str, Any]:
    normalized = {key.lower(): value for key, value in headers.items()}
    timestamp = normalized.get("x-keychat-timestamp", "")
    signature = normalized.get("x-keychat-signature", "").removeprefix("v1=")
    if not timestamp.isdigit() or len(signature) != 64:
        raise WebhookError("Invalid Key Chat webhook signature headers")
    if abs(time.time() - int(timestamp)) > tolerance_seconds:
        raise WebhookError("Stale Key Chat webhook")
    expected = hmac.new(secret.encode(), timestamp.encode() + b"." + raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise WebhookError("Invalid Key Chat webhook signature")
    try:
        value = json.loads(raw_body)
    except (ValueError, UnicodeDecodeError) as error:
        raise WebhookError("Invalid Key Chat webhook JSON") from error
    if not isinstance(value, dict):
        raise WebhookError("Webhook payload must be an object")
    return value


def dispatch_webhook(
    raw_body: bytes,
    headers: Mapping[str, str],
    secret: str,
    handlers: Mapping[str, Callable[[dict[str, Any]], Any]],
) -> Any:
    event = verify_webhook(raw_body, headers, secret)
    handler = handlers.get(str(event.get("type"))) or handlers.get("*")
    return handler(event) if handler else {}
