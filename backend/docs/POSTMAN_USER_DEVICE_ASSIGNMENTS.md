# 🚀 **Guia Postman - Atribuição de Usuários a Dispositivos DHCP**

## **Configuração Inicial**

### **1. Variáveis de Ambiente**
Configure no Postman:
- `base_url`: `http://127.0.0.1:8000`
- `api_base`: `{{base_url}}/api/devices`

### **2. Collection JSON para Importar**
```json
{
  "info": {
    "name": "IoT-EDU User-Device Assignments",
    "description": "Endpoints para atribuição de usuários a dispositivos DHCP",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://127.0.0.1:8000"
    },
    {
      "key": "api_base",
      "value": "{{base_url}}/api/devices"
    }
  ],
  "item": [
    {
      "name": "Atribuir Dispositivo a Usuário",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"user_id\": 1,\n  \"device_id\": 1,\n  \"notes\": \"Dispositivo de monitoramento atribuído ao administrador\",\n  \"assigned_by\": 1\n}"
        },
        "url": {
          "raw": "{{api_base}}/assignments",
          "host": ["{{api_base}}"],
          "path": ["assignments"]
        }
      }
    },
    {
      "name": "Remover Atribuição",
      "request": {
        "method": "DELETE",
        "url": {
          "raw": "{{api_base}}/assignments/1/1",
          "host": ["{{api_base}}"],
          "path": ["assignments", "1", "1"]
        }
      }
    },
    {
      "name": "Listar Dispositivos do Usuário",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{api_base}}/users/1/devices",
          "host": ["{{api_base}}"],
          "path": ["users", "1", "devices"]
        }
      }
    },
    {
      "name": "Listar Usuários do Dispositivo",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{api_base}}/devices/1/users",
          "host": ["{{api_base}}"],
          "path": ["devices", "1", "users"]
        }
      }
    },
    {
      "name": "Buscar Atribuições",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{api_base}}/assignments/search?query=joner",
          "host": ["{{api_base}}"],
          "path": ["assignments", "search"],
          "query": [
            {
              "key": "query",
              "value": "joner"
            }
          ]
        }
      }
    },
    {
      "name": "Estatísticas de Atribuições",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{api_base}}/assignments/statistics",
          "host": ["{{api_base}}"],
          "path": ["assignments", "statistics"]
        }
      }
    }
  ]
}
```

---

## **📋 Endpoints Disponíveis**

### **1. 🔗 Atribuir Dispositivo a Usuário**

**Método**: `POST`  
**URL**: `{{api_base}}/assignments`  
**Headers**: 
```
Content-Type: application/json
```

**Body (JSON)**:
```json
{
  "user_id": 1,
  "device_id": 1,
  "notes": "Dispositivo de monitoramento atribuído ao administrador",
  "assigned_by": 1
}
```

**Exemplo de Resposta**:
```json
{
  "id": 1,
  "user_id": 1,
  "device_id": 1,
  "assigned_at": "2024-01-01T12:00:00",
  "assigned_by": 1,
  "notes": "Dispositivo de monitoramento atribuído ao administrador",
  "is_active": true,
  "user": {
    "id": 1,
    "email": "jomermello@hotmail.com",
    "nome": "joner mello",
    "instituicao": "unipampa",
    "ultimo_login": "2025-09-01T14:36:49"
  },
  "device": {
    "id": 1,
    "server_id": 1,
    "pf_id": 0,
    "mac": "bc:24:11:68:fb:77",
    "ipaddr": "10.30.30.3",
    "cid": "openvas",
    "hostname": "openvas",
    "descr": "openvas",
    "created_at": "2025-09-01T14:36:49",
    "updated_at": "2025-09-01T14:36:49"
  }
}
```

---

### **2. 🗑️ Remover Atribuição**

**Método**: `DELETE`  
**URL**: `{{api_base}}/assignments/{user_id}/{device_id}`  

**Exemplo**: `{{api_base}}/assignments/1/1`

**Exemplo de Resposta**:
```json
{
  "status": "success",
  "message": "Atribuição removida com sucesso",
  "user_id": 1,
  "device_id": 1
}
```

---

### **3. 📋 Listar Dispositivos do Usuário**

