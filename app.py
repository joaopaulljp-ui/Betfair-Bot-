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
    "alerts": []
}

def add_alert(msg):
    state["alerts"].insert(0, msg)
    print(msg)

def get_odds():
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={API_KEY}&regions=eu&markets=h2h"
    try:
        r = requests.get(url)
        return r.json()
    except:
        return []

def check_arbitrage(game):
    odds = []
    for book in game.get("bookmakers", []):
        for market in book.get("markets", []):
            for outcome in market.get("outcomes", []):
                odds.append(outcome["price"])

    if len(odds) >= 2:
        inv = sum(1/o for o in odds[:2])
        if inv < 1:
            add_alert(f"🚨 ARBITRAGEM: {game['home_team']} x {game['away_team']}")

def bot_loop():
    while state["running"]:
        games = get_odds()
        state["games"] = games

        for g in games:
            check_arbitrage(g)

        time.sleep(10)

HTML = """
<h2>Bot de Alertas</h2>
<button onclick="start()">Start</button>
<button onclick="stop()">Stop</button>
<div id="alerts"></div>

<script>
function start(){fetch('/start',{method:'POST'})}
function stop(){fetch('/stop',{method:'POST'})}

setInterval(()=>{
 fetch('/status').then(r=>r.json()).then(d=>{
  document.getElementById('alerts').innerHTML = d.alerts.join('<br>')
 })
},2000)
</script>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/start", methods=["POST"])
def start():
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
    app.run(host="0.0.0.0", port=port)
