from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Alert(db.Model):
    __tablename__ = "alerts"
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    esporte = db.Column(db.String(100))
    jogo = db.Column(db.String(200))
    liga = db.Column(db.String(100))
    margem = db.Column(db.Float)
    lucro_potencial = db.Column(db.Float)
    casa1 = db.Column(db.String(100))
    odd1 = db.Column(db.Float)
    resultado1 = db.Column(db.String(100))
    link1 = db.Column(db.String(500))
    casa2 = db.Column(db.String(100))
    odd2 = db.Column(db.Float)
    resultado2 = db.Column(db.String(100))
    link2 = db.Column(db.String(500))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    enviado_telegram = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "esporte": self.esporte,
            "jogo": self.jogo,
            "liga": self.liga,
            "mensagem": self.mensagem,
            "margem": self.margem,
            "lucro": self.lucro_potencial,
            "casa1": self.casa1,
            "odd1": self.odd1,
            "resultado1": self.resultado1,
            "link1": self.link1,
            "casa2": self.casa2,
            "odd2": self.odd2,
            "resultado2": self.resultado2,
            "link2": self.link2,
            "data": self.data_criacao.strftime("%d/%m/%Y %H:%M:%S") if self.data_criacao else "",
            "enviado_telegram": self.enviado_telegram
        }

class Arbitrage(db.Model):
    __tablename__ = "arbitrages"
    
    id = db.Column(db.Integer, primary_key=True)
    esporte = db.Column(db.String(100))
    jogo = db.Column(db.String(200), nullable=False)
    liga = db.Column(db.String(100))
    casa1 = db.Column(db.String(100))
    resultado1 = db.Column(db.String(100))
    odd1 = db.Column(db.Float)
    link1 = db.Column(db.String(500))
    casa2 = db.Column(db.String(100))
    resultado2 = db.Column(db.String(100))
    odd2 = db.Column(db.Float)
    link2 = db.Column(db.String(500))
    margem = db.Column(db.Float, nullable=False)
    lucro_potencial = db.Column(db.Float)
    data_deteccao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="pendente")
    
    def to_dict(self):
        return {
            "id": self.id,
            "esporte": self.esporte,
            "jogo": self.jogo,
            "liga": self.liga,
            "casa1": self.casa1,
            "resultado1": self.resultado1,
            "odd1": self.odd1,
            "link1": self.link1,
            "casa2": self.casa2,
            "resultado2": self.resultado2,
            "odd2": self.odd2,
            "link2": self.link2,
            "margem": self.margem,
            "lucro": self.lucro_potencial,
            "data": self.data_deteccao.strftime("%d/%m/%Y %H:%M:%S") if self.data_deteccao else "",
            "status": self.status
        }

class Statistics(db.Model):
    __tablename__ = "statistics"
    
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, default=datetime.utcnow)
    arbitragens_detectadas = db.Column(db.Integer, default=0)
    alertas_cartoes = db.Column(db.Integer, default=0)
    alertas_valor = db.Column(db.Integer, default=0)
    odds_erradas = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            "data": self.data.strftime("%d/%m/%Y"),
            "arbitragens": self.arbitragens_detectadas,
            "cartoes": self.alertas_cartoes,
            "valor": self.alertas_valor,
            "odds_erradas": self.odds_erradas
        }
