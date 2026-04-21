class OddsCalculator:

    @staticmethod
    def calcular_margem(odds):
        try:
            odds_list = list(odds)

            if len(odds_list) < 2:
                return None

            soma_inversa = sum(1 / float(odd) for odd in odds_list)
            margem = (soma_inversa - 1) * 100
            return round(margem, 2)

        except Exception as e:
            print(f"Erro ao calcular margem: {e}")
            return None

    @staticmethod
    def calcular_lucro_potencial(stake, odds_list):
        try:
            margem_inversa = sum(1 / float(o) for o in odds_list)

            if margem_inversa >= 1:
                return 0

            lucro = stake * (1 - margem_inversa)
            return round(lucro, 2)

        except Exception:
            return 0

    @staticmethod
    def distribuir_stake(bankroll, odds_list):
        try:
            total = sum(1 / float(o) for o in odds_list)

            stakes = []
            for odd in odds_list:
                valor = bankroll / total / float(odd)
                stakes.append(round(valor, 2))

            return stakes

        except Exception:
            return None
