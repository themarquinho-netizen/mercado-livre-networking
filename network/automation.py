
import re
from datetime import datetime
from pathlib import Path

from network.connection import (
    build_device_config,
    connect_device,
)
from network.vlan import build_vlan_commands
from network.backup import save_backup
from network.relatorio_vlan import gerar_relatorio
from network.auditoria import registrar_auditoria


def save_vlan_evidence(host, stage, content):
    """Salva uma evidencia do estado das VLANs."""
    directory = Path("backups") / "evidencias"
    directory.mkdir(parents=True, exist_ok=True)

    safe_host = re.sub(r"[^A-Za-z0-9_.-]", "_", host)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    filename = directory / (
        f"{safe_host}_{stage}_{timestamp}.txt"
    )

    filename.write_text(content, encoding="utf-8")
    return filename


def automate_cisco(
    host,
    username,
    password,
    hostname,
    vlans,
    port=22,
    dry_run=True,
):
    if not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9-]{0,62}", hostname
    ):
        raise ValueError("Hostname invalido")

    commands = []

    for vlan_id, vlan_name in vlans.items():
        commands.extend(
            build_vlan_commands(int(vlan_id), vlan_name)
        )

    commands.append(f"hostname {hostname}")

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "commands": commands,
            "message": (
                "Pre-validacao concluida. "
                "Nenhuma alteracao aplicada."
            ),
        }

    config = build_device_config(
        host=host,
        username=username,
        password=password,
        port=port,
    )

    connection = None

    try:
        connection = connect_device(config)

        # 1. Captura configuracao e VLANs antes da mudanca
        running_config = connection.send_command(
            "show running-config"
        )

        vlans_before = connection.send_command(
            "show vlan brief"
        )

        backup_file = save_backup(host, running_config)

        evidence_before = save_vlan_evidence(
            host, "ANTES", vlans_before
        )

        # 2. Aplica configuracoes
        output = connection.send_config_set(
            commands,
            error_pattern=(
                r"% ?(?:Invalid input|Error|Incomplete command)"
            ),
        )

        # 3. Captura estado apos a mudanca
        vlans_after = connection.send_command(
            "show vlan brief"
        )

        hostname_output = connection.send_command(
            "show running-config | include ^hostname"
        )

        evidence_after = save_vlan_evidence(
            host, "DEPOIS", vlans_after
        )

        # 4. Valida hostname
        expected_hostname = f"hostname {hostname}"

        if expected_hostname not in hostname_output:
            raise RuntimeError(
                "Hostname nao corresponde ao esperado"
            )

        # 5. Valida VLANs
        for vlan_id, vlan_name in vlans.items():
            pattern = (
                rf"(?m)^\s*{int(vlan_id)}\s+"
                rf"{re.escape(vlan_name)}\s+active\b"
            )

            if not re.search(pattern, vlans_after):
                raise RuntimeError(
                    f"VLAN {vlan_id} nao validada"
                )

        # 6. Salva configuracao
        # 6. Salva configuracao
        save_output = connection.save_config()

        # 7. Gera relatorio comparando VLANs antes e depois
        relatorio_file = gerar_relatorio(
            vlans_before,
            vlans_after,
            host,
        )
        registrar_auditoria(
            equipamento=host,
            acao="CONFIGURACAO_CISCO",
            status="SUCESSO",
            detalhes=(
                f"Hostname: {hostname}; "
                f"VLANs: {list(vlans.keys())}; "
                f"Backup: {backup_file}; "
                f"Relatorio: {relatorio_file}"
            ),
        )
        return {
            "success": True,
            "backup": str(backup_file),
            "configuration_output": output,
            "save_output": save_output,
            "vlan_output": vlans_after,
            "hostname_output": hostname_output,
            "vlan_evidence_before": str(evidence_before),
            "vlan_evidence_after": str(evidence_after),
             "vlan_report": str(relatorio_file),
        }
    except Exception as erro:
        try:
            registrar_auditoria(
                equipamento=host,
                acao="CONFIGURACAO_CISCO",
                status="FALHA",
                detalhes=(
                    f"Tipo do erro: {type(erro).__name__}; "
                    "A automacao nao foi concluida. "
                    "Verificar logs e estado do equipamento."
                ),
            )
        except Exception:
            pass

        raise

    finally:
        if connection:
            connection.disconnect()