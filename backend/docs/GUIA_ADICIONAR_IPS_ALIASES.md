# 🔧 Guia: Como Adicionar IPs a Aliases Existentes

## 📋 Visão Geral

Este guia explica como adicionar novos endereços IP a um alias existente sem substituir os endereços atuais.

## 🎯 Funcionalidade Implementada

### **Endpoint:** `POST /api/devices/aliases-db/{alias_name}/add-addresses`

**Descrição:** Adiciona novos endereços IP a um alias existente, mantendo os endereços atuais.

---

## 🧪 Como Testar no Postman

### **1. Configuração Inicial**
```
api_base: http://127.0.0.1:8000/api/devices
```

### **2. Adicionar IPs a um Alias Existente**

**Método:** `POST`  
**URL:** `{{api_base}}/aliases-db/authorized_devices/add-addresses`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "addresses": [
    {
      "address": "192.168.1.210",
      "detail": "Dispositivo adicional 1"
    },
    {
      "address": "192.168.1.211",
      "detail": "Dispositivo adicional 2"
    },
    {
      "address": "192.168.1.212",
      "detail": "Dispositivo adicional 3"
    }
  ]
}
```

**Resposta Esperada:**
```json
{
  "id": 5,
  "pf_id": 4,
  "name": "authorized_devices",
  "alias_type": "host",
  "descr": "authorized_devices",
  "addresses": [
    {
      "address": "10.30.30.88",
      "detail": "Entry added Thu, 24 Jul 2025 14:28:31 -0300"
    },
    {
      "address": "10.30.30.81",
      "detail": "Entry added Fri, 25 Jul 2025 07:35:34 -0300"
    },
    {
      "address": "10.30.30.250",
      "detail": "Entry added Thu, 31 Jul 2025 11:05:27 -0300"
    },
    {
      "address": "192.168.1.210",
      "detail": "Dispositivo adicional 1"
    },
    {
      "address": "192.168.1.211",
      "detail": "Dispositivo adicional 2"
    },
    {
      "address": "192.168.1.212",
      "detail": "Dispositivo adicional 3"
    }
  ],
  "created_at": "2025-09-02T00:30:38",
  "updated_at": "2025-09-02T01:24:03"
}
```

---

## 🔧 Como Usar via cURL

### **Adicionar um IP:**
```bash
curl -X POST "http://127.0.0.1:8000/api/devices/aliases-db/authorized_devices/add-addresses" \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": [
      {
        "address": "192.168.1.210",
        "detail": "Dispositivo adicional 1"
      }
    ]
  }'
```

### **Adicionar múltiplos IPs:**
```bash
curl -X POST "http://127.0.0.1:8000/api/devices/aliases-db/authorized_devices/add-addresses" \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": [
      {
        "address": "192.168.1.210",
        "detail": "Dispositivo adicional 1"
      },
      {
        "address": "192.168.1.211",
        "detail": "Dispositivo adicional 2"
      },
      {
        "address": "192.168.1.212",
        "detail": "Dispositivo adicional 3"
      }
    ]
  }'
```

---

## 📝 Como Usar via Python

### **Script de Exemplo:**
```python
import requests

