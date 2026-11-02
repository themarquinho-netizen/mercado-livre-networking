# Plano de automação de VPN IPsec — FortiGate ↔ Palo Alto

**Desafio Técnico de Networking — Mercado Livre | Parte 2**
**Status:** proposta técnica / planejamento. **Não foi implementada nem testada uma VPN real.**

## 1. Objetivo e escopo

Planejar a configuração automatizada de uma VPN IPsec site-to-site **route-based** entre um FortiGate e um Palo Alto, com parâmetros compatíveis, rotas, políticas, verificação, alertas e possibilidade de reversão. A implementação e os scripts executáveis são opcionais no enunciado.

## 2. Topologia lógica e endereçamento (exemplos fictícios)

```text
LAN FortiGate 10.10.10.0/24                       LAN Palo Alto 10.20.20.0/24
         |                                                    |
    [FortiGate] ==== Internet / IKEv2 / ESP ==== [Palo Alto]
     WAN 203.0.113.10                         WAN 198.51.100.20
     Tunnel 169.255.1.1/30                    Tunnel 169.255.1.2/30
                 Rede ponto a ponto: 169.255.1.0/30
```

> Os IPs WAN são de faixas reservadas para documentação (RFC 5737). As LANs e o /30 do túnel são valores de exemplo. Substituir por endereços autorizados antes de qualquer implantação. A rede de túnel `169.255.1.0/30` foi especificada no desafio; validar a política de endereçamento e compatibilidade com o ambiente real.

| Parâmetro | FortiGate | Palo Alto |
|---|---|---|
| WAN pública (exemplo) | 203.0.113.10 | 198.51.100.20 |
| LAN protegida (exemplo) | 10.10.10.0/24 | 10.20.20.0/24 |
| Interface de túnel | Interface IPsec (nome lógico `VPN-PA`) | `tunnel.1` |
| IP de túnel | 169.255.1.1/30 | 169.255.1.2/30 |
| Rota remota | 10.20.20.0/24 → túnel IPsec | 10.10.10.0/24 → tunnel.1 |

## 3. Propostas criptográficas compatíveis

| Parâmetro | Proposta comum |
|---|---|
| Versão IKE | IKEv2 |
| Autenticação | PSK forte e única por túnel; certificado é alternativa preferível em escala |
| IKE Phase 1 | AES-256 / SHA-256 / DH grupo 14 (ou grupo superior suportado pelos dois) |
| Lifetime IKE | 28.800 segundos |
| IPsec Phase 2 | ESP AES-256 / SHA-256, PFS grupo 14 |
| Lifetime IPsec | 3.600 segundos |
| NAT-T | Habilitar quando houver NAT no caminho |
| DPD / monitoramento | Habilitar com intervalos compatíveis e política de recuperação |
| Tráfego | Route-based, com seletores/proxy IDs coerentes nas duas pontas |

**Nota de compatibilidade:** a sintaxe, disponibilidade de algoritmos, parâmetros de integridade, PFS, seletores e interface de túnel dependem da versão de FortiOS e PAN-OS. As propostas acima são uma base conservadora de interoperabilidade, não uma configuração validada. Preferir AES-GCM quando ambas as versões e o desenho permitirem, ajustando a integridade de acordo com a implementação.

## 4. Ferramentas e interfaces de automação

- **Python** como orquestrador, com validação de dados e logs estruturados.
- **FortiGate:** API REST do FortiOS com token de conta de automação e escopo mínimo; SSH/Netmiko apenas como alternativa controlada.
- **Palo Alto:** API XML e/ou REST, conforme o recurso e versão suportados; autenticação por chave/API key. Alterações no candidato de configuração exigem **commit** para entrar em vigor; considerar o status assíncrono do job.
- **Git:** versionar templates, documentação, testes e exemplos sanitizados; nunca segredos, tokens ou backups reais.
- **Cofre de segredos:** variável de ambiente protegida ou secret manager; PSK e credenciais não devem aparecer em logs.

## 5. Fluxo lógico da automação

1. **Entrada:** carregar inventário, WANs, LANs, interfaces, PSK (via cofre), propostas IKE/IPsec, endereços de túnel, rotas e políticas.
2. **Pré-checagens:** validar endereços e sobreposições, reachability dos peers, licenças/versões, capacidade de API, interfaces, zonas, objetos e regras existentes.
3. **Backup e inventário:** coletar estado atual e configuração relevante de ambos os firewalls, protegendo os arquivos e registrando identificadores de mudança.
4. **Dry Run:** gerar plano/diff sem aplicar mudanças; verificar se os parâmetros de ambas as pontas são compatíveis e se a alteração é idempotente.
5. **FortiGate:** criar objetos de endereço; configurar Phase 1 e Phase 2; vincular interface IPsec; configurar IP do túnel quando suportado pelo desenho; criar rotas estáticas e políticas LAN↔VPN; revisar NAT para evitar tradução indevida entre LANs.
6. **Palo Alto:** criar objetos de endereço; criar perfil IKE, IKE Gateway, perfil IPsec, interface `tunnel.1`, IP do túnel, túnel IPsec e associação ao virtual router e às zonas; configurar rotas e security policies; conferir proxy IDs/seletores se necessários para interoperabilidade.
7. **Ativação controlada:** validar a configuração candidata, executar commit no Palo Alto e aguardar a conclusão; aplicar/verificar no FortiGate; documentar a ordem de ativação e janela de mudança.
8. **Verificação:** consultar estado IKE/IPsec, contadores, rotas, políticas e tráfego de teste autorizado; comparar resultado com estado desejado.
9. **Registro e resultado:** salvar relatório sem segredos, diffs, horário, dispositivos, status e evidências; alertar sobre falhas ou divergências.

