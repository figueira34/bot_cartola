import requests
import os
import json
from datetime import datetime, timedelta

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

ARQUIVO_ESTADO = "estado.json"

def enviar(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

# ------------------ CONTROLE DE ESTADO ------------------
def carregar_estado():
    if os.path.exists(ARQUIVO_ESTADO):
        with open(ARQUIVO_ESTADO, "r") as f:
            return json.load(f)
    return {}

def salvar_estado(estado):
    with open(ARQUIVO_ESTADO, "w") as f:
        json.dump(estado, f)

estado = carregar_estado()
hoje = datetime.now().strftime("%Y-%m-%d")

# ------------------ API CARTOLA ------------------
url = "https://api.cartolafc.globo.com/mercado/status"
data = requests.get(url).json()
f = data["fechamento"]

data_fechamento = datetime(
    f["ano"], f["mes"], f["dia"], f["hora"], f["minuto"]
)

agora = datetime.now()
tempo_restante = data_fechamento - agora

print("Agora:", agora)
print("Fechamento:", data_fechamento)
print("Tempo restante:", tempo_restante)

# 🔒 MERCADO FECHADO
if agora > data_fechamento:
    if estado.get("fechado") != hoje:
        enviar("🔒 O mercado do Cartola está FECHADO.")
        estado["fechado"] = hoje
        salvar_estado(estado)
    exit()

# ⏰ ALERTA 1H ANTES
if tempo_restante <= timedelta(hours=1):
    if estado.get("alerta_1h") != hoje:
        # 👉 Aqui você pode chamar seu escalador depois
        enviar("⏰ FALTA MENOS DE 1 HORA PARA O MERCADO FECHAR!")
        estado["alerta_1h"] = hoje
        salvar_estado(estado)
    exit()

# 📅 AVISO DIÁRIO
if estado.get("aviso_diario") != hoje:
    horas = int(tempo_restante.total_seconds() // 3600)
    minutos = int((tempo_restante.total_seconds() % 3600) // 60)
    enviar(f"📅 O mercado fecha em {horas}h {minutos}min.")
    estado["aviso_diario"] = hoje
    salvar_estado(estado)