**Método**: `GET`  
**URL**: `{{api_base}}/users/{user_id}/devices`  
**Query Parameters**:
- `include_inactive`: `false` (opcional)

**Exemplo**: `{{api_base}}/users/1/devices`

**Exemplo de Resposta**:
```json
{
  "user": {
    "id": 1,
    "email": "jomermello@hotmail.com",
    "nome": "joner mello",
    "instituicao": "unipampa",
    "ultimo_login": "2025-09-01T14:36:49"
  },
  "devices": [
    {
      "id": 1,
      "server_id": 1,
      "pf_id": 0,
      "mac": "bc:24:11:68:fb:77",
      "ipaddr": "10.30.30.3",
      "cid": "openvas",
      "hostname": "openvas",
      "descr": "openvas",
      "created_at": "2025-09-01T14:36:49",
      "updated_at": "2025-09-01T14:36:49"
    }
  ],
  "total_devices": 1,
  "active_assignments": 1
}
```

---

### **4. 👥 Listar Usuários do Dispositivo**

**Método**: `GET`  
**URL**: `{{api_base}}/devices/{device_id}/users`  
**Query Parameters**:
- `include_inactive`: `false` (opcional)

**Exemplo**: `{{api_base}}/devices/1/users`

**Exemplo de Resposta**:
```json
{
  "device": {
    "id": 1,
    "server_id": 1,
    "pf_id": 0,
    "mac": "bc:24:11:68:fb:77",
    "ipaddr": "10.30.30.3",
    "cid": "openvas",
    "hostname": "openvas",
    "descr": "openvas",
    "created_at": "2025-09-01T14:36:49",
    "updated_at": "2025-09-01T14:36:49"
  },
  "users": [
    {
      "id": 1,
      "email": "jomermello@hotmail.com",
      "nome": "joner mello",
      "instituicao": "unipampa",
      "ultimo_login": "2025-09-01T14:36:49"
    }
  ],
  "total_users": 1,
  "active_assignments": 1
}
```

---

### **5. 🔍 Buscar Atribuições**

**Método**: `GET`  
**URL**: `{{api_base}}/assignments/search`  
**Query Parameters**:
- `query`: `joner` (obrigatório)

**Exemplo**: `{{api_base}}/assignments/search?query=joner`

**Exemplo de Resposta**:
```json
{
  "assignments": [
    {
      "id": 1,
      "user_id": 1,
      "device_id": 1,
      "assigned_at": "2024-01-01T12:00:00",
      "assigned_by": 1,
      "notes": "Dispositivo de monitoramento atribuído ao administrador",
      "is_active": true,
      "user": {
        "id": 1,
        "email": "jomermello@hotmail.com",
        "nome": "joner mello",
        "instituicao": "unipampa",
        "ultimo_login": "2025-09-01T14:36:49"
      },
      "device": {
        "id": 1,
        "server_id": 1,
        "pf_id": 0,
        "mac": "bc:24:11:68:fb:77",
        "ipaddr": "10.30.30.3",
        "cid": "openvas",
        "hostname": "openvas",
        "descr": "openvas",
        "created_at": "2025-09-01T14:36:49",
        "updated_at": "2025-09-01T14:36:49"
      }
    }
  ],
  "total_found": 1,
  "query": "joner"
}
```

---

### **6. 📊 Estatísticas de Atribuições**

**Método**: `GET`  
**URL**: `{{api_base}}/assignments/statistics`

**Exemplo de Resposta**:
```json
{
  "total_assignments": 2,
  "active_assignments": 2,
  "inactive_assignments": 0,
  "users_with_devices": 1,
  "devices_with_users": 2,
  "assignments_by_institution": {
    "unipampa": 2
  }
}
```

---

## **🧪 Scripts de Teste para Postman**

### **Script de Pré-requisição (Pre-request Script)**
```javascript
// Verificar se o servidor está rodando
pm.test("Servidor está rodando", function () {
    pm.response.to.have.status(200);
});
```

