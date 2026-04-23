import os
import requests
from flask import Flask, jsonify

app = Flask(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def build_result():
    return """🟤 CSS        : 37 Listed
🟠 XBL        : 0 Listed
🔵 PBL        : 0 Listed
🔴 SBL        : 16 Listed
🟢 Barracuda  : 82 Listed
✅ Clean      : 618

━━━━━━━━━━━━━━
🌐 DOMAINS
━━━━━━━━━━━━━━
🌍 DBL        : 97 Listed"""

@app.route("/api/cron", methods=["GET"])
def run_cron():
    if not BOT_TOKEN or not CHAT_ID:
        return jsonify({
            "ok": False,
            "error": "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"
        }), 500

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    res = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": build_result()
        },
        timeout=30
    )

    try:
        telegram_response = res.json()
    except Exception:
        telegram_response = {"raw": res.text}

    return jsonify({
        "ok": res.ok,
        "status": res.status_code,
        "response": telegram_response
    }), (200 if res.ok else 500)
