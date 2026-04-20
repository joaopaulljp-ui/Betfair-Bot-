from decimal import Decimal

class OddsCalculator:
    @staticmethod
    def calcular_margem(odds_dict):
        try:
            if len(odds_dict) < 2:
                return None
            soma_inversa = sum(Decimal(1) / Decimal(str(odd)) for odd in odds_dict.values())
            margem = (float(soma_inversa) - 1) * 100
            return margem
        except Exception as e:
            print(f"Erro ao calcular margem: {e}")
            return None
    
    @staticmethod
    def encontrar_melhor_odd(outcomes_dict):
        best = {}
        for outcome, casas in outcomes_dict.items():
            if casas:
                melhor_casa = max(casas.items(), key=lambda x: x[1])
                best[outcome] = melhor_casa
        return best
    
    @staticmethod
    def calcular_lucro_potencial(stake, odds_list):
        try:
            margem_inversa = sum(1 / odd for odd in odds_list)
            if margem_inversa >= 1:
                return 0
            lucro = stake * (1 - margem_inversa)
            return round(lucro, 2)
        except:
            return 0
    
    @staticmethod
    def distribuir_stake(bankroll, odds_list):
        try:
            stakes = []
            for odd in odds_list:
                stake = bankroll / sum(1/o for o in odds_list) / odd
                stakes.append(round(stake, 2))
            return stakes
        except:
            return None
