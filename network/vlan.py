def build_vlan_commands(vlan_id, vlan_name):
    if not isinstance(vlan_id, int) or not 1 <= vlan_id <= 4094:
        raise ValueError("VLAN ID deve estar entre 1 e 4094")

    if not vlan_name or not vlan_name.strip():
        raise ValueError("O nome da VLAN é obrigatório")

    if any(char.isspace() for char in vlan_name):
        raise ValueError("O nome da VLAN não pode conter espaços")

    return [
        f"vlan {vlan_id}",
        f"name {vlan_name}",
    ]
