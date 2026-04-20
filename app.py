import os
import json
import time
import threading
import datetime
import requests
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

CONFIG = {
    "app_key": os.environ.get("BETFAIR_APP_KEY", ""),
    "username": os.environ.get("BETFAIR_USERNAME", ""),
    "password": os.environ.get("BETFAIR_PASSWORD", ""),
    "stake": float(os.environ.get("STAKE", "50")),
    "min_odd": float(os.environ.get("MIN_ODD", "1.5")),
    "max_odd": float(os.environ.get("MAX_ODD", "4.0")),
    "delay_threshold": float(os.environ.get("DELAY_THRESHOLD", "4")),
    "check_interval": float(os.environ.get("CHECK_INTERVAL", "1.5")),
    "dry_run": os.environ.get("DRY_RUN", "true").lower() == "true",
}

BETFAIR_LOGIN_URL = "https://identitysso-cert.betfair.com/api/login"
BETTING_API = "https://api.betfair.com/exchange/betting/json-rpc/v1"

state = {
    "running": False,
    "session_token": None,
    "headers": {},
    "balance": 0.0,
    "markets": [],
    "monitored": {},
    "bets": [],
    "log": [],
    "opportunities": 0,
}

def add_log(msg, level="INFO"):
    entry = {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "msg": msg
    }
    state["log"].insert(0, entry)
    print(f"[{entry['time']}] [{level}] {msg}")

def login():
    add_log("Autenticando...")
    if not CONFIG["app_key"]:
        add_log("Configure variáveis no Railway", "ERROR")
        return False
    return True

def bot_loop():
    add_log("Bot iniciado")
    while state["running"]:
        time.sleep(2)

HTML = """
<h1>Bot rodando</h1>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/start", methods=["POST"])
def start():
    state["running"] = True
    threading.Thread(target=bot_loop, daemon=True).start()
    return jsonify({"ok": True})

@app.route("/api/stop", methods=["POST"])
def stop():
    state["running"] = False
    return jsonify({"ok": True})

@app.route("/api/status")
def status():
    return jsonify({"running": state["running"]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    add_log("Servidor iniciado")
    app.run(host="0.0.0.0", port=port)