## 6. Roteamento, zonas e políticas

- **FortiGate:** rota `10.20.20.0/24` pela interface IPsec; políticas permitindo apenas origem `10.10.10.0/24` e destino `10.20.20.0/24` (e retorno conforme necessidade), serviços explicitamente autorizados e **sem NAT** para o tráfego protegido.
- **Palo Alto:** `tunnel.1` associado ao virtual router e a uma zona VPN; rota `10.10.10.0/24` via `tunnel.1`; políticas entre zona LAN e zona VPN para os fluxos autorizados. Considerar regras de NAT existentes e criar isenção quando necessária.
- **Tráfego de túnel:** se usar /30 para roteamento ou testes, conferir se as implementações aceitam os IPs na interface e se as regras/seletores permitem o tráfego. O /30 não substitui as redes LAN protegidas.
- **Retorno:** validar as rotas de volta e evitar assimetria, especialmente em ambientes com múltiplos links ou VRFs.

## 7. Particularidades entre fabricantes

- Diferenças entre nomes e opções de algoritmos, DH/PFS, lifetimes, DPD e NAT-T.
- FortiGate Phase 2 selectors versus Palo Alto proxy IDs/traffic selectors: garantir correspondência ou negociação adequada para VPN route-based.
- Palo Alto utiliza configuração candidata e **commit**; FortiGate normalmente aplica mudanças de configuração diretamente pela API.
- Diferenças de interface, zonas, políticas, ordem de regras, NAT, roteamento e permissões de API.
- Tratamento de falha parcial: uma ponta pode estar configurada enquanto a outra falha. A automação deve detectar e oferecer reversão controlada.

## 8. Validação e alertas

| Etapa | Validação proposta | Alerta se falhar |
|---|---|---|
| Pré-configuração | IPs, sub-redes, parâmetros e reachability dos peers | `VALIDACAO_PARAMETROS` |
| Aplicação FortiGate | Resposta da API, leitura de configuração e rotas | `FALHA_CONFIG_FORTIGATE` |
| Aplicação Palo Alto | Validação do candidato, job de commit e leitura de configuração | `FALHA_COMMIT_PALO_ALTO` |
| IKE / Phase 1 | Estado da IKE SA, logs e negociação | `IKE_DOWN` |
| IPsec / Phase 2 | IPsec SAs e contadores de encapsulamento/decapsulamento | `IPSEC_DOWN` |
| Tráfego | Ping/TCP autorizado entre hosts de teste, captura de sessões e contadores | `TRAFEGO_INDISPONIVEL` |
| Conformidade | Comparar objetos, propostas, políticas e rotas com o plano | `CONFIG_DRIFT` |

**Exemplos de consulta:** FortiGate: diagnósticos `diagnose vpn ike gateway list` e `diagnose vpn tunnel list`, além de API/monitoramento disponíveis na versão; Palo Alto: comandos operacionais `show vpn ike-sa` e `show vpn ipsec-sa`, monitor de túneis e jobs de commit. A sintaxe deve ser validada na versão instalada. A automação pode enviar alertas por e-mail, webhook ou sistema de chamados com severidade, dispositivo, etapa e identificador de execução, **sem** divulgar PSK/tokens.

## 9. Plano de rollback

1. Capturar previamente a configuração relevante de ambas as pontas e o identificador da mudança.
2. Se houver falha de validação, interromper novas ações; não assumir que a alteração foi revertida automaticamente.
3. No Palo Alto, restaurar configuração candidata/snapshot apropriado e realizar commit de reversão conforme procedimento autorizado.
4. No FortiGate, reverter os objetos, rotas e políticas introduzidos ou restaurar configuração aprovada com cautela para não afetar alterações concorrentes.
5. Verificar restauração de rotas, políticas, serviços e estado anterior; registrar evidências e comunicar resultado.

## 10. Critérios de aceite

- Parâmetros IKEv2/ESP coerentes nas duas pontas e sem divergências.
- Configurações de objetos, interfaces, políticas e rotas correspondentes ao plano.
- Commit Palo Alto concluído e configuração FortiGate confirmada.
- IKE SA e IPsec SAs estabelecidas, **se houver ambiente de teste**.
- Comunicação bidirecional entre hosts de teste autorizados, **se houver ambiente de teste**.
- Alertas claros em caso de falha, com evidências, sem exposição de segredos.
- Possibilidade documentada de rollback.

## 11. Limitações e próximos passos

Este documento atende à **etapa de planejamento** solicitada. Não declara implantação, execução de API, negociação IPsec ou testes de tráfego reais. Para implementar, seria necessário obter versões FortiOS/PAN-OS, endereços e interfaces definitivos, credenciais protegidas, autorização de mudança, janela e ambiente de homologação. Scripts de configuração e testes reais são entregáveis opcionais no desafio.

## 12. Referência do desafio

*Laboratório de Candidatos — Networking Mercado Livre*, Parte 2: Automação (Planejamento) da Configuração de VPN IPsec entre FortiGate e Palo Alto, páginas 4–5.
