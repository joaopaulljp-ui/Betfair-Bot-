from datetime import datetime
from database import db, Alert, Arbitrage, Statistics
from arbitrage.calculator import OddsCalculator
from config import Config

class ArbitrageDetector:
    MIN_MARGIN = -2.0
    
    @staticmethod
    def gerar_link_aposta(casa, resultado, evento_id=None):
        """Gera link direto para a aposta na casa"""
        try:
            casa_lower = casa.lower()
            
            if "bet365" in casa_lower:
                return f"{Config.BOOKMAKERS['bet365']['url_base']}/sports"
            elif "betano" in casa_lower:
                return f"{Config.BOOKMAKERS['betano']['url_base']}"
            elif "sportingbet" in casa_lower:
                return f"{Config.BOOKMAKERS['sportingbet']['url_base']}"
            elif "rivalo" in casa_lower:
                return f"{Config.BOOKMAKERS['rivalo']['url_base']}"
            elif "1xbet" in casa_lower:
                return f"{Config.BOOKMAKERS['1xbet']['url_base']}"
            elif "superbet" in casa_lower:
                return f"{Config.BOOKMAKERS['superbet']['url_base']}"
            elif "7kbet" in casa_lower or "7k" in casa_lower:
                return f"{Config.BOOKMAKERS['7kbet']['url_base']}"
            elif "vaidebet" in casa_lower or "vai de" in casa_lower:
                return f"{Config.BOOKMAKERS['vaidebet']['url_base']}"
            
            return None
        except Exception as e:
            print(f"Erro ao gerar link: {e}")
            return None
    
    @staticmethod
    def filtrar_casas_brasil(bookmakers_list):
        """Filtra apenas casas que operam no Brasil"""
        casas_brasil = []
        casas_config = Config.BOOKMAKERS
        
        for bookmaker in bookmakers_list:
            casa = bookmaker.get('title', '').lower()
            
            for chave, info in casas_config.items():
                if chave in casa or info['nome'].lower() in casa:
                    if info['operando_brasil']:
                        casas_brasil.append(bookmaker)
                        break
        
        return casas_brasil
    
    @staticmethod
    def processar_jogo(game_data):
        """Processa um jogo e detecta arbitragens (apenas casas Brasil)"""
        try:
            game_id = game_data.get('id')
            home = game_data.get('home_team', 'Time A')
            away = game_data.get('away_team', 'Time B')
            sport_key = game_data.get('sport_key', 'soccer')
            league_title = game_data.get('league_title', 'Liga')
            nome_jogo = f"{home} x {away}"
            
            bookmakers = ArbitrageDetector.filtrar_casas_brasil(
                game_data.get('bookmakers', [])
            )
            
            if len(bookmakers) < 2:
                return None
            
            outcomes_dict = {}
            
            for bookmaker in bookmakers:
                casa = bookmaker.get('title', 'Desconhecida')
                
                for market in bookmaker.get('markets', []):
                    if market.get('key') != 'h2h':
                        continue
                    
                    for outcome in market.get('outcomes', []):
                        resultado = outcome.get('name', '')
                        odd = float(outcome.get('price', 0))
                        link = ArbitrageDetector.gerar_link_aposta(casa, resultado)
                        
                        if resultado not in outcomes_dict:
                            outcomes_dict[resultado] = {}
                        
                        outcomes_dict[resultado][casa] = {
                            'odd': odd,
                            'link': link,
                            'resultado': resultado
                        }
            
            if len(outcomes_dict) < 2:
                return None
            
            melhores = {}
            for outcome, casas in outcomes_dict.items():
                if casas:
                    melhor_casa = max(casas.items(), key=lambda x: x[1]['odd'])
                    melhores[outcome] = melhor_casa
            
            if len(melhores) < 2:
                return None
            
            odds_list = [info[1]['odd'] for info in melhores.values()]
            
            margem = OddsCalculator.calcular_margem({info[1]['odd'] for info in melhores.values()})
            
            if margem is None or margem >= ArbitrageDetector.MIN_MARGIN:
                return None
            
            lucro = OddsCalculator.calcular_lucro_potencial(200, odds_list)
            
            melhores_items = list(melhores.items())
            resultado1_nome, (casa1, info1) = melhores_items[0]
            resultado2_nome, (casa2, info2) = melhores_items[1] if len(melhores_items) > 1 else (None, (None, None))
            
            msg = f"""
🚨 ARBITRAGEM DETECTADA!
📊 {nome_jogo}
🏆 {league_title}
📈 Margem: {margem:.2f}%
💰 Lucro potencial: R$ {lucro:.2f}

🏢 Casas do Brasil:
✅ {casa1}: {info1['odd']} em {resultado1_nome}
✅ {casa2}: {info2['odd']} em {resultado2_nome}
"""
            
            arb = Arbitrage(
                esporte=sport_key,
                jogo=nome_jogo,
                liga=league_title,
                casa1=casa1,
                resultado1=resultado1_nome,
                odd1=info1['odd'],
                link1=info1['link'],
                casa2=casa2,
                resultado2=resultado2_nome,
                odd2=info2['odd'],
                link2=info2['link'],
                margem=abs(margem),
                lucro_potencial=lucro
            )
            db.session.add(arb)
            
            alert = Alert(
                tipo='arb',
                esporte=sport_key,
                liga=league_title,
                mensagem=msg,
                jogo=nome_jogo,
                margem=abs(margem),
                lucro_potencial=lucro,
                casa1=casa1,
                resultado1=resultado1_nome,
                odd1=info1['odd'],
                link1=info1['link'],
                casa2=casa2,
                resultado2=resultado2_nome,
                odd2=info2['odd'],
                link2=info2['link']
            )
            db.session.add(alert)
            db.session.commit()
            
            return {
                'tipo': 'arb',
                'mensagem': msg,
                'margem': abs(margem),
                'lucro': lucro,
                'link1': info1['link'],
                'link2': info2['link']
            }
        
        except Exception as e:
            print(f"Erro ao processar jogo: {e}")
            return None
