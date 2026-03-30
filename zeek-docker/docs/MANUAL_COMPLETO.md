# Manual Completo da Sonda SIMIR

##  Índice
1. [Visão Geral](#visão-geral)
2. [O que é o Zeek](#o-que-é-o-zeek)
3. [Como o SIMIR Funciona](#como-o-simir-funciona)
4. [Instalação e Configuração](#instalação-e-configuração)
5. [Arquivos de Log do Zeek](#arquivos-de-log-do-zeek)
6. [Sistema de Detecção de Port Scan](#sistema-de-detecção-de-port-scan)
7. [Sistema de Detecção de Força Bruta](#sistema-de-detecção-de-força-bruta)
8. [Sistema de Detecção de DDoS](#sistema-de-detecção-de-ddos)
9. [Intelligence Framework](#intelligence-framework)
10. [Sistema de Detecção de Exfiltração de Dados](#sistema-de-detecção-de-exfiltração-de-dados)
11. [Sistema de Detecção de DNS Tunneling](#sistema-de-detecção-de-dns-tunneling)
12. [Sistema de Detecção de Movimento Lateral](#sistema-de-detecção-de-movimento-lateral)
13. [Sistema de Detecção de SQL Injection](#sistema-de-detecção-de-sql-injection)
14. [Sistema de Detecção de Beaconing](#sistema-de-detecção-de-beaconing)
15. [Sistema de Detecção de Anomalias de Protocolo](#sistema-de-detecção-de-anomalias-de-protocolo)
16. [Sistema de Detecção de ICMP Tunneling](#sistema-de-detecção-de-icmp-tunneling)
17. [Gerenciamento do Sistema](#gerenciamento-do-sistema)
18. [Troubleshooting](#troubleshooting)
19. [Monitoramento Avançado](#monitoramento-avançado)
20. [Referências](#referências)

---

##  Visão Geral

A **SIMIR** (Sonda Inteligente de Monitoramento Interno da Rede) é um sistema completo de monitoramento de rede baseado no **Zeek** (anteriormente conhecido como Bro), com funcionalidades avançadas de detecção de port scan e sistema de alertas por email.

### Características Principais:
-  **Monitoramento passivo** de tráfego de rede
-  **Detecção automática** de port scans
-  **Detecção de ataques de força bruta** em SSH, FTP e HTTP
-  **Alertas por email** em tempo real
-  **Containerizado** com Docker
-  **Análise de threat intelligence**
-  **Logs estruturados** em formato JSON/TSV

### Melhorias Recentes - Agregação Inteligente de Alertas

A partir da versão atual, o SIMIR implementa **agregação inteligente de alertas** para reduzir ruído operacional e melhorar a análise de incidentes:

#### **DNS Tunneling Detector**
- Agregação por IP de origem (não por domínio individual)
- Redução de 100+ alertas para 3-5 alertas contextualizados
- Supressão de 10 minutos para alertas do mesmo IP
- Alerta agregado "DNS Tunneling Pattern" resume atividade total

**Exemplo**: 200 queries suspeitas = 3 alertas (High Entropy + Long Subdomain + Tunneling Pattern)

#### **Data Exfiltration Detector**
- ICMP agora é **ignorado automaticamente**
- Evita falsos positivos de ping-flood sendo reportados como exfiltração
- Foco em protocolos reais de transferência de dados (TCP/UDP)

**Correção**: Ping-flood (900K+ pacotes ICMP) não gera mais alertas de "Large Upload"

#### **Benefícios Operacionais**
- Redução de ruído em até 95%
- Contextualização de atividade maliciosa
- Análise mais rápida e eficiente pelo SOC
- Menor chance de alert fatigue

---

##  O que é o Zeek

### Definição
O **Zeek** é uma plataforma de monitoramento de segurança de rede que fornece visibilidade abrangente do tráfego de rede. Diferente de firewalls ou sistemas de detecção de intrusão tradicionais, o Zeek atua como um "sensor passivo" que analisa o tráfego sem interferir na comunicação.

### Como o Zeek Monitora a Rede

#### 1. **Captura de Pacotes**
```
[Interface de Rede] → [Zeek Engine] → [Scripts de Análise] → [Logs Estruturados]
```

O Zeek utiliza o **libpcap** para capturar pacotes diretamente da interface de rede:
- Modo **promíscuo**: Captura todo o tráfego que passa pela interface
- **Análise em tempo real**: Processa pacotes conforme chegam
- **Zero impacto**: Não interfere no tráfego da rede

#### 2. **Análise de Protocolos**
O Zeek possui parsers nativos para dezenas de protocolos:
- **Camada 3**: IP, ICMP, IPv6
- **Camada 4**: TCP, UDP
- **Aplicação**: HTTP, HTTPS, DNS, SSH, FTP, SMTP, etc.

#### 3. **Geração de Eventos**
Para cada conexão ou atividade detectada, o Zeek gera **eventos**:
```zeek
event connection_established(c: connection) {
    # Evento gerado quando conexão TCP é estabelecida
}

event http_request(c: connection, method: string, original_URI: string) {
    # Evento gerado para cada requisição HTTP
}
```

#### 4. **Scripts Personalizados**
Scripts Zeek (em linguagem própria) definem:
- Quais eventos monitorar
- Como processar os dados
- Que logs gerar
- Quando emitir alertas

### Vantagens do Zeek

#### **Visibilidade Completa**
- Registra **todas** as conexões de rede
- Extrai metadados detalhados (não o conteúdo)
- Identifica protocolos automaticamente

#### **Flexibilidade**
- Scripts totalmente customizáveis
- Integração com sistemas externos
- Formato de logs configurável

#### **Performance**
- Processamento em alta velocidade
- Baixo overhead de CPU/memória
- Escalável para redes de grande porte

---

##  Como a SIMIR Funciona

### Arquitetura do Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Tráfego de    │    │      Zeek        │    │     Sonda     │
│     Rede        │───▶│   Container      │───▶│     SIMIR       │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌──────────────┐       ┌─────────────────┐
                       │   Logs do    │       │   Alertas por   │
                       │     Zeek     │       │     Email       │
                       └──────────────┘       └─────────────────┘
```

### Fluxo de Detecção

1. **Captura**: Zeek monitora interface de rede
2. **Análise**: Scripts personalizados detectam padrões
3. **Logging**: Eventos são registrados em logs
4. **Monitoramento**: Sonda SIMIR lê logs continuamente
5. **Detecção**: Algoritmos identificam ameaças (port scans, força bruta, IPs maliciosos)
6. **Alerta**: Notificações são geradas nos logs

### Estrutura do Projeto

```
├── docker-compose.yml    # Configuração do Docker Compose
├── Dockerfile           # Definição da imagem Docker
├── start-simir.sh       # Inicialização rápida do sistema
├── scripts/            # Scripts de gerenciamento e testes
│   ├── simir-control.sh           # Interface de controle completa
│   ├── simir-monitor.py           # Monitor avançado de port scan
│   ├── simir-autostart.sh         # Auto-inicialização no container
│   ├── entrypoint.sh              # Script de entrada do container
│   ├── check-interface.sh         # Verificação de interface de rede
│   ├── setup-permissions.sh       # Configuração de permissões
│   ├── compartilhar-internet.sh   # Compartilhamento de internet
│   ├── verificar-internet.sh      # Verificação de conectividade
│   ├── update-threat-feeds.sh     # Atualização de feeds de ameaças
│   ├── test-brute-force.sh        # Teste de detecção de força bruta
│   ├── test-intelligence.sh       # Teste do Intelligence Framework
│   ├── test-intelligence-complete.sh  # Teste completo de intelligence
│   └── test-complete.sh           # Teste completo do sistema
├── site/               # Scripts Zeek personalizados
│   ├── local.zeek                 # Configuração principal do Zeek
│   ├── port-scan-detector.zeek    # Detector de port scan
│   ├── brute-force-detector.zeek  # Detector de força bruta
│   ├── intelligence-framework.zeek # Framework de inteligência
│   ├── ddos-detector.zeek         # Detector de DDoS
│   ├── simir-notice-standards.zeek # Padrões de alertas SIMIR
│   └── intel/                     # Feeds de inteligência de ameaças
│       ├── malicious-ips.txt
│       ├── malicious-domains.txt
│       ├── malware-domains.txt
│       └── [outros feeds...]
├── logs/              # Logs do Zeek (ignorados pelo git exceto notice.log)
└── docs/              # Documentação do projeto
```

### Componentes da SIMIR

#### Container Zeek
- Engine principal de monitoramento de rede
- Scripts de detecção customizados (port scan, força bruta, DDoS, intelligence)
- Geração de logs estruturados em JSON/TSV

#### Monitor Python (simir-monitor.py)
- Análise em tempo real dos logs do Zeek
- Sistema de threat intelligence
- Detecção de padrões de ataque

#### Scripts de Gerenciamento
- simir-control.sh: Interface de controle principal
- Scripts de teste: Validação de detecções
- Scripts de atualização: Feeds de inteligência

---

##  Instalação e Configuração

### Pré-requisitos

#### Sistema Operacional
- **Linux** (Ubuntu, Debian, CentOS, etc.)
- **Docker** e **Docker Compose**
- **Git** para clonagem do repositório

#### Hardware Mínimo
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disco**: 10GB livre
- **Rede**: Interface para monitoramento

### Instalação Passo a Passo

#### 1. **Clonar o Repositório**
```bash
git clone <URL_DO_REPOSITORIO> simir
cd simir
```

#### 2. **Instalar Dependências**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose git python3

# CentOS/RHEL
sudo yum install -y docker docker-compose git python3

# Iniciar Docker
sudo systemctl start docker
sudo systemctl enable docker

# Adicionar usuário ao grupo docker (opcional)
sudo usermod -aG docker $USER
# (faça logout/login após este comando)
```

#### 3. **Configurar Interface de Rede**

**Identificar Interfaces Disponíveis:**
```bash
ip addr show
# ou
ifconfig
```

**Editar Configuração:**
```bash
# Edite docker-compose.yml
nano docker-compose.yml

# Altere a linha:
environment:
  - ZEEK_INTERFACE=sua_interface_aqui  # ex: eth0, enp0s3, etc.
```

#### 4. **Configuração Rápida**
```bash
# Inicialização automática
./start-simir.sh

# Passo a passo
docker-compose build
docker-compose up -d               # Iniciar container
./scripts/simir-control.sh start   # Iniciar monitor
```

#### 5. **Verificar Funcionamento**
```bash
# Ver status
./scripts/simir-control.sh status

# Ver logs
docker-compose logs -f

# Testar detecção
./scripts/simir-control.sh simulate
```

---

##  Arquivos de Log do Zeek

O Zeek gera diversos tipos de logs, cada um com informações específicas sobre diferentes aspectos do tráfego de rede.

### Localização dos Logs
```bash
# Dentro do container
/usr/local/zeek/spool/zeek/

# No host (via docker exec)
docker exec SIMIR_Z ls -la /usr/local/zeek/spool/zeek/
```

### Principais Arquivos de Log

#### 1. **conn.log** - Conexões de Rede
**Descrição**: Registra todas as conexões TCP, UDP e ICMP.

**Campos Principais**:
- `ts`: Timestamp da conexão
- `id.orig_h`: IP de origem
- `id.orig_p`: Porta de origem
- `id.resp_h`: IP de destino
- `id.resp_p`: Porta de destino
- `proto`: Protocolo (tcp/udp/icmp)
- `duration`: Duração da conexão
- `orig_bytes`: Bytes enviados pelo originador
- `resp_bytes`: Bytes enviados pelo respondedor
- `conn_state`: Estado da conexão

**Estados de Conexão Importantes**:
- `S0`: Tentativa de conexão sem resposta
- `S1`: Conexão estabelecida, não finalizada
- `SF`: Conexão normal, finalizada
- `REJ`: Conexão rejeitada
- `S2`: Conexão estabelecida, originador fechou
- `S3`: Conexão estabelecida, respondedor fechou

**Exemplo de Entrada**:
```json
{
  "ts": 1641895234.123456,
  "uid": "CwTLJM1KZJzqZJX7Ng",
  "id.orig_h": "192.168.1.100",
  "id.orig_p": 52341,
  "id.resp_h": "93.184.216.34",
  "id.resp_p": 80,
  "proto": "tcp",
  "duration": 0.164,
  "orig_bytes": 76,
  "resp_bytes": 295,
  "conn_state": "SF"
}
```

#### 2. **http.log** - Tráfego HTTP
**Descrição**: Detalha requisições e respostas HTTP.

**Campos Principais**:
- `method`: Método HTTP (GET, POST, etc.)
- `host`: Host solicitado
- `uri`: URI requisitada
- `status_code`: Código de resposta HTTP
- `user_agent`: User-Agent do cliente
- `request_body_len`: Tamanho do corpo da requisição
- `response_body_len`: Tamanho da resposta

**Exemplo**:
```json
{
  "ts": 1641895234.123456,
  "method": "GET",
  "host": "example.com",
  "uri": "/index.html",
  "status_code": 200,
  "user_agent": "Mozilla/5.0...",
  "request_body_len": 0,
  "response_body_len": 1270
}
```

#### 3. **dns.log** - Consultas DNS
**Descrição**: Registra todas as consultas e respostas DNS.

**Campos Principais**:
- `query`: Nome consultado
- `qtype_name`: Tipo de registro (A, AAAA, MX, etc.)
- `rcode_name`: Código de resposta (NOERROR, NXDOMAIN, etc.)
- `answers`: Respostas retornadas
- `TTL`: Time To Live dos registros

#### 4. **ssl.log** - Conexões TLS/SSL
**Descrição**: Detalhes sobre conexões criptografadas.

**Campos Principais**:
- `server_name`: Nome do servidor (SNI)
- `cert_chain_fuids`: IDs dos certificados
- `subject`: Subject do certificado
- `issuer`: Emissor do certificado
- `version`: Versão TLS/SSL

#### 5. **ssh.log** - Conexões SSH
**Descrição**: Informações sobre sessões SSH.

**Campos Principais**:
- `auth_success`: Sucesso da autenticação
- `auth_attempts`: Tentativas de autenticação
- `client`: Software cliente SSH
- `server`: Software servidor SSH

#### 6. **ftp.log** - Transferências FTP
**Descrição**: Atividade em servidores FTP.

**Campos Principais**:
- `user`: Usuário autenticado
- `password`: Senha (se em texto claro)
- `command`: Comando FTP executado
- `reply_code`: Código de resposta do servidor

#### 7. **smtp.log** - Email SMTP
**Descrição**: Transferência de emails via SMTP.

**Campos Principais**:
- `mailfrom`: Remetente
- `rcptto`: Destinatários
- `date`: Data do email
- `subject`: Assunto
- `helo`: Identificação HELO/EHLO

#### 8. **notice.log** - Alertas e Notices
**Descrição**: **LOG MAIS IMPORTANTE PARA A SIMIR**. Contém alertas gerados por scripts Zeek, incluindo detecções de port scan.

**Campos Principais**:
- `note`: Tipo de alerta
- `msg`: Mensagem descritiva
- `src`: IP de origem do alerta
- `dst`: IP de destino
- `actions`: Ações tomadas

**Tipos de Alertas Relevantes**:
- `PortScan::Port_Scan`: Port scan detectado
- `PortScan::Port_Scan_Target`: Host sendo escaneado
- `PortScan::Closed_Port_Access`: Tentativas em portas fechadas
- `BruteForce::SSH_Bruteforce`: Ataque de força bruta SSH detectado
- `BruteForce::FTP_Bruteforce`: Ataque de força bruta FTP detectado
- `BruteForce::HTTP_Bruteforce`: Ataque de força bruta HTTP detectado
- `BruteForce::Generic_Bruteforce`: Ataque de força bruta genérico detectado

**Exemplo de Port Scan**:
```json
{
  "ts": 1641895234.123456,
  "note": "PortScan::Port_Scan",
  "msg": "Port scan detectado de 192.168.1.100 para 10 hosts, 25 portas diferentes em 2m30s",
  "src": "192.168.1.100",
  "dst": "192.168.1.0/24",
  "actions": ["Notice::ACTION_LOG"]
}
```

**Exemplo de Força Bruta**:
```json
{
  "ts": 1641895234.123456,
  "note": "BruteForce::SSH_Bruteforce",
  "msg": "Possível ataque de força bruta SSH detectado de 192.168.1.100 para 192.168.1.10 (15 tentativas em 5 minutos)",
  "src": "192.168.1.100",
  "dst": "192.168.1.10",
  "actions": ["Notice::ACTION_LOG"]
}
```

#### 9. **files.log** - Transferências de Arquivos
**Descrição**: Arquivos transferidos via HTTP, FTP, SMTP, etc.

**Campos Principais**:
- `fuid`: ID único do arquivo
- `mime_type`: Tipo MIME
- `filename`: Nome do arquivo
- `source`: Fonte da transferência
- `is_orig`: Direção da transferência

#### 10. **intel.log** - Threat Intelligence
**Descrição**: Matches com feeds de threat intelligence.

**Campos Principais**:
- `indicator`: Indicador matched
- `indicator_type`: Tipo (IP, domain, etc.)
- `sources`: Fontes de intelligence

### Formato dos Logs

#### **TSV (Tab-Separated Values)**
Formato padrão mais antigo:
```
#separator \x09
#set_separator	,
#empty_field	(empty)
#unset_field	-
#path	conn
#open	2024-07-10-22-15-23
#fields	ts	uid	id.orig_h	id.orig_p	id.resp_h	id.resp_p	proto	service	duration
1641895234.123456	CwTLJM1KZJzqZJX7Ng	192.168.1.100	52341	93.184.216.34	80	tcp	http	0.164
```

#### **JSON**
Formato moderno configurado na SIMIR:
```json
{
  "ts": 1641895234.123456,
  "uid": "CwTLJM1KZJzqZJX7Ng",
  "id.orig_h": "192.168.1.100",
  "id.orig_p": 52341,
  "id.resp_h": "93.184.216.34",
  "id.resp_p": 80,
  "proto": "tcp",
  "service": "http",
  "duration": 0.164
}
```

### Analisando Logs

#### **Visualizar Logs em Tempo Real**
```bash
# Dentro do container
docker exec -it SIMIR_Z tail -f /usr/local/zeek/spool/zeek/conn.log

# Logs específicos
docker exec -it SIMIR_Z tail -f /usr/local/zeek/spool/zeek/notice.log  # Alertas
docker exec -it SIMIR_Z tail -f /usr/local/zeek/spool/zeek/http.log    # HTTP
docker exec -it SIMIR_Z tail -f /usr/local/zeek/spool/zeek/dns.log     # DNS
```

#### **Filtrar por IP**
```bash
# Conexões de um IP específico
docker exec SIMIR_Z grep "192.168.1.100" /usr/local/zeek/spool/zeek/conn.log

# Consultas DNS de um host
docker exec SIMIR_Z grep "192.168.1.100" /usr/local/zeek/spool/zeek/dns.log
```

#### **Analisar Port Scans**
```bash
# Todos os alertas de port scan
docker exec SIMIR_Z grep "Port_Scan" /usr/local/zeek/spool/zeek/notice.log

# Conexões rejeitadas (possíveis scans)
docker exec SIMIR_Z grep "REJ\|S0" /usr/local/zeek/spool/zeek/conn.log
```

---

##  Sistema de Detecção de Port Scan

### Como Funciona a Detecção

#### 1. **Monitoramento de Conexões**
O script `port-scan-detector.zeek` monitora o evento `connection_state_remove`, que é gerado quando uma conexão termina.

#### 2. **Rastreamento de Padrões**
Para cada IP, o sistema mantém:
- **Hosts contactados**: Lista de IPs de destino
- **Portas acessadas**: Lista de portas diferentes
- **Número de conexões**: Contador total
- **Timestamps**: Primeiro e último evento

#### 3. **Algoritmos de Detecção**

##### **Port Scan Horizontal**
```zeek
# Detecta quando um IP escaneia múltiplas portas
if (|scanner$ports| >= port_scan_threshold) {
    # Gerar alerta de port scan
}
```

##### **Port Scan Vertical**
```zeek
# Detecta quando um IP é escaneado por múltiplos hosts
if (|target$hosts| >= port_scan_threshold) {
    # Gerar alerta de alvo de scan
}
```

##### **Tentativas em Portas Fechadas**
```zeek
# Detecta múltiplas tentativas rejeitadas
if (connection_failed && scanner$connections >= closed_port_threshold) {
    # Gerar alerta de portas fechadas
}
```

#### 4. **Classificação de Severidade**
O monitor Python analisa os alertas e classifica:

**Fatores de Risco**:
- Número de portas escaneadas
- Portas críticas envolvidas (SSH, RDP, etc.)
- Histórico do IP atacante
- Velocidade do scan

**Níveis de Severidade**:
- **LOW** (1-2 pontos): Atividade suspeita leve
- **MEDIUM** (3-4 pontos): Scan moderado
- **HIGH** (5-7 pontos): Scan intenso
- **CRITICAL** (8+ pontos): Ataque direcionado

### Configurações de Detecção

#### **Parâmetros Ajustáveis**
```json
{
  "detection": {
    "port_scan_threshold": 10,          // Portas para considerar scan
    "time_window_minutes": 5,           // Janela de análise
    "suspicious_ports": [22, 23, 80, 443, 3389, 445, 135, 139],
    "whitelist_ips": ["127.0.0.1", "::1"],
    "closed_port_threshold": 5          // Tentativas em portas fechadas
  }
}
```

#### **Portas Monitoradas**
- **SSH (22)**: Acesso remoto
- **Telnet (23)**: Acesso inseguro
- **HTTP (80)**: Web servers
- **HTTPS (443)**: Web seguro
- **SMB (445)**: Compartilhamento Windows
- **RDP (3389)**: Desktop remoto
- **NetBIOS (135, 139)**: Serviços Windows

### Tipos de Alertas Gerados

#### 1. **Port_Scan**
```
Port scan detectado de 192.168.1.100 para 15 hosts, 25 portas diferentes em 3m45s
```

#### 2. **Port_Scan_Target**
```
Host 192.168.1.10 está sendo escaneado por 5 hosts diferentes
```

#### 3. **Closed_Port_Access**
```
Múltiplas tentativas em portas fechadas de 192.168.1.100 (12 tentativas)
```

### Rate Limiting e Anti-Spam

#### **Cooldown de Alertas**
- **5 minutos** entre alertas similares
- **Máximo 10 alertas** por hora por tipo
- **Severidade CRITICAL** ignora alguns limites

#### **Deduplicação**
- IDs únicos por tipo de alerta + IP
- Histórico de alertas enviados
- Prevenção de spam por scans contínuos

---

##  Sistema de Detecção de Força Bruta

### Visão Geral

O sistema de detecção de força bruta da SIMIR complementa a detecção de port scan, identificando tentativas repetidas de autenticação em serviços como SSH, FTP e HTTP. Este sistema monitora padrões de comportamento suspeito que podem indicar ataques automatizados.

### Como Funciona a Detecção

#### 1. **Monitoramento de Protocolos**
O script `brute-force-detector.zeek` monitora múltiplos protocolos:
- **SSH**: Eventos de capacidades do servidor (`ssh_server_capabilities`)
- **FTP**: Respostas de autenticação (`ftp_reply`)
- **HTTP**: Códigos de resposta de autenticação (`http_reply`)
- **Genérico**: Análise de conexões rejeitadas (`connection_state_remove`)

#### 2. **Rastreamento de Tentativas**
Para cada IP de origem, o sistema mantém:
- **Contador de tentativas**: Número total de tentativas de autenticação
- **Timestamps**: Primeira e última tentativa
- **Alvo específico**: IP de destino sendo atacado
- **Tipo de protocolo**: SSH, FTP, HTTP ou genérico

#### 3. **Algoritmos de Detecção**

##### **Detecção SSH**
```zeek
# Detecta múltiplas conexões SSH do mesmo IP
if (attempts >= ssh_bruteforce_threshold) {
    # Gerar alerta de força bruta SSH
}
```

##### **Detecção FTP**
```zeek
# Monitora códigos de erro FTP (530 = login incorrect)
if (reply_code == 530 && attempts >= ftp_bruteforce_threshold) {
    # Gerar alerta de força bruta FTP
}
```

##### **Detecção HTTP**
```zeek
# Monitora códigos 401/403 (unauthorized/forbidden)
if ((status_code == 401 || status_code == 403) && attempts >= http_bruteforce_threshold) {
    # Gerar alerta de força bruta HTTP
}
```

##### **Detecção Genérica**
```zeek
# Analisa conexões rejeitadas ou falhadas
if (conn_state in rejected_states && attempts >= generic_bruteforce_threshold) {
    # Gerar alerta de força bruta genérica
}
```

### Configurações de Detecção

#### **Parâmetros Configuráveis**
```zeek
# Thresholds de detecção
const ssh_bruteforce_threshold = 10 &redef;
const ftp_bruteforce_threshold = 8 &redef;
const http_bruteforce_threshold = 15 &redef;
const generic_bruteforce_threshold = 20 &redef;

# Janela de tempo para análise
const bruteforce_time_window = 5min &redef;
```

#### **Protocolos Monitorados**
- **SSH (porta 22)**: Tentativas de login remoto
- **FTP (porta 21)**: Autenticação em servidores FTP
- **HTTP/HTTPS (portas 80/443)**: Ataques a formulários web
- **Genérico**: Qualquer padrão de conexões rejeitadas

### Tipos de Alertas Gerados

#### 1. **SSH_Bruteforce**
```
Possível ataque de força bruta SSH detectado de 192.168.1.100 para 192.168.1.10 (15 tentativas em 5 minutos)
```

#### 2. **FTP_Bruteforce**
```
Possível ataque de força bruta FTP detectado de 10.0.0.50 para 10.0.0.100 (12 tentativas em 3 minutos)
```

#### 3. **HTTP_Bruteforce**
```
Possível ataque de força bruta HTTP detectado de 203.0.113.25 para 192.168.1.5 (25 tentativas em 8 minutos)
```

#### 4. **Generic_Bruteforce**
```
Possível ataque de força bruta detectado de 172.16.0.10 para 172.16.0.20 (30 tentativas em 10 minutos)
```

### Integração com SIMIR

#### **Ativação do Sistema**
O sistema é ativado automaticamente quando os scripts Zeek são carregados:

```bash
# Verificar se está ativo
docker exec SIMIR_Z grep "brute-force-detector" /usr/local/zeek/logs/current/loaded_scripts.log

# Verificar alertas em tempo real
docker exec SIMIR_Z tail -f /usr/local/zeek/logs/current/notice.log | grep BruteForce
```

#### **Teste do Sistema**
```bash
# Teste direto
./scripts/test-brute-force.sh
```

#### **Opções de Teste Disponíveis**
```bash
# Teste completo do sistema (todos os detectores)
./scripts/test-complete.sh

# Teste de detecção de porta bruta
./scripts/test-brute-force.sh

# Teste de intelligence framework
./scripts/test-intelligence.sh
./scripts/test-intelligence-complete.sh
```

### Logs e Monitoramento

#### **Verificar Detecções**
```bash
# Alertas de força bruta recentes
docker exec SIMIR_Z grep "BruteForce::" /usr/local/zeek/logs/current/notice.log

# Estatísticas por tipo
docker exec SIMIR_Z grep "BruteForce::" /usr/local/zeek/logs/current/notice.log | cut -d'"' -f8 | sort | uniq -c

# Monitoramento em tempo real
docker exec SIMIR_Z tail -f /usr/local/zeek/logs/current/notice.log | grep --color=always "BruteForce"
```

#### **Análise de Padrões**
```bash
# IPs mais ativos em ataques
docker exec SIMIR_Z grep "BruteForce::" /usr/local/zeek/logs/current/notice.log | grep -o '"src":"[^"]*"' | sort | uniq -c | sort -nr

# Alvos mais atacados
docker exec SIMIR_Z grep "BruteForce::" /usr/local/zeek/logs/current/notice.log | grep -o '"dst":"[^"]*"' | sort | uniq -c | sort -nr
```

### Prevenção de Falsos Positivos

#### **Lista Branca (Whitelist)**
Para evitar alertas desnecessários, configure IPs confiáveis:

```zeek
# Adicionar IPs confiáveis
const bruteforce_whitelist: set[addr] = {
    127.0.0.1,      # Localhost
    192.168.1.1,    # Gateway
    10.0.0.100,     # Servidor de monitoramento
} &redef;
```

#### **Ajuste de Sensibilidade**
```zeek
# Para ambientes com mais tráfego legítimo
const ssh_bruteforce_threshold = 20 &redef;     # Aumentar threshold
const bruteforce_time_window = 10min &redef;    # Aumentar janela de tempo

# Para ambientes mais sensíveis
const ssh_bruteforce_threshold = 5 &redef;      # Diminuir threshold
const bruteforce_time_window = 2min &redef;     # Diminuir janela de tempo
```

### Limitações e Considerações

#### **Limitações Atuais**
- **SSH**: Detecta conexões múltiplas, não falhas de autenticação específicas
- **Criptografia**: Não analisa conteúdo de conexões criptografadas
- **Protocolos customizados**: Limitado aos protocolos padrão suportados

#### **Funcionalidades Futuras**
- Integração com logs de sistema (auth.log, secure.log)
- Detecção de força bruta em outros protocolos (SMTP, IMAP, RDP)
- Análise comportamental avançada
- Integração com threat intelligence feeds
- Rate limiting automático via iptables

### Troubleshooting

#### **Sistema Não Detecta Ataques**
```bash
# Verificar se scripts estão carregados
docker exec SIMIR_Z zeekctl status
docker exec SIMIR_Z grep "brute-force-detector" /usr/local/zeek/logs/current/loaded_scripts.log

# Reinstalar scripts se necessário
docker exec SIMIR_Z zeekctl install
docker exec SIMIR_Z zeekctl restart
```

#### **Muitos Falsos Positivos**
```bash
# Ajustar thresholds
nano site/brute-force-detector.zeek
# Aumentar valores de *_bruteforce_threshold

# Adicionar IPs à whitelist
# Editar bruteforce_whitelist no script
```

#### **Teste Manual**
```bash
# Executar teste de força bruta
./scripts/test-brute-force.sh

# Verificar se alertas são gerados
docker exec SIMIR_Z tail -10 /usr/local/zeek/logs/current/notice.log
```

---

## 🧠 Intelligence Framework

### O que é o Intelligence Framework

O **Intelligence Framework** do Zeek é um sistema avançado que permite usar **feeds de inteligência de ameaças** (IOCs - Indicators of Compromise) para detectar automaticamente atividades maliciosas conhecidas. Este sistema compara o tráfego de rede observado contra bases de dados de indicadores maliciosos.

### Como Funciona

O framework monitora continuamente:
- **IPs maliciosos** em conexões de rede
- **Domínios maliciosos** em consultas DNS
- **URLs maliciosas** em requisições HTTP
- **Hashes de arquivos** maliciosos
- **Outros indicadores** personalizados

```
[Tráfego de Rede] → [Intelligence Framework] → [Comparação com IOCs] → [Alertas]
```

### Arquitetura do Sistema

#### **Componentes Principais**
1. **intelligence-framework.zeek**: Script principal de detecção
2. **Feeds de IOCs**: Bases de dados de indicadores maliciosos
3. **Sistema de alertas**: Notificações quando IOCs são encontrados
4. **Logs de inteligência**: Registro detalhado das detecções

#### **Tipos de IOCs Suportados**
- `Intel::ADDR`: Endereços IP maliciosos
- `Intel::DOMAIN`: Domínios maliciosos
- `Intel::URL`: URLs maliciosas
- `Intel::FILE_HASH`: Hashes de arquivos maliciosos
- `Intel::EMAIL`: Endereços de email maliciosos
- `Intel::USER_NAME`: Nomes de usuário suspeitos

### Configuração e Feeds

#### **Estrutura de Feeds**
```bash
site/intel/
├── malicious-ips.txt      # IPs maliciosos
├── malicious-domains.txt  # Domínios maliciosos
├── malicious-urls.txt     # URLs maliciosas
└── backup/                # Backups automáticos
```

#### **Formato dos Feeds**
```bash
# Exemplo: malicious-ips.txt
#fields	indicator	indicator_type	meta.source	meta.desc
185.220.100.240	Intel::ADDR	TorProject	Tor exit node
192.168.100.100	Intel::ADDR	Internal	IP suspeito interno
```

### Detecções e Alertas

#### **Tipos de Alertas**
- **Intelligence::Intel_Hit**: Indicador genérico detectado
- **Intelligence::Malicious_IP**: IP malicioso identificado
- **Intelligence::Malicious_Domain**: Domínio malicioso acessado
- **Intelligence::Malicious_URL**: URL maliciosa acessada
- **Intelligence::Malicious_Hash**: Hash malicioso encontrado

#### **Exemplo de Alerta**
```json
{
  "ts": 1754608200.123456,
  "note": "Intelligence::Malicious_IP",
  "msg": "IP malicioso detectado: 185.220.100.240 (Fonte: TorProject) - Tor exit node",
  "src": "192.168.1.100",
  "actions": ["Notice::ACTION_LOG"],
  "suppress_for": 3600.0
}
```

### Uso e Operação

#### **Teste do Sistema**
```bash
# Teste básico
./scripts/test-intelligence.sh

# Teste completo
./scripts/test-intelligence-complete.sh
```

#### **Atualização de Feeds**
```bash
# Atualizar feeds de inteligência
./scripts/update-threat-feeds.sh
```

#### **Visualização de Logs**
```bash
# Ver logs de intelligence
tail -f logs/notice.log | grep -i "intel\|malicious"
docker exec SIMIR_Z tail -f /usr/local/zeek/logs/current/intel.log
```

### Integração com Feeds Externos

#### **Feeds Públicos Recomendados**
- **Abuse.ch**: Feodo Tracker, URLhaus
- **Malware Domain List**: Domínios maliciosos
- **Tor Project**: Exit nodes
- **Threat Intelligence Platforms**: Commercial feeds

#### **Automação de Updates**
```bash
# Configurar cron para atualizações automáticas
crontab -e

# Atualizar feeds a cada 6 horas (ajuste o caminho para sua instalação SIMIR)
0 */6 * * * /caminho/para/SIMIR/scripts/update-threat-feeds.sh >/dev/null 2>&1
```

### Personalização

#### **Adicionando Feeds Customizados**
```bash
# Criar novo feed
echo "#fields	indicator	indicator_type	meta.source	meta.desc" > site/intel/custom-feed.txt
echo "evil.domain.com	Intel::DOMAIN	Custom	Domínio interno malicioso" >> site/intel/custom-feed.txt

# Atualizar configuração em intelligence-framework.zeek
nano site/intelligence-framework.zeek
# Adicionar linha: "/usr/local/zeek/share/zeek/site/intel/custom-feed.txt"
```

#### **Configuração de Thresholds**
```zeek
# Em intelligence-framework.zeek
const intel_suppress_time = 1800.0 &redef;  # 30 minutos
const enable_intel_logging = T &redef;
```

### Monitoramento e Métricas

#### **Comandos de Verificação**
```bash
# Verificar feeds carregados
docker exec SIMIR_Z zeek -e "print Intel::read_files;"

# Estatísticas de inteligência
docker exec SIMIR_Z grep -c "Intel::" /usr/local/zeek/logs/current/intel.log

# Status do framework
docker exec SIMIR_Z zeekctl diag | grep -i intel
```

#### **Análise de Performance**
```bash
# Contar IOCs por tipo
grep "Intel::" logs/notice_PortScan_BruteForce.log | \
  jq -r '.note' | sort | uniq -c | sort -nr

# Top IPs maliciosos detectados
grep "Malicious_IP" logs/notice_PortScan_BruteForce.log | \
  jq -r '.src' | sort | uniq -c | sort -nr | head -10
```

### Troubleshooting

#### **Framework Não Carrega**
```bash
# Verificar sintaxe dos scripts
docker exec SIMIR_Z zeek -g site/intelligence-framework.zeek

# Verificar logs de erro
docker exec SIMIR_Z tail /usr/local/zeek/logs/current/stderr.log
```

#### **Feeds Não São Carregados**
```bash
# Verificar formato dos feeds
head -5 site/intel/malicious-ips.txt

# Verificar permissões
ls -la site/intel/

# Recriar índices
docker exec SIMIR_Z zeekctl install
docker exec SIMIR_Z zeekctl restart
```

#### **Muitos Falsos Positivos**
```bash
# Filtrar IPs locais/conhecidos
# Adicionar whitelist no intelligence-framework.zeek
const intel_whitelist_subnets = { 192.168.0.0/16, 10.0.0.0/8 } &redef;
```

---

##  Gerenciamento do Sistema

### Scripts de Controle

#### **simir-control.sh** - Interface Principal
```bash
# Menu interativo
./scripts/simir-control.sh

# Comandos diretos
./scripts/simir-control.sh configure     # Configurar email
./scripts/simir-control.sh start         # Iniciar tudo
./scripts/simir-control.sh stop          # Parar tudo
./scripts/simir-control.sh status        # Ver status
./scripts/simir-control.sh test-email    # Testar email
./scripts/simir-control.sh simulate      # Simular port scan
./scripts/simir-control.sh test-bruteforce # Testar força bruta
./scripts/simir-control.sh logs monitor  # Ver logs do monitor
```

#### **start-simir.sh** - Inicialização Rápida
```bash
# Configuração e inicialização automática
./start-simir.sh
```

### Comandos Docker

#### **Gerenciamento de Container**
```bash
# Construir imagem
docker-compose build

# Iniciar serviços
docker-compose up -d

# Ver status
docker-compose ps

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down

# Acessar shell do container
docker exec -it SIMIR_Z bash
```

#### **Debugging**
```bash
# Logs detalhados
docker-compose logs --tail=100 SIMIR_Z

# Verificar processos dentro do container
docker exec SIMIR_Z ps aux

# Verificar arquivos de log
docker exec SIMIR_Z ls -la /usr/local/zeek/spool/zeek/

# Verificar configuração Zeek
docker exec SIMIR_Z zeekctl status
```

### Monitoramento de Status

#### **Status do Sistema**
```bash
./scripts/simir-control.sh status
```

**Saída Exemplo**:
```
=== STATUS DO SISTEMA SIMIR ===

Container Zeek:
  [OK] Rodando
  📅 Iniciado em: 2024-07-10
   Logs: Disponíveis

Monitor de Port Scan:
  [OK] Rodando (PID: 12345)
   Logs: 150 linhas
  ⏰ Última atividade: 2024-07-10 22:15:30

Configuração de Email:
  [OK] Configurado
   Remetente: alert@exemplo.com
  📬 Destinatário: rafaelbartorres@gmail.com

Alertas Recentes:
  📨 Total de alertas enviados: 3
   Últimos alertas:
    • 2024-07-10 22:10:15 - Port scan detectado...
    • 2024-07-10 21:45:30 - Tentativas em portas fechadas...
```

#### **Logs de Monitoramento**
```bash
# Logs da Sonda SIMIR
tail -f /tmp/simir_monitor.log

# Logs específicos de alertas
grep -i "alert\|port scan" /tmp/simir_monitor.log

# Status de saúde do container
docker exec SIMIR_Z zeekctl status
```

### Configurações Avançadas

#### **Ajustar Threshold de Detecção**
```bash
# Editar configuração
nano /tmp/simir_config.json

# Ou via variáveis de ambiente
export SIMIR_PORT_SCAN_THRESHOLD=15
export SIMIR_TIME_WINDOW_MINUTES=10
```

#### **Adicionar IPs à Whitelist**
```json
{
  "detection": {
    "whitelist_ips": [
      "127.0.0.1",
      "::1",
      "192.168.1.1",      // Gateway
      "10.0.0.100"        // Scanner legítimo
    ]
  }
}
```

#### **Personalizar Portas Monitoradas**
```json
{
  "detection": {
    "suspicious_ports": [
      22,    // SSH
      23,    // Telnet
      80,    // HTTP
      443,   // HTTPS
      3389,  // RDP
      445,   // SMB
      1433,  // SQL Server
      3306,  // MySQL
      5432   // PostgreSQL
    ]
  }
}
```

---

##  Troubleshooting

### Problemas Comuns

#### 1. **Container Não Inicia**

**Sintomas**:
```bash
docker-compose ps
# Mostra container como "Exit 1" ou similar
```

**Diagnóstico**:
```bash
docker-compose logs SIMIR_Z
```

**Soluções Comuns**:

##### **Interface de Rede Inválida**
```bash
# Verificar interfaces disponíveis
ip addr show

# Atualizar docker-compose.yml
nano docker-compose.yml
# Alterar ZEEK_INTERFACE para interface correta
```

##### **Permissões Insuficientes**
```bash
# Executar com privilégios
sudo ./scripts/setup-permissions.sh

# Ou executar container como root
# Adicionar em docker-compose.yml:
# user: root
```

#### 2. **Zeek Não Detecta Tráfego**

**Sintomas**:
- Logs vazios ou muito poucos
- Ausência de conn.log ou logs com poucos registros

**Diagnóstico**:
```bash
# Verificar se Zeek está rodando
docker exec SIMIR_Z zeekctl status

# Verificar interface
docker exec SIMIR_Z ip addr show

# Verificar se há tráfego na interface
docker exec SIMIR_Z tcpdump -i eth0 -c 10
```

**Soluções**:

##### **Interface em Modo Bridge**
```bash
# Configurar interface em modo promíscuo
sudo ip link set dev eth0 promisc on

# Verificar configuração
ip link show eth0
```

##### **Firewall Bloqueando**
```bash
# Verificar regras iptables
sudo iptables -L

# Temporariamente desabilitar firewall
sudo iptables -F
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT
sudo iptables -P OUTPUT ACCEPT
```

#### 3. **Email Não Funciona**

**Sintomas**:
```
[ERRO] ERRO: (535, b'5.7.8 Username and Password not accepted')
```

**Soluções**:

##### **Gerar Nova App Password**
1. Acesse: https://myaccount.google.com/security
2. Vá em "Senhas de app"
3. Gere nova senha para "Mail"
4. Reconfigure: `./scripts/config-email.sh`

##### **Verificar 2FA**
```bash
# Confirmar que verificação em duas etapas está ativa
# Na conta Google: Segurança > Verificação em duas etapas
```

##### **Testar Configuração Manualmente**
```bash
# Teste direto Python
python3 -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('seu_email@gmail.com', 'app_password_aqui')
print('[OK] Autenticação OK')
server.quit()
"
```

#### 4. **Sonda SIMIR Não Inicia**

**Sintomas**:
```bash
./scripts/simir-control.sh status
# Monitor de Port Scan: Parado
```

**Diagnóstico**:
```bash
# Verificar logs de erro
cat /tmp/simir_monitor.log

# Verificar se Python está disponível
python3 --version

# Testar script manualmente
python3 ./scripts/simir-monitor.py
```

**Soluções**:

##### **Dependências Python Faltando**
```bash
# Instalar dependências
sudo apt install python3-pip
```

##### **Arquivo de Configuração Inválido**
```bash
# Verificar configuração JSON
cat /tmp/simir_config.json | python3 -m json.tool

# Recriar container
docker-compose down
docker-compose up -d
```

#### 5. **Notice.log Não Sendo Criado**

**Sintomas**:
- Container Zeek rodando normalmente
- Outros logs (conn.log, dns.log, etc.) sendo gerados
- Ausência do arquivo notice.log

**Diagnóstico**:
```bash
# Verificar se scripts personalizados estão carregados
docker exec SIMIR_Z cat /usr/local/zeek/logs/current/loaded_scripts.log | grep site

# Verificar erros de sintaxe
docker exec SIMIR_Z zeekctl diag
```

**Soluções**:

##### **Scripts Não Carregados**
```bash
# Instalar scripts no Zeek (SEMPRE necessário após modificações)
docker exec SIMIR_Z zeekctl install

# Reiniciar Zeek
docker exec SIMIR_Z zeekctl restart

# Verificar se scripts foram carregados
docker exec SIMIR_Z cat /usr/local/zeek/logs/current/loaded_scripts.log | grep port-scan-detector
```

##### **Erro de Sintaxe no Notice::policy**
```zeek
# INCORRETO (vai gerar erro):
redef Notice::policy += {
    [$pred(n: Notice::Info) = { return T; },
     $action = Notice::ACTION_LOG]
};

# CORRETO:
hook Notice::policy(n: Notice::Info)
{
    add n$actions[Notice::ACTION_LOG];
}
```

##### **Falta de Tráfego para Gerar Notices**
```bash
# Gerar tráfego para testar
docker exec SIMIR_Z curl -s google.com > /dev/null

# Ou simular port scan
nmap -sS -F localhost
```

**Arquivos Importantes**:
- Scripts fonte: `/usr/local/zeek/share/zeek/site/`
- Scripts instalados: `/usr/local/zeek/spool/installed-scripts-do-not-touch/site/`
- Notice.log: `/usr/local/zeek/logs/current/notice.log`

#### 6. **Port Scan Não Detectado**

**Sintomas**:
- Alertas de port scan não aparecem no notice.log
- Comportamento inesperado na detecção de scans

**Diagnóstico**:
```bash
# Verificar últimos eventos no notice.log
docker exec SIMIR_Z tail -n 50 /usr/local/zeek/logs/current/notice.log

# Verificar configuração atual do Zeek
docker exec SIMIR_Z cat /usr/local/zeek/etc/zeekctl.cfg | grep -i "port-scan-detector"

# Testar detecção manualmente
zeek -r <(echo "GET / HTTP/1.1
Host: example.com
Connection: close

") -C -s http.log
```

**Soluções**:

##### **Reinstalar Scripts de Detecção**
```bash
# Reinstalar scripts padrão do Zeek
docker exec SIMIR_Z zeekctl install

# Reiniciar Zeek
docker exec SIMIR_Z zeekctl restart
```

##### **Ajustar Sensibilidade de Detecção**
```json
{
  "detection": {
    "port_scan_threshold": 5,
    "time_window_minutes": 1
  }
}
```

##### **Verificar Conflitos com Outros Sistemas**
```bash
# Verificar se há outros IDS/IPS ativos
sudo iptables -L -v -n

# Desabilitar temporariamente outros sistemas de segurança
sudo systemctl stop snort
sudo systemctl stop suricata
```

#### 7. **Sistema de Força Bruta Não Detecta Ataques**

**Sintomas**:
- Ausência de alertas `BruteForce::*` no notice.log
- Comportamento inesperado na detecção de tentativas de força bruta

**Diagnóstico**:
```bash
# Verificar se script de força bruta está carregado
docker exec SIMIR_Z grep "brute-force-detector" /usr/local/zeek/logs/current/loaded_scripts.log

# Verificar últimos alertas de força bruta
docker exec SIMIR_Z grep "BruteForce::" /usr/local/zeek/logs/current/notice.log

# Testar detecção manualmente
./scripts/test-brute-force.sh
```

**Soluções Comuns**:

##### **Script Não Carregado**
```bash
# Verificar se está no local.zeek
docker exec SIMIR_Z grep "brute-force-detector" /usr/local/zeek/share/zeek/site/local.zeek

# Reinstalar scripts
docker exec SIMIR_Z zeekctl install
docker exec SIMIR_Z zeekctl restart
```

##### **Thresholds Muito Altos**
```bash
# Verificar configuração atual
docker exec SIMIR_Z grep "_threshold" /usr/local/zeek/share/zeek/site/brute-force-detector.zeek

# Ajustar para valores mais sensíveis
# Editar o arquivo e diminuir os valores de threshold
```

##### **Falta de Tráfego para Detectar**
```bash
# Simular tentativas SSH
for i in {1..15}; do ssh -o ConnectTimeout=1 invalid_user@localhost 2>/dev/null; done

# Verificar se alertas foram gerados
docker exec SIMIR_Z tail -10 /usr/local/zeek/logs/current/notice.log | grep BruteForce
```

#### 8. **Muitos Falsos Positivos de Força Bruta**

**Sintomas**:
- Excesso de alertas `BruteForce::*` para atividade legítima
- Alertas para IPs conhecidos e confiáveis

**Soluções**:

##### **Configurar Whitelist**
```bash
# Editar script de detecção
nano site/brute-force-detector.zeek

# Adicionar IPs confiáveis em bruteforce_whitelist
const bruteforce_whitelist: set[addr] = {
    192.168.1.1,    # Gateway
    10.0.0.100,     # Servidor de backup
} &redef;
```

##### **Ajustar Sensibilidade**
```bash
# Aumentar thresholds
const ssh_bruteforce_threshold = 20 &redef;    # Era 10
const ftp_bruteforce_threshold = 15 &redef;    # Era 8
const http_bruteforce_threshold = 30 &redef;   # Era 15

# Aumentar janela de tempo
const bruteforce_time_window = 10min &redef;   # Era 5min
```

---

### [OK] Validação Final do Sistema

#### **Verificar Status Completo**
```bash
# Status geral
./scripts/simir-control.sh status

# Verificar se notice.log existe e está sendo gerado
docker exec SIMIR_Z ls -la /usr/local/zeek/logs/current/notice.log
docker exec SIMIR_Z tail -5 /usr/local/zeek/logs/current/notice.log

# Verificar scripts carregados
docker exec SIMIR_Z grep "port-scan-detector\|brute-force-detector\|local.zeek" /usr/local/zeek/logs/current/loaded_scripts.log
```

#### **Teste de Funcionalidade**
```bash
# 1. Testar detecção de port scan
nmap -sS -F localhost

# 2. Testar detecção de força bruta
./scripts/test-brute-force.sh

# 3. Aguardar alguns segundos e verificar alertas
sleep 10
docker exec SIMIR_Z tail -10 /usr/local/zeek/logs/current/notice.log

# Verificar alertas de força bruta especificamente
docker exec SIMIR_Z grep "BruteForce::" /usr/local/zeek/logs/current/notice.log

# 4. Verificar logs do monitor
tail -20 /tmp/simir_monitor.log

# 5. Testar email (se configurado)
./scripts/simir-control.sh test-email
```

#### **Indicadores de Sucesso**
- [OK] Container Zeek rodando (`docker-compose ps`)
- [OK] Logs sendo gerados (`conn.log`, `dns.log`, `http.log`)
- [OK] **notice.log existe e contém alertas**
- [OK] Scripts personalizados carregados (`port-scan-detector.zeek` e `brute-force-detector.zeek`)
- [OK] Sonda SIMIR processando logs
- [OK] Detecção de port scan funcional
- [OK] Detecção de força bruta funcional
- [OK] Emails funcionando (se configurado)

---

##  Monitoramento Avançado

### Integração com Sistemas de Monitoramento

#### 1. **Prometheus/Grafana**
- Exportar métricas do Zeek para Prometheus
- Criar dashboards no Grafana para visualização

#### 2. **ELK Stack (Elasticsearch, Logstash, Kibana)**
- Enviar logs do Zeek para Elasticsearch
- Analisar e visualizar logs no Kibana

#### 3. **Splunk**
- Integrar com o Splunk para análise avançada
- Criar alertas e relatórios personalizados

### Exemplos de Consultas e Dashboards

#### **Grafana**
- **Painel de Conexões por Protocolo**
  - Gráfico de linhas mostrando número de conexões por protocolo (TCP, UDP, ICMP)
- **Mapa de Calor de Port Scans**
  - Mapa de calor mostrando frequência de tentativas de conexão por porta

#### **Kibana**
- **Descoberta de Logs**
  - Consultar logs em tempo real
  - Filtrar por IP, porta, protocolo, etc.
- **Alertas de Segurança**
  - Criar alertas baseados em consultas salvas
  - Notificações por email, webhook, etc.

#### **Splunk**
- **Painel de Monitoramento em Tempo Real**
  - Visualizar eventos do Zeek em tempo real
  - Filtrar por tipo de evento, severidade, etc.
- **Relatórios Agendados**
  - Criar relatórios diários/semanais sobre atividades suspeitas
  - Envio automático por email

### Exemplos de Consultas

#### **Elasticsearch**
```json
GET zeek-*/_search
{
  "query": {
    "match": {
      "note": "PortScan::Port_Scan"
    }
  }
}
```

#### **Splunk**
```spl
index=zeek sourcetype=zeek:notice note="PortScan::Port_Scan"
| stats count by src, dst
| sort -count
```

---

##  Sistema de Detecção de Exfiltração de Dados

### O que é Exfiltração de Dados?

**Exfiltração de dados** (Data Exfiltration) é o processo não autorizado de transferir dados de um sistema comprometido para um local controlado pelo atacante. É frequentemente o objetivo final de um ataque bem-sucedido.

### Técnicas Comuns

#### **Upload Direto**
- Transferência via HTTP/HTTPS POST
- FTP/SFTP upload
- Email com anexos grandes
- Cloud storage (Dropbox, Google Drive)

#### **Download Massivo**
- Roubo de bases de dados
- Backup files
- Código-fonte
- Documentos confidenciais

#### **Transferências Múltiplas**
- Dividir dados em múltiplos pedaços
- Enviar para vários destinos
- Evitar detecção por volume único

### Como o SIMIR Detecta

O detector `data-exfiltration-detector.zeek` monitora:

1. **Volume de Upload**: Transferências grandes de dados enviados
2. **Volume de Download**: Downloads massivos suspeitos
3. **Múltiplos Destinos**: Uploads para vários IPs externos
4. **Padrões Temporais**: Transferências rápidas em curto período

### Tipos de Alertas

#### 1. **Large Upload**
```
[DATA-EXFIL] [HIGH] Large Upload: 192.168.1.100 uploaded 150.50 MB in 3m20s
```
**Significado**: Host enviou mais de 100 MB em curto período
**Threshold**: 100 MB em 5 minutos

#### 2. **Massive Download**
```
[DATA-EXFIL] [HIGH] Massive Download: 192.168.1.100 downloaded 750.25 MB in 4m15s
```
**Significado**: Host recebeu mais de 500 MB
**Threshold**: 500 MB em 5 minutos

#### 3. **Massive Transfer**
```
[DATA-EXFIL] [CRITICAL] Massive Transfer: 192.168.1.100 transferred 1.25 GB in 8m30s
```
**Significado**: Transferência total > 1 GB (upload + download)
**Threshold**: 1 GB total

#### 4. **Multiple External Transfers**
```
[DATA-EXFIL] [CRITICAL] Multiple External Transfers: 192.168.1.100 uploaded 250 MB to 8 different external IPs
```
**Significado**: Dados divididos e enviados para múltiplos destinos
**Threshold**: 50 MB para 5+ IPs externos

### Campos no notice.log

```
proto: tcp
note: DataExfil::Large_Upload
msg: Large Upload: 192.168.1.100 uploaded 150.50 MB in 3m20s
sub: upload
src: 192.168.1.100
dst: -
p: -
n: 150.50
```

### Configuração

```zeek
# Em local.zeek ou data-exfiltration-detector.zeek
redef DataExfil::large_upload_threshold = 100 * 1024 * 1024;      # 100 MB
redef DataExfil::massive_download_threshold = 500 * 1024 * 1024;  # 500 MB
redef DataExfil::massive_threshold = 1024 * 1024 * 1024;          # 1 GB
redef DataExfil::tracking_interval = 5min;                        # Janela
redef DataExfil::external_transfer_threshold = 50 * 1024 * 1024;  # 50 MB
redef DataExfil::external_ip_threshold = 5;                       # IPs
```

### Teste Manual

```bash
# Simular upload grande
dd if=/dev/zero of=test_file bs=1M count=150
curl -F "file=@test_file" http://external-server/upload

# Simular download massivo
wget --limit-rate=10M http://server/large_database_backup.sql

# Verificar alerta
docker exec SIMIR_Z tail -f /usr/local/zeek/spool/zeek/notice.log | grep DATA-EXFIL
```

### Redução de Falsos Positivos

- **Whitelist de IPs**: Servidores de backup legítimos
- **Horários**: Backups agendados fora do horário de alerta
- **Usuários Autorizados**: Excluir usuários admin/backup
- **Ajuste de Thresholds**: Aumentar limites conforme necessidade

### Protocolos Ignorados Automaticamente

O detector **ignora automaticamente** protocolos que não são relevantes para exfiltração de dados:

#### **ICMP é Ignorado**

```zeek
# Ignora protocolos não relevantes para exfiltração de dados
# ICMP: detectado por DDoS/ICMP Tunnel detectors
if (c$conn$proto == icmp)
    return;
```

**Por quê?**
- ICMP não é usado para transferência normal de dados
- Ping floods geram milhões de pacotes pequenos, não são exfiltração
- ICMP tunneling é detectado pelo detector dedicado `icmp-tunnel-detector.zeek`
- Evita falsos positivos: ping-flood não deve alertar como "Large Upload"

**Exemplo de Falso Positivo Corrigido**:
```
Antes: Ping-flood (906.585 pacotes ICMP) alertava como:
  - [DATA-EXFIL] Large Upload: 1.03 GB uploaded
  - [DATA-EXFIL] Massive Transfer: 1.20 GB transferred
  
Depois: Ping-flood não gera alertas de DATA-EXFIL (correto)
  - ICMP flood deve ser detectado por ddos-detector.zeek
```

#### **Foco em Protocolos de Dados**

O detector monitora apenas:
- **TCP**: HTTP, HTTPS, FTP, SSH, SMB (protocolos de transferência real)
- **UDP**: DNS (via dns-tunneling-detector.zeek), aplicações de dados

---

##  Sistema de Detecção de DNS Tunneling

### O que é DNS Tunneling?

**DNS Tunneling** é uma técnica que abusa do protocolo DNS para estabelecer canais de comunicação encobertos. Atacantes usam para:
- **Exfiltração de dados**: Enviar informações via queries DNS
- **Comunicação C2**: Controle remoto via DNS responses
- **Bypass de firewalls**: DNS é raramente bloqueado

### Técnicas de DNS Tunneling

#### **Encoding de Dados em Subdomínios**
```
3q2.78b3.4h5k.d3f2.a8c1.malicious.com
```
Cada subdomain carrega pedaços de dados codificados

#### **Queries TXT para Comandos**
```
Query: cmd123.c2server.com TXT
Response: "base64_encoded_command"
```

#### **Alta Entropia**
Strings aleatórias indicam dados codificados:
```
abcd1234efgh5678ijklmnop.badsite.com
```

### Como o SIMIR Detecta

O detector `dns-tunneling-detector.zeek` identifica:

1. **Alta Entropia**: Cálculo de entropia de Shannon
2. **Subdomínios Longos**: > 60 caracteres
3. **NXDOMAIN Excessivo**: DGA (Domain Generation Algorithm)
4. **TXT Queries Suspeitas**: Queries TXT frequentes
5. **Padrões de Encoding**: Base64, Hex

### Tipos de Alertas

#### 1. **High Entropy DNS**
```
[DNS-TUNNEL] [HIGH] High Entropy DNS: 192.168.1.100 queried 'abcd1234efgh5678.bad.com' (entropy: 4.25, pattern: encoding)
```
**Significado**: Query com entropia > 3.5 indica dados codificados
**Threshold**: Shannon entropy > 3.5

#### 2. **Long DNS Subdomain**
```
[DNS-TUNNEL] [MEDIUM] Long DNS Subdomain: 192.168.1.100 queried very long subdomain (85 chars)
```
**Significado**: Subdomínio anormalmente longo
**Threshold**: > 60 caracteres

#### 3. **Excessive NXDOMAIN**
```
[DNS-TUNNEL] [HIGH] Excessive NXDOMAIN: 192.168.1.100 generated 75 NXDOMAIN responses in 4m30s (possible DGA)
```
**Significado**: Múltiplas queries para domínios inexistentes (DGA de malware)
**Threshold**: 50+ NXDOMAIN em 5 minutos

#### 4. **Large TXT Query**
```
[DNS-TUNNEL] [MEDIUM] Large TXT Query: 192.168.1.100 made suspicious TXT query
```
**Significado**: Query TXT pode carregar comandos C2

### Cálculo de Entropia de Shannon

```zeek
function calculate_entropy(s: string): double {
    local char_counts: table[string] of count;
    local total = |s|;
    local entropy = 0.0;
    
    # Contar frequência de cada caractere
    for (i in s) {
        local c = s[i];
        if (c !in char_counts)
            char_counts[c] = 0;
        ++char_counts[c];
    }
    
    # Calcular entropia
    for (c in char_counts) {
        local p = char_counts[c] / total + 0.0;
        entropy += -p * log2(p);
    }
    
    return entropy;
}
```

**Interpretação**:
- Entropia 0-2: Baixa (texto normal)
- Entropia 2-3.5: Média (palavras comuns)
- Entropia > 3.5: Alta (dados codificados/aleatórios)

### Campos no notice.log

```
proto: udp
note: DNSTunnel::High_Entropy
msg: High Entropy DNS: 192.168.1.100 queried 'abc123xyz.bad.com' (entropy: 4.25, pattern: encoding)
sub: entropy:4.25
src: 192.168.1.100
dst: 8.8.8.8
p: 53
n: 1
```

### Configuração

```zeek
redef DNSTunnel::entropy_threshold = 3.5;         # Entropia de Shannon
redef DNSTunnel::long_subdomain_threshold = 60;   # Caracteres
redef DNSTunnel::nxdomain_threshold = 50;         # NXDOMAIN count
redef DNSTunnel::tracking_interval = 5min;        # Janela de tempo
```

### Agregação de Alertas por IP de Origem

O detector implementa **agregação inteligente de alertas** para reduzir ruído e melhorar análise:

#### **Comportamento Correto**

Quando um IP realiza múltiplas queries DNS suspeitas (exemplo: 200 queries com alta entropia):

**Antes da agregação** (comportamento incorreto):
- 200 queries DNS suspeitas = 200 alertas individuais
- Analista sobrecarregado com alertas repetitivos
- Difícil identificar padrão de ataque

**Depois da agregação** (comportamento correto):
- 1 alerta inicial "High Entropy DNS" (primeira query detectada)
- 1 alerta "Long Subdomain" (primeiro subdomínio longo)
- 1 alerta agregado "DNS Tunneling Pattern" resumindo a atividade
- **Total: 3 alertas em vez de 200+**

#### **Exemplo Real**

Teste com container `dns-tunneling` (200 queries aleatórias):

```
[DNS-TUNNEL] [HIGH] High Entropy DNS: 192.168.0.67 queried 
'4a3c0ddd93f4672f7f6d4adb30ffff1cf9aec45cf675bbbaceb8d2bdf.com' 
(entropy: 3.74, pattern: encoding)

[DNS-TUNNEL] [MEDIUM] Long Subdomain: 192.168.0.67 queried 
'29780d727ca08ab38dcdcbf2116bce9e9dcbbd1fcba695edc6a319ca7dbc0.com' 
(subdomain: 61 chars)

[DNS-TUNNEL] [CRITICAL] DNS Tunneling Pattern: 192.168.0.67 shows 
tunneling behavior (long: 0, suspicious: 10 domains)
```

**Resultado**: 3 alertas contextualizados em vez de 128 alertas individuais

#### **Vantagens da Agregação**

✅ **Redução de Ruído**: Menos alertas repetitivos
✅ **Contextualização**: Alerta agregado mostra padrão de comportamento
✅ **Priorização**: SOC pode focar no IP suspeito, não em cada query individual
✅ **Operacional**: Análise mais eficiente e rápida

#### **Supressão por IP**

```zeek
# Identifier usa apenas o IP de origem, não o domínio individual
$identifier=fmt("dns_entropy_%s", orig)
$suppress_for=10min
```

- Primeiro alerta gerado imediatamente
- Alertas subsequentes do mesmo IP suprimidos por 10 minutos
- Alerta de padrão agregado (DNS_Tunneling_Pattern) resume atividade total

### Teste Manual

```bash
# Simular query com alta entropia
dig abcd1234efgh5678ijklmnop9876.malicious.com

# Simular subdomain longo
dig $(python3 -c "print('a'*70)").test.com

# Simular DGA (NXDOMAIN excessivo)
for i in {1..60}; do dig random$RANDOM.nonexistent.com; done

# Query TXT suspeita
dig TXT cmd.c2server.com

# Verificar alertas
docker exec SIMIR_Z grep "DNS-TUNNEL" /usr/local/zeek/spool/zeek/notice.log
```

### Padrões de Encoding Detectados

```zeek
# Base64
[A-Za-z0-9+/=]{20,}

# Hexadecimal
[0-9a-fA-F]{40,}

# Ambos indicam dados codificados
```

---

##  Sistema de Detecção de Movimento Lateral

### O que é Movimento Lateral?

**Movimento Lateral** (Lateral Movement) é a técnica usada por atacantes para se mover através de uma rede após comprometer um host inicial. Objetivos:
- **Escalação de privilégios**: Acessar sistemas mais críticos
- **Descoberta de ativos**: Mapear a rede interna
- **Persistência**: Estabelecer múltiplos pontos de acesso
- **Alcançar o alvo**: Chegar a dados sensíveis

### Técnicas Comuns

#### **RDP Hopping**
- Conectar via RDP (3389) para múltiplos hosts
- Usado após roubo de credenciais

#### **SSH Pivoting**
- SSH (22) para múltiplos servidores
- Tunneling através de hosts comprometidos

#### **SMB Lateral Movement**
- SMB (445) para compartilhamentos de rede
- PsExec, WMI, PowerShell remoting

#### **Admin Port Scanning**
- Varredura de portas administrativas
- Busca por serviços vulneráveis

### Como o SIMIR Detecta

O detector `lateral-movement-detector.zeek` monitora:

1. **Conexões RDP Internas**: Múltiplas conexões RDP entre hosts internos
2. **SSH Scanning Interno**: SSH para vários hosts internos
3. **SMB Scanning**: Múltiplas tentativas SMB
4. **Multiple Admin Ports**: Varredura de portas administrativas
5. **Internal Host Scanning**: Scanning generalizado interno

### Tipos de Alertas

#### 1. **RDP Lateral Movement**
```
[LATERAL-MOVE] [CRITICAL] RDP Lateral Movement: 192.168.1.50 connected via RDP to 7 internal hosts in 12m5s
```
**Significado**: Host se conectou via RDP para múltiplos hosts internos
**Threshold**: 5+ hosts em 15 minutos
**Portas**: 3389 (RDP)

#### 2. **SSH Lateral Movement**
```
[LATERAL-MOVE] [CRITICAL] SSH Lateral Movement: 192.168.1.50 connected via SSH to 8 internal hosts in 10m15s
```
**Significado**: Múltiplas conexões SSH internas
**Threshold**: 5+ hosts
**Portas**: 22 (SSH)

#### 3. **SMB Lateral Movement**
```
[LATERAL-MOVE] [HIGH] SMB Lateral Movement: 192.168.1.50 connected via SMB to 6 internal hosts in 8m20s
```
**Significado**: Scanning ou acesso SMB suspeito
**Threshold**: 5+ hosts
**Portas**: 445 (SMB)

#### 4. **Multiple Admin Ports**
```
[LATERAL-MOVE] [HIGH] Multiple Admin Ports: 192.168.1.50 scanned 7 different administrative ports internally
```
**Significado**: Varredura de múltiplas portas administrativas
**Portas Monitoradas**: 22, 23, 135, 139, 445, 1433, 3306, 3389, 5432

#### 5. **Internal Host Scanning**
```
[LATERAL-MOVE] [MEDIUM] Internal Host Scanning: 192.168.1.50 scanned 12 internal hosts
```
**Significado**: Descoberta ativa de hosts internos

### Portas Administrativas Monitoradas

| Porta | Serviço | Uso em Movimento Lateral |
|-------|---------|--------------------------|
| 22 | SSH | Login remoto, pivoting |
| 23 | Telnet | Acesso legado |
| 135 | MS-RPC | Exploração Windows |
| 139 | NetBIOS | Compartilhamentos Windows |
| 445 | SMB | PsExec, WMI, compartilhamentos |
| 1433 | MS SQL | Database access |
| 3306 | MySQL | Database access |
| 3389 | RDP | Remote Desktop |
| 5432 | PostgreSQL | Database access |

### Lógica de Exclusão (Redução de Falsos Positivos)

O detector **exclui automaticamente** hosts que parecem ser servidores legítimos:

```zeek
function is_likely_server(ip: addr): bool {
    local ip_str = fmt("%s", ip);
    
    # Excluir gateways comuns
    if (/\.1$/ in ip_str || /\.2$/ in ip_str || /\.254$/ in ip_str)
        return T;
    
    # Excluir servidores típicos (.10, .11, .12, etc.)
    if (/\.10$/ in ip_str || /\.11$/ in ip_str || /\.12$/ in ip_str)
        return T;
    
    return F;
}
```

**IPs Excluídos**:
- `.1`, `.2`: Gateways
- `.254`: Gateway alternativo
- `.10`, `.11`, `.12`, `.20`, `.30`: Servidores típicos

### Campos no notice.log

```
proto: tcp
note: LateralMove::RDP_Movement
msg: RDP Lateral Movement: 192.168.1.50 connected via RDP to 7 internal hosts in 12m5s
sub: RDP:3389
src: 192.168.1.50
dst: -
p: 3389
n: 7
```

### Configuração

```zeek
redef LateralMove::host_threshold = 5;            # Hosts internos
redef LateralMove::admin_port_threshold = 5;      # Portas admin
redef LateralMove::tracking_interval = 15min;     # Janela de tempo
```

### Teste Manual

```bash
# Simular RDP lateral movement
for host in 192.168.1.{10..20}; do 
    nc -zv $host 3389 2>/dev/null
done

# Simular SSH scanning interno
for host in 192.168.1.{10..20}; do 
    nc -zv $host 22 2>/dev/null
done

# Simular SMB scanning
for host in 192.168.1.{10..20}; do 
    nc -zv $host 445 2>/dev/null
done

# Verificar alertas
docker exec SIMIR_Z grep "LATERAL-MOVE" /usr/local/zeek/spool/zeek/notice.log
```

### Contexto de Segurança

Movimento lateral é **extremamente suspeito** porque:
1. Usuários normais não se conectam a múltiplos hosts administrativos
2. Indica que atacante já tem credenciais válidas
3. Precede frequentemente roubo de dados ou ransomware
4. Sugere reconhecimento avançado da rede

**Ação Recomendada**: Investigação imediata e isolamento do host de origem.

---

##  Sistema de Detecção de SQL Injection

### O que é SQL Injection?

**SQL Injection (SQLi)** é uma vulnerabilidade crítica que permite que atacantes injetem comandos SQL maliciosos em aplicações web. Consequências:
- **Roubo de dados**: Acesso a toda base de dados
- **Bypass de autenticação**: Login como admin
- **Modificação de dados**: UPDATE, DELETE maliciosos
- **Execução de comandos**: RCE via xp_cmdshell (SQL Server)

### Tipos de SQL Injection

#### **Union-Based**
```sql
' UNION SELECT username, password FROM users--
```
Combina queries para extrair dados

#### **Boolean-Based Blind**
```sql
' OR 1=1--
' AND 1=1--
```
Infere informações por respostas true/false

#### **Time-Based Blind**
```sql
'; WAITFOR DELAY '00:00:05'--
'; SELECT SLEEP(5)--
```
Usa delays para confirmar vulnerabilidade

#### **Stacked Queries**
```sql
'; DROP TABLE users--
'; UPDATE users SET is_admin=1--
```
Executa múltiplos statements

### Como o SIMIR Detecta

O detector `sql-injection-detector.zeek` analisa:

1. **HTTP URI**: Parâmetros GET
2. **HTTP Body**: Dados POST
3. **30+ Padrões SQLi**: UNION, SELECT, DROP, OR 1=1, etc.
4. **SQL Error Disclosure**: Mensagens de erro expostas
5. **Classificação de Severidade**: CRITICAL, HIGH, MEDIUM

### Tipos de Alertas

#### 1. **High-Risk SQL Injection**
```
[SQLi] [CRITICAL] High-Risk SQL Injection: 192.168.1.100 attempted dangerous SQLi against 10.0.0.50: /admin.php?id=1' DROP TABLE users--
```
**Significado**: Tentativa de SQLi perigosa (DROP, DELETE, xp_cmdshell)
**Severidade**: CRITICAL
**Padrões**: DROP, DELETE, EXEC, xp_cmdshell, INTO OUTFILE

#### 2. **Medium-Risk SQL Injection**
```
[SQLi] [HIGH] Medium-Risk SQL Injection: 192.168.1.100 attempted SQLi against 10.0.0.50: /login.php?user=admin' OR '1'='1
```
**Significado**: SQLi clássico de bypass ou extração
**Severidade**: HIGH
**Padrões**: UNION SELECT, OR 1=1, admin'--, WAITFOR DELAY

#### 3. **Low-Risk SQL Injection**
```
[SQLi] [MEDIUM] Low-Risk SQL Injection: 192.168.1.100 attempted basic SQLi against 10.0.0.50: /search.php?q=test' OR '1'='1'--
```
**Significado**: Tentativa básica de SQLi
**Severidade**: MEDIUM
**Padrões**: Comentários SQL, aspas não escapadas

#### 4. **SQL Error Disclosure**
```
[SQLi] [MEDIUM] SQL Error Disclosure: 10.0.0.50 disclosed SQL error in response (potential vulnerability)
```
**Significado**: Servidor expôs mensagem de erro SQL
**Indicação**: Aplicação vulnerável a SQLi

### 30+ Padrões SQLi Detectados

#### **CRITICAL (Severity: 3)**
```
DROP.*TABLE
DELETE.*FROM
EXEC.*xp_
xp_cmdshell
INTO.*OUTFILE
LOAD_FILE
```

#### **HIGH (Severity: 2)**
```
UNION.*SELECT
SELECT.*FROM.*WHERE
INSERT.*INTO
UPDATE.*SET
WAITFOR.*DELAY
SLEEP\(
BENCHMARK\(
```

#### **MEDIUM (Severity: 1)**
```
OR\s+1\s*=\s*1
AND\s+1\s*=\s*1
admin'--
' OR '
' AND '
' OR 1=1
```

### Classificação Automática de Severidade

```zeek
function get_sqli_severity(pattern: string): count {
    # CRITICAL - Comandos destrutivos
    if (/(DROP|DELETE|EXEC|xp_cmdshell|INTO.*OUTFILE)/ in pattern)
        return 3;
    
    # HIGH - Extração e manipulação de dados
    if (/(UNION.*SELECT|INSERT|UPDATE|WAITFOR|SLEEP|BENCHMARK)/ in pattern)
        return 2;
    
    # MEDIUM - Bypass básico
    return 1;
}
```

### Campos no notice.log

```
proto: tcp
note: SQLi::High_Risk_Injection
msg: High-Risk SQL Injection: 192.168.1.100 attempted dangerous SQLi against 10.0.0.50: /admin.php?id=1' DROP TABLE users--
sub: uri:/admin.php?id=1' DROP TABLE users--
src: 192.168.1.100
dst: 10.0.0.50
p: 80
n: 1
```

### Detecção de SQL Errors

Mensagens de erro comuns detectadas:

```
SQL syntax.*MySQL
Warning.*mysql_
ORA-\d{5}
Microsoft SQL Server
ODBC SQL Server Driver
```

Quando detectado:
```
[SQLi] [MEDIUM] SQL Error Disclosure: 10.0.0.50 disclosed SQL error in response
```

### Teste Manual

```bash
# CRITICAL - DROP TABLE
curl "http://target/admin.php?id=1' DROP TABLE users--"

# HIGH - UNION SELECT
curl "http://target/page.php?id=1' UNION SELECT null,username,password FROM users--"

# HIGH - Time-based
curl "http://target/search.php?q=test'; WAITFOR DELAY '00:00:05'--"

# MEDIUM - OR 1=1
curl "http://target/login.php?user=admin' OR '1'='1&pass=x"

# MEDIUM - Comment injection
curl "http://target/auth.php?user=admin'--&pass=x"

# Verificar alertas
docker exec SIMIR_Z grep "SQLi" /usr/local/zeek/spool/zeek/notice.log
```

### URL Decoding Automático

O detector decodifica URLs automaticamente:

```
%27 → '
%20 → space
%2D%2D → --
```

Exemplo:
```
/page.php?id=1%27%20OR%20%271%27%3D%271
    ↓
/page.php?id=1' OR '1'='1
```

### Limitações

- **Não detecta**: Ataques SQLi muito ofuscados ou encodados múltiplas vezes
- **Pode gerar falsos positivos**: Queries legítimas com palavras SQL
- **Baseado em padrões**: Não é análise semântica completa

### Mitigação Recomendada

1. **Prepared Statements**: Use sempre
2. **Input Validation**: Whitelist de caracteres
3. **Least Privilege**: Conexão DB com mínimos privilégios
4. **WAF**: Web Application Firewall
5. **Error Handling**: Não exponha erros SQL

---

##  Sistema de Detecção de Beaconing

### O que é Beaconing?

**Beaconing** é um padrão de comunicação periódica e regular usado por malware para:
- **Check-in com C2**: Verificar se há novos comandos
- **Exfiltração gradual**: Enviar dados em pequenos pedaços
- **Manter conexão**: Keep-alive para persistência
- **Evitar detecção**: Parecer tráfego legítimo

### Características de Beaconing

#### **Intervalos Regulares**
```
Connection 1: 10:00:00
Connection 2: 10:00:30  (30s depois)
Connection 3: 10:01:00  (30s depois)
Connection 4: 10:01:30  (30s depois)
```

#### **Payload Similar**
Tamanho dos dados similar entre conexões:
```
Request 1: 256 bytes
Request 2: 258 bytes
Request 3: 255 bytes
```

#### **Alta Regularidade**
Baixa variação (jitter) nos intervalos:
```
Variance: 0.05 (5%)  ← Muito regular = suspeito
Variance: 0.50 (50%) ← Irregular = normal
```

### Como o SIMIR Detecta

O detector `beaconing-detector.zeek` calcula:

1. **Variância dos Intervalos**: Mede regularidade temporal
2. **Coeficiente de Variação**: Jitter normalizado
3. **Similaridade de Payload**: Tamanhos de dados
4. **Contagem de Conexões**: Mínimo 10 para análise

### Algoritmo de Detecção

```zeek
# 1. Calcular intervalos entre conexões
intervals: [30s, 30s, 31s, 29s, 30s, ...]

# 2. Calcular média dos intervalos
avg_interval = sum(intervals) / count(intervals)
              = 30s

# 3. Calcular variância
variance = Σ(interval - avg)² / count
         = 0.8

# 4. Calcular coeficiente de variação (CV)
CV = sqrt(variance) / avg_interval
   = 0.047  (4.7%)

# 5. Comparar com threshold
if (CV <= 0.15)  # 15% ou menos
    → BEACONING DETECTADO!
```

### Tipos de Alertas

#### 1. **Beaconing Detected**
```
[BEACONING] [CRITICAL] Beaconing Detected: 192.168.1.100 -> 203.0.113.50:8080 shows regular periodic pattern (avg: 30s, regularity: 0.08, connections: 15)
```
**Significado**: Comunicação extremamente regular detectada
**Threshold**: Jitter ≤ 15%, min 10 conexões
**Intervalo típico**: 5s - 5min

#### 2. **Beaconing with Similar Payload**
```
[BEACONING] [CRITICAL] Beaconing with Similar Payload: 192.168.1.100 -> 203.0.113.50:443 shows regular pattern with similar payload sizes
```
**Significado**: Além de regular, payloads são similares
**Indicação forte**: C2 com respostas padronizadas

#### 3. **Potential Beaconing**
```
[BEACONING] [HIGH] Potential Beaconing: 192.168.1.100 -> 203.0.113.50:8080 shows somewhat regular pattern (avg: 45s, regularity: 0.18, connections: 12)
```
**Significado**: Regularidade moderada, requer investigação
**Threshold**: Jitter 15-25%

### Cálculo de Variância

```zeek
function calculate_variance(intervals: vector of interval): double {
    local sum = 0.0;
    local count = |intervals|;
    
    # Calcular média
    for (i in intervals)
        sum += interval_to_double(intervals[i]);
    local avg = sum / count;
    
    # Calcular variância
    local variance = 0.0;
    for (i in intervals) {
        local diff = interval_to_double(intervals[i]) - avg;
        variance += diff * diff;
    }
    variance = variance / count;
    
    return variance;
}
```

### Cálculo de Regularidade (CV)

```zeek
function calculate_regularity(intervals: vector of interval): double {
    local variance = calculate_variance(intervals);
    local std_dev = sqrt(variance);
    
    local sum = 0.0;
    for (i in intervals)
        sum += interval_to_double(intervals[i]);
    local avg = sum / |intervals|;
    
    # Coeficiente de variação
    if (avg > 0.0)
        return std_dev / avg;
    else
        return 1.0;
}
```

### Detecção de Payload Similar

```zeek
function has_similar_payload_sizes(orig_sizes: vector of count, 
                                    resp_sizes: vector of count): bool {
    if (|orig_sizes| < 5)
        return F;
    
    # Calcular média dos orig_bytes
    local sum = 0;
    for (i in orig_sizes)
        sum += orig_sizes[i];
    local avg = sum / |orig_sizes|;
    
    if (avg == 0)
        return F;
    
    # Verificar se todos estão dentro de 20% da média
    for (i in orig_sizes) {
        local diff = abs(orig_sizes[i] - avg) / avg + 0.0;
        if (diff > 0.2)  # 20% de variação
            return F;
    }
    
    return T;
}
```

### Campos no notice.log

```
proto: tcp
note: Beaconing::Beacon_Detected
msg: Beaconing Detected: 192.168.1.100 -> 203.0.113.50:8080 shows regular periodic pattern (avg: 30s, regularity: 0.08, connections: 15)
sub: interval:30s,cv:0.08
src: 192.168.1.100
dst: 203.0.113.50
p: 8080
n: 15
```

### Configuração

```zeek
redef Beaconing::min_connections = 10;            # Mínimo de conexões para análise
redef Beaconing::jitter_threshold = 0.15;         # 15% de variação máxima
redef Beaconing::min_interval = 5sec;             # Intervalo mínimo considerado
redef Beaconing::max_interval = 5min;             # Intervalo máximo considerado
```

### Teste Manual

```bash
# Simular beaconing (intervalo de 30s)
while true; do 
    curl -s http://c2-server:8080/beacon > /dev/null
    sleep 30
done

# Simular com wget
while true; do 
    wget -q -O /dev/null http://c2-server:8080/check-in
    sleep 60
done

# Simular com netcat (apenas conexão TCP)
while true; do 
    echo "beacon" | nc c2-server 8080
    sleep 45
done

# Verificar alertas (aguardar 10+ conexões)
docker exec SIMIR_Z grep "BEACONING" /usr/local/zeek/spool/zeek/notice.log
```

### Falsos Positivos Comuns

1. **Update checks**: Software verificando atualizações
   - Windows Update, apt-get, yum
   - Mitigation: Whitelist de domínios conhecidos

2. **Monitoring agents**: Nagios, Zabbix, Prometheus
   - Mitigation: Excluir IPs de monitoramento

3. **Time sync**: NTP queries
   - Mitigation: Excluir porta 123

4. **Keep-alive HTTP**: Conexões persistentes legítimas
   - Mitigation: Aumentar min_connections

### Whitelist de Domínios Legítimos

```zeek
global legitimate_update_domains: set[string] = {
    "windowsupdate.microsoft.com",
    "update.microsoft.com",
    "ubuntu.com",
    "debian.org",
    "centos.org"
};
```

### Características de Beaconing Malicioso

| Característica | Benigno | Malicioso |
|----------------|---------|-----------|
| Interval | Variável (5-30min) | Muito regular (10-60s) |
| Jitter | Alto (>30%) | Baixo (<15%) |
| Destino | Domínios conhecidos | IPs suspeitos |
| Payload | Variável | Muito similar |
| Horário | Business hours | 24/7 |

---

##  Sistema de Detecção de Anomalias de Protocolo

### O que são Anomalias de Protocolo?

**Anomalias de protocolo** ocorrem quando:
- Protocolos rodam em portas não-padrão
- Certificados SSL são inválidos
- Serviços inesperados em portas conhecidas
- Evasão de firewalls e filtros

### Técnicas Comuns

#### **Port Evasion**
```
HTTP em porta 8888 (não 80)
SSH em porta 2222 (não 22)
```
Objetivo: Evitar bloqueios de firewall

#### **SSL/TLS Inválido**
- Certificados auto-assinados
- Certificados expirados
- Common Name incorreto

#### **Protocol Tunneling**
- HTTP túnel dentro de DNS
- SSH túnel em porta 443

### Como o SIMIR Detecta

O detector `protocol-anomaly-detector.zeek` identifica:

1. **HTTP em porta não-padrão**: ≠ 80/8080/8000
2. **HTTPS em porta não-padrão**: ≠ 443/8443
3. **SSH em porta não-padrão**: ≠ 22
4. **Certificados SSL inválidos**: Auto-assinados, expirados
5. **Atividade em portas altas**: > 40000
6. **Protocolos inesperados**: Ex: HTTP em porta 22

### Tipos de Alertas

#### 1. **HTTP on Non-Standard Port**
```
[PROTO-ANOMALY] [HIGH] HTTP on Non-Standard Port: 192.168.1.100 -> 203.0.113.50:8888 using HTTP
```
**Significado**: Tráfego HTTP em porta que não é 80/8080/8000
**Portas Padrão**: 80, 8080, 8000
**Suspeita**: Evasão de firewall ou serviço malicioso

#### 2. **HTTPS on Non-Standard Port**
```
[PROTO-ANOMALY] [HIGH] HTTPS on Non-Standard Port: 192.168.1.100 -> 203.0.113.50:8443 using HTTPS
```
**Significado**: HTTPS/SSL em porta customizada
**Portas Padrão**: 443, 8443
**Suspeita**: Túnel C2 ou proxy malicioso

#### 3. **SSH on Non-Standard Port**
```
[PROTO-ANOMALY] [HIGH] SSH on Non-Standard Port: 192.168.1.100 -> 203.0.113.50:2222 using SSH
```
**Significado**: SSH não está na porta 22
**Porta Padrão**: 22
**Contexto**: Pode ser backdoor ou hardening legítimo

#### 4. **Invalid SSL Certificate**
```
[PROTO-ANOMALY] [MEDIUM] Invalid SSL Certificate: 192.168.1.100 -> 203.0.113.50:443 has invalid/self-signed certificate
```
**Significado**: Certificado auto-assinado ou com problemas
**Indicação**: Phishing, MITM, ou servidor interno

#### 5. **High Port Activity**
```
[PROTO-ANOMALY] [MEDIUM] High Port Activity: 192.168.1.100 -> 203.0.113.50:45678 unusual activity on high port
```
**Significado**: Tráfego em porta > 40000
**Threshold**: 40000
**Suspeita**: Backdoors, trojans

#### 6. **Unexpected Protocol on Standard Port**
```
[PROTO-ANOMALY] [HIGH] Unexpected Protocol on Standard Port: 192.168.1.100 -> 203.0.113.50:22 unexpected HTTP traffic
```
**Significado**: Protocolo diferente do esperado para aquela porta
**Exemplo**: HTTP na porta 22 (porta SSH)

### Portas Padrão Definidas

```zeek
global http_standard_ports: set[port] = { 80/tcp, 8080/tcp, 8000/tcp };
global https_standard_ports: set[port] = { 443/tcp, 8443/tcp };
global ssh_standard_port: port = 22/tcp;
```

### Detecção de SSL Inválido

```zeek
event ssl_established(c: connection) {
    if (c$ssl?$validation_status && 
        c$ssl$validation_status != "ok") {
        
        # Certificado inválido detectado
        NOTICE([
            $note=ProtoAnomaly::Invalid_SSL,
            $conn=c,
            $msg=fmt("Invalid SSL Certificate"),
            $identifier=cat(c$id$orig_h, c$id$resp_h, c$id$resp_p)
        ]);
    }
}
```

**Status de validação**:
- `ok`: Válido
- `self signed certificate`: Auto-assinado
- `certificate has expired`: Expirado
- `unable to get local issuer certificate`: CA desconhecida

### Campos no notice.log

```
proto: tcp
note: ProtoAnomaly::HTTP_Non_Standard
msg: HTTP on Non-Standard Port: 192.168.1.100 -> 203.0.113.50:8888 using HTTP
sub: port:8888
src: 192.168.1.100
dst: 203.0.113.50
p: 8888
n: 1
```

### Configuração

```zeek
redef ProtoAnomaly::high_port_threshold = 40000;  # Porta alta threshold

# Portas padrão podem ser redefinidas
redef http_standard_ports += { 8081/tcp, 8082/tcp };
redef https_standard_ports += { 8444/tcp };
```

### Teste Manual

```bash
# HTTP em porta não-padrão
python3 -m http.server 8888
curl http://localhost:8888

# SSH em porta customizada
ssh -p 2222 user@host

# HTTPS em porta alta
openssl s_server -accept 45000 -cert cert.pem -key key.pem
curl -k https://localhost:45000

# Verificar alertas
docker exec SIMIR_Z grep "PROTO-ANOMALY" /usr/local/zeek/spool/zeek/notice.log
```

### Whitelist de Serviços Conhecidos

Para reduzir falsos positivos de serviços legítimos:

```zeek
# Em local.zeek
redef http_standard_ports += {
    3000/tcp,  # Node.js dev server
    8081/tcp,  # Tomcat alternativo
    9090/tcp   # Prometheus
};

redef https_standard_ports += {
    8444/tcp   # HTTPS alternativo interno
};
```

### Contexto de Segurança

#### **Quando é Suspeito**
- SSH em porta alta (> 10000) sem justificativa
- HTTPS com certificado auto-assinado para domínio externo
- HTTP em portas aleatórias com tráfego pesado
- Múltiplas portas não-padrão do mesmo host

#### **Quando é Normal**
- Servidores de desenvolvimento (Node.js 3000, Flask 5000)
- Hardening de SSH (porta customizada documentada)
- Serviços internos com certificados internos
- Aplicações corporativas em portas específicas

### Investigação Recomendada

1. **Verificar processo**: `netstat -tulpn | grep <port>`
2. **Identificar serviço**: `lsof -i :<port>`
3. **Analisar payload**: Capturar com tcpdump
4. **Verificar destino**: Quem é o IP remoto?
5. **Contexto do usuário**: Quem iniciou a conexão?

---

##  Sistema de Detecção de ICMP Tunneling

### O que é ICMP Tunneling?

**ICMP Tunneling** é uma técnica de evasão que usa o protocolo ICMP (ping) para:
- **Exfiltração de dados**: Codificar dados no payload do ICMP
- **Comunicação C2**: Canal de comando e controle
- **Bypass de firewall**: ICMP raramente é bloqueado
- **Túnel de rede**: Encapsular outros protocolos

### Como ICMP é Abusado

#### **Ping Normal**
```
ICMP Echo Request: 64 bytes (padrão)
0000: 4500 0054 0000 4000 4001 ... [IP header]
0020: 0800 xxxx xxxx xxxx [ICMP: tipo 8, código 0]
0028: 6162 6364 6566 6768 [Payload: "abcdefgh" - padrão]
```

#### **ICMP Tunneling**
```
ICMP Echo Request: 256 bytes (suspeito!)
0000: 4500 0154 0000 4000 4001 ... [IP header]
0020: 0800 xxxx xxxx xxxx [ICMP: tipo 8, código 0]
0028: 5468 6973 2069 7320 ... [Payload: dados arbitrários]
      7365 6372 6574 2064 ...
      6174 6121 ...         ["This is secret data!"]
```

### Ferramentas de ICMP Tunneling

- **ptunnel**: ICMP tunneling para TCP/UDP
- **icmptunnel**: Ferramenta Python
- **Hping3**: Craft custom ICMP packets
- **Malware C2**: Múltiplos malwares usam ICMP

### Como o SIMIR Detecta

O detector `icmp-tunnel-detector.zeek` identifica:

1. **Payload Grande**: > 128 bytes (normal = 64)
2. **Alto Volume**: > 100 pacotes ICMP em 5 min
3. **Padrões Anormais**: ICMP unreachable suspeito
4. **Timing Regular**: Beaconing via ICMP

### Tipos de Alertas

#### 1. **Large ICMP Payload**
```
[ICMP-TUNNEL] [HIGH] Large ICMP Payload: 192.168.1.100 sent ICMP with 256 bytes payload to 203.0.113.50 (normal: 64 bytes)
```
**Significado**: Pacote ICMP com payload anormalmente grande
**Threshold**: > 128 bytes
**Normal**: 64 bytes (ping padrão Linux/Windows)

#### 2. **High ICMP Volume**
```
[ICMP-TUNNEL] [HIGH] High ICMP Volume: 192.168.1.100 sent 150 ICMP packets to 203.0.113.50 in 4m30s
```
**Significado**: Volume excessivo de ICMP para um destino
**Threshold**: > 100 pacotes em 5 minutos
**Normal**: Poucos pings esporádicos

#### 3. **Unusual ICMP Pattern**
```
[ICMP-TUNNEL] [MEDIUM] Unusual ICMP Pattern: 192.168.1.100 shows abnormal ICMP unreachable pattern
```
**Significado**: Padrão suspeito de ICMP unreachable/timeout
**Indicação**: Scanning ou tunneling

#### 4. **ICMP Data Exfiltration**
```
[ICMP-TUNNEL] [CRITICAL] ICMP Data Exfiltration: 192.168.1.100 -> 203.0.113.50 large payload (320 bytes) + high volume (85 packets)
```
**Significado**: Combinação de payload grande + alto volume
**Indicação forte**: Exfiltração ativa via ICMP

### Anatomia do ICMP

#### **ICMP Echo Request (Tipo 8)**
```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   Type (8)    |   Code (0)    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Checksum             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|        Identifier             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|      Sequence Number          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Data (payload)       |
|            ...                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Payload Normal**: "abcdefghijklmnopqrstuvwxyz" (alfabeto)
**Payload Tunneling**: Dados arbitrários/codificados

### Tamanhos de Payload por Sistema

| Sistema | Tamanho Padrão | Comando |
|---------|----------------|---------|
| Linux | 56 bytes | `ping -c 1 host` |
| Windows | 32 bytes | `ping host` |
| MacOS | 56 bytes | `ping -c 1 host` |

**SIMIR considera**:
- ≤ 64 bytes: Normal
- 65-127 bytes: Levemente suspeito
- ≥ 128 bytes: **ALERTA**

### Campos no notice.log

```
proto: icmp
note: ICMPTunnel::Large_Payload
msg: Large ICMP Payload: 192.168.1.100 sent ICMP with 256 bytes payload to 203.0.113.50 (normal: 64 bytes)
sub: payload:256
src: 192.168.1.100
dst: 203.0.113.50
p: -
n: 1
```

### Configuração

```zeek
redef ICMPTunnel::large_payload_threshold = 128;  # Bytes
redef ICMPTunnel::high_volume_threshold = 100;    # Pacotes
redef ICMPTunnel::tracking_interval = 5min;       # Janela de tempo
```

### Teste Manual

```bash
# Ping normal (não deve alertar)
ping -c 10 8.8.8.8

# Ping com payload grande
ping -c 5 -s 200 target_host

# Ping com payload muito grande
ping -c 5 -s 500 target_host

# Alto volume de pings
ping -f target_host  # Flood ping (requer root)

# Simular tunneling com hping3
sudo hping3 --icmp --data 300 target_host

# Verificar alertas
docker exec SIMIR_Z grep "ICMP-TUNNEL" /usr/local/zeek/spool/zeek/notice.log
```

### Exemplo de ptunnel (ICMP Tunneling Real)

**Servidor**:
```bash
sudo ptunnel -x password123
```

**Cliente**:
```bash
sudo ptunnel -p server_ip -lp 8000 -da localhost -dp 22 -x password123
ssh -p 8000 localhost
```

Resultado: SSH tunelado dentro de ICMP!

### Detecção no Zeek

```zeek
event icmp_echo_request(c: connection, icmp: icmp_conn, id: count, 
                        seq: count, payload: string) {
    local payload_len = |payload|;
    
    if (payload_len > ICMPTunnel::large_payload_threshold) {
        NOTICE([
            $note=ICMPTunnel::Large_Payload,
            $conn=c,
            $msg=fmt("Large ICMP Payload: %s sent ICMP with %d bytes", 
                     c$id$orig_h, payload_len),
            $sub=fmt("payload:%d", payload_len),
            $n=payload_len
        ]);
    }
}
```

### Análise de Payload ICMP

```bash
# Capturar ICMP e ver payload
sudo tcpdump -i any -n icmp -X

# Exemplo de saída:
# 0x0030:  abcd efgh ijkl mnop  ← Payload normal
# 0x0030:  5468 6973 2069 7320  ← Payload com dados ("This is ")
```

### Falsos Positivos

1. **Ferramentas de diagnóstico**
   - `mtr` (My TraceRoute): Usa ICMP
   - `pathping`: Windows network tool

2. **Monitoramento de rede**
   - PRTG Network Monitor
   - Nagios ICMP checks

3. **Jogos online**
   - Alguns jogos usam ICMP para latency checks

**Mitigation**: Whitelist de IPs conhecidos

```zeek
global monitoring_servers: set[addr] = {
    192.168.1.10,  # PRTG server
    192.168.1.20   # Nagios
};
```

### Indicadores de Tunneling Real

| Característica | Normal | Tunneling |
|----------------|--------|-----------|
| Payload Size | 32-64 bytes | 128+ bytes |
| Volume | < 20 pings | > 100 pings |
| Frequência | Esporádico | Regular/constante |
| Destino | Múltiplos | Único repetido |
| Timing | Irregular | Regular (beaconing) |

### Investigação Recomendada

1. **Capturar tráfego**: `tcpdump -i any icmp -w icmp.pcap`
2. **Analisar no Wireshark**: Ver conteúdo do payload
3. **Verificar processo**: `lsof -i -n | grep ICMP`
4. **Checar destino**: Quem é o IP? Reputação?
5. **Correlacionar**: Outros alertas do mesmo host?

---

##  Referências

### Documentação Oficial
- **Zeek**: https://zeek.org/docs/
- **Docker**: https://docs.docker.com/
- **Docker Compose**: https://docs.docker.com/compose/

### Recursos de Threat Intelligence
- **Abuse.ch**: https://abuse.ch/
- **URLhaus**: https://urlhaus.abuse.ch/
- **Feodo Tracker**: https://feodotracker.abuse.ch/
- **Malware Domain List**: https://www.malwaredomainlist.com/
- **Tor Exit Nodes**: https://check.torproject.org/torbulkexitlist

### Scripts e Ferramentas
- **Intelligence Framework**: `site/intelligence-framework.zeek`
- **Port Scan Detector**: `site/port-scan-detector.zeek`
- **Brute Force Detector**: `site/brute-force-detector.zeek`
- **DDoS Detector**: `site/ddos-detector.zeek`

### Testes Disponíveis
```bash
# Teste completo do sistema
./scripts/test-complete.sh

# Testes específicos
./scripts/test-brute-force.sh
./scripts/test-intelligence.sh
./scripts/test-intelligence-complete.sh
```

---

**Nota**: Este é um documento vivo e pode ser atualizado com novas informações. O sistema SIMIR inclui detecção de port scan, ataques de força bruta, DDoS e intelligence framework integrado.


**Última atualização**: Setembro 2025 - Adicionado Intelligence Framework
