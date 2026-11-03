from unittest.mock import MagicMock, patch

import pytest

from network.automation import automate_cisco


VLANS = {
    10: "VLAN_DADOS",
    20: "VLAN_VOZ",
    50: "VLAN_SEGURANCA",
}

VLANS_CORRETAS = """
1    default          active
10   VLAN_DADOS       active
20   VLAN_VOZ         active
50   VLAN_SEGURANCA   active
"""


def executar_simulacao(vlans_retornadas, hostname_retornado):
    conexao = MagicMock()

    def responder_comando(comando):
        if comando == "show running-config":
            return "hostname SW-LAB"
        if comando == "show vlan brief":
            return vlans_retornadas
        if comando == "show running-config | include ^hostname":
            return hostname_retornado
        return ""

    conexao.send_command.side_effect = responder_comando

    with (
        patch("network.automation.connect_device", return_value=conexao),
        patch("network.automation.save_backup"),
        patch("network.automation.save_vlan_evidence"),
        patch("network.automation.registrar_auditoria"),
    ):
        with pytest.raises(RuntimeError) as erro:
            automate_cisco(
                host="192.0.2.10",
                username="usuario_teste",
                password="senha_ficticia",
                hostname="SWITCH-AUTOMATIZADO",
                vlans=VLANS,
                dry_run=False,
            )

    conexao.disconnect.assert_called_once()
    return str(erro.value)


def test_alerta_vlan_divergente():
    vlans_erradas = VLANS_CORRETAS.replace(
        "VLAN_DADOS", "VLAN_ERRADA"
    )

    mensagem = executar_simulacao(
        vlans_erradas,
        "hostname SWITCH-AUTOMATIZADO",
    )

    assert mensagem == "VLAN 10 nao validada"


def test_alerta_hostname_divergente():
    mensagem = executar_simulacao(
        VLANS_CORRETAS,
        "hostname SWITCH-INCORRETO",
    )

    assert mensagem == "Hostname nao corresponde ao esperado"
