import os
import requests
import time
import threading
import datetime
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# =========================
# CONFIG
# =========================
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
BANKROLL = float(os.environ.get("BANKROLL", "200"))

TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")

# Casas que o usuário consegue operar no Brasil
BR_BOOKMAKERS = [
    "Betano",
    "Superbet",
    "Sportingbet",
    "KTO",
    "Novibet"
]

state = {
    "running": False,
    "alerts": [],
    "stats": {"arb": 0},
    "scan_count": 0,
    "last_scan": "—",
    "games_live": 0,
    "last_alerts": {}
}

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    if not TG_TOKEN or not TG_CHAT:
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": msg},
            timeout=6
        )
    except:
        pass

# =========================
# ALERTAS
# =========================
def add_alert(tipo, msg, key=None):
    now = time.time()

    if key:
        last = state["last_alerts"].get(key, 0)
        if now - last < 60:
            return
        state["last_alerts"][key] = now

    state["alerts"].insert(0, {
        "tipo": tipo,
        "msg": msg,
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    })

    state["stats"][tipo] = state["stats"].get(tipo, 0) + 1
    send_telegram(msg)

# =========================
# API
# =========================
def get_games():
    if not ODDS_API_KEY:
        return []

    try:
        url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"
        r = requests.get(url, timeout=10)
        data = r.json()
        return data if isinstance(data, list) else []
    except:
        return []

# =========================
# FILTRAR CASAS BR
# =========================
def filter_br_books(game):
    result = {}

    for book in game.get("bookmakers", []):
        name = book.get("title", "")

        # só marca se for casa BR
        is_br = any(b.lower() in name.lower() for b in BR_BOOKMAKERS)

        if not is_br:
            continue

        for market in book.get("markets", []):
            if market.get("key") != "h2h":
                continue

            for outcome in market.get("outcomes", []):
                o = outcome["name"]
                p = float(outcome["price"])

                if o not in result:
                    result[o] = {}

                result[o][name] = p

    return result

# =========================
# ARBITRAGEM (APENAS BR)
# =========================
def check_arbitrage(game):
    br = filter_br_books(game)

    if len(br) < 2:
        return

    best = {}

    for outcome, books in br.items():
        if books:
            best_book = max(books, key=books.get)
            best[outcome] = books[best_book]

    odds = list(best.values())
    inv = sum(1 / o for o in odds)

    if inv >= 1:
        return

    margin = (1 - inv) * 100

    msg = (
        f"🚨 ARBITRAGEM BR\n"
        f"{game.get('home_team')} x {game.get('away_team')}\n"
        f"Margem: {margin:.2f}%"
    )

    add_alert("arb", msg, key=f"arb_{game.get('id')}")

# =========================
# LOOP
# =========================
def bot_loop():
    send_telegram("🤖 BOT PRO ATIVO")

    while state["running"]:
        games = get_games()

        state["games_live"] = len(games)
        state["scan_count"] += 1
        state["last_scan"] = datetime.datetime.now().strftime("%H:%M:%S")

        for g in games:
            check_arbitrage(g)

        time.sleep(10)

# =========================
# FRONTEND SIMPLES
# =========================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>BOT PRO BR</title>
<style>
body { font-family: Arial; background:#111; color:white; text-align:center; }
button { padding:10px; margin:5px; }
.card { background:#222; margin:10px; padding:10px; border-radius:8px; }
</style>
</head>
<body>

<h2>⚡ BOT PRO ARBITRAGEM BR</h2>

<button onclick="start()">START</button>
<button onclick="stop()">STOP</button>

<p id="status"></p>

<div id="alerts"></div>

<script>
function start(){ fetch('/start',{method:'POST'}) }
function stop(){ fetch('/stop',{method:'POST'}) }

setInterval(()=>{
 fetch('/status')
 .then(r=>r.json())
 .then(d=>{
   document.getElementById('status').innerText =
   `Rodando: ${d.running} | Jogos: ${d.games_live}`

   let html = ""
   d.alerts.forEach(a=>{
     html += `<div class='card'>
       <b>${a.tipo}</b><br>${a.msg}<br>${a.time}
     </div>`
   })

   document.getElementById('alerts').innerHTML = html
 })
},2000)
</script>

</body>
</html>
"""

# =========================
# ROUTES
# =========================
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

# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
