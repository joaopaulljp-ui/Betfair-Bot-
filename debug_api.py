from config import Config
import requests

print("🔍 DEBUG API")
print(f"API Key: {Config.ODDS_API_KEY}")

if not Config.ODDS_API_KEY:
    print("❌ CHAVE NÃO CONFIGURADA!")
    exit(1)

url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/"
params = {
    "apiKey": Config.ODDS_API_KEY,
    "regions": "br",
    "markets": "h2h"
}

try:
    r = requests.get(url, params=params, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Resposta: {r.text[:500]}")
except Exception as e:
    print(f"Erro: {e}")
