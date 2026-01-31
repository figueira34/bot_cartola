import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

REPO = "figueira34/bot_cartola"
WORKFLOW_FILE = "mercado.yml"


# ================= TELEGRAM =================
def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = keyboard  # Telegram aceita dict

    r = requests.post(url, json=payload)
    print("📤 TELEGRAM RESPONSE:", r.status_code, r.text)


def answer_callback(callback_id):
    """Remove o loading do botão"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    requests.post(url, json={"callback_query_id": callback_id})


# ================= GITHUB =================
def run_workflow():
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",  # 🔥 padrão correto
        "Accept": "application/vnd.github+json"
    }

    data = {
        "ref": "main",
        "inputs": {
            "manual": "true"  # informa ao monitor que é execução via botão
        }
    }

    r = requests.post(url, headers=headers, json=data)
    print("🚀 GITHUB RESPONSE:", r.status_code, r.text)
    return r.status_code


# ================= WEBHOOK =================
@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("📥 UPDATE RECEBIDO:", data)

    # 🔹 Mensagem normal (abre o painel)
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

        answer_callback(query["id"])  # 🔥 ESSENCIAL

        if action == "status":
            send_message(chat_id, "🔎 Rodando monitor do mercado...")

            status = run_workflow()

            if status == 204:
                send_message(chat_id, "✅ Monitor acionado no GitHub!")
            else:
                send_message(chat_id, "❌ Erro ao acionar automação.")

    return jsonify({"ok": True})


# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
