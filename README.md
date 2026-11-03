# Network Automation | Desafio Técnico de Networking

Automação de configuração e validação de switches Cisco, desenvolvida em Python, com interface web Flask e comunicação SSH via Netmiko. O projeto foi validado em laboratório Cisco Modeling Labs (CML) e inclui documentação de planejamento de VPN IPsec entre FortiGate e Palo Alto.

## Objetivo

Padronizar alterações de configuração em switches Cisco e reduzir erros operacionais por meio de pré-visualização de comandos, coleta de backup, validação do estado após a alteração e registro de auditoria.

## Tecnologias

- Python 3, Flask, Netmiko e Pytest
- HTML e CSS
- Git e GitHub
- Cisco Modeling Labs (CML), com switch Cisco virtual

## Funcionalidades

**Inventário e acesso:** cadastro de equipamentos, consulta de informações e teste de conexão SSH.

**Automação Cisco:** definição de hostname e configuração das VLANs 10, 20 e 50. A interface permite pré-visualizar os comandos (dry run) antes de executá-los. Na aplicação real, o sistema coleta informações anteriores, envia a configuração, consulta o estado resultante, valida hostname e VLANs, salva a configuração e registra o resultado.

**Backup e rastreabilidade:** backup de configuração, histórico de arquivos, comparação entre backups, relatórios de VLANs, auditoria de operações, filtros, exportação CSV e indicadores no dashboard.

### Parâmetros utilizados na validação do laboratório

| Item | Configuração esperada |
| --- | --- |
| Hostname | `SWITCH-AUTOMATIZADO` |
| VLAN 10 | `VLAN_DADOS` |
| VLAN 20 | `VLAN_VOZ` |
| VLAN 50 | `VLAN_SEGURANCA` |

A alteração foi aplicada no switch virtual e conferida por comandos Cisco, incluindo `show vlan brief`, `show running-config | include ^hostname` e `show startup-config | include ^hostname`.

> **Atenção:** a opção de aplicação altera a configuração do equipamento. Utilize apenas em ambientes autorizados e revise os comandos antes da execução.

## Estrutura principal

```text
mercado-livre-networking/
├── app.py
├── requirements.txt
├── README.md
├── network/
│   ├── automation.py
│   ├── connection.py
│   ├── vlan.py
│   ├── backup.py
│   ├── compare.py
│   ├── auditoria.py
│   ├── dashboard.py
│   └── relatorio_vlan.py
├── templates/
│   ├── index.html
│   └── comparacao.html
├── static/
│   └── style.css
├── tests/
│   ├── test_network.py
│   └── test_alertas.py
└── docs/
    ├── evidencias/
    └── vpn/
```

Arquivos locais de inventário, credenciais, backups e logs não fazem parte da entrega pública.

## Instalação e execução

Pré-requisitos: Python 3, acesso SSH a um equipamento Cisco autorizado e conectividade de rede entre o computador e o equipamento.

No PowerShell do Windows:

```powershell
git clone https://github.com/themarquinho-netizen/mercado-livre-networking.git
cd mercado-livre-networking
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Acesse `http://127.0.0.1:5000` no navegador. Cadastre o switch Cisco e informe usuário e senha SSH nos campos da interface. Para conferir a sequência de comandos sem modificar o equipamento, use **Pré-validar configuração**. Para realizar a alteração, utilize **Aplicar configuração Cisco** apenas após revisar os parâmetros.

## Testes e validação

Foram executados sete testes automatizados com Pytest:

```powershell
python -m pytest -q tests/test_network.py tests/test_alertas.py
```

Resultado registrado: **7 testes aprovados**.

Os testes abrangem construção de parâmetros de conexão, validação de entrada, geração de comandos VLAN, backup e detecção de divergência de hostname e nome de VLAN. Os dois testes de divergência utilizam respostas simuladas (`mock`), sem alterar o equipamento. A aplicação efetiva das VLANs e do hostname foi validada separadamente no Cisco CML.

### Evidências da Parte 1

- [Formulário de automação](docs/evidencias/01-frontend-automacao.png)
- [Confirmação da configuração aplicada](docs/evidencias/02-configuracao-aplicada.png)
- [Validação das VLANs e hostname no Cisco](docs/evidencias/03-validacao-cisco.png)
- [Evidência complementar de configuração](docs/evidencias/04-startup-config.png)
- [Resultado dos testes e alertas de divergência](docs/evidencias/05-testes-validacao-alertas.txt)

A evidência de hostname salvo na startup-config foi também verificada em console com `show startup-config | include ^hostname`.

## Parte 2 — Planejamento de VPN IPsec

A segunda parte apresenta o planejamento de uma VPN site-to-site entre FortiGate e Palo Alto, considerando endereçamento WAN, redes internas autorizadas, endereçamento do túnel, parâmetros de negociação IKE/IPsec, políticas de segurança, roteamento, automação, validação e monitoramento.

- [Planejamento técnico da VPN](docs/vpn/planejamento-vpn.md)
- [Topologia da VPN FortiGate ↔ Palo Alto](docs/vpn/Planejamento%20de%20VPN%20Site-to-Site%20Segura.png)

**Escopo:** documentação de arquitetura e procedimentos. A implantação prática da VPN entre os dois fabricantes não faz parte dos testes realizados neste repositório.

## Segurança e cuidados operacionais

- Não publicar credenciais, tokens, chaves privadas ou segredos de VPN.
- Manter `.env`, arquivos de inventário local, backups e logs fora do repositório público.
- Validar conectividade e permissões SSH antes de executar mudanças.
- Utilizar a pré-visualização dos comandos e manter backup anterior à alteração.
- Conferir o estado real do equipamento após a execução; a pré-visualização não equivale a uma validação do estado remoto.

## Situação da entrega

- Automação Cisco e interface web implementadas.
- Configuração de VLANs e hostname aplicada e validada em laboratório CML.
- Backup, auditoria e comparação de configurações implementados.
- Sete testes automatizados aprovados, incluindo dois cenários simulados de divergência.
- Planejamento e topologia da VPN publicados.
- Código, documentação e evidências disponíveis no GitHub.

## Repositório

https://github.com/themarquinho-netizen/mercado-livre-networking
