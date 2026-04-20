import  os
from dotenv import load_dotenv

load_dotenv()

class  Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///betfair_bot.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
    BANKROLL = float(os.environ.get("BANKROLL", "200"))
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
    SCRAPER_TIMEOUT = 30
    MIN_MARGIN = 2.0
    
    # ✅ APENAS CASAS QUE OPERAM NO BRASIL
    BOOKMAKERS = {
        "bet365": {
            "nome": "Bet365",
            "url_base": "https://www.bet365.com.br",
            "operando_brasil": True
        },
        "betano": {
            "nome": "Betano",
            "url_base": "https://www.betano.com.br",
            "operando_brasil": True
        },
        "sportingbet": {
            "nome": "Sportingbet",
            "url_base": "https://www.sportingbet.com.br",
            "operando_brasil": True
        },
        "rivalo": {
            "nome": "Rivalo",
            "url_base": "https://www.rivalo.com.br",
            "operando_brasil": True
        },
        "1xbet": {
            "nome": "1xBet",
            "url_base": "https://www.1xbet.com.br",
            "operando_brasil": True
        },
        "superbet": {
            "nome": "Superbet",
            "url_base": "https://www.superbet.com.br",
            "operando_brasil": True
        },
        "7kbet": {
            "nome": "7K Bet",
            "url_base": "https://www.7kbet.com.br",
            "operando_brasil": True
        },
        "vaidebet": {
            "nome": "Vai de Bet",
            "url_base": "https://www.vaidebet.com.br",
            "operando_brasil": True
        }
    }
    
    # ✅ ESPORTES INTERNACIONAIS (todos disponíveis)
    SPORTS = {
        "soccer": "Futebol",
        "basketball": "Basquete",
        "americanfootball": "Futebol Americano",
        "baseball": "Beisebol",
        "ice_hockey": "Hóquei no Gelo",
        "tennis": "Tênis"
    }