### **Script de Teste (Tests Script)**
```javascript
// Teste básico de resposta
pm.test("Status code é 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Resposta é JSON", function () {
    pm.response.to.be.json;
});

pm.test("Resposta tem tempo de resposta aceitável", function () {
    pm.expect(pm.response.responseTime).to.be.below(5000);
});

// Testes específicos para cada endpoint
if (pm.info.requestName === "Atribuir Dispositivo a Usuário") {
    pm.test("Dispositivo atribuído com sucesso", function () {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property("id");
        pm.expect(jsonData).to.have.property("user");
        pm.expect(jsonData).to.have.property("device");
        pm.expect(jsonData.is_active).to.be.true;
    });
}

if (pm.info.requestName === "Listar Dispositivos do Usuário") {
    pm.test("Dispositivos do usuário retornados", function () {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property("user");
        pm.expect(jsonData).to.have.property("devices");
        pm.expect(jsonData).to.have.property("total_devices");
        pm.expect(jsonData).to.have.property("active_assignments");
    });
}

if (pm.info.requestName === "Listar Usuários do Dispositivo") {
    pm.test("Usuários do dispositivo retornados", function () {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property("device");
        pm.expect(jsonData).to.have.property("users");
        pm.expect(jsonData).to.have.property("total_users");
        pm.expect(jsonData).to.have.property("active_assignments");
    });
}

if (pm.info.requestName === "Buscar Atribuições") {
    pm.test("Busca de atribuições realizada", function () {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property("assignments");
        pm.expect(jsonData).to.have.property("total_found");
        pm.expect(jsonData).to.have.property("query");
    });
}

if (pm.info.requestName === "Estatísticas de Atribuições") {
    pm.test("Estatísticas retornadas", function () {
        const jsonData = pm.response.json();
        pm.expect(jsonData).to.have.property("total_assignments");
        pm.expect(jsonData).to.have.property("active_assignments");
        pm.expect(jsonData).to.have.property("users_with_devices");
        pm.expect(jsonData).to.have.property("devices_with_users");
    });
}
```

---

## **📝 Exemplos de Uso Prático**

### **Cenário 1: Atribuir Dispositivo OpenVAS ao Administrador**
```bash
curl -X POST http://127.0.0.1:8000/api/devices/assignments \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "device_id": 1,
    "notes": "Servidor de monitoramento de vulnerabilidades",
    "assigned_by": 1
  }'
```

### **Cenário 2: Ver Dispositivos do Usuário**
```bash
curl http://127.0.0.1:8000/api/devices/users/1/devices
```

### **Cenário 3: Ver Quem Tem Acesso ao OpenVAS**
```bash
curl http://127.0.0.1:8000/api/devices/devices/1/users
```

### **Cenário 4: Buscar Todas as Atribuições do Joner**
```bash
curl "http://127.0.0.1:8000/api/devices/assignments/search?query=joner"
```

### **Cenário 5: Ver Estatísticas Gerais**
```bash
curl http://127.0.0.1:8000/api/devices/assignments/statistics
```

---

## **🔧 Ordem de Execução Recomendada**

1. **Primeiro**: Execute "Salvar Dados DHCP" para popular o banco
2. **Segundo**: Execute "Atribuir Dispositivo a Usuário" 
3. **Terceiro**: Execute "Listar Dispositivos do Usuário"
4. **Quarto**: Execute "Listar Usuários do Dispositivo"
5. **Quinto**: Execute "Buscar Atribuições"
6. **Sexto**: Execute "Estatísticas de Atribuições"
7. **Sétimo**: Execute "Remover Atribuição" (opcional)

---

## **⚠️ Dicas Importantes**

- **Certifique-se** de que o servidor está rodando
- **Execute primeiro** o endpoint de salvar dados DHCP
- **Use IDs válidos** de usuários e dispositivos existentes
- **Verifique os logs** do servidor se houver erros
- **Teste com dados reais** do seu ambiente

---

## **🚨 Troubleshooting**

### **Erro 404 - Usuário não encontrado**
- Verifique se o usuário existe na tabela `users`
- Confirme o ID do usuário

### **Erro 404 - Dispositivo não encontrado**
- Verifique se o dispositivo existe na tabela `dhcp_static_mappings`
- Execute primeiro o endpoint de salvar dados DHCP

### **Erro 400 - Atribuição já existe**
- A atribuição já está ativa para este usuário e dispositivo
- Use o endpoint de remoção primeiro se necessário

### **Erro 500 - Erro interno**
- Verifique os logs do servidor
- Confirme se as tabelas foram criadas corretamente
- Teste a conexão com o banco de dados
