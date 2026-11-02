
import re
from pathlib import Path
from datetime import datetime


def extrair_vlans(texto):
    vlans = {}

    for linha in texto.splitlines():
        resultado = re.match(
            r"^\s*(\d+)\s+(\S+)\s+(active|act/unsup)\b",
            linha
        )

        if resultado:
            vlan_id = int(resultado.group(1))
            nome = resultado.group(2)

            vlans[vlan_id] = nome

    return vlans


def comparar_vlans(antes, depois):
    vlans_antes = extrair_vlans(antes)
    vlans_depois = extrair_vlans(depois)

    resultado = []

    for vlan_id in sorted(set(vlans_antes) | set(vlans_depois)):
        nome_antes = vlans_antes.get(vlan_id)
        nome_depois = vlans_depois.get(vlan_id)

        if nome_antes is None:
            status = "CRIADA"
        elif nome_depois is None:
            status = "REMOVIDA"
        elif nome_antes != nome_depois:
            status = "RENOMEADA"
        else:
            status = "MANTIDA"

        resultado.append(
            f"VLAN {vlan_id}: "
            f"{nome_antes or '-'} -> {nome_depois or '-'} "
            f"| {status}"
        )

    return resultado


def gerar_relatorio(antes, depois, equipamento):
    linhas = comparar_vlans(antes, depois)

    pasta = Path("backups") / "relatorios"
    pasta.mkdir(parents=True, exist_ok=True)

    data = datetime.now().strftime("%Y%m%d_%H%M%S")

    arquivo = pasta / f"relatorio_vlans_{data}.txt"

    conteudo = (
        "RELATORIO DE COMPARACAO DE VLANS\n"
        f"Equipamento: {equipamento}\n"
        f"Data: {datetime.now():%d/%m/%Y %H:%M:%S}\n\n"
        + "\n".join(linhas)
        + "\n"
    )

    arquivo.write_text(conteudo, encoding="utf-8")

    return arquivo
