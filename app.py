import os
import requests
import time
import threading
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# ========================
# CONFIG
# ========================
API_KEY = os.environ.get("ODDS_API_KEY")
BANKROLL = float(os.environ.get("BANKROLL", 100))

TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID")

state = {
    "running": False,
    "alerts": [],
    "last_alerts": {}
}

# ========================
# TELEGRAM
# ========================
def send_telegram(msg):
    if not TG_TOKEN or not TG_CHAT:
        print("Telegram não configurado")
        return

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": TG_CHAT,
            "text": msg
        }, timeout=5)
    except Exception as e:
        print("Erro Telegram:", e)

# 🔥 TESTE AUTOMÁTICO AO INICIAR
send_telegram("✅ TESTE OK - BOT CONECTADO AO TELEGRAM")

# ========================
# ALERTAS
# ========================
def add_alert(msg, key=None):
    now = time.time()

    if key:
        last = state["last_alerts"].get(key, 0)
        if now - last < 60:
            return
        state["last_alerts"][key] = now

    print(msg)
    state["alerts"].insert(0, msg)
    send_telegram(msg)

# ========================
# LINKS DAS CASAS
# ========================
def get_link(book):
    links = {
        "Betfair": "https://www.betfair.com",
        "Bet365": "https://www.bet365.com",
        "Pinnacle": "https://www.pinnacle.com",
        "Coolbet": "https://www.coolbet.com"
    }
    return links.get(book, "https://www.google.com")

# ========================
# API ODDS
# ========================
def get_games():
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={API_KEY}&regions=eu&markets=h2h"
    try:
        return requests.get(url, timeout=10).json()
    except:
        return []

# ========================
# CALCULAR STAKE
# ========================
def calc_stakes(odds):
    inv = sum(1/o for o in odds)
    return [(BANKROLL / o) / inv for o in odds]

# ========================
# ARBITRAGEM
# ========================
def check_arbitrage(game):
    best = {}

    for book in game.get("bookmakers", []):
        for market in book.get("markets", []):
            for outcome in market.get("outcomes", []):
                name = outcome["name"]
                price = outcome["price"]
                book_name = book["title"]

                if name not in best or price > best[name]["price"]:
                    best[name] = {"price": price, "book": book_name}

    if len(best) < 2:
        return

    odds = [v["price"] for v in best.values()]
    inv = sum(1/o for o in odds)

    if inv < 1:
        margem = (1 - inv) * 100
        stakes = calc_stakes(odds)

        detalhes = ""
        for (name, data), stake in zip(best.items(), stakes):
            detalhes += (
                f"{name}: {data['price']} ({data['book']})\n"
                f"Apostar: R${stake:.2f}\n"
                f"{get_link(data['book'])}\n\n"
            )

        lucro = min([s * o for s, o in zip(stakes, odds)]) - sum(stakes)

        msg = (
            f"🚨 ARBITRAGEM\n\n"
            f"{game['home_team']} x {game['away_team']}\n\n"
            f"{detalhes}"
            f"Lucro: R${lucro:.2f}\n"
            f"Margem: {margem:.2f}%"
        )

        add_alert(msg, f"arb_{game['id']}")

# ========================
# LOOP
# ========================
def bot_loop():
    while state["running"]:
        games = get_games()

        for g in games:
            check_arbitrage(g)

        time.sleep(10)

# ========================
# INTERFACE
# ========================
HTML = """
<h2>BOT PRO ARBITRAGEM</h2>
<button onclick="start()">Start</button>
<button onclick="stop()">Stop</button>
<div id="alerts" style="white-space: pre-line;"></div>

<script>
function start(){fetch('/start',{method:'POST'})}
function stop(){fetch('/stop',{method:'POST'})}

setInterval(()=>{
 fetch('/status').then(r=>r.json()).then(d=>{
  document.getElementById('alerts').innerHTML = d.alerts.join('\\n\\n-----\\n\\n')
 })
},2000)
</script>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/start", methods=["POST"])
def start():
    if not state["running"]:
        state["running"] = True
        threading.Thread(target=bot_loop, daemon=True).start()
    return jsonify({"ok": True})

@app.route("/stop", methods=["POST"])
def stop():
    state["running"] = False
    return jsonify({"ok": True})

@app.route("/status")
def status():
    return jsonify(state)

# ========================
# START
# ========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("Servidor iniciado")
    app.run(host="0.0.0.0", port=port)
