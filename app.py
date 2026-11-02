
import json
import os
import uuid
import csv
from io import BytesIO
from flask import send_file
from pathlib import Path
from datetime import datetime
from network.automation import automate_cisco
from network.backup import save_backup
from network.compare import compare_backups
from io import StringIO
from network.dashboard import calcular_indicadores


from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    send_file,
    abort
)


from network.connection import build_device_config, connect_device

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "network-automation-local")

DATABASE = "equipamentos.json"

DEVICE_TYPES = {
    "Dell OS10": "dell_os10",
    "Cisco IOS": "cisco_ios",
    "Juniper JunOS": "juniper_junos",
    "Fortinet FortiGate": "fortinet",
    "Palo Alto": "paloalto_panos"
}


def load_devices():
    if not os.path.exists(DATABASE):
        return []

    try:
        with open(DATABASE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


def save_devices(devices):
    with open(DATABASE, "w", encoding="utf-8") as file:
        json.dump(devices, file, indent=4, ensure_ascii=False)

def carregar_auditoria(limite=None):
    arquivo = Path(app.root_path) / "logs" / "auditoria.jsonl"
    registros = []

    if not arquivo.is_file():
        return registros

    with arquivo.open("r", encoding="utf-8") as f:
        for linha in f:
            try:
                registro = json.loads(linha)

                if not isinstance(registro, dict):
                    continue

                data = registro.get("data", "")

                try:
                    data_formatada = datetime.fromisoformat(
                        data
                    ).strftime("%d/%m/%Y %H:%M:%S")
                except (ValueError, TypeError):
                    data_formatada = str(data)

                registros.append({
                    "data": data_formatada,
                    "equipamento": registro.get(
                        "equipamento", "-"
                    ),
                    "acao": registro.get("acao", "-"),
                    "status": registro.get("status", "-"),
                    "detalhes": registro.get("detalhes", "")
                })

            except json.JSONDecodeError:
                continue

    if limite is None:
        return list(reversed(registros))

    if limite <= 0:
        return []

    return list(reversed(registros[-limite:]))

def filtrar_auditoria(registros, status, equipamento, inicio, fim):
    status = status.upper()

    if status not in {"TODOS", "SUCESSO", "FALHA", "SIMULADO"}:
        status = "TODOS"

    if status != "TODOS":
        registros = [
            r for r in registros
            if str(r.get("status", "")).upper() == status
        ]

    if equipamento:
        registros = [
            r for r in registros
            if equipamento.lower()
            in str(r.get("equipamento", "")).lower()
        ]

    def converter_data(valor):
        if not valor:
            return None
        try:
            return datetime.strptime(valor, "%Y-%m-%d").date()
        except ValueError:
            return None

    data_inicial = converter_data(inicio)
    data_final = converter_data(fim)

    if data_inicial or data_final:
        filtrados = []

        for registro in registros:
            try:
                data_registro = datetime.strptime(
                    registro["data"], "%d/%m/%Y %H:%M:%S"
                ).date()
            except (ValueError, TypeError, KeyError):
                continue

            if data_inicial and data_registro < data_inicial:
                continue

            if data_final and data_registro > data_final:
                continue

            filtrados.append(registro)

        registros = filtrados

    return registros

@app.route("/auditoria/exportar")
def exportar_auditoria():
    registros = carregar_auditoria()

    status = request.args.get(
        "status_auditoria", "TODOS"
    ).strip()

    equipamento = request.args.get(
        "equipamento_auditoria", ""
    ).strip()

    inicio = request.args.get(
        "data_inicio", ""
    ).strip()

    fim = request.args.get(
        "data_fim", ""
    ).strip()

    registros = filtrar_auditoria(
        registros,
        status,
        equipamento,
        inicio,
        fim
    )

    saida = StringIO()
    escritor = csv.writer(saida, delimiter=";")

    escritor.writerow([
        "Data",
        "Equipamento",
        "Acao",
        "Status",
        "Detalhes"
    ])

    for registro in registros:
        escritor.writerow([
            registro.get("data", ""),
            registro.get("equipamento", ""),
            registro.get("acao", ""),
            registro.get("status", ""),
            registro.get("detalhes", "")
        ])

    conteudo = "\ufeff" + saida.getvalue()

    return app.response_class(
        conteudo,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=historico_auditoria.csv"
        }
    )

