from netmiko import ConnectHandler


def build_device_config(host, username, password, device_type="cisco_ios", port=22):
    if not host:
        raise ValueError("O endereço IP ou hostname é obrigatório")

    if not username:
        raise ValueError("O usuário é obrigatório")

    if not password:
        raise ValueError("A senha é obrigatória")

    return {
        "device_type": device_type,
        "host": host,
        "username": username,
        "password": password,
        "port": port,
    }


def connect_device(device_config):
    return ConnectHandler(**device_config)
