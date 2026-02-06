import os
import json
import requests
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

REPO = "figueira34/bot_cartola"
WORKFLOW_FILE = "mercado.yml"

CONFIG_FILE = "config.json"


# ================= CONFIG =================
def carregar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"orcamento": 100.00}


def salvar_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


# ================= TELEGRAM =================
def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = keyboard

    r = requests.post(url, json=payload)
    print("📤 TELEGRAM RESPONSE:", r.status_code, r.text)


def answer_callback(callback_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    requests.post(url, json={"callback_query_id": callback_id})


# ================= GITHUB =================
def run_workflow():
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {
        "ref": "main",
        "inputs": {
            "manual": "true"
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

    # 🔹 MENSAGENS DE TEXTO
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        # ===== COMANDO ORÇAMENTO =====
        if text.startswith("/orcamento"):
            match = re.search(r"[\d\.]+", text)
            if match:
                novo_valor = float(match.group())
                cfg = carregar_config()
                cfg["orcamento"] = novo_valor
                salvar_config(cfg)
                send_message(chat_id, f"💰 Orçamento atualizado para C$ {novo_valor}")
            else:
                send_message(chat_id, "Use: /orcamento 120.5")
            return jsonify({"ok": True})

        # ===== VER ORÇAMENTO =====
        if text.startswith("/verorcamento"):
            cfg = carregar_config()
            send_message(chat_id, f"💰 Orçamento atual: C$ {cfg['orcamento']}")
            return jsonify({"ok": True})

        # ===== ABRIR PAINEL =====
        keyboard = {
            "inline_keyboard": [
                [{"text": "📊 Status do Mercado", "callback_data": "status"}]
            ]
        }
        send_message(chat_id, "Painel Cartola ⚽", keyboard)

    # 🔹 CLIQUE EM BOTÃO
    if "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        action = query["data"]

        answer_callback(query["id"])

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
