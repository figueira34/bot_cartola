import requests
import os
from datetime import datetime

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

url = "https://api.cartolafc.globo.com/mercado/status"
r = requests.get(url)
data = r.json()

print("Resposta da API:", data)
