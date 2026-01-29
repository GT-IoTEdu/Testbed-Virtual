# Containers Docker para Simulação de Ataques

Este diretório contém containers Docker para simular ataques de rede e um servidor alvo vulnerável para testes do SIMIR.

## 🚀 Início Rápido

### Modo Automático (RECOMENDADO)

Se você já configurou o SIMIR com `./start-simir.sh` (Modo 2 - Rede Docker), tudo já está pronto!

```bash
# Menu interativo com todos os ataques
./run-attack.sh
```

O script detecta automaticamente se você está no modo Docker ou físico e executa os ataques corretamente.

---

## 📋 Componentes

### Servidor Alvo

**`target-server/`** - Servidor web vulnerável (Nginx + SSH)
- **IP fixo**: 172.18.0.2 (na rede Docker simir-net)
- **Portas**: 22 (SSH), 80 (HTTP)
- **Credenciais SSH**: root / toor
- **Uso**: Alvo para todos os ataques

**Gerenciamento:**
```bash
# Iniciar servidor alvo
./start-target.sh

# Parar servidor alvo
docker stop SIMIR_TARGET
```

### Containers de Ataque


| Container | Detector Zeek | Descrição |
|-----------|--------------|-----------|
| **dos-http** | `ddos-detector.zeek` | HTTP Flood - 12.000+ requisições HTTP |
| **brute-force-ssh** | `brute-force-detector.zeek` | 100 tentativas de login SSH |
| **ping-flood** | `icmp-tunnel-detector.zeek` | ICMP Flood - 10s de pings contínuos |
| **dns-tunneling** | `dns-tunneling-detector.zeek` | 200 queries DNS com dados exfiltrados |
| **sql-injection** | `sql-injection-detector.zeek` | Exploits SQL injection com sqlmap |

---

## 🎯 Scripts Principais

### `run-attack.sh` - Menu Interativo de Ataques

Menu interativo para executar qualquer ataque com um comando:

```bash
./run-attack.sh
```

**Características:**
- ✅ Detecta automaticamente se está no modo Docker ou físico
- ✅ Configura rede correta (simir-net ou host)
- ✅ Mostra comandos esperados para verificar detecções
- ✅ Interface amigável com descrições dos ataques

**Menu:**
```
==========================================
  SIMIR - Attack Simulation Menu
==========================================

Target Server: 172.18.0.2

Available Attacks:
  1) DoS HTTP         - HTTP Flood Attack
  2) Brute Force SSH  - SSH Login Attempts
  3) Ping Flood       - ICMP Flood
  4) DNS Tunneling    - DNS Exfiltration
  5) SQL Injection    - SQL Injection Attempts

  0) Exit

Select attack to run:
```

### `start-target.sh` - Iniciar Servidor Alvo

Inicia o servidor alvo na rede Docker:

```bash
./start-target.sh
```

**O que faz:**
- Verifica se a rede `simir-net` existe
- Inicia container `SIMIR_TARGET` com IP fixo 172.18.0.2
- Atualiza automaticamente o arquivo `target.var`
- Mostra status e instruções

### `build-images.sh` - Construir Imagens de Ataque

Constrói todas as imagens Docker dos ataques:

```bash
./build-images.sh
```

**Nota:** No modo Docker (usando `start-simir.sh`), as imagens são construídas automaticamente.

---

## 📝 Arquivo `target.var`

Contém as variáveis de ambiente com IPs dos alvos:

```bash
TARGET_HOST="172.18.0.2"    # IP do servidor alvo (SSH, ping)
TARGET_WEB="172.18.0.2"     # IP do servidor web (HTTP, SQL)
```

**Atualização Automática:**
- ✅ `start-simir.sh` (Modo 2) atualiza automaticamente
- ✅ `start-target.sh` atualiza ao iniciar o servidor

**Atualização Manual:**
```bash
echo 'TARGET_HOST="172.18.0.2"' > target.var
echo 'TARGET_WEB="172.18.0.2"' >> target.var
```

---

## 🔧 Uso Manual dos Containers

### Modo Docker (Recomendado)

Se você usou `start-simir.sh` (Modo 2), execute:

```bash
# Com menu interativo
./run-attack.sh

# Ou diretamente
docker run --rm --network simir-net dos-http
docker run --rm --network simir-net brute-force-ssh
docker run --rm --network simir-net ping-flood
docker run --rm --network simir-net dns-tunneling
docker run --rm --network simir-net sql-injection
```

### Modo Interface Física