@app.route("/")
def index():
    devices = load_devices()
    backups = []
    relatorios_vlan = []
    todos_registros = carregar_auditoria()
    indicadores = calcular_indicadores(todos_registros)
    auditoria = todos_registros

    status_filtro = request.args.get(
        "status_auditoria", "TODOS"
    ).upper()

    equipamento_filtro = request.args.get(
        "equipamento_auditoria", ""
    ).strip()

    data_inicio = request.args.get(
        "data_inicio", ""
    ).strip()

    data_fim = request.args.get(
        "data_fim", ""
    ).strip()


    auditoria = filtrar_auditoria(
        auditoria,
        status_filtro,
        equipamento_filtro,
        data_inicio,
        data_fim
    )


    # Paginacao do historico de auditoria
    por_pagina = 50

    try:
        pagina = int(request.args.get("pagina", 1))
    except (ValueError, TypeError):
        pagina = 1

    pagina = max(1, pagina)

    total_filtrado = len(auditoria)
    total_paginas = max(
        1,
        (total_filtrado + por_pagina - 1) // por_pagina
    )

    pagina = min(pagina, total_paginas)

    inicio_pagina = (pagina - 1) * por_pagina
    fim_pagina = inicio_pagina + por_pagina

    auditoria = auditoria[inicio_pagina:fim_pagina]


    relatorios_dir = Path(app.root_path) / "backups" / "relatorios"

    if relatorios_dir.exists():
        for arquivo in relatorios_dir.glob("*.txt"):
            stat = arquivo.stat()

            relatorios_vlan.append({
                "filename": arquivo.name,
                "size": stat.st_size,
                "date": datetime.fromtimestamp(
                    stat.st_mtime
                ).strftime("%d/%m/%Y %H:%M:%S"),
            })

    relatorios_vlan.sort(
        key=lambda item: item["date"],
        reverse=True
    )

    backup_dir = Path("backups")

    if backup_dir.exists():
        for file in backup_dir.glob("*.cfg"):
            stat = file.stat()

            backups.append({
                "filename": file.name,
                "size": stat.st_size,
                "date": datetime.fromtimestamp(
                    stat.st_mtime
                ).strftime("%d/%m/%Y %H:%M:%S")
            })

    backups.sort(
        key=lambda item: item["filename"],
        reverse=True
    )
    return render_template(
        "index.html",
        devices=devices,
        device_types=DEVICE_TYPES,
        backups=backups,
        relatorios_vlan=relatorios_vlan,
        auditoria=auditoria,
        status_filtro=status_filtro,
        equipamento_filtro=equipamento_filtro,
        data_inicio=data_inicio,
        data_fim=data_fim,
        indicadores=indicadores,
        pagina=pagina,
        total_paginas=total_paginas,
        total_filtrado=total_filtrado
    )


@app.route("/relatorios/vlan/visualizar/<path:filename>")
def visualizar_relatorio_vlan(filename):
    from flask import abort, send_file

    pasta = Path(app.root_path) / "backups" / "relatorios"

    if Path(filename).name != filename or not filename.endswith(".txt"):
        abort(404)

    arquivo = pasta / filename

    if not arquivo.is_file():
        abort(404)

    return send_file(arquivo, mimetype="text/plain; charset=utf-8")


@app.route("/relatorios/vlan/download/<path:filename>")
def download_relatorio_vlan(filename):
    from flask import abort, send_from_directory

    pasta = Path(app.root_path) / "backups" / "relatorios"

    if Path(filename).name != filename or not filename.endswith(".txt"):
        abort(404)

    if not (pasta / filename).is_file():
        abort(404)

    return send_from_directory(
        pasta,
        filename,
        as_attachment=True
    )
@app.route("/backups/download/<path:filename>")
def download_backup(filename):
    backup_dir = Path(app.root_path) / "backups"

    # Permitir somente arquivos CFG com nome simples.
    if (
        not filename.endswith(".cfg")
        or filename != Path(filename).name
        or "\\" in filename
    ):
        abort(404)

    if not (backup_dir / filename).is_file():
        abort(404)

    return send_from_directory(
        backup_dir,
        filename,
        as_attachment=True,
        download_name=filename
    )

@app.route("/backups/visualizar/<filename>")
def visualizar_backup(filename):
    backup_dir = Path(app.root_path) / "backups"

    # Aceitar apenas nomes simples de arquivos .cfg
    if (
        not filename.endswith(".cfg")
        or filename in (".", "..")
        or "/" in filename
        or "\\" in filename
    ):
        abort(404)

    backup_file = backup_dir / filename

    if not backup_file.is_file():
        abort(404)

    return send_file(
        backup_file,
        mimetype="text/plain; charset=utf-8",
        as_attachment=False
    )

