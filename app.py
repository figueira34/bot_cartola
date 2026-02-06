import os
import json
import requests
import re
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

REPO = "figueira34/bot_cartola"
WORKFLOW_FILE = "mercado.yml"
CONFIG_FILE = "orcamento.json"

# Guarda quem está editando orçamento
usuarios_editando = set()

# ================= CONFIG =================
def carregar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"orcamento": 100.00}


def salvar_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def atualizar_config_no_github(cfg):
    url = f"https://api.github.com/repos/{REPO}/contents/orcamento.json"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    r = requests.get(url, headers=headers)
    sha = r.json()["sha"]

    conteudo = base64.b64encode(json.dumps(cfg, indent=2).encode()).decode()

    data = {
        "message": "Atualiza orçamento via bot",
        "content": conteudo,
        "sha": sha
    }

    r = requests.put(url, headers=headers, json=data)
    print("📦 GITHUB CONFIG UPDATE:", r.status_code, r.text)


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


# ================= GITHUB ACTION =================
def run_workflow():
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {"ref": "main", "inputs": {"manual": "true"}}

    r = requests.post(url, headers=headers, json=data)
    print("🚀 GITHUB RESPONSE:", r.status_code, r.text)
    return r.status_code


# ================= WEBHOOK =================
@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("📥 UPDATE:", data)

    # ===== MENSAGEM NORMAL =====
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()

        # Usuário está em modo edição de orçamento
        if chat_id in usuarios_editando:
            match = re.search(r"[\d\.]+", text)
            if match:
                novo_valor = float(match.group())
                cfg = carregar_config()
                cfg["orcamento"] = novo_valor
                salvar_config(cfg)
                atualizar_config_no_github(cfg)

                usuarios_editando.remove(chat_id)
                send_message(chat_id, f"💰 Orçamento atualizado para C$ {novo_valor}")
            else:
                send_message(chat_id, "Envie apenas o número. Ex: 120.5")
            return jsonify({"ok": True})

        # Abre painel
        keyboard = {
            "inline_keyboard": [
                [{"text": "📊 Status do Mercado", "callback_data": "status"}],
                [{"text": "💰 Ver Orçamento", "callback_data": "ver_orcamento"}],
                [{"text": "✏️ Alterar Orçamento", "callback_data": "alterar_orcamento"}]
            ]
        }

        send_message(chat_id, "Painel Cartola ⚽", keyboard)

    # ===== BOTÕES =====
    if "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        action = query["data"]

        answer_callback(query["id"])

        if action == "status":
            send_message(chat_id, "🔎 Rodando monitor...")
            status = run_workflow()
            if status == 204:
                send_message(chat_id, "✅ Monitor acionado!")
            else:
                send_message(chat_id, "❌ Erro ao acionar GitHub.")

        elif action == "ver_orcamento":
            cfg = carregar_config()
            send_message(chat_id, f"💰 Orçamento atual: C$ {cfg['orcamento']}")

        elif action == "alterar_orcamento":
            usuarios_editando.add(chat_id)
            send_message(chat_id, "Digite o novo valor do orçamento:")

    return jsonify({"ok": True})


# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
