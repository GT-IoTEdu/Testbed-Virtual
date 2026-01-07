# 📱 Guia Postman - Endereços IP DHCP

## 🎯 Visão Geral

Este guia mostra como testar o endpoint `/api/devices/dhcp/ip-addresses` usando o Postman.

## 🔗 URL Base

```
http://127.0.0.1:8000/api/devices/dhcp/ip-addresses
```

## 📋 Configuração Inicial

### 1. **Criar Nova Collection**

1. Abra o Postman
2. Clique em **"New"** → **"Collection"**
3. Nome: `DHCP IP Addresses`
4. Descrição: `Endpoints para gerenciar endereços IP DHCP`

### 2. **Configurar Variável de Ambiente**

1. Clique em **"Environments"** → **"New"**
2. Nome: `API IoT EDU`
3. Adicione a variável:
   - **Variable**: `api_base`
   - **Initial Value**: `http://127.0.0.1:8000/api/devices`
   - **Current Value**: `http://127.0.0.1:8000/api/devices`

## 🚀 Testes Disponíveis

### **Teste 1: Listar Todos os IPs**

#### Configuração:
- **Method**: `GET`
- **URL**: `{{api_base}}/dhcp/ip-addresses`
- **Headers**: `Content-Type: application/json`

#### Resultado Esperado:
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

---

### **Teste 2: Filtrar Apenas IPs Livres**

#### Configuração:
- **Method**: `GET`
- **URL**: `{{api_base}}/dhcp/ip-addresses?status_filter=free`
- **Headers**: `Content-Type: application/json`

#### Resultado Esperado:
```json
{
  "range_info": {
    "server_id": "lan",
    "interface": "lan",
    "range_from": "10.30.30.1",
    "range_to": "10.30.30.100",
    "total_ips": 100,
    "used_ips": 0,
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
    }
  ],
  "summary": {
    "total": 100,
    "used": 0,
    "free": 91,
    "reserved": 0
  }
}
```

---

### **Teste 3: Filtrar Apenas IPs Usados**

#### Configuração:
- **Method**: `GET`
- **URL**: `{{api_base}}/dhcp/ip-addresses?status_filter=used`
- **Headers**: `Content-Type: application/json`

#### Resultado Esperado:
```json
{
  "range_info": {
    "server_id": "lan",
    "interface": "lan",
    "range_from": "10.30.30.1",
    "range_to": "10.30.30.100",
    "total_ips": 100,
    "used_ips": 9,
    "free_ips": 0,
    "reserved_ips": 0
  },
  "ip_addresses": [
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
    "free": 0,
    "reserved": 0
  }
}
```

---

### **Teste 4: Range Personalizado**

#### Configuração:
- **Method**: `GET`
- **URL**: `{{api_base}}/dhcp/ip-addresses?range_from=10.30.30.1&range_to=10.30.30.50`
- **Headers**: `Content-Type: application/json`

#### Resultado Esperado:
```json
{
  "range_info": {
    "server_id": "lan",
    "interface": "lan",
    "range_from": "10.30.30.1",
    "range_to": "10.30.30.50",
    "total_ips": 50,
    "used_ips": 5,
    "free_ips": 45,
    "reserved_ips": 0
  },
  "ip_addresses": [...],
  "summary": {
    "total": 50,
    "used": 5,
    "free": 45,
    "reserved": 0
  }
}
```

---

### **Teste 5: Servidor Específico**

#### Configuração:
- **Method**: `GET`
- **URL**: `{{api_base}}/dhcp/ip-addresses?server_id=wan`
- **Headers**: `Content-Type: application/json`

---

## 📊 Collection JSON para Importar