@app.route("/backups/comparar", methods=["POST"])
def comparar_backups():
    backup_dir = Path(app.root_path) / "backups"

    anterior = request.form.get("backup_old", "")
    atual = request.form.get("backup_new", "")

    arquivos = {
        arquivo.name
        for arquivo in backup_dir.glob("*.cfg")
        if arquivo.is_file()
    }

    if anterior not in arquivos or atual not in arquivos:
        flash("Selecione dois backups válidos.", "error")
        return redirect(url_for("index"))

    if anterior == atual:
        flash("Selecione dois backups diferentes.", "error")
        return redirect(url_for("index"))

    resultado = compare_backups(
        backup_dir / anterior,
        backup_dir / atual
    )

    return render_template(
        "comparacao.html",
        backup_old=anterior,
        backup_new=atual,
        result=resultado
    )

@app.route("/backups/relatorio", methods=["POST"])
def baixar_relatorio_comparacao():
    backup_dir = Path(app.root_path) / "backups"

    anterior = request.form.get("backup_old", "")
    atual = request.form.get("backup_new", "")

    arquivos = {
        arquivo.name
        for arquivo in backup_dir.glob("*.cfg")
        if arquivo.is_file()
    }

    if anterior not in arquivos or atual not in arquivos:
        abort(400)

    if anterior == atual:
        abort(400)

    resultado = compare_backups(
        backup_dir / anterior,
        backup_dir / atual
    )

    linhas = [
        "NETWORK AUTOMATION - RELATORIO DE COMPARACAO",
        "=" * 55,
        f"Backup anterior: {anterior}",
        f"Backup atual: {atual}",
        "",
        f"Linhas adicionadas: {resultado['added_count']}",
        f"Linhas removidas: {resultado['removed_count']}",
        f"Total de alteracoes: {resultado['total_changes']}",
        "",
        "DIFERENCAS:",
        "-" * 55
    ]

    if resultado["identical"]:
        linhas.append("Nenhuma alteracao identificada.")
    else:
        linhas.extend(resultado["differences"])

    conteudo = "\n".join(linhas).encode("utf-8")

    return send_file(
        BytesIO(conteudo),
        mimetype="text/plain; charset=utf-8",
        as_attachment=True,
        download_name="relatorio_comparacao.txt"
    )

@app.route("/health")
def health():
    return {
        "status": "online",
        "application": "Network Automation"
    }


@app.route("/equipamentos/cadastrar", methods=["POST"])
def cadastrar_equipamento():
    hostname = request.form.get("hostname", "").strip()
    host = request.form.get("host", "").strip()
    manufacturer = request.form.get("manufacturer", "").strip()
    device_type = request.form.get("device_type", "").strip()

    try:
        port = int(request.form.get("port", "22"))
    except ValueError:
        flash("Porta SSH inválida.", "error")
        return redirect(url_for("index"))

    if not all([hostname, host, manufacturer, device_type]):
        flash("Preencha todos os campos obrigatórios.", "error")
        return redirect(url_for("index"))

    if device_type not in DEVICE_TYPES.values():
        flash("Tipo de equipamento inválido.", "error")
        return redirect(url_for("index"))

    if not 1 <= port <= 65535:
        flash("Informe uma porta entre 1 e 65535.", "error")
        return redirect(url_for("index"))

    devices = load_devices()

    if any(device["host"] == host for device in devices):
        flash("Este endereço IP já está cadastrado.", "error")
        return redirect(url_for("index"))

    device = {
        "id": uuid.uuid4().hex[:8],
        "hostname": hostname,
        "host": host,
        "manufacturer": manufacturer,
        "device_type": device_type,
        "port": port,
        "status": "Não testado"
    }

    devices.append(device)
    save_devices(devices)

    flash(f"Equipamento {hostname} cadastrado com sucesso!", "success")

    return redirect(url_for("index"))


