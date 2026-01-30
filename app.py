import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

REPO = "henrique_fig/bot_cartola"
WORKFLOW_FILE = "monitor.yml"


# ================= TELEGRAM =================
def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)

    r = requests.post(url, json=payload)

    print("📤 TELEGRAM RESPONSE:", r.status_code, r.text)


# ================= GITHUB =================
def run_workflow():
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {"ref": "main"}

    r = requests.post(url, headers=headers, json=data)
    print("🚀 GITHUB RESPONSE:", r.status_code, r.text)


# ================= WEBHOOK =================
@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("📥 UPDATE RECEBIDO:", data)

    # 🔹 Mensagem normal (quando você fala com o bot)
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]

        keyboard = {
            "inline_keyboard": [
                [{"text": "📊 Status do Mercado", "callback_data": "status"}]
            ]
        }

        send_message(chat_id, "Painel Cartola ⚽", keyboard)

    # 🔹 Clique em botão
    if "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        action = query["data"]

        if action == "status":
            send_message(chat_id, "🔎 Rodando monitor do mercado...")
            run_workflow()

    return jsonify({"ok": True})


# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
