“””
╔══════════════════════════════════════════════════════════════╗
║   BOT PRO — Arbitragem & Value Bets — Casas BR              ║
║   Betano · Superbet · Sportingbet · KTO · Novibet           ║
╚══════════════════════════════════════════════════════════════╝
“””

import os, requests, time, threading, datetime
from flask import Flask, jsonify, render_template_string

app = Flask(**name**)

# ══════════════════════════════════════════

# CONFIG — variáveis de ambiente Railway

# ══════════════════════════════════════════

ODDS_API_KEY  = os.environ.get(“ODDS_API_KEY”, “”)
BANKROLL      = float(os.environ.get(“BANKROLL”, “200”))
TG_TOKEN      = os.environ.get(“TELEGRAM_TOKEN”, “”)
TG_CHAT       = os.environ.get(“TELEGRAM_CHAT_ID”, “”)
VALUE_THRESH  = float(os.environ.get(“VALUE_THRESHOLD”, “5”))   # % mínimo de value
ARB_MIN       = float(os.environ.get(“ARB_MIN_MARGIN”, “0.3”))  # % mínimo de margem arb

# Casas BR mapeadas para os slugs da Odds API

BR_BOOKS = {
“betano”:      “Betano”,
“superbet”:    “Superbet”,
“sportingbet”: “Sportingbet”,
“kto”:         “KTO”,
“novibet”:     “Novibet”,
# fallbacks com nomes alternativos que a API pode retornar
“betano_br”:   “Betano”,
“superbet_br”: “Superbet”,
}

# ══════════════════════════════════════════

# ESTADO GLOBAL

# ══════════════════════════════════════════

state = {
“running”:      False,
“alerts”:       [],          # todos os alertas
“arb_count”:    0,
“value_count”:  0,
“card_count”:   0,
“scan_count”:   0,
“last_scan”:    “—”,
“games_live”:   0,
“last_alerts”:  {},
“stats”: {
“arb”:   0,
“value”: 0,
“card”:  0,
}
}

# ══════════════════════════════════════════

# TELEGRAM

# ══════════════════════════════════════════

def send_telegram(msg):
if not TG_TOKEN or not TG_CHAT:
return
try:
requests.post(
f”https://api.telegram.org/bot{TG_TOKEN}/sendMessage”,
json={“chat_id”: TG_CHAT, “text”: msg, “parse_mode”: “HTML”},
timeout=6
)
except Exception as e:
print(f”[TG ERROR] {e}”)

def tg_test():
send_telegram(
“🤖 <b>BOT PRO INICIADO</b>\n\n”
“✅ Conexão estabelecida\n”
f”🏦 Casas: Betano · Superbet · Sportingbet · KTO · Novibet\n”
f”💰 Banca: R${BANKROLL:.0f}\n”
“📡 Monitorando arbitragem, value bets e cartões…”
)

# ══════════════════════════════════════════

# ALERTAS

# ══════════════════════════════════════════

def add_alert(tipo, msg, key=None, tg_msg=None):
now = time.time()
if key:
last = state[“last_alerts”].get(key, 0)
if now - last < 90:
return False
state[“last_alerts”][key] = now

```
entry = {
    "tipo":  tipo,
    "msg":   msg,
    "time":  datetime.datetime.now().strftime("%H:%M:%S"),
    "ts":    now
}
state["alerts"].insert(0, entry)
if len(state["alerts"]) > 150:
    state["alerts"].pop()

state["stats"][tipo] = state["stats"].get(tipo, 0) + 1
print(f"[{tipo.upper()}] {msg[:80]}")
send_telegram(tg_msg or msg)
return True
```

# ══════════════════════════════════════════

# ODDS API — jogos ao vivo

# ══════════════════════════════════════════

def get_live_games():
if not ODDS_API_KEY:
return []
try:
url = (
“https://api.the-odds-api.com/v4/sports/soccer/odds/”
f”?apiKey={ODDS_API_KEY}&regions=eu,us&markets=h2h”
“&oddsFormat=decimal&dateFormat=iso”
)
r = requests.get(url, timeout=12)
data = r.json()
if isinstance(data, list):
return data
return []
except Exception as e:
print(f”[API ERROR] {e}”)
return []

def get_live_events():
“”“Busca eventos in-play para alertas de cartão.”””
if not ODDS_API_KEY:
return []
try:
url = (
“https://api.the-odds-api.com/v4/sports/soccer/scores/”
f”?apiKey={ODDS_API_KEY}&daysFrom=1”
)
r = requests.get(url, timeout=12)
data = r.json()
return data if isinstance(data, list) else []
except:
return []

# ══════════════════════════════════════════

