import pytest

from network.connection import build_device_config
from network.backup import save_backup
from network.vlan import build_vlan_commands


def test_build_device_config():
    config = build_device_config(
        host="192.168.1.1",
        username="admin",
        password="123456"
    )

    assert config["host"] == "192.168.1.1"
    assert config["device_type"] == "cisco_ios"


def test_connection_requires_host():
    with pytest.raises(ValueError):
        build_device_config("", "admin", "123456")


def test_save_backup(tmp_path):
    result = save_backup(
        "SW-CORE-01",
        "show running-config",
        str(tmp_path)
    )

    assert result.exists()
    assert result.read_text(encoding="utf-8") == "show running-config"


def test_build_vlan_commands():
    commands = build_vlan_commands(100, "REDE_DADOS")

    assert commands == [
        "vlan 100",
        "name REDE_DADOS"
    ]


def test_vlan_invalid_id():
    with pytest.raises(ValueError):
        build_vlan_commands(5000, "REDE_DADOS")
