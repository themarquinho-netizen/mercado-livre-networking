
import json
from datetime import datetime
from pathlib import Path


def registrar_auditoria(
    equipamento,
    acao,
    status,
    detalhes=""
):
    pasta = Path("logs")
    pasta.mkdir(parents=True, exist_ok=True)

    arquivo = pasta / "auditoria.jsonl"

    registro = {
        "data": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "equipamento": equipamento,
        "acao": acao,
        "status": status,
        "detalhes": detalhes,
    }

    with arquivo.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(registro, ensure_ascii=False) + "\n"
        )

    return registro
