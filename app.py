import os
import time
import threading
import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
import requests

from config import Config
from database import db, Alert, Arbitrage
from arbitrage.detector import ArbitrageDetector
from arbitrage.calculator import OddsCalculator

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

state = {
    "running": False,
    "last_scan": None,
    "games_live": 0,
    "arbitragens_detectadas": 0,
    "alertas_hoje": 0
}

with app.app_context():
    db.create_all()
    print("✅ Banco de dados inicializado!")

def get_games_api():
    """Obtém jogos de TODOS os esportes internacionais"""
    if not Config.ODDS_API_KEY:
        print("❌ SEM API KEY")
        return []
    
    todos_jogos = []
    
    esportes = [
        "soccer",
        "basketball",
        "americanfootball",
        "baseball",
        "ice_hockey",
        "tennis"
    ]
    
    for esporte in esportes:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{esporte}/odds/"
            params = {
                "apiKey": Config.ODDS_API_KEY,
                "regions": "br",
                "markets": "h2h"
            }
            
            print(f"🔍 Buscando {esporte}...")
            print(f"   URL: {url}")
            
            r = requests.get(url, params=params, timeout=10)
            
            print(f"   Status: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                
                print(f"   Data type: {type(data)}")
                
                if isinstance(data, list):
                    todos_jogos.extend(data)
                    print(f"✅ {esporte}: {len(data)} jogos")
                elif isinstance(data, dict):
                    if "data" in data:
                        todos_jogos.extend(data["data"])
                        print(f"✅ {esporte}: {len(data['data'])} jogos")
                    else:
                        print(f"⚠️ {esporte}: Resposta inesperada")
                        print(f"   Keys: {list(data.keys())}")
                        print(f"   Sample: {str(data)[:200]}")
            else:
                print(f"❌ {esporte}: Erro {r.status_code}")
                print(f"   Response: {r.text[:500]}")
        
        except Exception as e:
            print(f"❌ {esporte}: Exception {type(e).__name__}: {e}")
    
    print(f"\n📊 TOTAL: {len(todos_jogos)} jogos coletados")
    return todos_jogos

def bot_loop():
    print("🚀 BOT INICIADO")
    
    while state["running"]:
        try:
            jogos = get_games_api()
            
            state["games_live"] = len(jogos)
            state["last_scan"] = datetime.datetime.now().strftime("%H:%M:%S")
            
            print(f"📊 Total de {len(jogos)} jogos - {state['last_scan']}")
            
            for jogo in jogos:
                resultado = ArbitrageDetector.processar_jogo(jogo)
                
                if resultado:
                    state["arbitragens_detectadas"] += 1
                    print(f"✅ ARBITRAGEM DETECTADA!")
            
            time.sleep(10)
        
        except Exception as e:
            print(f"❌ ERRO NO LOOP: {e}")
            time.sleep(5)

@app.route("/api/status")
def api_status():
    with app.app_context():
        alertas_hoje = Alert.query.filter(
            Alert.data_criacao >= datetime.datetime.utcnow().date()
        ).all()
        
        return jsonify({
            "running": state["running"],
            "last_scan": state["last_scan"],
            "games_live": state["games_live"],
            "arbitragens": state["arbitragens_detectadas"],
            "alertas_hoje": len(alertas_hoje),
            "alertas": [a.to_dict() for a in alertas_hoje[-5:]]
        })

@app.route("/api/start", methods=["POST"])
def api_start():
    if not state["running"]:
        state["running"] = True
        threading.Thread(target=bot_loop, daemon=True).start()
        return jsonify({"ok": True, "mensagem": "Bot iniciado"})
    return jsonify({"ok": False, "mensagem": "Bot já está rodando"})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    state["running"] = False
    return jsonify({"ok": True, "mensagem": "Bot parado"})

@app.route("/api/alertas")
def api_alertas():
    with app.app_context():
        alertas = Alert.query.order_by(Alert.data_criacao.desc()).limit(100).all()
        return jsonify([a.to_dict() for a in alertas])

@app.route("/api/arbitragens")
def api_arbitragens():
    with app.app_context():
        arbs = Arbitrage.query.order_by(Arbitrage.data_deteccao.desc()).limit(100).all()
        return jsonify([a.to_dict() for a in arbs])

@app.route("/api/stats")
def api_stats():
    with app.app_context():
        hoje = datetime.datetime.utcnow().date()
        
        stats = {
            "arbitragens_hoje": Arbitrage.query.filter(
                Arbitrage.data_deteccao >= datetime.datetime.combine(hoje, datetime.time.min)
            ).count(),
            "alertas_hoje": Alert.query.filter(
                Alert.data_criacao >= datetime.datetime.combine(hoje, datetime.time.min)
            ).count(),
            "total_arbitragens": Arbitrage.query.count(),
            "total_alertas": Alert.query.count()
        }
        
        return jsonify(stats)

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/alertas")
def alertas():
    with app.app_context():
        alertas_list = Alert.query.order_by(Alert.data_criacao.desc()).limit(100).all()
        return render_template("alertas.html", alertas=alertas_list)

@app.route("/stats")
def stats():
    with app.app_context():
        arbs = Arbitrage.query.count()
        alertas_count = Alert.query.count()
        
        return render_template("stats.html", 
                             total_arbs=arbs, 
                             total_alertas=alertas_count)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Servidor rodando em http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
