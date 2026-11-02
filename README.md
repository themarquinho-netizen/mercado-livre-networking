# Network Automation — Desafio Técnico Mercado Livre

## 1. Visão geral

Projeto desenvolvido em Python para automatizar atividades de administração de equipamentos de rede Cisco, utilizando SSH e uma interface web.

A solução foi construída como parte de um desafio técnico, com foco em automação, segurança operacional, rastreabilidade e validação de configurações.

## 2. Tecnologias utilizadas

- Python 3
- Flask — interface web
- Netmiko — comunicação SSH com equipamentos Cisco
- Pytest — testes automatizados
- HTML e CSS — frontend
- Git — versionamento
- Cisco Modeling Labs (CML) — laboratório virtual

## 3. Funcionalidades

### Gerenciamento de equipamentos

- Cadastro e consulta de equipamentos Cisco.
- Teste de conectividade SSH.
- Visualização de informações dos equipamentos.

### Automação Cisco

- Configuração das VLANs 10, 20 e 50.
- Alteração de hostname.
- Pré-validação dos comandos por meio de Dry Run.
- Aplicação de configurações via SSH.
- Captura de informações antes e depois das alterações.

**Atenção:** o modo de aplicação realiza alterações no equipamento. Recomenda-se executar a pré-validação antes de aplicar configurações.

### Backup e comparação

- Coleta e armazenamento de configurações.
- Histórico de backups.
- Comparação entre arquivos de configuração.

### Relatórios e auditoria

- Relatórios de alterações de VLANs.
- Registro de operações de automação.
- Filtros por equipamento, status e período.
- Exportação de histórico em CSV.
- Dashboard de indicadores.
- Paginação do histórico.

## 4. Estrutura do projeto

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
│   └── test_network.py
└── docs/
    ├── evidencias/
    └── vpn/
```

## 5. Instalação

Clone o repositório:

```bash
git clone URL_DO_REPOSITORIO
cd mercado-livre-networking
```

Crie um ambiente virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

## 6. Execução

Inicie a aplicação:

```powershell
python app.py
```

Acesse no navegador:

```text
http://127.0.0.1:5000
```

Cadastre o equipamento Cisco, informe os parâmetros necessários e utilize as funcionalidades disponíveis na interface.

## 7. Testes

Execute:

```powershell
python -m pytest -q
```

Os testes automatizados verificam funcionalidades específicas do projeto. A validação completa da aplicação em equipamentos de rede deve ser realizada separadamente.

## 8. Segurança

- Credenciais devem permanecer fora do código versionado.
- O arquivo `.env` não deve ser publicado.
- Backups e logs locais não devem ser enviados ao repositório.
- O modo Dry Run permite revisar comandos antes da aplicação.
- Alterações reais devem ser executadas somente em equipamentos autorizados.

## 9. Laboratório

O ambiente de testes utiliza o Cisco Modeling Labs (CML), com switch Cisco virtual, VLANs e comunicação SSH.

As evidências de funcionamento serão disponibilizadas na pasta `docs/evidencias`, após revisão para remoção de informações sensíveis.

## 10. Planejamento de VPN

A segunda parte do desafio contempla o planejamento de uma VPN IPsec entre equipamentos FortiGate e Palo Alto.

A documentação técnica será disponibilizada em `docs/vpn`, incluindo os parâmetros de negociação, redes envolvidas, políticas de segurança, roteamento, validação e monitoramento.

A implementação prática da VPN é tratada separadamente do planejamento.

## 11. Status do projeto

- Interface web: implementada.
- Módulos de automação: implementados.
- Backup e comparação: implementados.
- Auditoria e relatórios: implementados.
- Testes automatizados: executados com sucesso em validações anteriores.
- Homologação final da automação Cisco: pendente.
- Revisão final da documentação VPN: pendente.
- Publicação e entrega: pendentes.

## 12. Autor

Projeto desenvolvido para avaliação técnica de conhecimentos em redes, segurança e automação de infraestrutura.