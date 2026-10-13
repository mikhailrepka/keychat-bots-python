# Key Chat Bots SDK for Python

Server-side Python 3.10+ client for the Key Chat Bot Runtime API and signed webhooks.

## Install

After the first PyPI release:

```bash
pip install keychat-bots
```

Local development:

```bash
git clone https://github.com/mikhailrepka/keychat-bots-python.git
cd keychat-bots-python
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
```

Use a local checkout from another project with `pip install -e ../keychat-bots-python`.

## Connect and reply

```python
import os
from uuid import uuid4
from keychat_bots import KeyChatBot
from keychat_bots.client import callback_button, command_button

bot = KeyChatBot(os.environ["KEYCHAT_BOT_TOKEN"])
result = bot.send_message(
    chat_id,
    {
        "text": "**Choose an action**",
        "format": "markdown",
        "keyboard": {"rows": [[command_button("/help")], [callback_button("details", "Details", "job-42")]]},
        "menu": {"rows": [[command_button("/start"), command_button("/settings")]]},
    },
    idempotency_key=str(uuid4()),
)
```

Omit `menu` to keep the current menu; use `"menu": None` to hide it. Callback buttons do not send a visible message. Update a bot message with `bot.edit_message(chat_id, event_id, content)` and reply with `bot.reply(...)`.

```python
media = bot.upload_media("result.png", mime_type="image/png")
bot.send_message(chat_id, {"attachments": [{"type": "image", **media}]})
```

## Receive webhooks

Always verify the signature against the raw body before parsing JSON:

```python
from keychat_bots import dispatch_webhook

result = dispatch_webhook(raw_body, request_headers, os.environ["KEYCHAT_WEBHOOK_SECRET"], {
    "message.created": lambda event: bot.send_message(
        event["data"]["chat_id"],
        {"text": "Echo: " + event["data"]["message"]["text"]},
    ),
    "button.clicked": lambda event: {"ok": True},
    "inline.query": lambda event: {"results": [{"id": "one", "type": "text", "text": event["data"]["query"]}]},
})
```

Return the result as JSON with a 2xx status. Queue events can be retried; deduplicate by webhook `event.id` and use `idempotency_key` when sending.

A complete FastAPI endpoint is included in [`examples/fastapi_app.py`](./examples/fastapi_app.py). Run it with `pip install fastapi uvicorn` and `uvicorn examples.fastapi_app:app --port 3000`.

## Documentation

Build and serve the API reference:

```bash
pip install -e '.[dev]'
pdoc keychat_bots -o docs
python -m http.server 8000 -d docs
```

Platform documentation: <https://chat.wokey.pro/docs/bots/>. Default API endpoint: `https://chat.wokey.pro/_keychat`; pass `base_url=` for local tests.
