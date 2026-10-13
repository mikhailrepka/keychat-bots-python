import hashlib
import hmac
import json
import time

from keychat_bots import verify_webhook


def test_verify_webhook():
    body = json.dumps({"api_version": "1", "type": "endpoint.test", "data": {}}, separators=(",", ":")).encode()
    timestamp = str(int(time.time()))
    signature = hmac.new(b"secret", timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    event = verify_webhook(body, {"X-KeyChat-Timestamp": timestamp, "X-KeyChat-Signature": f"v1={signature}"}, "secret")
    assert event["type"] == "endpoint.test"
