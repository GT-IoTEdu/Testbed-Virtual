# 📊 Guia de Endereços IP - DHCP

## 🎯 Visão Geral

Este guia explica como usar o endpoint `/api/devices/dhcp/ip-addresses` para listar endereços IP usados e livres no range DHCP.

## 🔗 Endpoint

```
GET /api/devices/dhcp/ip-addresses
```

## 📋 Parâmetros

| Parâmetro | Tipo | Obrigatório | Padrão | Descrição |
|-----------|------|-------------|--------|-----------|
| `server_id` | string | Não | `lan` | ID do servidor DHCP |
| `range_from` | string | Não | `10.30.30.1` | IP inicial do range |
| `range_to` | string | Não | `10.30.30.100` | IP final do range |
| `status_filter` | string | Não | `all` | Filtro por status (`used`, `free`, `all`) |

## 📊 Resposta

```json
{
  "range_info": {
    "server_id": "lan",
    "interface": "lan",
    "range_from": "10.30.30.1",
    "range_to": "10.30.30.100",
    "total_ips": 100,
    "used_ips": 9,
    "free_ips": 91,
    "reserved_ips": 0
  },
  "ip_addresses": [
    {
      "ip": "10.30.30.1",
      "status": "free",
      "mac": null,
      "hostname": null,
      "description": null,
      "last_seen": null
    },
    {
      "ip": "10.30.30.3",
      "status": "used",
      "mac": "bc:24:11:68:fb:77",
      "hostname": "openvas",
      "description": "openvas",
      "last_seen": null
    }
  ],
  "summary": {
    "total": 100,
    "used": 9,
    "free": 91,
    "reserved": 0
  }
}
```

## 🚀 Exemplos de Uso

### 1. Listar Todos os IPs (Padrão)

```bash
curl -X GET "http://127.0.0.1:8000/api/devices/dhcp/ip-addresses"
```

**Resposta:** Lista todos os IPs no range 10.30.30.1-100

### 2. Filtrar Apenas IPs Livres

```bash
curl -X GET "http://127.0.0.1:8000/api/devices/dhcp/ip-addresses?status_filter=free"
```

**Resposta:** Lista apenas IPs disponíveis para uso

### 3. Filtrar Apenas IPs Usados

```bash
curl -X GET "http://127.0.0.1:8000/api/devices/dhcp/ip-addresses?status_filter=used"
```

**Resposta:** Lista apenas IPs já atribuídos a dispositivos

### 4. Range Personalizado

```bash
curl -X GET "http://127.0.0.1:8000/api/devices/dhcp/ip-addresses?range_from=10.30.30.1&range_to=10.30.30.50"
```

**Resposta:** Lista IPs no range 10.30.30.1-50

### 5. Servidor Específico

```bash
curl -X GET "http://127.0.0.1:8000/api/devices/dhcp/ip-addresses?server_id=wan"
```

**Resposta:** Lista IPs do servidor WAN

## 📱 Exemplos no Postman

### Collection para Postman

```json
{
  "info": {
    "name": "DHCP IP Addresses",
    "description": "Endpoints para gerenciar endereços IP DHCP"
  },
  "item": [
    {
      "name": "Listar Todos os IPs",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{api_base}}/dhcp/ip-addresses",
          "host": ["{{api_base}}"],
          "path": ["dhcp", "ip-addresses"]
        }
      }
    },
    {
      "name": "IPs Livres",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{api_base}}/dhcp/ip-addresses?status_filter=free",
          "host": ["{{api_base}}"],
          "path": ["dhcp", "ip-addresses"],
          "query": [
            {
              "key": "status_filter",
              "value": "free"
            }
          ]
        }
      }
    },
    {
      "name": "IPs Usados",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{api_base}}/dhcp/ip-addresses?status_filter=used",
          "host": ["{{api_base}}"],
          "path": ["dhcp", "ip-addresses"],
          "query": [
            {
              "key": "status_filter",
              "value": "used"
            }
          ]
        }
      }
    }
  ]
}
```

## 🔧 Scripts de Teste

### Python - Listar IPs Livres

```python
import requests

def get_free_ips():
    """Lista IPs livres disponíveis."""
    response = requests.get('http://127.0.0.1:8000/api/devices/dhcp/ip-addresses?status_filter=free')
    
    if response.status_code == 200:
        data = response.json()
        free_ips = data['ip_addresses']
        
        print(f"📊 IPs Livres: {len(free_ips)}")
        for ip_info in free_ips[:10]:  # Primeiros 10
            print(f"   - {ip_info['ip']}")
    else:
        print(f"❌ Erro: {response.status_code}")

get_free_ips()
```

### PowerShell - Verificar IP Específico

```powershell
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/devices/dhcp/ip-addresses" -Method Get

# Verificar se um IP específico está livre
$target_ip = "10.30.30.15"
$ip_info = $response.ip_addresses | Where-Object { $_.ip -eq $target_ip }

if ($ip_info.status -eq "free") {
    Write-Host "✅ IP $target_ip está livre"
} else {
    Write-Host "❌ IP $target_ip está usado por: $($ip_info.mac)"
}
```

## 📊 Status dos IPs

| Status | Descrição |
|--------|-----------|
| `free` | IP disponível para uso |
| `used` | IP já atribuído a um dispositivo |
| `reserved` | IP reservado (não implementado ainda) |

## 🎯 Casos de Uso

### 1. **Encontrar IP Livre para Novo Dispositivo**
```bash
curl "http://127.0.0.1:8000/api/devices/dhcp/ip-addresses?status_filter=free" | jq '.ip_addresses[0].ip'
```

### 2. **Verificar Se IP Está Disponível**
```bash
curl "http://127.0.0.1:8000/api/devices/dhcp/ip-addresses" | jq '.ip_addresses[] | select(.ip == "10.30.30.15")'
```

### 3. **Listar Todos os Dispositivos Ativos**
```bash
curl "http://127.0.0.1:8000/api/devices/dhcp/ip-addresses?status_filter=used" | jq '.ip_addresses[] | "\(.ip): \(.mac) - \(.description)"'
```

### 4. **Estatísticas do Range**
```bash
curl "http://127.0.0.1:8000/api/devices/dhcp/ip-addresses" | jq '.summary'
```

## ⚠️ Observações Importantes

1. **Range Padrão:** O sistema usa range 10.30.30.1-100 por padrão
2. **Sincronização:** Os dados são baseados nos mapeamentos estáticos do banco de dados
3. **Performance:** Para ranges muito grandes, considere usar filtros
4. **Atualização:** Os dados são atualizados em tempo real

## 🔄 Integração com Outros Endpoints

- **Cadastrar Dispositivo:** Use um IP livre do endpoint `/dhcp/save`
- **Verificar Dispositivo:** Use `/dhcp/devices/ip/{ip}` para detalhes
- **Buscar Dispositivo:** Use `/dhcp/devices/search` para busca por MAC/IP

---

## 📞 Suporte

Para dúvidas ou problemas, consulte a documentação da API ou entre em contato com a equipe de desenvolvimento.
