import os
import requests
import time
import threading
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

API_KEY = os.environ.get("ODDS_API_KEY")

state = {
    "running": False,
    "games": [],
    "alerts": [],
    "history": {},
    "last_alerts": {}
}

def add_alert(msg, key=None):
    now = time.time()

    # evita repetição
    if key:
        last = state["last_alerts"].get(key, 0)
        if now - last < 60:
            return
        state["last_alerts"][key] = now

    print(msg)
    state["alerts"].insert(0, msg)
    if len(state["alerts"]) > 50:
        state["alerts"].pop()

# ------------------------
# LINKS DAS CASAS
# ------------------------
def get_book_link(book):
    links = {
        "Betfair": "https://www.betfair.com/exchange/plus/",
        "Bet365": "https://www.bet365.com",
        "Pinnacle": "https://www.pinnacle.com",
        "Coolbet": "https://www.coolbet.com",
        "William Hill": "https://www.williamhill.com",
    }
    return links.get(book, "https://www.google.com")

# ------------------------
# API ODDS
# ------------------------
def get_odds():
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={API_KEY}&regions=eu&markets=h2h"
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except:
        return []

# ------------------------
# ARBITRAGEM
# ------------------------
def check_arbitrage(game):
    best = {}

    for book in game.get("bookmakers", []):
        book_name = book.get("title")

        for market in book.get("markets", []):
            for outcome in market.get("outcomes", []):
                name = outcome["name"]
                price = outcome["price"]

                if name not in best or price > best[name]["price"]:
                    best[name] = {
                        "price": price,
                        "book": book_name
                    }

    if len(best) < 2:
        return

    inv = sum(1/v["price"] for v in best.values())

    if inv < 0.98:
        margem = (1 - inv) * 100

        detalhes = "\n".join([
            f"{k}: {v['price']} ({v['book']})\n👉 {get_book_link(v['book'])}"
            for k, v in best.items()
        ])

        key = f"arb_{game['id']}"

        add_alert(
            f"🚨 ARBITRAGEM\n\n"
            f"{game['home_team']} x {game['away_team']}\n\n"
            f"{detalhes}\n\n"
            f"Margem: {margem:.2f}%",
            key
        )

# ------------------------
# VARIAÇÃO DE ODDS
# ------------------------
def detect_movement(game):
    game_id = game["id"]

    current_odds = []

    for book in game.get("bookmakers", []):
        for market in book.get("markets", []):
            for outcome in market.get("outcomes", []):
                current_odds.append(outcome["price"])

    if not current_odds:
        return

    avg_now = sum(current_odds) / len(current_odds)

    if game_id not in state["history"]:
        state["history"][game_id] = avg_now
        return

    old = state["history"][game_id]
    change = ((avg_now - old) / old) * 100

    if abs(change) > 10:
        key = f"mov_{game_id}"

        add_alert(
            f"⚡ VARIAÇÃO FORTE\n\n"
            f"{game['home_team']} x {game['away_team']}\n"
            f"Variação: {change:.1f}%",
            key
        )

    state["history"][game_id] = avg_now

# ------------------------
# LOOP PRINCIPAL
# ------------------------
def bot_loop():
    while state["running"]:
        games = get_odds()
        state["games"] = games

        for g in games:
            check_arbitrage(g)
            detect_movement(g)

        time.sleep(10)

# ------------------------
# INTERFACE
# ------------------------
HTML = """
<h2>Bot de Alertas PRO</h2>
<button onclick="start()">Start</button>
<button onclick="stop()">Stop</button>
<div id="alerts" style="white-space: pre-line;"></div>

<script>
function start(){fetch('/start',{method:'POST'})}
function stop(){fetch('/stop',{method:'POST'})}

setInterval(()=>{
 fetch('/status').then(r=>r.json()).then(d=>{
  document.getElementById('alerts').innerHTML = d.alerts.join('\\n\\n-----------------------\\n\\n')
 })
},2000)
</script>
"""

@app.route("/")
def index():
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("🚀 Bot rodando...")
    app.run(host="0.0.0.0", port=port)
