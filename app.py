import os
import requests
import time
import threading
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

API_KEY = os.environ.get("ODDS_API_KEY")
BANKROLL = float(os.environ.get("BANKROLL", 100))

state = {
    "running": False,
    "alerts": [],
    "history": {},
    "last_alerts": {}
}

def add_alert(msg, key=None):
    now = time.time()

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
    }
    return links.get(book, "https://www.google.com")

# ------------------------
# API ODDS
# ------------------------
def get_odds():
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={API_KEY}&regions=eu&markets=h2h"
    try:
        return requests.get(url, timeout=10).json()
    except:
        return []

# ------------------------
# CÁLCULO DE STAKE
# ------------------------
def calculate_stakes(odds):
    inv_sum = sum(1/o for o in odds)
    stakes = [(BANKROLL / o) / inv_sum for o in odds]
    return stakes

# ------------------------
# ARBITRAGEM PRO
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

    odds = [v["price"] for v in best.values()]
    inv = sum(1/o for o in odds)

    if inv < 1:
        margem = (1 - inv) * 100
        stakes = calculate_stakes(odds)

        detalhes = ""
        for (name, data), stake in zip(best.items(), stakes):
            detalhes += (
                f"{name}: {data['price']} ({data['book']})\n"
                f"👉 {get_book_link(data['book'])}\n"
                f"💰 Apostar: R${stake:.2f}\n\n"
            )

        lucro = min([stake * odd for stake, odd in zip(stakes, odds)]) - sum(stakes)

        key = f"arb_{game['id']}"

        add_alert(
            f"🚨 ARBITRAGEM REAL\n\n"
            f"{game['home_team']} x {game['away_team']}\n\n"
            f"{detalhes}"
            f"💵 Lucro estimado: R${lucro:.2f}\n"
            f"📊 Margem: {margem:.2f}%",
            key
        )

# ------------------------
# VARIAÇÃO
# ------------------------
def detect_movement(game):
    gid = game["id"]
    odds = []

    for b in game.get("bookmakers", []):
        for m in b.get("markets", []):
            for o in m.get("outcomes", []):
                odds.append(o["price"])

    if not odds:
        return

    avg = sum(odds) / len(odds)

    if gid not in state["history"]:
        state["history"][gid] = avg
        return

    old = state["history"][gid]
    change = ((avg - old) / old) * 100

    if abs(change) > 10:
        add_alert(
            f"⚡ VARIAÇÃO FORTE\n{game['home_team']} x {game['away_team']}\n{change:.1f}%",
            f"mov_{gid}"
        )

    state["history"][gid] = avg

# ------------------------
# LOOP
# ------------------------
def bot_loop():
    while state["running"]:
        games = get_odds()

        for g in games:
            check_arbitrage(g)
            detect_movement(g)

        time.sleep(10)

# ------------------------
# FRONT
# ------------------------
HTML = """
<h2>Bot PRO Arbitragem</h2>
<button onclick="start()">Start</button>
<button onclick="stop()">Stop</button>
<div id="alerts" style="white-space: pre-line;"></div>

<script>
function start(){fetch('/start',{method:'POST'})}
function stop(){fetch('/stop',{method:'POST'})}
setInterval(()=>{
 fetch('/status').then(r=>r.json()).then(d=>{
  document.getElementById('alerts').innerHTML = d.alerts.join('\\n\\n----------------\\n\\n')
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