def adicionar_ips_ao_alias(alias_name, novos_ips):
    """Adiciona IPs a um alias existente."""
    
    url = f"http://127.0.0.1:8000/api/devices/aliases-db/{alias_name}/add-addresses"
    
    payload = {
        "addresses": novos_ips
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ IPs adicionados com sucesso!")
        print(f"   Alias: {data['name']}")
        print(f"   Total de endereços: {len(data['addresses'])}")
        return data
    else:
        print(f"❌ Erro: {response.status_code} - {response.text}")
        return None

# Exemplo de uso
novos_ips = [
    {"address": "192.168.1.210", "detail": "Dispositivo adicional 1"},
    {"address": "192.168.1.211", "detail": "Dispositivo adicional 2"}
]

resultado = adicionar_ips_ao_alias("authorized_devices", novos_ips)
```

---

## ⚠️ Importante

### **1. Tipos de Alias Suportados**
- ✅ **`host`**: Aceita IPs individuais (ex: `192.168.1.100`)
- ❌ **`network`**: Aceita apenas redes CIDR (ex: `192.168.1.0/24`)

### **2. Validações Automáticas**
- **Duplicatas**: IPs já existentes não são adicionados novamente
- **Formato**: Validação automática do formato de IP
- **pf_id**: Alias deve ter `pf_id` válido para sincronização com pfSense

### **3. Sincronização**
- **Banco Local**: IPs são adicionados ao banco de dados
- **pfSense**: Mudanças são sincronizadas automaticamente
- **Timestamp**: Campo `updated_at` é atualizado

---

## 🚨 Códigos de Erro

### **404 Not Found**
```json
{
  "detail": "Alias 'alias_inexistente' não encontrado"
}
```

### **400 Bad Request**
```json
{
  "detail": "Alias 'alias_existente' não possui pf_id válido para atualização no pfSense"
}
```

### **500 Internal Server Error**
```json
{
  "detail": "Erro ao adicionar endereços: Erro específico do sistema"
}
```

---

## 📊 Exemplos Práticos

### **Exemplo 1: Adicionar Dispositivos IoT**
```json
{
  "addresses": [
    {
      "address": "192.168.1.100",
      "detail": "Sensor de temperatura - Lab 1"
    },
    {
      "address": "192.168.1.101",
      "detail": "Sensor de umidade - Lab 2"
    },
    {
      "address": "192.168.1.102",
      "detail": "Câmera de segurança - Entrada"
    }
  ]
}
```

### **Exemplo 2: Adicionar Servidores**
```json
{
  "addresses": [
    {
      "address": "192.168.1.10",
      "detail": "Servidor Web - Produção"
    },
    {
      "address": "192.168.1.11",
      "detail": "Servidor de Banco de Dados"
    }
  ]
}
```

### **Exemplo 3: Adicionar Dispositivos de Rede**
```json
{
  "addresses": [
    {
      "address": "192.168.1.1",
      "detail": "Gateway Principal"
    },
    {
      "address": "192.168.1.254",
      "detail": "Switch de Distribuição"
    }
  ]
}
```

---

## 🔄 Diferença entre Atualizar e Adicionar

### **Atualizar (PATCH):**
- Substitui TODOS os endereços existentes
- Usa endpoint: `PATCH /aliases-db/{alias_name}`
- Útil para reconfiguração completa

### **Adicionar (POST):**
- Adiciona aos endereços existentes
- Usa endpoint: `POST /aliases-db/{alias_name}/add-addresses`
- Útil para expansão incremental

---

## 🎯 Casos de Uso Comuns

1. **Expansão de Rede**: Adicionar novos dispositivos à rede
2. **Manutenção**: Adicionar IPs temporários durante manutenção
3. **Escalabilidade**: Adicionar servidores conforme necessário
4. **Segurança**: Adicionar dispositivos autorizados gradualmente

---

## 📋 Checklist de Teste

- [ ] Verificar se o alias existe
- [ ] Confirmar que é do tipo `host`
- [ ] Verificar se tem `pf_id` válido
- [ ] Testar adição de IP único
- [ ] Testar adição de múltiplos IPs
- [ ] Verificar se duplicatas são ignoradas
- [ ] Confirmar sincronização com pfSense
- [ ] Verificar atualização do timestamp

---

## 🔗 Endpoints Relacionados

- **Listar aliases**: `GET /aliases-db`
- **Buscar alias**: `GET /aliases-db/{alias_name}`
- **Atualizar alias**: `PATCH /aliases-db/{alias_name}`
- **Criar alias**: `POST /aliases-db/create`
- **Adicionar IPs**: `POST /aliases-db/{alias_name}/add-addresses`
