# Snort3 - Detector de Intrusão

Sistema de detecção de intrusão baseado em Snort3 para monitoramento de ataques de rede.

## 📁 Arquivos

```
snort3/
├── Dockerfile         # Imagem Docker com Snort3
├── snort.lua          # Configuração do Snort3
├── local.rules        # Regras de detecção
└── start_snort.sh     # Script de inicialização
```

## 🚀 Uso Rápido

```bash
# Construir
docker build -t snort3 .

# Executar (substitua enp0s3 pela sua interface)
docker run --rm --privileged --network host snort3 enp0s3
#ou
docker run --rm --privileged --network host joaoprdo/snort3:latest enp0s3

```

> [!NOTE]
> A imagem pode demorar alguns minutos (cerca de 18 minutos) para ser construída, pois compila o Snort3 e suas dependências.
> Para adiantar o processo, você pode usar a imagem já pronta do Docker Hub:

```bash
docker pull joaoprdo/snort3:latest
```

## 🔍 Ataques Detectados

| Tipo                | Descrição              | Threshold           |
| ------------------- | ---------------------- | ------------------- |
| **HTTP DoS**        | GET/POST flood         | 20/10 req em 5s     |
| **SSH Brute Force** | Múltiplas conexões SSH | 10 tent em 60s      |
| **ICMP Flood**      | Ping flood             | 50 pings em 5s      |
| **SQL Injection**   | UNION, OR 1=1, quotes  | Qualquer ocorrência |
| **DNS Tunneling**   | Alto volume DNS        | 50 queries em 10s   |

## 📊 Logs

Os alertas são salvos em `/opt/snort3/logs/`:

- `alert_full.txt` - Detalhes completos

## ⚙️ Parâmetros

```bash
# Interface específica
docker run --rm --privileged --network host snort3 wlan0
#ou
docker run --rm --privileged --network host joaoprdo/snort3:latest enp0s3

# Com alertas rápidos
docker run --rm --privileged --network host snort3 enp0s3 -A fast
#ou
docker run --rm --privileged --network host joaoprdo/snort3:latest  enp0s3 -A fast

# Persistir logs
docker run --rm --privileged --network host \
  -v $(pwd)/logs:/opt/snort3/logs \
  snort3 enp0s3
#ou
docker run --rm --privileged --network host \
  -v $(pwd)/logs:/opt/snort3/logs \
  joaoprdo/snort3:latest enp0s3
```
