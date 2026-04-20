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
    except Exception as e:
        print("TG ERROR:", e)

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
# API (CORRIGIDA DEFINITIVA)
# =========================
def get_games():
    if not ODDS_API_KEY:
        print("❌ SEM API KEY")
        return []

    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu,us&markets=h2h"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        # 🔍 DEBUG IMPORTANTE
        print("=== API DEBUG ===")
        print("TYPE:", type(data))
        print("SAMPLE:", str(data)[:300])

        # ✔ CASO 1: lista direta (normal)
        if isinstance(data, list):
            return data

        # ✔ CASO 2: dict com lista dentro
        if isinstance(data, dict):
            for key in ["data", "results", "response"]:
                if key in data and isinstance(data[key], list):
                    return data[key]

        # ✔ CASO 3: erro da API
        if isinstance(data, dict) and "error_code" in data:
            print("❌ API ERROR:", data)
            return []

        return []

    except Exception as e:
        print("❌ REQUEST ERROR:", e)
        return []

# =========================
# ARBITRAGEM SIMPLES
# =========================
def check_arbitrage(game):
    try:
        books = {}

        for b in game.get("bookmakers", []):
            name = b.get("title", "")

            for m in b.get("markets", []):
                if m.get("key") != "h2h":
                    continue

                for o in m.get("outcomes", []):
                    outcome = o["name"]
                    price = float(o["price"])

                    if outcome not in books:
                        books[outcome] = {}

                    books[outcome][name] = price

        if len(books) < 2:
            return

        best = {}
        for outcome, bks in books.items():
            best[outcome] = max(bks.values())

        odds = list(best.values())
        inv = sum(1 / o for o in odds)

        if inv >= 1:
            return

        margin = (1 - inv) * 100

        msg = (
            f"🚨 ARBITRAGEM\n"
            f"{game.get('home_team')} x {game.get('away_team')}\n"
            f"Margem: {margin:.2f}%"
        )

        add_alert("arb", msg, key=game.get("id"))

    except Exception as e:
        print("ARB ERROR:", e)

# =========================
# LOOP
# =========================
def bot_loop():
    print("BOT INICIADO")

    while state["running"]:
        games = get_games()

        state["games_live"] = len(games)
        state["scan_count"] += 1
        state["last_scan"] = datetime.datetime.now().strftime("%H:%M:%S")

        print(f"📊 Jogos recebidos: {len(games)}")

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
<title>BOT PRO</title>
<style>
body{font-family:Arial;background:#111;color:#fff;text-align:center}
button{padding:10px;margin:5px}
.card{background:#222;margin:10px;padding:10px;border-radius:8px}
</style>
</head>
<body>

<h2>⚡ BOT PRO ARBITRAGEM</h2>

<button onclick="start()">START</button>
<button onclick="stop()">STOP</button>

<p id="status"></p>

<div id="alerts"></div>

<script>
function start(){fetch('/start',{method:'POST'})}
function stop(){fetch('/stop',{method:'POST'})}

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