Se você usou `start-simir.sh` (Modo 1), precisa executar de **outra máquina**:

```bash
# Em outra máquina na rede
docker run --rm dos-http
docker run --rm brute-force-ssh
docker run --rm ping-flood
docker run --rm dns-tunneling
docker run --rm sql-injection
```

---

## 📖 Detalhes dos Ataques

### 1. DoS HTTP (`dos-http`)

**Descrição:** Ataque de negação de serviço HTTP com múltiplas técnicas

**O que faz:**
- Apache Bench: 10.000 requisições GET (200 conexões paralelas)
- POST Flood: 1.000 requisições POST maliciosas
- Slowloris: 200 conexões lentas (exaustão de recursos)
- Header Flood: 500 requisições com headers grandes (2KB)

**Total:** ~12.000+ conexões HTTP

**Detecção Esperada:**
```bash
docker exec SIMIR_Z grep 'DoS\|DDoS' /usr/local/zeek/spool/zeek/notice.log
```

**Alerta:** `DoS_Attack_Detected` quando >100 conexões de uma origem

---

### 2. Brute Force SSH (`brute-force-ssh`)

**Descrição:** Ataque de força bruta contra SSH

**O que faz:**
- Hydra: 100 tentativas de login SSH
- Usuário: root
- Alvo: ${TARGET_HOST}:22
- Senhas: Lista de senhas comuns

**Detecção Esperada:**
```bash
docker exec SIMIR_Z grep -i brute /usr/local/zeek/spool/zeek/notice.log
```

**Alerta:** `SSH_Brute_Force` quando >5 tentativas falhadas

---

### 3. Ping Flood (`ping-flood`)

**Descrição:** Inundação ICMP para DoS

**O que faz:**
- 10 segundos de pings contínuos
- Sem intervalo entre pacotes
- Payload: 1200 bytes
- Alvo: ${TARGET_HOST}

**Volume:** ~900.000 pacotes ICMP

**Detecção Esperada:**
```bash
docker exec SIMIR_Z grep 'ICMP' /usr/local/zeek/spool/zeek/notice.log
```

**Alerta:** `ICMP_Flood_Detected` quando >1000 pacotes/min

---

### 4. DNS Tunneling (`dns-tunneling`)

**Descrição:** Exfiltração de dados via DNS

**O que faz:**
- 200 queries DNS
- Subdomínios aleatórios com até 50 caracteres
- Simula túnel de dados
- Alta entropia nos nomes

**Detecção Esperada:**
```bash
docker exec SIMIR_Z grep 'DNS' /usr/local/zeek/spool/zeek/notice.log
```

**Alertas:**
- `DNS_High_Entropy` - Subdomínios com alta entropia
- `DNS_Long_Subdomain` - Subdomínios muito longos
- `DNS_Tunneling_Pattern` - Padrão de tunelamento agregado

---

### 5. SQL Injection (`sql-injection`)

**Descrição:** Exploits de injeção SQL

**O que faz:**
- Sqlmap contra ${TARGET_WEB}
- Testes de todas as vulnerabilidades
- Tentativas de dump de dados
- Bypass de autenticação

**Detecção Esperada:**
```bash
docker exec SIMIR_Z grep 'SQL' /usr/local/zeek/spool/zeek/notice.log
```

**Alerta:** `SQL_Injection_Attack` quando detecta padrões SQL maliciosos

---

## 🏗️ Estrutura de Diretórios

```
ataques_docker/
├── README.md                          # Este arquivo
├── run-attack.sh                      # Menu interativo de ataques ⭐
├── start-target.sh                    # Inicia servidor alvo ⭐
├── build-images.sh                    # Constrói todas as imagens
├── target.var                         # IPs dos alvos (atualizado automaticamente)
├── docker-compose-target-net.yml      # Config do servidor alvo
│
├── target-server/                     # Servidor alvo vulnerável ⭐
│   ├── Dockerfile                     # Nginx + OpenSSH
│   └── entrypoint.sh                  # Script de inicialização
│
├── dos-http/
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── brute-force-ssh/
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── ping-flood/
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── dns-tunneling/
│   ├── Dockerfile
│   └── entrypoint.sh
│
└── sql-injection/
    ├── Dockerfile
    └── entrypoint.sh
```

---

## ⚠️ Visibilidade do Zeek

### Problema: Localhost → Localhost

**O Zeek NÃO vê tráfego localhost → localhost!**

Quando você executa ataques do próprio servidor SIMIR contra ele mesmo, o tráfego usa loopback e não passa pela interface que o Zeek monitora.

