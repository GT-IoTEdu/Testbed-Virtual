
# IDS Log Monitor - SSE Server

Monitor de logs em tempo real para Suricata, Snort e Zeek com API SSE (Server-Sent Events).

## 🚀 Funcionalidades

- **Stream em tempo real** de alertas de IDS
- **Suporte múltiplo**: Suricata, Snort e Zeek
- **API SSE** para consumo por dashboards
- **Filtros de SID** para ignorar alertas específicos
- **Autenticação por API Key**
- **Endpoints de health check**

## 📋 Pré-requisitos

- Python 3.8+
- Suricata, Snort ou Zeek instalados e configurados
- Acesso aos diretórios de logs dos IDS
- Porta 8001 disponível

## 🛠️ Instalação

### 1. Clonar o projeto

```bash
git clone https://github.com/GT-IoTEdu/API
cd ids-log-monitor
```

### 2. Criar ambiente virtual

```bash
# Criar virtual environment
python3 -m venv venv

# Ativar o ambiente (Linux/macOS)
source venv/bin/activate

# Ativar o ambiente (Windows)
venv\Scripts\activate
```

### 3. Instalar dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Se o arquivo `requirements.txt` não existir, crie-o com:

```bash
echo "fastapi==0.104.1
uvicorn[standard]==0.24.0
aiofiles==23.2.1
python-multipart==0.0.6" > requirements.txt
```

Ou instale manualmente:

```bash
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 aiofiles==23.2.1
```

## ⚙️ Configuração

### 1. Verificar caminhos dos logs

Edite o arquivo `sse_server.py` para ajustar os caminhos dos logs:

```python
# Linhas 18-20 - Ajuste conforme sua instalação
LOG_FILE_SURICATA = "/var/log/suricata/fast.log"
LOG_FILE_SNORT = "/var/log/snort/alert"
LOG_FILE_ZEEK = "/home/ubuntu/zeek-logs/notice.log"
```

### 2. Configurar API Keys (opcional)

Por padrão, a API key está definida como:
```python
API_KEYS = {
    "srv-monitoramento": "a8f4c2d9-1c9b-4b6f-9d6e-aaa111bbb222"
}
```

Para alterar ou adicionar mais chaves, edite o dicionário `API_KEYS`.

### 3. Configurar SIDs ignorados (opcional)

Para ignorar alertas específicos por SID:
```python
IGNORED_SIDS = {
    "999999",
    "2017515"
}
```

## 🚀 Execução

### 1. Ativar ambiente virtual

```bash
source venv/bin/activate
```

### 2. Iniciar o servidor

```bash
uvicorn sse_server:app --host 0.0.0.0 --port 8001
```

**Parâmetros:**
- `--host 0.0.0.0`: Escuta em todas interfaces de rede
- `--port 8001`: Porta do servidor
- `--reload`: Ativar auto-reload durante desenvolvimento (opcional)

### 3. Verificar se está funcionando

Acesse no navegador:
- Interface de documentação: http://localhost:8001/docs
- Health check: http://localhost:8001/health

## 🔌 Endpoints da API

### SSE Streams
```
GET /sse/alerts?api_key={API_KEY}       # Suricata
GET /sse/snort?api_key={API_KEY}        # Snort
GET /sse/zeek?api_key={API_KEY}         # Zeek
GET /sse/all?api_key={API_KEY}          # Todos combinados
```

### Outros Endpoints
```
GET /health                             # Status do serviço
GET /zeek/recent?api_key={API_KEY}&limit=50  # Alertas recentes Zeek
```

## 📊 Consumindo os Streams

### Exemplo via (Browser)

    http://192.168.59.103:8001/sse/snort?api_key=a8f4c2d9-1c9b-4b6f-9d6e-aaa111bbb222
    http://192.168.59.103:8001/sse/alerts?api_key=a8f4c2d9-1c9b-4b6f-9d6e-aaa111bbb222
    http://192.168.59.103:8001/sse/zeek?api_key=a8f4c2d9-1c9b-4b6f-9d6e-aaa111bbb222
## Exemplo de Log gerado

    {"ts":1770398159.951102,"proto":"tcp","note":"SQLInjection::SQL_Injection_Attempt","msg":"[SQLi] [CRITICAL] SQL Injection Attempt: [PRIVATE] 192.168.59.1 -> [PRIVATE] 192.168.59.103 GET /dvwa/vulnerabilities/sqli/?id=1\\xbf',(SELECT /*!00000(CASE WHEN (9871=9871) THEN SLEEP(5) ELSE 9871 END))*/-- DiZD","sub":"sqli_CRITICAL","src":"192.168.59.1","dst":"192.168.59.103","p":80,"actions":["Notice::ACTION_LOG"],"email_dest":[],"suppress_for":180.0}

## 🐛 Troubleshooting

### Problema: "Arquivo de log não encontrado"
**Solução:** Verifique os caminhos no código e permissões:
```bash
sudo chmod +r /var/log/suricata/fast.log
```

### Problema: Conexão SSE fecha automaticamente
**Solução:** Configurar keep-alive no proxy:
```nginx
proxy_read_timeout 86400s;
```


### Verificar logs do servidor
```bash
# Executar com logging detalhado
uvicorn sse_server:app --host 0.0.0.0 --port 8001 --log-level debug
```
