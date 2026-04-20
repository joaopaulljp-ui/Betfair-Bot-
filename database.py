 Classe Alerta   Alerta(DB.Modelo):
 __nome de tabuleiro__ = "Alertas"
    
 ID = DB. Coluna(DB.Integrista, primário_chave=É verdade.)
 tipo = db. Coluna(DB.Corda(50), anulável=Falso.)  # arb, valor, etc
       mensagem = db.   Coluna(DB.Texto, anulável=Falso.)
    
     # Informações do jogo # Informações do jogo
       esporte = db.  Coluna(DB.Corda(100))  # Futebol, Basquete, etc Column(db.String(100))  # Futebol, Basquete, etc
       jogo = db.  Coluna(DB.Corda(200))  # Time A vs Time B Column(db.String(200))  # Time A vs Time B
 Liga = dB. Coluna(DB.Corda(100))  # Campeonato Column(db.String(100))  # Campeonato
    
     # Arbitragem # Arbitragem
      margem = db.  Coluna(DB.Flutuação)
 lucro_potencial = db. Coluna(DB.Flutuação)
    
     # Casas de apostas envolvidas # Casas de apostas envolvidas
 Casa1 = db. Coluna(DB.Corda(100))
 ODD1 = DB. Coluna(DB.Flutuação)
 Resultado1 = db. Coluna(DB.Corda(100))  # tempo a, tempo b, desenho
 Link1 = db. Coluna(DB.Corda(500))  # Link direto para aposta
    
 Casa2 = db. Coluna(DB.Corda(100))
 ODD2 = dB. Coluna(DB.Flutuação)
 Resultado2 = db. Coluna(DB.Corda(100))
 Link2 = db. Coluna(DB.Corda(500))
    
    # estado
 data_criacao = db. Coluna(DB.DataTempo, default=datetime.Mas   agora.   agora.)
      enviado_telegram = db.  Coluna(DB.Booleano, padrão=Falso.)
    
 DEF To_Dict(Eu.):
         Retorno  {
            "ID": Eu.ID,
            "Tipo": Eu.Tipo,
             "esporte": Eu.esporte,  "esporte": Eu.esporte,
             "Jogo": Eu.jogo,  "Jogo": Eu.jogo,
            "Liga": Eu.liga,
             "mensagem": Eu.mensagem,  "mensagem": Eu.mensagem,
             "Margem": Eu.margem,  "Margem": Eu.margem,
            "Lucro": Eu.lucro_potencial,
             "casa1": Eu.Casa1,  "casa1": Eu.Casa1,
            "Estranho1": Eu.ímpar1,
             "Resultado1": Eu.Resultado1,  "Resultado1": Eu.Resultado1,
            "Link1": Eu.Ligação1,
             "casa2": Eu.Casa2,  "casa2": Eu.Casa2,
            "Odd2": Eu.ímpar2,
             "Resultado2": Eu.Resultado2,  "Resultado2": Eu.Resultado2,
            "Link2": Eu.Ligação2,
            "Dados": Eu.Data_Criacao.tempo  de força de  força("% D/% M/% Y (% H):% M:%S")  Se... Eu.Data_Criacao  Mais?  "",
             "enviado_telegram": Eu.enviado_telegram "enviado_telegram": Eu.enviado_telegram
        }
ClasseMaisdede          ?  (DB. Modelo)  :    Arbitragem(DB.Modelo):
  __nome de tabuleiro__ =  "arbitrages" "arbitrages"
    
 ID = DB. Coluna (DB. Integro, primário_chave=verdadeiro) Column(DB.Integer, primário_chave=True)
      esporte = db. Column(DB.String(100)) Column(DB.String(100))
  jogo = db.  Coluna (DB. Corda (200), anulável = falso) Column(DB.String(200), anulável=False)
 Liga = dB. Coluna (DB. Corda (100)) Column(DB.String(100))
    
     # Melhores odds # Melhores odds
 Casa1 = db. Coluna (DB. Corda (100)) Column(DB.String(100))
 Resultado1 = db. Coluna (DB. Corda (100)) Column(DB.String(100))
 ODD1 = DB. Coluna (DB. Flutuação) Column(DB.Float)
 Link1 = db. Coluna (DB. Corda (500)) Column(DB.String(500))
    
 Casa2 = db. Coluna (DB. Corda (100)) Column(DB.String(100))
 Resultado2 = db. Coluna (DB. Corda (100)) Column(DB.String(100))
 ODD2 = dB. Coluna (DB. Flutuação) Column(DB.Float)
 Link2 = db. Coluna (DB. Corda (500)) Column(DB.String(500))
    
 # lucro # Lucro
  margem = db.  Coluna (DB. Flutuante, nulo = falso) Column(DB.Float, anulável=False)
 lucro_potencial = db. Coluna (DB. Flutuação) Column(DB.Float)
    
 # estado # Status
 data_deteccao = db. Coluna (DB. Data Tempo, padrão=tempo.utcnow) Column(DB.DateTime, default=datetime.utcnow)
 Status = dB. Coluna (DB. String(50), padrão="pendente") Column(DB.String(50), padrão="pendente")
    
 Def. to_Dict (Eu.):  to_Dict (Eu.):  def to_dict(Eu.):
 Retorno return {
 "ID": Auto.id,  "id": Eu.id,
             "esporte": Eu.esporte,  "esporte": Eu.esporte,
             "Jogo": Eu.jogo,  "jogo": Eu.jogo,
 "Liga": Eu.Liga,  "liga": Eu.liga,
             "casa1": Eu.casa1,  "casa1": Eu.casa1,
             "Resultado1": Eu.resultado1,  "resultado1": Eu.resultado1,
 "ODD1": Eu.Odd1,  "odd1": Eu.odd1,
 "Link1": Eu.Link1,  "link1": Eu.link1,
             "casa2": Eu.casa2,  "casa2": Eu.casa2,
             "Resultado2": Eu.resultado2,  "resultado2": Eu.resultado2,
 "ODD2": Eu.Odd2,  "odd2": Eu.odd2,
 "Link2": Eu.Link2,  "link2": Eu.link2,
             "Margem": Eu.margem,  "margem": Eu.margem,
 "Lucro": Eu.lucro_potencial,  "lucro": Eu.lucro_potencial,
 "dados": Eu.data_deteccao.strftime("%d/%m/%Y %H:%M:%S") Veja a si mesmo.data_deteccao else "",  "data": Eu.data_deteccao.strftime("%d/%m/%Y %H:%M:%S") if Eu.data_deteccao else "",
 "Status": Eu.Status "status": Eu.status
        }
