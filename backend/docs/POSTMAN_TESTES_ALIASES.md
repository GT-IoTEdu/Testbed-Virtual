# 🧪 Guia de Testes Postman - Sistema de Aliases

## 📋 Configuração Inicial

### 1. Configurar Variáveis de Ambiente
```
api_base: http://127.0.0.1:8000/api/devices
```

---

## 🔄 1. SALVAR ALIASES DO PFSENSE NO BANCO

### **POST** `{{api_base}}/aliases-db/save`

**Descrição:** Sincroniza todos os aliases do pfSense com o banco de dados local.

**Headers:**
```
Content-Type: application/json
```

**Body:** (vazio - não precisa de body)

**Resposta Esperada:**
```json
{
  "status": "success",
  "aliases_saved": 0,
  "aliases_updated": 9,
  "addresses_saved": 0,
  "addresses_updated": 15,
  "timestamp": "2025-09-02T01:01:10.6183",
  "pfsense_saved": true,
  "pfsense_message": "Aliases sincronizados com sucesso"
}
```

---

## 📋 2. LISTAR ALIASES DO BANCO

### **GET** `{{api_base}}/aliases-db`

**Descrição:** Lista todos os aliases armazenados no banco de dados local.

**Headers:**
```
Content-Type: application/json
```

**Query Parameters:**
```
page: 1 (opcional)
per_page: 20 (opcional)
```

**Resposta Esperada:**
```json
{
  "aliases": [
    {
      "id": 1,
      "pf_id": 0,
      "name": "Teste_API_IoT_EDU",
      "alias_type": "host",
      "descr": "Alias para todos os dispositivos IoT",
      "addresses": [
        {
          "address": "192.168.1.100",
          "detail": "Sensor Lab 1"
        },
        {
          "address": "192.168.1.101",
          "detail": "Sensor Lab 2"
        }
      ],
      "created_at": "2025-09-02T00:30:38",
      "updated_at": "2025-09-02T00:32:21"
    }
  ],
  "total": 9,
  "page": 1,
  "per_page": 20,
  "has_next": false,
  "has_prev": false
}
```

---

## 🔍 3. BUSCAR ALIASES

### **GET** `{{api_base}}/aliases-db/search?query=Teste`

**Descrição:** Busca aliases por nome ou descrição.

**Headers:**
```
Content-Type: application/json
```

**Query Parameters:**
```
query: Teste (obrigatório)
```

**Resposta Esperada:**
```json
{
  "query": "Teste",
  "total_found": 2,
  "aliases": [
    {
      "id": 1,
      "pf_id": 0,
      "name": "Teste_API_IoT_EDU",
      "alias_type": "host",
      "descr": "Alias para todos os dispositivos IoT",
      "addresses": [...],
      "created_at": "2025-09-02T00:30:38",
      "updated_at": "2025-09-02T00:32:21"
    }
  ]
}
```

---

## 📊 4. ESTATÍSTICAS DE ALIASES

### **GET** `{{api_base}}/aliases-db/statistics`

**Descrição:** Obtém estatísticas sobre os aliases no banco de dados.

**Headers:**
```
Content-Type: application/json
```

**Resposta Esperada:**
```json
{
  "total_aliases": 9,
  "aliases_by_type": {
    "host": 7,
    "network": 2
  },
  "total_addresses": 15,
  "created_today": 1,
  "updated_today": 3
}
```

---

## ➕ 5. CRIAR NOVO ALIAS

### **POST** `{{api_base}}/aliases-db/create`

