import requests
import os
import json
from datetime import datetime, timedelta
import pytz

# ---------- CONFIG ----------
TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ARQUIVO_ESTADO = "estado.json"

# ---------- TELEGRAM ----------
def enviar(msg):
    print("📤 Enviando mensagem:", msg)
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )
    print("📨 TELEGRAM RESPONSE:", r.status_code, r.text)


# ---------- ESTADO (não persiste entre actions, mas evita spam na mesma execução) ----------
def carregar_estado():
    if os.path.exists(ARQUIVO_ESTADO):
        try:
            with open(ARQUIVO_ESTADO, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_estado(estado):
    with open(ARQUIVO_ESTADO, "w") as f:
        json.dump(estado, f, indent=2)

estado = carregar_estado()
hoje = datetime.now().strftime("%Y-%m-%d")

# ---------- FUSO HORÁRIO BRASIL ----------
brasil = pytz.timezone("America/Sao_Paulo")
agora = datetime.now(brasil)

print("🕒 Agora (Brasil):", agora)

# ---------- API CARTOLA ----------
url = "https://api.cartolafc.globo.com/mercado/status"
data = requests.get(url).json()
print("📡 API Cartola:", data)

f = data["fechamento"]

data_fechamento = brasil.localize(datetime(
    f["ano"], f["mes"], f["dia"], f["hora"], f["minuto"]
))

print("🔒 Fechamento mercado:", data_fechamento)

tempo_restante = data_fechamento - agora
print("⏳ Tempo restante:", tempo_restante)

# ---------- MERCADO FECHADO ----------
if agora > data_fechamento:
    enviar("🔒 O mercado do Cartola está FECHADO.")
    exit()

# ---------- ALERTA 1H ----------
if tempo_restante <= timedelta(hours=1):
    horas = int(tempo_restante.total_seconds() // 3600)
    minutos = int((tempo_restante.total_seconds() % 3600) // 60)
    enviar(f"⏰ FALTA MENOS DE 1 HORA! Fecha em {horas}h {minutos}min.")
    exit()

# ---------- AVISO PADRÃO ----------
horas = int(tempo_restante.total_seconds() // 3600)
minutos = int((tempo_restante.total_seconds() % 3600) // 60)
enviar(f"📅 O mercado fecha em {horas}h {minutos}min.")
