from datetime import datetime
from database import db, Alert, Arbitrage, Statistics
from arbitrage.calculator import OddsCalculator

class ArbitrageDetector:
    MIN_MARGIN = -2.0
    
    @staticmethod
    def processar_jogo(game_data):
        try:
            game_id = game_data.get('id')
            home = game_data.get('home_team', 'Time A')
            away = game_data.get('away_team', 'Time B')
            nome_jogo = f"{home} x {away}"
            
            outcomes_dict = {}
            
            for bookmaker in game_data.get('bookmakers', []):
                casa = bookmaker.get('title', 'Desconhecida')
                
                for market in bookmaker.get('markets', []):
                    if market.get('key') != 'h2h':
                        continue
                    
                    for outcome in market.get('outcomes', []):
                        resultado = outcome.get('name', '')
                        odd = float(outcome.get('price', 0))
                        
                        if resultado not in outcomes_dict:
                            outcomes_dict[resultado] = {}
                        
                        outcomes_dict[resultado][casa] = odd
            
            if len(outcomes_dict) < 2:
                return None
            
            melhores = OddsCalculator.encontrar_melhor_odd(outcomes_dict)
            
            if len(melhores) < 2:
                return None
            
            odds_list = [odd for casa, odd in melhores.values()]
            
            margem = OddsCalculator.calcular_margem({casa: odd for casa, odd in melhores.values()})
            
            if margem is None or margem >= ArbitrageDetector.MIN_MARGIN:
                return None
            
            lucro = OddsCalculator.calcular_lucro_potencial(200, odds_list)
            
            msg = f"""
🚨 ARBITRAGEM DETECTADA!
📊 {nome_jogo}
📈 Margem: {margem:.2f}%
💰 Lucro potencial: R$ {lucro:.2f}
"""
            
            for resultado, (casa, odd) in melhores.items():
                msg += f"\n✅ {resultado}: {casa} @ {odd}"
            
            arb = Arbitrage(
                jogo=nome_jogo,
                odds={casa: odd for casa, odd in melhores.values()},
                margem=abs(margem),
                lucro_potencial=lucro
            )
            db.session.add(arb)
            
            alert = Alert(
                tipo='arb',
                mensagem=msg,
                jogo=nome_jogo,
                margem=abs(margem)
            )
            db.session.add(alert)
            db.session.commit()
            
            return {
                'tipo': 'arb',
                'mensagem': msg,
                'margem': abs(margem),
                'lucro': lucro
            }
        
        except Exception as e:
            print(f"Erro ao processar jogo: {e}")
            return None
