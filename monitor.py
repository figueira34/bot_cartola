import requests
import os
import json
from datetime import datetime, timedelta
import pytz

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ARQUIVO_ESTADO = "estado.json"

tz = pytz.timezone("America/Sao_Paulo")

def enviar(msg):
    print("📤 Enviando:", msg)
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

# ---------- ESTADO ----------
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
hoje = datetime.now(tz).strftime("%Y-%m-%d")

# ---------- API CARTOLA ----------
url = "https://api.cartolafc.globo.com/mercado/status"
data = requests.get(url).json()
f = data["fechamento"]

data_fechamento = tz.localize(datetime(
    f["ano"], f["mes"], f["dia"], f["hora"], f["minuto"]
))

agora = datetime.now(tz)
tempo_restante = data_fechamento - agora

print("Agora:", agora)
print("Fechamento:", data_fechamento)
print("Tempo restante:", tempo_restante)

# ---------- FORMATADOR DE TEMPO ----------
def formatar_tempo(delta):
    total = int(delta.total_seconds())
    dias = total // 86400
    horas = (total % 86400) // 3600
    minutos = (total % 3600) // 60

    if dias > 0:
        return f"{dias} dias {horas}h {minutos}min"
    return f"{horas}h {minutos}min"

# ---------- MERCADO FECHADO ----------
if agora > data_fechamento:
    if estado.get("fechado") != hoje:
        enviar("🔒 O mercado do Cartola está FECHADO.")
        estado["fechado"] = hoje
        salvar_estado(estado)
    exit()

# ---------- DIA DO FECHAMENTO ----------
eh_dia_fechamento = agora.date() == data_fechamento.date()

# ---------- ALERTA 1H ----------
if tempo_restante <= timedelta(hours=1):
    enviar(f"⏰ FALTA MENOS DE 1 HORA! Fecha em {formatar_tempo(tempo_restante)}")
    exit()

# ---------- DIA NORMAL (UMA VEZ) ----------
if not eh_dia_fechamento:
    if estado.get("aviso_diario") != hoje:
        enviar(f"📅 O mercado fecha em {formatar_tempo(tempo_restante)}.")
        estado["aviso_diario"] = hoje
        salvar_estado(estado)
    exit()

# ---------- DIA DO FECHAMENTO (PODE REPETIR) ----------
enviar(f"🔥 HOJE FECHA! Restam {formatar_tempo(tempo_restante)}")
