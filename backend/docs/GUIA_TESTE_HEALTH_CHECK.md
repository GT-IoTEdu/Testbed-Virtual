# 🏥 Guia: Teste do Endpoint de Saúde da API

## 📋 Visão Geral

O endpoint `GET /health` é responsável por verificar a saúde da API IoT-EDU, retornando informações sobre o status do sistema, timestamp e versão.

## 🎯 Endpoint

```
GET /health
```

### 📍 URL Completa
```
http://127.0.0.1:8000/health
```

## 📊 Resposta Esperada

### ✅ Resposta de Sucesso (200 OK)
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "2.0.0"
}
```

### 📋 Campos da Resposta
- **`status`**: Status da API (`"healthy"` ou `"unhealthy"`)
- **`timestamp`**: Timestamp ISO 8601 da verificação
- **`version`**: Versão atual da API

## 🧪 Como Testar

### 🔧 Método 1: Postman (Recomendado)

#### 1. Importar Coleção
1. Abra o Postman
2. Clique em **Import**
3. Selecione o arquivo: `postman/IoT-EDU_Health_Check.postman_collection.json`
4. Clique em **Import**

#### 2. Configurar Ambiente
1. Clique em **Environments** (ícone de engrenagem)
2. Crie um novo ambiente ou use o existente
3. Configure a variável:
   ```
   base_url: http://127.0.0.1:8000
   ```

#### 3. Executar Teste
1. Selecione a requisição **"1. Health Check - Verificação de Saúde"**
2. Clique em **Send**
3. Verifique os resultados dos testes automáticos

### 🔧 Método 2: cURL

#### Comando Básico
```bash
curl -X GET "http://127.0.0.1:8000/health" \
  -H "Content-Type: application/json"
```

#### Comando com Headers Detalhados
```bash
curl -X GET "http://127.0.0.1:8000/health" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -v
```

### 🔧 Método 3: Navegador

1. Abra o navegador
2. Acesse: `http://127.0.0.1:8000/health`
3. Verifique a resposta JSON

### 🔧 Método 4: Python (requests)

```python
import requests
import json

def test_health_endpoint():
    url = "http://127.0.0.1:8000/health"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response.elapsed.total_seconds()}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Version: {data.get('version')}")
            print(f"Timestamp: {data.get('timestamp')}")
            
            # Validações
            assert data['status'] == 'healthy', "Status should be 'healthy'"
            assert 'version' in data, "Version field should be present"
            assert 'timestamp' in data, "Timestamp field should be present"
            
            print("✅ Health check passed!")
        else:
            print(f"❌ Health check failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_health_endpoint()
```

## ✅ Validações Automáticas

### 🔍 Testes Postman Incluídos

A coleção inclui os seguintes testes automáticos:

1. **Status Code**: Verifica se retorna 200 OK
2. **Response Time**: Verifica se resposta é menor que 1000ms
3. **Required Fields**: Verifica presença dos campos obrigatórios
4. **Status Value**: Verifica se status é 'healthy'
5. **Timestamp Format**: Verifica formato ISO do timestamp

### 📊 Exemplo de Resultado dos Testes

```
✅ Status code is 200
✅ Response time is less than 1000ms
✅ Response has required fields
✅ Status is 'healthy'
✅ Timestamp is valid ISO format
```

## 🚨 Cenários de Erro

### ❌ Servidor Não Iniciado
```json
{
  "error": "Connection refused"
}
```

### ❌ Servidor com Problemas
```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "2.0.0",
  "error": "Database connection failed"
}
```

### ❌ Timeout
```json
{
  "error": "Request timeout"
}
```

## 🔧 Troubleshooting

### Problema: Connection Refused
**Solução**: Verificar se o servidor está rodando
```bash
# Verificar se o servidor está ativo
python start_server.py
```

### Problema: Timeout
**Solução**: Verificar configurações de rede
```bash
# Testar conectividade
ping 127.0.0.1
```

### Problema: Resposta Lenta
**Solução**: Verificar recursos do sistema
```bash
# Verificar uso de CPU e memória
top
```

## 📈 Monitoramento Contínuo

### 🔄 Script de Monitoramento

```python
import requests
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitor_health():
    url = "http://127.0.0.1:8000/health"
    
    while True:
        try:
            start_time = time.time()
            response = requests.get(url, timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Health OK - Status: {data['status']}, Response Time: {response_time:.3f}s")
            else:
                logger.error(f"❌ Health Failed - Status Code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Connection Error: {e}")
            
        time.sleep(60)  # Verificar a cada 1 minuto

if __name__ == "__main__":
    monitor_health()
```

### 📊 Alertas

Configure alertas para:
- Status diferente de "healthy"
- Tempo de resposta > 1000ms
- Falhas de conexão
- Status code diferente de 200

## 🎯 Casos de Uso

### 🔍 Verificação Rápida
- Teste inicial ao iniciar o servidor
- Verificação antes de executar outros testes
- Monitoramento de saúde em produção

### 📊 Monitoramento
- Verificação contínua da API
- Alertas de falha
- Métricas de performance

### 🧪 Testes de Integração
- Validação de deploy
- Testes de smoke
- Verificação de ambiente

## 📝 Logs e Debug

### 🔍 Habilitar Logs Detalhados

```python
import requests
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Fazer requisição com logs
response = requests.get("http://127.0.0.1:8000/health")
logger.debug(f"Response: {response.text}")
```

### 📊 Métricas Importantes

- **Response Time**: < 1000ms
- **Availability**: > 99.9%
- **Status**: Always "healthy"
- **Version**: Consistent

---

**Guia criado em**: Setembro 2025  
**Versão**: 1.0  
**Mantido por**: Equipe IoT-EDU
