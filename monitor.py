import requests
import os
from datetime import datetime, timedelta

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def enviar(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

# 🔹 Puxa dados do mercado
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
    enviar("🔒 O mercado do Cartola está FECHADO.")

# ⏰ 1 HORA ANTES
elif tempo_restante <= timedelta(hours=1):
    # Aqui você pode chamar sua função do escalador
    # time = montar_time()
    # enviar(f"⏰ Falta menos de 1h!\nSeu time:\n{time}")
    enviar("⏰ FALTA MENOS DE 1 HORA PARA O MERCADO FECHAR!")

# 📅 AVISO DIÁRIO NORMAL
else:
    horas = int(tempo_restante.total_seconds() // 3600)
    minutos = int((tempo_restante.total_seconds() % 3600) // 60)
    enviar(f"📅 O mercado fecha em {horas}h {minutos}min.")
