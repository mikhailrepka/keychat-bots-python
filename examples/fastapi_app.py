import os

from fastapi import FastAPI, HTTPException, Request
from keychat_bots import KeyChatBot, dispatch_webhook

app = FastAPI()
bot = KeyChatBot(os.environ["KEYCHAT_BOT_TOKEN"])
secret = os.environ["KEYCHAT_WEBHOOK_SECRET"]


@app.post("/webhook")
async def webhook(request: Request):
    raw_body = await request.body()

    def message_created(event):
        bot.send_message(event["data"]["chat_id"], {"text": "Echo: " + event["data"]["message"]["text"]})
        return {}

    try:
        return dispatch_webhook(raw_body, request.headers, secret, {
            "message.created": message_created,
            "button.clicked": lambda event: {"ok": True},
            "inline.query": lambda event: {"results": [{"id": "result", "type": "text", "text": event["data"]["query"]}]},
        })
    except ValueError as error:
        raise HTTPException(401, str(error)) from error