@app.route("/equipamentos/<device_id>/testar", methods=["POST"])
def testar_equipamento(device_id):
    devices = load_devices()

    device = next(
        (item for item in devices if item["id"] == device_id),
        None
    )

    if device is None:
        flash("Equipamento não encontrado.", "error")
        return redirect(url_for("index"))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Informe usuário e senha SSH.", "error")
        return redirect(url_for("index"))

    connection = None

    try:
        config = build_device_config(
            host=device["host"],
            username=username,
            password=password,
            device_type=device["device_type"],
            port=device["port"]
        )

        connection = connect_device(config)
        device["status"] = "Conectado"
        flash(
            f"Conexão SSH estabelecida com {device['hostname']}!",
            "success"
        )

    except Exception:
        device["status"] = "Falha na conexão"
        flash(
            "Não foi possível conectar. Verifique IP, porta, "
            "credenciais e acesso SSH.",
            "error"
        )

    finally:
        if connection:
            try:
                connection.disconnect()
            except Exception:
                pass

        save_devices(devices)

    return redirect(url_for("index"))


@app.route("/cisco/configurar", methods=["POST"])
def configurar_cisco():
    devices = load_devices()

    device_id = request.form.get("device_id", "")

    device = next(
        (item for item in devices if item["id"] == device_id),
        None
    )

    if device is None or device["device_type"] != "cisco_ios":
        flash("Selecione um switch Cisco válido.", "error")
        return redirect(url_for("index"))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    hostname = request.form.get("new_hostname", "").strip()

    if not username or not password:
        flash("Informe as credenciais SSH.", "error")
        return redirect(url_for("index"))

    import re

    if not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9-]{0,62}", hostname
    ):
        flash("Hostname inválido.", "error")
        return redirect(url_for("index"))

    from network.vlan import build_vlan_commands

    try:
        commands = []

        for vlan_id in (10, 20, 50):
            vlan_name = request.form.get(
                f"vlan_{vlan_id}", ""
            ).strip()

            commands.extend(
                build_vlan_commands(vlan_id, vlan_name)
            )

        commands.append(f"hostname {hostname}")

    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("index"))

    # Executa a automação Cisco.
    # ATENCAO: o modo apply altera o equipamento.

    action = request.form.get("action", "preview")

    if action not in ("preview", "apply"):
        flash("Ação inválida.", "error")
        return redirect(url_for("index"))

    try:
        result = automate_cisco(
            host=device["host"],
            username=username,
            password=password,
            hostname=hostname,
            vlans={
                10: request.form.get("vlan_10", "").strip(),
                20: request.form.get("vlan_20", "").strip(),
                50: request.form.get("vlan_50", "").strip(),
            },
            port=device["port"],
            dry_run=(action == "preview"),
        )

        if result["success"]:
            if action == "preview":
                flash(
                    "Pré-validação concluída. Comandos preparados: "
                    + " | ".join(result["commands"])
                    + ". Nenhuma alteração aplicada.",
                    "success"
                )
            else:
                device["hostname"] = hostname
                device["status"] = "Conectado"
                save_devices(devices)

                flash(
                    f"Configuração aplicada e validada! "
                    f"Backup: {result['backup']}",
                    "success"
                )

    except Exception:
        app.logger.exception("Falha na automação Cisco")
        flash(
            "Falha na automação. Verifique o terminal "
            "do Flask antes de tentar novamente. "
            "A configuração pode ter sido parcialmente aplicada.",
            "error"
        )

    return redirect(url_for("index"))
@app.route("/equipamentos/<device_id>/backup", methods=["POST"])
def backup_equipamento(device_id):
    devices = load_devices()

    device = next(
        (item for item in devices if item["id"] == device_id),
        None
    )

    if device is None:
        flash("Equipamento não encontrado.", "error")
        return redirect(url_for("index"))

    if device["device_type"] != "cisco_ios":
        flash("Backup disponível inicialmente para Cisco IOS.", "error")
        return redirect(url_for("index"))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Informe usuário e senha SSH.", "error")
        return redirect(url_for("index"))

    connection = None

    try:
        config = build_device_config(
            host=device["host"],
            username=username,
            password=password,
            device_type=device["device_type"],
            port=device["port"]
        )

        connection = connect_device(config)

        running_config = connection.send_command(
            "show running-config",
            read_timeout=60
        )

        if not running_config.strip():
            raise RuntimeError("Configuração retornada vazia.")

        if running_config.lstrip().startswith(
            ("%", "Invalid input", "Error:")
        ):
            raise RuntimeError("Falha ao obter configuração.")

        backup_file = save_backup(
            device["hostname"],
            running_config
        )

        flash(
            f"Backup realizado com sucesso: {backup_file}",
            "success"
        )

    except Exception:
        app.logger.exception("Falha ao realizar backup")
        flash(
            "Falha no backup. Verifique a conexão SSH "
            "e os logs do Flask.",
            "error"
        )

    finally:
        if connection:
            connection.disconnect()

    return redirect(url_for("index"))
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