```json
{
  "info": {
    "name": "DHCP IP Addresses",
    "description": "Endpoints para gerenciar endereços IP DHCP",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "1. Listar Todos os IPs",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "url": {
          "raw": "{{api_base}}/dhcp/ip-addresses",
          "host": ["{{api_base}}"],
          "path": ["dhcp", "ip-addresses"]
        },
        "description": "Lista todos os endereços IP no range DHCP"
      }
    },
    {
      "name": "2. IPs Livres",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
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
        },
        "description": "Lista apenas IPs livres disponíveis"
      }
    },
    {
      "name": "3. IPs Usados",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
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
        },
        "description": "Lista apenas IPs já atribuídos"
      }
    },
    {
      "name": "4. Range Personalizado",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "url": {
          "raw": "{{api_base}}/dhcp/ip-addresses?range_from=10.30.30.1&range_to=10.30.30.50",
          "host": ["{{api_base}}"],
          "path": ["dhcp", "ip-addresses"],
          "query": [
            {
              "key": "range_from",
              "value": "10.30.30.1"
            },
            {
              "key": "range_to",
              "value": "10.30.30.50"
            }
          ]
        },
        "description": "Lista IPs em range específico"
      }
    },
    {
      "name": "5. Servidor Específico",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "url": {
          "raw": "{{api_base}}/dhcp/ip-addresses?server_id=wan",
          "host": ["{{api_base}}"],
          "path": ["dhcp", "ip-addresses"],
          "query": [
            {
              "key": "server_id",
              "value": "wan"
            }
          ]
        },
        "description": "Lista IPs do servidor WAN"
      }
    }
  ]
}
```

## 🔧 Como Importar a Collection

### **Método 1: Importar JSON**
1. Abra o Postman
2. Clique em **"Import"**
3. Cole o JSON acima na aba **"Raw text"**
4. Clique em **"Continue"** → **"Import"**

### **Método 2: Criar Manualmente**
1. Crie uma nova collection
2. Para cada teste, clique em **"Add request"**
3. Configure conforme as especificações acima

## 📋 Parâmetros Disponíveis

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `server_id` | string | `lan` | ID do servidor DHCP |
| `range_from` | string | `10.30.30.1` | IP inicial do range |
| `range_to` | string | `10.30.30.100` | IP final do range |
| `status_filter` | string | `all` | Filtro por status |

### **Valores para status_filter:**
- `free` - Apenas IPs livres
- `used` - Apenas IPs usados
- `all` - Todos os IPs (padrão)

## 🎯 Casos de Uso Práticos

### **1. Encontrar IP Livre para Novo Dispositivo**
```
GET {{api_base}}/dhcp/ip-addresses?status_filter=free
```
- Use o primeiro IP da lista retornada

### **2. Verificar Se IP Específico Está Disponível**
```
GET {{api_base}}/dhcp/ip-addresses
```
- Procure pelo IP na resposta
- Verifique o campo `status`

### **3. Obter Estatísticas do Range**
```
GET {{api_base}}/dhcp/ip-addresses
```
- Veja o campo `summary` na resposta

### **4. Listar Dispositivos Ativos**
```
GET {{api_base}}/dhcp/ip-addresses?status_filter=used
```
- Lista todos os dispositivos com IP atribuído

## ⚠️ Dicas Importantes

1. **Certifique-se de que o servidor está rodando** em `http://127.0.0.1:8000`

2. **Configure a variável de ambiente** `api_base` corretamente

3. **Verifique os headers** - use `Content-Type: application/json`

4. **Para ranges grandes**, use filtros para melhor performance

5. **Os dados são atualizados em tempo real** baseados no banco de dados

## 🔍 Troubleshooting

### **Erro 404 - Not Found**
- Verifique se o servidor está rodando
- Confirme a URL base

### **Erro 500 - Internal Server Error**
- Verifique os logs do servidor
- Confirme se o banco de dados está acessível

### **Resposta Vazia**
- Verifique se há dados no banco de dados
- Confirme se o range está correto

## 📊 Exemplos de Resposta

### **Resposta de Sucesso (Todos os IPs):**
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

---

## 🎯 Próximos Passos

Após testar no Postman, você pode:

1. **Integrar com outros endpoints** como `/dhcp/save`
2. **Criar scripts automatizados** usando a API
3. **Desenvolver interface web** consumindo estes endpoints
4. **Implementar monitoramento** dos IPs em tempo real

---

## 📞 Suporte

Para dúvidas ou problemas:
- Consulte os logs do servidor
- Verifique a documentação da API
- Entre em contato com a equipe de desenvolvimento
