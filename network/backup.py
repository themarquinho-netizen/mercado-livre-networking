from pathlib import Path
from datetime import datetime
import re


def save_backup(hostname, configuration, output_dir="backups"):
    safe_hostname = re.sub(r"[^a-zA-Z0-9_.-]", "_", hostname)

    if not safe_hostname:
        raise ValueError("Hostname inválido")

    if not configuration or not configuration.strip():
        raise ValueError("Configuração vazia. Backup cancelado.")

    backup_path = Path(output_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    filename = f"{safe_hostname}_{timestamp}.cfg"
    filepath = backup_path / filename

    filepath.write_text(configuration, encoding="utf-8")

    return filepath