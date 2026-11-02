
from collections import Counter


def calcular_indicadores(registros):
    contagem = Counter(
        str(registro.get("status", "")).upper()
        for registro in registros
    )

    return {
        "total": len(registros),
        "sucessos": contagem["SUCESSO"],
        "falhas": contagem["FALHA"],
        "simulacoes": contagem["SIMULADO"],
    }