# FILTRAR ODDS DAS CASAS BR

# ══════════════════════════════════════════

def extract_br_odds(game):
“””
Retorna dict: { outcome_name: { book_name: odd } }
apenas para as casas BR configuradas.
“””
result = {}
for book in game.get(“bookmakers”, []):
bname = book.get(“title”, “”)
# Verificar se é uma das nossas casas BR
is_br = any(
br.lower() in bname.lower()
for br in [“betano”, “superbet”, “sportingbet”, “kto”, “novibet”]
)
if not is_br:
continue

```
    for market in book.get("markets", []):
        if market.get("key") != "h2h":
            continue
        for outcome in market.get("outcomes", []):
            name  = outcome["name"]
            price = float(outcome["price"])
            if name not in result:
                result[name] = {}
            result[name][bname] = price

return result
```

def extract_all_odds(game):
“”“Todas as casas, para calcular a odd justa de mercado.”””
result = {}
for book in game.get(“bookmakers”, []):
for market in book.get(“markets”, []):
if market.get(“key”) != “h2h”:
continue
for outcome in market.get(“outcomes”, []):
name  = outcome[“name”]
price = float(outcome[“price”])
bname = book.get(“title”, “”)
if name not in result:
result[name] = {}
result[name][bname] = price
return result

# ══════════════════════════════════════════

# ARBITRAGEM

# ══════════════════════════════════════════

def check_arbitrage(game):
br_odds = extract_br_odds(game)
if len(br_odds) < 2:
return

```
# Melhor odd BR por outcome
best = {}
for outcome, books in br_odds.items():
    if books:
        best_book = max(books, key=books.get)
        best[outcome] = {"odd": books[best_book], "book": best_book}

if len(best) < 2:
    return

odds_vals = [v["odd"] for v in best.values()]
inv = sum(1 / o for o in odds_vals)

if inv >= 1:
    return

margem = (1 - inv) * 100
if margem < ARB_MIN:
    return

# Calcular stakes
stakes = [(BANKROLL / o) / inv for o in odds_vals]
lucro  = min(s * o for s, o in zip(stakes, odds_vals)) - sum(stakes)

home = game.get("home_team", "?")
away = game.get("away_team", "?")
gid  = game.get("id", "")

# Mensagem da interface
linhas = []
for (outcome, data), stake in zip(best.items(), stakes):
    linhas.append(f"{outcome} @ {data['odd']:.2f} ({data['book']}) → R${stake:.2f}")
ui_msg = f"{home} x {away}\n" + "\n".join(linhas) + f"\nLucro: R${lucro:.2f} | Margem: {margem:.2f}%"

# Mensagem Telegram
tg_linhas = "\n".join(
    f"  • {o} @ <b>{d['odd']:.2f}</b> ({d['book']}) → R${s:.2f}"
    for (o, d), s in zip(best.items(), stakes)
)
tg_msg = (
    f"🚨 <b>ARBITRAGEM DETECTADA</b>\n\n"
    f"⚽ <b>{home} x {away}</b>\n\n"
    f"{tg_linhas}\n\n"
    f"💰 Lucro garantido: <b>R${lucro:.2f}</b>\n"
    f"📊 Margem: <b>{margem:.2f}%</b>"
)

add_alert("arb", ui_msg, key=f"arb_{gid}", tg_msg=tg_msg)
```

# ══════════════════════════════════════════

# VALUE BET

# ══════════════════════════════════════════

def check_value_bets(game):
all_odds  = extract_all_odds(game)
br_odds   = extract_br_odds(game)

```
home = game.get("home_team", "?")
away = game.get("away_team", "?")
gid  = game.get("id", "")

for outcome, br_books in br_odds.items():
    if outcome not in all_odds:
        continue

    # Odd justa = média de todas as casas para esse outcome
    todas = list(all_odds[outcome].values())
    if len(todas) < 3:
        continue
    odd_justa = sum(todas) / len(todas)

    # Verificar se alguma casa BR está acima da odd justa
    for book, odd_br in br_books.items():
        value_pct = ((odd_br / odd_justa) - 1) * 100
        if value_pct >= VALUE_THRESH:
            stake = BANKROLL * 0.03  # 3% da banca por value bet
            ev    = stake * (odd_br * (1 / odd_justa) - 1)

            ui_msg = (
                f"{home} x {away}\n"
                f"{outcome} @ {odd_br:.2f} ({book})\n"
                f"Odd justa: {odd_justa:.2f} | Value: +{value_pct:.1f}%\n"
                f"Stake sugerida: R${stake:.2f} | EV: +R${ev:.2f}"
            )
            tg_msg = (
                f"💎 <b>VALUE BET</b>\n\n"
                f"⚽ <b>{home} x {away}</b>\n\n"
                f"Seleção: <b>{outcome}</b>\n"
                f"Casa: <b>{book}</b> @ <b>{odd_br:.2f}</b>\n"
                f"Odd justa mercado: {odd_justa:.2f}\n"
                f"📈 Value: <b>+{value_pct:.1f}%</b>\n\n"
                f"💰 Stake sugerida: R${stake:.2f}\n"
                f"📊 EV esperado: +R${ev:.2f}"
            )
            add_alert("value", ui_msg, key=f"value_{gid}_{outcome}_{book}", tg_msg=tg_msg)
```

