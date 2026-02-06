import os
import json
import requests
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

REPO = "figueira34/bot_cartola"
WORKFLOW_MERCADO = "mercado.yml"
WORKFLOW_ESCALADOR = "escalador.yml"

CONFIG_FILE = "orcamento.json"


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

    payload = {"chat_id": chat_id, "text": text}

    if keyboard:
        payload["reply_markup"] = keyboard

    r = requests.post(url, json=payload)
    print("📤 TELEGRAM:", r.status_code, r.text)


def answer_callback(callback_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    requests.post(url, json={"callback_query_id": callback_id})


# ================= GITHUB =================
def run_workflow(workflow):
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{workflow}/dispatches"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {"ref": "main"}

    r = requests.post(url, headers=headers, json=data)
    print(f"🚀 GITHUB {workflow}:", r.status_code, r.text)
    return r.status_code


# ================= TECLADO =================
def painel_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📊 Status do Mercado", "callback_data": "status"}],
            [{"text": "🤖 Rodar Escalador", "callback_data": "escalar"}],
            [{"text": "💰 Ver Orçamento", "callback_data": "ver_orcamento"}],
            [{"text": "✏️ Alterar Orçamento", "callback_data": "alterar_orcamento"}]
        ]
    }


# ================= WEBHOOK =================
@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("📥 UPDATE:", data)

    # ========= MENSAGEM TEXTO =========
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        # Usuário digitou um valor de orçamento
        if re.match(r"^\d+(\.\d+)?$", text):
            novo_valor = float(text)
            cfg = carregar_config()
            cfg["orcamento"] = novo_valor
            salvar_config(cfg)
            send_message(chat_id, f"💰 Orçamento salvo: C$ {novo_valor}")
            return jsonify({"ok": True})

        send_message(chat_id, "Painel Cartola ⚽", painel_keyboard())

    # ========= BOTÕES =========
    if "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        action = query["data"]

        answer_callback(query["id"])

        if action == "status":
            send_message(chat_id, "🔎 Rodando monitor...")
            if run_workflow(WORKFLOW_MERCADO) == 204:
                send_message(chat_id, "✅ Monitor acionado!")
            else:
                send_message(chat_id, "❌ Erro no monitor.")

        elif action == "escalar":
            send_message(chat_id, "🤖 Montando melhor time...")
            if run_workflow(WORKFLOW_ESCALADOR) == 204:
                send_message(chat_id, "🚀 Escalador iniciado!")
            else:
                send_message(chat_id, "❌ Erro ao rodar escalador.")

        elif action == "ver_orcamento":
            cfg = carregar_config()
            send_message(chat_id, f"💰 Orçamento atual: C$ {cfg['orcamento']}")

        elif action == "alterar_orcamento":
            send_message(chat_id, "Digite apenas o valor do novo orçamento.\nEx: 125.5")

    return jsonify({"ok": True})


# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
