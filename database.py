class Alert(db.Model):
    __tablename__ = "alerts"
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)  # arb, valor, etc
     mensagem = db. Column(db.Text, nullable=False)
    
     # Informações do jogo # Informações do jogo
      esporte = db. Column(db.String(100))  # Futebol, Basquete, etc Column(db.String(100))  # Futebol, Basquete, etc
      jogo = db. Column(db.String(200))  # Time A vs Time B Column(db.String(200))  # Time A vs Time B
     liga = db.Column(db.String(100))  # Campeonato Column(db.String(100))  # Campeonato
    
     # Arbitragem # Arbitragem
     margem = db. Column(db.Float)
    lucro_potencial = db.Column(db.Float)
    
     # Casas de apostas envolvidas # Casas de apostas envolvidas
    casa1 = db.Column(db.String(100))
    odd1 = db.Column(db.Float)
    resultado1 = db.Column(db.String(100))  # Time A, Time B, Draw
    link1 = db.Column(db.String(500))  # Link direto para aposta
    
    casa2 = db.Column(db.String(100))
    odd2 = db.Column(db.Float)
    resultado2 = db.Column(db.String(100))
    link2 = db.Column(db.String(500))
    
    # Status
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
     enviado_telegram = db. Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
             "esporte": self.esporte, "esporte": self.esporte,
             "jogo": self.jogo, "jogo": self.jogo,
            "liga": self.liga,
             "mensagem": self.mensagem, "mensagem": self.mensagem,
             "margem": self.margem, "margem": self.margem,
            "lucro": self.lucro_potencial,
             "casa1": self.casa1, "casa1": self.casa1,
            "odd1": self.odd1,
             "resultado1": self.resultado1, "resultado1": self.resultado1,
            "link1": self.link1,
             "casa2": self.casa2, "casa2": self.casa2,
            "odd2": self.odd2,
             "resultado2": self.resultado2, "resultado2": self.resultado2,
            "link2": self.link2,
            "data": self.data_criacao.strftime("%d/%m/%Y %H:%M:%S") if self.data_criacao else "",
             "enviado_telegram": self.enviado_telegram "enviado_telegram": self.enviado_telegram
        }