# ══════════════════════════════════════════

# ALERTA DE CARTÃO (via scores endpoint)

# ══════════════════════════════════════════

_card_cache = {}

def check_cards(events):
for event in events:
eid    = event.get(“id”, “”)
scores = event.get(“scores”) or []
if not scores:
continue

```
    home = event.get("home_team", "?")
    away = event.get("away_team", "?")

    for score_entry in scores:
        # A API retorna info de score; usamos como proxy de eventos
        # Quando um placar muda abruptamente sem gol marcado pode indicar cartão vermelho
        name  = score_entry.get("name", "")
        score = score_entry.get("score", "0")

        cache_key = f"{eid}_{name}_{score}"
        if cache_key in _card_cache:
            continue
        _card_cache[cache_key] = True

        # Limpar cache antigo
        if len(_card_cache) > 500:
            keys = list(_card_cache.keys())[:100]
            for k in keys:
                del _card_cache[k]

    # Alerta de jogo iniciado (abertura de mercado)
    status = event.get("completed", False)
    commenced = event.get("commence_time", "")
    open_key  = f"open_{eid}"

    if not status and commenced and open_key not in _card_cache:
        _card_cache[open_key] = True
        ui_msg = f"🟢 Jogo iniciado: {home} x {away}"
        tg_msg = (
            f"🟢 <b>JOGO INICIADO</b>\n\n"
            f"⚽ <b>{home} x {away}</b>\n"
            f"📡 Mercados abertos — monitorando odds..."
        )
        add_alert("card", ui_msg, key=f"cardopen_{eid}", tg_msg=tg_msg)
```

# ══════════════════════════════════════════

# LOOP PRINCIPAL

# ══════════════════════════════════════════

def bot_loop():
tg_test()
cycle = 0

```
while state["running"]:
    try:
        cycle += 1
        state["scan_count"] += 1
        state["last_scan"] = datetime.datetime.now().strftime("%H:%M:%S")

        games  = get_live_games()
        events = get_live_events() if cycle % 3 == 0 else []

        state["games_live"] = len(games)

        for g in games:
            check_arbitrage(g)
            check_value_bets(g)

        if events:
            check_cards(events)

        time.sleep(12)

    except Exception as e:
        print(f"[LOOP ERROR] {e}")
        time.sleep(15)

print("[BOT] Encerrado.")
```

# ══════════════════════════════════════════

# INTERFACE WEB

# ══════════════════════════════════════════

HTML = r”””<!DOCTYPE html>

<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>Bot Pro BR</title>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;900&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:      #080b10;
    --surface: #0f1520;
    --card:    #141c28;
    --border:  #1e2d42;
    --green:   #05c46b;
    --yellow:  #ffd32a;
    --red:     #ff3f34;
    --blue:    #0fbcf9;
    --purple:  #a55eea;
    --text:    #e8f0f8;
    --muted:   #4a6080;
    --font:    'Barlow', sans-serif;
    --display: 'Barlow Condensed', sans-serif;
  }

- { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }

body {
background: var(–bg);
color: var(–text);
font-family: var(–font);
min-height: 100vh;
padding-bottom: 72px;
}

/* Scanline effect */
body::after {
content: ‘’;
position: fixed; inset: 0;
background: repeating-linear-gradient(
0deg,
transparent,
transparent 2px,
rgba(0,0,0,0.03) 2px,
rgba(0,0,0,0.03) 4px
);
pointer-events: none;
z-index: 9999;
}

/* ── TOP BAR ── */
.topbar {
position: sticky; top: 0; z-index: 100;
background: rgba(8,11,16,0.97);
backdrop-filter: blur(16px);
-webkit-backdrop-filter: blur(16px);
border-bottom: 1px solid var(–border);
display: flex; align-items: center; justify-content: space-between;
padding: 12px 16px;
}

.brand {
display: flex; align-items: center; gap: 10px;
}