### Soluções

#### 1. Modo Docker (RECOMENDADO) ⭐

Use `start-simir.sh` e selecione **Modo 2 - Rede Docker**:
- ✅ Tudo na mesma máquina
- ✅ Zeek vê todo o tráfego
- ✅ Fácil de usar
- ✅ Isolado e seguro

```bash
cd /home/rafael/SIMIR
./start-simir.sh
# Escolha: 2 (Modo Rede Docker)

# Executar ataques
cd ataques_docker
./run-attack.sh
```

#### 2. Modo Interface Física

Use `start-simir.sh` e selecione **Modo 1 - Interface Física**:
- ⚠️ Requer **outra máquina** na rede para executar ataques
- ✅ Simula ambiente real
- ✅ Para produção

#### 3. Mais Informações

Veja documentação completa:
- [VISIBILITY_ISSUE.md](./VISIBILITY_ISSUE.md) - Explicação técnica
- [DOCKER_MONITORING_GUIDE.md](./DOCKER_MONITORING_GUIDE.md) - Guia completo
- [DOCKER_NETWORK_ARCHITECTURE.md](./DOCKER_NETWORK_ARCHITECTURE.md) - Arquitetura

---

## 🔍 Monitoramento de Detecções

### Ver Alertas em Tempo Real

```bash
docker exec SIMIR_Z tail -f /usr/local/zeek/spool/zeek/notice.log
```

### Buscar Alertas Específicos

```bash
# DoS/DDoS
docker exec SIMIR_Z grep 'DoS\|DDoS' /usr/local/zeek/spool/zeek/notice.log

# Brute Force
docker exec SIMIR_Z grep -i brute /usr/local/zeek/spool/zeek/notice.log

# DNS Tunneling
docker exec SIMIR_Z grep 'DNS' /usr/local/zeek/spool/zeek/notice.log

# SQL Injection
docker exec SIMIR_Z grep 'SQL' /usr/local/zeek/spool/zeek/notice.log

# ICMP Flood
docker exec SIMIR_Z grep 'ICMP' /usr/local/zeek/spool/zeek/notice.log
```

### Estatísticas

```bash
# Contar alertas por tipo
docker exec SIMIR_Z cat /usr/local/zeek/spool/zeek/notice.log | \
  grep -v '^#' | awk '{print $11}' | sort | uniq -c

# Total de alertas
docker exec SIMIR_Z grep -v '^#' /usr/local/zeek/spool/zeek/notice.log | wc -l
```

---

## 🆘 Troubleshooting

### Ataque não detectado

**Verifique o modo:**
```bash
# Está no modo Docker?
docker network ls | grep simir-net

# Servidor alvo está rodando?
docker ps | grep SIMIR_TARGET

# Zeek está rodando?
docker exec SIMIR_Z zeekctl status
```

### Servidor alvo não responde

```bash
# Reiniciar servidor alvo
docker stop SIMIR_TARGET
./start-target.sh

# Verificar conectividade
docker run --rm --network simir-net alpine ping -c 3 172.18.0.2
```

### Containers não encontram target

```bash
# Verificar target.var
cat target.var

# Atualizar manualmente
echo 'TARGET_HOST="172.18.0.2"' > target.var
echo 'TARGET_WEB="172.18.0.2"' >> target.var

# Reconstruir imagens
./build-images.sh
```

---

## 📚 Documentação Adicional

- **[VISIBILITY_ISSUE.md](./VISIBILITY_ISSUE.md)** - Por que localhost não funciona
- **[DOCKER_MONITORING_GUIDE.md](./DOCKER_MONITORING_GUIDE.md)** - Guia completo do modo Docker
- **[DOCKER_NETWORK_ARCHITECTURE.md](./DOCKER_NETWORK_ARCHITECTURE.md)** - Arquitetura técnica
- **[../START_GUIDE.md](../START_GUIDE.md)** - Guia de início do SIMIR
- **[../docs/MANUAL_COMPLETO.md](../docs/MANUAL_COMPLETO.md)** - Manual completo

---

## ⚖️ Aviso Legal

**USO APENAS EM AMBIENTES DE TESTE!**

Estes ataques são para **fins educacionais e de teste** em ambientes controlados. O uso em sistemas sem autorização é **ilegal** e pode resultar em consequências criminais.

- ✅ Use apenas em redes de teste
- ✅ Obtenha autorização por escrito
- ✅ Documente todos os testes
- ❌ Nunca use em produção sem permissão
- ❌ Nunca ataque sistemas de terceiros
