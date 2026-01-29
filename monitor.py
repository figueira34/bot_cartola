import requests
from datetime import datetime
import os

TOKEN = os.environ["8285797708:AAHGRbNPuZw-YY11WzImyY4Z3b6r_YiTCNU"]
CHAT_ID = os.environ["1261554292"]

def enviar(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

# API Cartola
url = "https://api.cartola.globo.com/mercado/status"
dados = requests.get(url).json()

f = dados["fechamento"]

fechamento = datetime(f["ano"], f["mes"], f["dia"], f["hora"], f["minuto"])
agora = datetime.now()

diff_min = int((fechamento - agora).total_seconds() / 60)

# 🔒 MERCADO JÁ FECHOU
if diff_min <= 0:
    # aviso diário só uma vez pela manhã
    if agora.hour == 9 and agora.minute < 30:
        enviar("🔒 O mercado está FECHADO. Rodada em andamento.")
    exit()

# 🟢 MERCADO AINDA ABERTO
# ⏳ AVISO DIÁRIO
if agora.hour == 9 and agora.minute < 30:
    horas = diff_min // 60
    minutos = diff_min % 60
    enviar(f"⏳ Mercado fecha em {horas}h {minutos}min")

# 🚨 ALERTA 1H ANTES
if 0 < diff_min <= 60:
    enviar("🚨 FALTA 1 HORA PARA O MERCADO FECHAR!")