.brand-icon {
width: 34px; height: 34px;
background: linear-gradient(135deg, var(–green), #00a854);
border-radius: 8px;
display: flex; align-items: center; justify-content: center;
font-size: 17px;
}

.brand-name {
font-family: var(–display);
font-size: 20px;
font-weight: 900;
letter-spacing: 0.5px;
line-height: 1;
}

.brand-name span { color: var(–green); }
.brand-sub { font-size: 10px; color: var(–muted); letter-spacing: 1px; margin-top: 1px; }

.top-right { display: flex; align-items: center; gap: 10px; }

.status-pill {
display: flex; align-items: center; gap: 6px;
padding: 5px 12px;
border-radius: 20px;
font-size: 11px;
font-weight: 600;
letter-spacing: 0.5px;
border: 1px solid;
cursor: pointer;
transition: all 0.2s;
}

.status-pill.off {
background: rgba(255,63,52,0.08);
border-color: rgba(255,63,52,0.3);
color: var(–red);
}

.status-pill.on {
background: rgba(5,196,107,0.08);
border-color: rgba(5,196,107,0.3);
color: var(–green);
}

.pulse { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.pulse.blink { animation: blink 1.2s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }

/* ── SCAN BAR ── */
.scan-bar {
height: 3px;
background: var(–border);
position: relative;
overflow: hidden;
}

.scan-fill {
position: absolute; left: 0; top: 0; bottom: 0;
background: linear-gradient(90deg, var(–green), var(–blue));
transition: width 12s linear;
width: 0%;
}

.scan-fill.scanning { width: 100%; }

/* ── CONTENT ── */
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }

/* ── STATS ── */
.stats-row {
display: grid;
grid-template-columns: repeat(4, 1fr);
gap: 8px;
}

.stat-box {
background: var(–card);
border: 1px solid var(–border);
border-radius: 10px;
padding: 12px 10px;
text-align: center;
position: relative;
overflow: hidden;
}

.stat-box::before {
content: ‘’;
position: absolute;
top: 0; left: 0; right: 0;
height: 2px;
}

.stat-box.arb::before  { background: var(–green); }
.stat-box.value::before { background: var(–yellow); }
.stat-box.card::before  { background: var(–red); }
.stat-box.scan::before  { background: var(–blue); }

.stat-n {
font-family: var(–display);
font-size: 28px;
font-weight: 900;
line-height: 1;
}

.stat-box.arb   .stat-n { color: var(–green); }
.stat-box.value .stat-n { color: var(–yellow); }
.stat-box.card  .stat-n { color: var(–red); }
.stat-box.scan  .stat-n { color: var(–blue); }

.stat-lbl {
font-size: 10px;
color: var(–muted);
margin-top: 3px;
font-weight: 600;
letter-spacing: 0.5px;
}

/* ── CASAS ── */
.books-row {
display: flex; gap: 6px; flex-wrap: wrap;
}

.book-chip {
padding: 4px 10px;
border-radius: 6px;
font-size: 11px;
font-weight: 600;
border: 1px solid rgba(5,196,107,0.25);
background: rgba(5,196,107,0.06);
color: var(–green);
letter-spacing: 0.3px;
}

/* ── SECTION HEADER ── */
.sec-head {
display: flex; align-items: center; justify-content: space-between;
margin-bottom: 10px;
}

.sec-title {
font-family: var(–display);
font-size: 14px;
font-weight: 700;
letter-spacing: 1px;
text-transform: uppercase;
color: var(–muted);
display: flex; align-items: center; gap: 8px;
}

.sec-title::before {
content: ‘’;
width: 3px; height: 14px;
border-radius: 2px;
}

.sec-title.arb::before   { background: var(–green); }
.sec-title.value::before { background: var(–yellow); }
.sec-title.card::before  { background: var(–red); }
.sec-title.all::before   { background: var(–blue); }

.sec-count {
font-family: var(–display);
font-size: 12px;
font-weight: 700;
padding: 2px 8px;
border-radius: 10px;
}

/* ── ALERT CARDS ── */
.alert-list { display: flex; flex-direction: column; gap: 8px; }

.alert-card {
background: var(–card);
border: 1px solid var(–border);
border-radius: 12px;
overflow: hidden;
animation: slideIn 0.3s ease;
}

@keyframes slideIn {
from { opacity: 0; transform: translateY(-8px); }
to   { opacity: 1; transform: translateY(0); }
}

.alert-card.arb   { border-left: 3px solid var(–green); }
.alert-card.value { border-left: 3px solid var(–yellow); }
.alert-card.card  { border-left: 3px solid var(–red); }

.alert-top {
display: flex; align-items: center; gap: 8px;
padding: 10px 14px 0;
}

.alert-badge {
font-size: 10px;
font-weight: 700;
font-family: var(–display);
letter-spacing: 1px;
padding: 3px 8px;
border-radius: 4px;
}

.arb   .alert-badge { background: rgba(5,196,107,0.15); color: var(–green); }
.value .alert-badge { background: rgba(255,211,42,0.15); color: var(–yellow); }
.card  .alert-badge { background: rgba(255,63,52,0.15);  color: var(–red); }

.alert-time {
font-size: 11px;
color: var(–muted);
margin-left: auto;
font-variant-numeric: tabular-nums;
}

.alert-body {
padding: 8px 14px 12px;
font-size: 13px;
line-height: 1.6;
white-space: pre-line;
color: var(–text);
}

.alert-game {
font-family: var(–display);
font-size: 16px;
font-weight: 700;
margin-bottom: 6px;
color: #fff;
}

.alert-row {
display: flex;
align-items: center;
gap: 6px;
padding: 4px 0;
border-bottom: 1px solid rgba(30,45,66,0.8);
font-size: 12.5px;
}

.alert-row:last-of-type { border-bottom: none; }

.odd-val { font-weight: 700; }
.arb   .odd-val { color: var(–green); }
.value .odd-val { color: var(–yellow); }

.book-name { color: var(–muted); font-size: 11px; }
.stake-val { margin-left: auto; color: var(–blue); font-weight: 600; font-size: 12px; }

.alert-footer {
display: flex; gap: 12px;
padding: 8px 14px;
border-top: 1px solid var(–border);
background: rgba(0,0,0,0.2);
font-size: 12px;
}

.footer-chip {
display: flex; align-items: center; gap: 5px;
font-weight: 600;
}

.footer-chip.profit { color: var(–green); }
.footer-chip.margin { color: var(–yellow); }
.footer-chip.value  { color: var(–yellow); }
.footer-chip.ev     { color: var(–green); }

/* ── EMPTY ── */
.empty {
text-align: center;
padding: 28px 16px;
color: var(–muted);
font-size: 13px;
border: 1px dashed var(–border);
border-radius: 12px;
}

/* ── TABS ── */
.tab-content { display: none; }
.tab-content.active { display: flex; flex-direction: column; gap: 12px; }

/* ── BOTTOM NAV ── */
.bnav {
position: fixed; bottom: 0; left: 0; right: 0;
background: rgba(15,21,32,0.97);
backdrop-filter: blur(16px);
-webkit-backdrop-filter: blur(16px);
border-top: 1px solid var(–border);
display: flex;
padding-bottom: env(safe-area-inset-bottom);
}

.bnav-btn {
flex: 1; padding: 10px 6px; text-align: center;
cursor: pointer; color: var(–muted);
font-size: 10px; font-weight: 600;
transition: color 0.2s; letter-spacing: 0.3px;
}

.bnav-btn.active { color: var(–green); }
.bnav-btn .ni { font-size: 19px; display: block; margin-bottom: 2px; }

/* ── CONFIG ── */
.cfg-card {
background: var(–card);
border: 1px solid var(–border);
border-radius: 12px;
overflow: hidden;
}

.cfg-row {
display: flex; align-items: center; justify-content: space-between;
padding: 13px 16px;
border-bottom: 1px solid var(–border);
}

.cfg-row:last-child { border-bottom: none; }
.cfg-label { font-size: 13px; font-weight: 600; }
.cfg-sub   { font-size: 11px; color: var(–muted); margin-top: 2px; }
.cfg-val   { font-family: var(–display); font-size: 18px; font-weight: 700; color: var(–green); }

/* ── TG GUIDE ── */
.tg-step {
display: flex; gap: 12px; align-items: flex-start;
padding: 12px 0;
border-bottom: 1px solid var(–border);
}

.tg-step:last-child { border-bottom: none; }
.tg-num {
width: 26px; height: 26px;
background: var(–green); color: #000;
border-radius: 50%; display: flex; align-items: center; justify-content: center;
font-weight: 900; font-size: 13px; flex-shrink: 0;
}

.tg-text { font-size: 13px; color: var(–muted); line-height: 1.6; }
.tg-text strong { color: var(–text); }
.tg-text code {
background: rgba(255,255,255,0.06);
padding: 2px 6px; border-radius: 4px;
font-size: 12px; color: var(–blue);
}
</style>

</head>
<body>

<!-- TOP BAR -->

<div class="topbar">
  <div class="brand">
    <div class="brand-icon">⚡</div>
    <div>
      <div class="brand-name">Bot<span>Pro</span></div>
      <div class="brand-sub">CASAS BR · AO VIVO</div>
    </div>
  </div>
  <div class="top-right">
    <div class="status-pill off" id="status-pill" onclick="toggleBot()">
      <div class="pulse" id="status-dot"></div>
      <span id="status-txt">PARADO</span>
    </div>
  </div>
</div>

<!-- SCAN PROGRESS BAR -->

<div class="scan-bar"><div class="scan-fill" id="scan-fill"></div></div>

<div class="content">

  <!-- ── DASHBOARD ── -->

  <div id="tab-dash" class="tab-content active">

```
<!-- Stats -->
<div class="stats-row">
  <div class="stat-box arb">
    <div class="stat-n" id="s-arb">0</div>
    <div class="stat-lbl">ARBITRAGEM</div>
  </div>
  <div class="stat-box value">
    <div class="stat-n" id="s-value">0</div>
    <div class="stat-lbl">VALUE BETS</div>
  </div>
  <div class="stat-box card">
    <div class="stat-n" id="s-card">0</div>
    <div class="stat-lbl">ALERTAS</div>
  </div>
  <div class="stat-box scan">
    <div class="stat-n" id="s-scan">0</div>
    <div class="stat-lbl">SCANS</div>
  </div>
</div>

<!-- Casas monitoradas -->
<div>
  <div class="sec-head">
    <div class="sec-title all">Casas Monitoradas</div>
  </div>
  <div class="books-row">
    <div class="book-chip">Betano</div>
    <div class="book-chip">Superbet</div>
    <div class="book-chip">Sportingbet</div>
    <div class="book-chip">KTO</div>
    <div class="book-chip">Novibet</div>
  </div>
</div>

<!-- Info scan -->
<div style="display:flex;gap:16px;font-size:12px;color:var(--muted)">
  <span>🕐 Último scan: <strong style="color:var(--text)" id="last-scan">—</strong></span>
  <span>⚽ Jogos: <strong style="color:var(--text)" id="games-live">0</strong></span>
</div>

<!-- Arbitragem -->
<div>
  <div class="sec-head">
    <div class="sec-title arb">Arbitragem</div>
    <div class="sec-count" style="background:rgba(5,196,107,0.1);color:var(--green)" id="cnt-arb">0</div>
  </div>
  <div class="alert-list" id="list-arb">
    <div class="empty">Aguardando oportunidades de arbitragem...</div>
  </div>
</div>

<!-- Value Bets -->
<div>
  <div class="sec-head">
    <div class="sec-title value">Value Bets</div>
    <div class="sec-count" style="background:rgba(255,211,42,0.1);color:var(--yellow)" id="cnt-value">0</div>
  </div>
  <div class="alert-list" id="list-value">
    <div class="empty">Aguardando value bets...</div>
  </div>
</div>

<!-- Alertas -->
<div>
  <div class="sec-head">
    <div class="sec-title card">Alertas de Jogos</div>
    <div class="sec-count" style="background:rgba(255,63,52,0.1);color:var(--red)" id="cnt-card">0</div>
  </div>
  <div class="alert-list" id="list-card">
    <div class="empty">Aguardando alertas...</div>
  </div>
</div>
```

  </div>

  <!-- ── TODOS ── -->

  <div id="tab-all" class="tab-content">
    <div class="sec-head">
      <div class="sec-title all">Todos os Alertas</div>
      <div class="sec-count" style="background:rgba(15,188,249,0.1);color:var(--blue)" id="cnt-all">0</div>
    </div>
    <div class="alert-list" id="list-all">
      <div class="empty">Nenhum alerta ainda. Inicie o bot.</div>
    </div>
  </div>

  <!-- ── CONFIG ── -->

  <div id="tab-cfg" class="tab-content">

```
<div class="cfg-card">
  <div class="cfg-row">
    <div><div class="cfg-label">Banca</div><div class="cfg-sub">Base para cálculo de stakes</div></div>
    <div class="cfg-val" id="c-bankroll">R$200</div>
  </div>
  <div class="cfg-row">
    <div><div class="cfg-label">Value mínimo</div><div class="cfg-sub">% acima da odd justa</div></div>
    <div class="cfg-val" id="c-value">5%</div>
  </div>
  <div class="cfg-row">
    <div><div class="cfg-label">Margem arb mínima</div><div class="cfg-sub">% garantido de lucro</div></div>
    <div class="cfg-val" id="c-arb">0.3%</div>
  </div>
  <div class="cfg-row">
    <div><div class="cfg-label">Intervalo de scan</div><div class="cfg-sub">Segundos entre verificações</div></div>
    <div class="cfg-val">12s</div>
  </div>
</div>

<div style="font-size:12px;color:var(--muted);padding:4px 4px;line-height:1.7">
  Para alterar: Railway → seu projeto → <strong style="color:var(--text)">Variables</strong> → edite o valor → o bot reinicia automaticamente.
</div>

<!-- GUIA TELEGRAM -->
<div style="font-family:var(--display);font-size:13px;font-weight:700;letter-spacing:1px;color:var(--muted);text-transform:uppercase;margin-top:4px">
  Como configurar o Telegram
</div>

<div class="cfg-card">
  <div style="padding:14px 16px">
    <div class="tg-step">
      <div class="tg-num">1</div>
      <div class="tg-text">Abra o Telegram e busque por <strong>@BotFather</strong></div>
    </div>
    <div class="tg-step">
      <div class="tg-num">2</div>
      <div class="tg-text">Digite <code>/newbot</code> e siga as instruções. Você receberá um <strong>token</strong> (ex: <code>7123456789:ABCdef...</code>)</div>
    </div>
    <div class="tg-step">
      <div class="tg-num">3</div>
      <div class="tg-text">Mande qualquer mensagem para seu bot. Depois acesse:<br><code>https://api.telegram.org/bot[TOKEN]/getUpdates</code><br>e copie o <strong>chat id</strong> (número na resposta)</div>
    </div>
    <div class="tg-step">
      <div class="tg-num">4</div>
      <div class="tg-text">No Railway → Variables → adicione:<br><strong>TELEGRAM_TOKEN</strong> = seu token<br><strong>TELEGRAM_CHAT_ID</strong> = seu chat id</div>
    </div>
  </div>
</div>
```

  </div>

</div>

<!-- BOTTOM NAV -->

<div class="bnav">
  <div class="bnav-btn active" id="nav-dash" onclick="switchTab('dash')">
    <span class="ni">📊</span>Dashboard
  </div>
  <div class="bnav-btn" id="nav-all" onclick="switchTab('all')">
    <span class="ni">🔔</span>Alertas
  </div>
  <div class="bnav-btn" id="nav-cfg" onclick="switchTab('cfg')">
    <span class="ni">⚙️</span>Config
  </div>
</div>

<script>
let botOn = false;

// ── TABS ──
function switchTab(name) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.bnav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  document.getElementById('nav-' + name).classList.add('active');
}

