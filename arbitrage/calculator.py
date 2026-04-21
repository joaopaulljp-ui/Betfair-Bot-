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