**Descrição:** Cria um novo alias no pfSense e salva no banco de dados local.

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "name": "meu_novo_alias",
  "alias_type": "host",
  "descr": "Descrição do meu novo alias",
  "addresses": [
    {
      "address": "192.168.1.100",
      "detail": "Dispositivo principal"
    },
    {
      "address": "192.168.1.101",
      "detail": "Dispositivo secundário"
    }
  ]
}
```

**Resposta Esperada:**
```json
{
  "id": 10,
  "pf_id": 9,
  "name": "meu_novo_alias",
  "alias_type": "host",
  "descr": "Descrição do meu novo alias",
  "addresses": [
    {
      "address": "192.168.1.100",
      "detail": "Dispositivo principal"
    },
    {
      "address": "192.168.1.101",
      "detail": "Dispositivo secundário"
    }
  ],
  "created_at": "2025-09-02T01:05:30",
  "updated_at": "2025-09-02T01:05:30"
}
```

---

## ✏️ 6. ATUALIZAR ALIAS EXISTENTE

### **PATCH** `{{api_base}}/aliases-db/{alias_name}`

**Descrição:** Atualiza um alias existente no banco de dados e no pfSense.

**Headers:**
```
Content-Type: application/json
```

### **6.1 Atualizar Apenas Descrição**

**URL:** `{{api_base}}/aliases-db/Teste_API_IoT_EDU`

**Body:**
```json
{
  "descr": "Nova descrição do alias"
}
```

**Resposta Esperada:**
```json
{
  "id": 1,
  "pf_id": 0,
  "name": "Teste_API_IoT_EDU",
  "alias_type": "host",
  "descr": "Nova descrição do alias",
  "addresses": [
    {
      "address": "192.168.1.100",
      "detail": "Sensor Lab 1"
    },
    {
      "address": "192.168.1.101",
      "detail": "Sensor Lab 2"
    }
  ],
  "created_at": "2025-09-02T00:30:38",
  "updated_at": "2025-09-02T01:10:15"
}
```

### **6.2 Atualizar Endereços**

**URL:** `{{api_base}}/aliases-db/Teste_API_IoT_EDU`

**Body:**
```json
{
  "addresses": [
    {
      "address": "192.168.1.200",
      "detail": "Dispositivo atualizado 1"
    },
    {
      "address": "192.168.1.201",
      "detail": "Dispositivo atualizado 2"
    }
  ]
}
```

### **6.3 Atualizar Tudo**

**URL:** `{{api_base}}/aliases-db/Teste_API_IoT_EDU`

**Body:**
```json
{
  "alias_type": "network",
  "descr": "Alias de rede atualizado",
  "addresses": [
    {
      "address": "192.168.1.0/24",
      "detail": "Rede principal"
    }
  ]
}
```

---

## 🚨 CÓDIGOS DE ERRO COMUNS

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
  "detail": "Erro ao atualizar alias: Erro específico do sistema"
}
```

---

## 📝 EXEMPLOS DE TESTE COMPLETO

### **Sequência de Testes Recomendada:**

1. **Salvar aliases do pfSense** → `POST /aliases-db/save`
2. **Listar aliases** → `GET /aliases-db`
3. **Buscar aliases** → `GET /aliases-db/search?query=Teste`
4. **Ver estatísticas** → `GET /aliases-db/statistics`
5. **Criar novo alias** → `POST /aliases-db/create`
6. **Atualizar alias** → `PATCH /aliases-db/{alias_name}`

### **Teste de Atualização Completo:**

```javascript
// Pré-request Script (opcional)
pm.environment.set("alias_name", "Teste_API_IoT_EDU");

// Test Script
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has required fields", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
    pm.expect(jsonData).to.have.property('name');
    pm.expect(jsonData).to.have.property('alias_type');
    pm.expect(jsonData).to.have.property('descr');
    pm.expect(jsonData).to.have.property('addresses');
});

pm.test("Alias was updated", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.descr).to.eql("Nova descrição do alias");
});
```

---

## ⚠️ IMPORTANTE

1. **Alias deve ter `pf_id` válido** para atualizações
2. **Campos opcionais** - atualize apenas o que precisa
3. **Sincronização** - mudanças são aplicadas no banco local e pfSense
4. **Validação** - sistema verifica existência antes de atualizar

---

## 🔗 Endpoints pfSense Originais

- **Listar aliases:** `GET /api/v2/firewall/aliases`
- **Criar alias:** `POST /api/v2/firewall/alias`
- **Atualizar alias:** `PATCH /api/v2/firewall/alias`
- **Deletar alias:** `DELETE /api/v2/firewall/alias`