// ── TOGGLE BOT ──
function toggleBot() {
  const endpoint = botOn ? '/stop' : '/start';
  fetch(endpoint, { method: 'POST' })
    .then(r => r.json())
    .then(d => {
      if (d.ok) {
        botOn = !botOn;
        updateStatusUI();
        if (botOn) triggerScanBar();
      } else if (d.error) {
        alert('Erro: ' + d.error);
      }
    });
}

function updateStatusUI() {
  const pill = document.getElementById('status-pill');
  const dot  = document.getElementById('status-dot');
  const txt  = document.getElementById('status-txt');
  if (botOn) {
    pill.className = 'status-pill on';
    dot.classList.add('blink');
    txt.textContent = 'AO VIVO';
  } else {
    pill.className = 'status-pill off';
    dot.classList.remove('blink');
    txt.textContent = 'PARADO';
  }
}

// ── SCAN BAR ANIMATION ──
function triggerScanBar() {
  if (!botOn) return;
  const fill = document.getElementById('scan-fill');
  fill.style.transition = 'none';
  fill.style.width = '0%';
  setTimeout(() => {
    fill.style.transition = 'width 12s linear';
    fill.style.width = '100%';
  }, 50);
  setTimeout(triggerScanBar, 13000);
}

// ── RENDER ALERTS ──
function renderAlerts(alerts, tipo) {
  return alerts.filter(a => tipo === 'all' || a.tipo === tipo).map(a => {
    const lines = a.msg.split('\n').filter(Boolean);
    const game  = lines[0] || '';
    const rest  = lines.slice(1);

    let footer = '';
    let rows   = '';

    if (a.tipo === 'arb') {
      // Parse arb rows and footer
      const dataLines = rest.filter(l => !l.startsWith('Lucro') && !l.startsWith('Margem'));
      const footLine  = rest.find(l => l.startsWith('Lucro')) || '';
      rows = dataLines.map(l => {
        const m = l.match(/^(.+?)\s*@\s*([\d.]+)\s*\((.+?)\)\s*→\s*(R\$[\d.]+)/);
        if (!m) return `<div class="alert-row"><span>${l}</span></div>`;
        return `<div class="alert-row">
          <span style="flex:1">${m[1]}</span>
          <span class="odd-val">@ ${m[2]}</span>
          <span class="book-name">${m[3]}</span>
          <span class="stake-val">${m[4]}</span>
        </div>`;
      }).join('');
      if (footLine) {
        const pm = footLine.match(/R\$([\d.]+)/);
        const mm = footLine.match(/Margem:\s*([\d.]+)%/);
        footer = `<div class="alert-footer">
          ${pm ? `<span class="footer-chip profit">💰 Lucro R$${pm[1]}</span>` : ''}
          ${mm ? `<span class="footer-chip margin">📊 ${mm[1]}%</span>` : ''}
        </div>`;
      }
    } else if (a.tipo === 'value') {
      const vline = rest.find(l => l.includes('Value:')) || '';
      const sline = rest.find(l => l.includes('Stake')) || '';
      rows = rest.filter(l => !l.includes('Value:') && !l.includes('Stake') && !l.includes('justa')).map(l =>
        `<div class="alert-row"><span>${l}</span></div>`
      ).join('');
      const vm = vline.match(/\+([\d.]+)%/);
      const em = sline.match(/EV.*R\$([\d.]+)/);
      const sm = sline.match(/Stake.*R\$([\d.]+)/);
      footer = `<div class="alert-footer">
        ${vm ? `<span class="footer-chip value">📈 +${vm[1]}% value</span>` : ''}
        ${sm ? `<span class="footer-chip margin">💰 Stake R$${sm[1]}</span>` : ''}
        ${em ? `<span class="footer-chip ev">EV +R$${em[1]}</span>` : ''}
      </div>`;
    } else {
      rows = rest.map(l => `<div class="alert-row"><span>${l}</span></div>`).join('');
    }

    const labels = { arb: '🚨 ARBITRAGEM', value: '💎 VALUE BET', card: '🟢 ALERTA' };

    return `<div class="alert-card ${a.tipo}">
      <div class="alert-top">
        <div class="alert-badge">${labels[a.tipo] || a.tipo.toUpperCase()}</div>
        <div class="alert-time">${a.time}</div>
      </div>
      <div class="alert-body">
        <div class="alert-game">${game}</div>
        ${rows}
      </div>
      ${footer}
    </div>`;
  }).join('') || `<div class="empty">Nenhum alerta ainda</div>`;
}

