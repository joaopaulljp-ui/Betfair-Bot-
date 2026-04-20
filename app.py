"""
BOT PRO — Arbitragem & Value Bets — Casas BR
Betano · Superbet · Sportingbet · KTO · Novibet
"""

import os
import requests
import time
import threading
import datetime
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# ========================
# CONFIG
# ========================
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
BANKROLL = float(os.environ.get("BANKROLL", "200"))

TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")

VALUE_THRESH = float(os.environ.get("VALUE_THRESHOLD", "5"))
ARB_MIN = float(os.environ.get("ARB_MIN_MARGIN", "0.3"))

# Casas BR
BR_BOOKS = ["Betano", "Superbet", "Sportingbet", "KTO", "Novibet"]

state = {
    "running": False,
    "alerts": [],
    "stats": {"arb": 0, "value": 0, "card": 0},
    "last_scan": "—",
    "scan_count": 0,
    "games_live": 0,
    "last_alerts": {}
}

# ========================
# TELEGRAM
# ========================
def send_telegram(msg):
    if not TG_TOKEN or not TG_CHAT:
        print("Telegram não configurado")
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": msg, "parse_mode": "HTML"},
            timeout=6
        )
    except Exception as e:
        print("Telegram error:", e)


def tg_test():
    send_telegram("🤖 BOT PRO ONLINE\nConexão OK")

# ========================
# ALERTAS
# ========================
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

# ========================
# API ODDS
# ========================
def get_games():
    if not ODDS_API_KEY:
        return []

    try:
        url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"
        r = requests.get(url, timeout=10)
        return r.json() if isinstance(r.json(), list) else []
    except:
        return []

# ========================
# ODDS BR
# ========================
def extract_br_odds(game):
    result = {}

    for book in game.get("bookmakers", []):
        name = book.get("title", "")

        if not any(b.lower() in name.lower() for b in BR_BOOKS):
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

# ========================
# ARBITRAGEM
# ========================
def check_arbitrage(game):
    br = extract_br_odds(game)
    if len(br) < 2:
        return

    best = {}

    for outcome, books in br.items():
        if books:
            b = max(books, key=books.get)
            best[outcome] = books[b]

    odds = list(best.values())
    inv = sum(1 / o for o in odds)

    if inv >= 1:
        return

    margin = (1 - inv) * 100
    if margin < ARB_MIN:
        return

    stakes = [(BANKROLL / o) / inv for o in odds]
    profit = min(s * o for s, o in zip(stakes, odds)) - sum(stakes)

    msg = (
        f"🚨 ARBITRAGEM\n"
        f"{game.get('home_team')} x {game.get('away_team')}\n"
        f"Lucro: R${profit:.2f} | Margem: {margin:.2f}%"
    )

    add_alert("arb", msg, key=f"arb_{game.get('id')}")

# ========================
# LOOP
# ========================
def bot_loop():
    tg_test()

    while state["running"]:
        games = get_games()

        state["games_live"] = len(games)
        state["scan_count"] += 1
        state["last_scan"] = datetime.datetime.now().strftime("%H:%M:%S")

        for g in games:
            check_arbitrage(g)

        time.sleep(12)

# ========================
# API
# ========================
@app.route("/")
def home():
    return "<h2>BOT PRO RODANDO</h2>"

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
    print("Bot iniciado")
    app.run(host="0.0.0.0", port=port)
