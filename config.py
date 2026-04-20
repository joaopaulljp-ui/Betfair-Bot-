import os
from dotenv import load_dotenv

load_dotenv()

class Config:
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
    BOOKMAKERS = [
        "bet365", "betano", "sportingbet", "rivalo", "1xbet",
        "superbet", "7kbet", "vaidebet"
    ]