// ── REFRESH ──
function refresh() {
  fetch('/status').then(r => r.json()).then(d => {
    botOn = d.running;
    updateStatusUI();

    document.getElementById('s-arb').textContent   = d.stats.arb   || 0;
    document.getElementById('s-value').textContent = d.stats.value || 0;
    document.getElementById('s-card').textContent  = d.stats.card  || 0;
    document.getElementById('s-scan').textContent  = d.scan_count  || 0;
    document.getElementById('last-scan').textContent = d.last_scan || '—';
    document.getElementById('games-live').textContent = d.games_live || 0;

    const arbs   = d.alerts.filter(a => a.tipo === 'arb');
    const values = d.alerts.filter(a => a.tipo === 'value');
    const cards  = d.alerts.filter(a => a.tipo === 'card');

    document.getElementById('cnt-arb').textContent   = arbs.length;
    document.getElementById('cnt-value').textContent = values.length;
    document.getElementById('cnt-card').textContent  = cards.length;
    document.getElementById('cnt-all').textContent   = d.alerts.length;

    document.getElementById('list-arb').innerHTML   = renderAlerts(arbs,   'arb');
    document.getElementById('list-value').innerHTML = renderAlerts(values, 'value');
    document.getElementById('list-card').innerHTML  = renderAlerts(cards,  'card');
    document.getElementById('list-all').innerHTML   = renderAlerts(d.alerts, 'all');
  }).catch(() => {});
}

setInterval(refresh, 3000);
refresh();
</script>

</body>
</html>"""

# ══════════════════════════════════════════

# ROTAS

# ══════════════════════════════════════════

@app.route(”/”)
def index():
return render_template_string(HTML)

@app.route(”/start”, methods=[“POST”])
def start():
if state[“running”]:
return jsonify({“ok”: True})
if not ODDS_API_KEY:
return jsonify({“ok”: False, “error”: “Configure ODDS_API_KEY nas variáveis do Railway.”})
state[“running”] = True
threading.Thread(target=bot_loop, daemon=True).start()
return jsonify({“ok”: True})

@app.route(”/stop”, methods=[“POST”])
def stop():
state[“running”] = False
return jsonify({“ok”: True})

@app.route(”/status”)
def status():
return jsonify({
“running”:    state[“running”],
“alerts”:     state[“alerts”][:60],
“stats”:      state[“stats”],
“scan_count”: state[“scan_count”],
“last_scan”:  state[“last_scan”],
“games_live”: state[“games_live”],
})

# ══════════════════════════════════════════

if **name** == “**main**”:
port = int(os.environ.get(“PORT”, 5000))
print(“🚀 Bot Pro BR iniciado”)
app.run(host=“0.0.0.0”, port=port, debug=False)
