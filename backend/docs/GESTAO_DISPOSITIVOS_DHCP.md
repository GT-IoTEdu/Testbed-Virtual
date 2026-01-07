# 📋 Gestão de Dispositivos no DHCP - Guia Completo

Este documento explica como funciona a **inclusão, exclusão e edição** de dispositivos no servidor DHCP do pfSense através da API IoT-EDU.

---

## 📌 Resumo Executivo

### **Apply Automático?**
❌ **NÃO** - Por padrão, as mudanças DHCP ficam pendentes e precisam ser aplicadas manualmente.

### **Opções para Aplicar Mudanças:**

1. **Parâmetro `apply=true`** - Nas operações de UPDATE e DELETE
2. **Endpoint `/dhcp/apply`** - Aplica todas as mudanças DHCP pendentes manualmente

---

## 🔧 1. CRIAR Mapeamento Estático (CREATE)

### **Endpoint**
```
POST /api/devices/dhcp/static_mapping
```

### **Request Body**
```json
{
  "mac": "00:11:22:33:44:55",
  "ipaddr": "192.168.1.100",
  "cid": "device001",
  "hostname": "device-hostname",
  "descr": "Dispositivo IoT",
  "parent_id": "lan"  // opcional, padrão: "lan"
}
```

### **Processo**
1. ✅ Verifica automaticamente duplicatas (IP ou MAC já existente)
2. ✅ Cadastra no **pfSense** via API v2
3. ✅ Salva no **banco de dados local**
4. ⚠️ **Mudanças ficam pendentes** - É necessário chamar `/dhcp/apply`

### **Response**
```json
{
  "success": true,
  "message": "Mapeamento estático DHCP cadastrado com sucesso no pfSense",
  "data": {
    "id": 5,
    "mac": "00:11:22:33:44:55",
    "ipaddr": "192.168.1.100",
    ...
  }
}
```

### **Exemplo cURL**
```bash
curl -X POST http://localhost:8000/api/devices/dhcp/static_mapping \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "00:11:22:33:44:55",
    "ipaddr": "192.168.1.100",
    "cid": "device001",
    "hostname": "device-hostname",
    "descr": "Dispositivo IoT"
  }'

# Depois, aplicar as mudanças:
curl -X POST http://localhost:8000/api/devices/dhcp/apply
```

---

## ✏️ 2. ATUALIZAR Mapeamento Estático (UPDATE)

### **Endpoint**
```
PATCH /api/devices/dhcp/static_mapping
```

### **Query Parameters**
- `parent_id` (string, opcional): ID do servidor DHCP (padrão: "lan")
- `mapping_id` (int, obrigatório): ID do mapeamento no pfSense
- `apply` (bool, opcional): Aplica as mudanças imediatamente (padrão: false)

### **Request Body**
```json
{
  "mac": "00:11:22:33:44:66",
  "ipaddr": "192.168.1.101",
  "cid": "device001-updated",
  "hostname": "new-hostname",
  "descr": "Nova descrição"
}
```

### **Processo**
1. ✅ Atualiza no **pfSense**
2. ✅ Atualiza no **banco de dados local**
3. ⚙️ **Apply opcional** via parâmetro `apply=true`

### **Exemplos**

#### **Sem apply automático (padrão)**
```bash
curl -X PATCH "http://localhost:8000/api/devices/dhcp/static_mapping?mapping_id=5" \
  -H "Content-Type: application/json" \
  -d '{
    "descr": "Nova descrição",
    "cid": "Novo CID"
  }'

# Depois, aplicar manualmente:
curl -X POST http://localhost:8000/api/devices/dhcp/apply
```

#### **Com apply automático**
```bash
curl -X PATCH "http://localhost:8000/api/devices/dhcp/static_mapping?mapping_id=5&apply=true" \
  -H "Content-Type: application/json" \
  -d '{
    "descr": "Nova descrição",
    "cid": "Novo CID"
  }'
```

### **Response**
```json
{
  "success": true,
  "message": "Mapeamento estático DHCP (ID: 5) atualizado com sucesso no pfSense e banco de dados local",
  "parent_id": "lan",
  "mapping_id": 5,
  "applied": true,
  "local_updated": true,
  "data": {...}
}
```

---

## 🗑️ 3. EXCLUIR Mapeamento Estático (DELETE)

### **Endpoint**
```
DELETE /api/devices/dhcp/static_mapping
```

### **Query Parameters**
- `parent_id` (string, opcional): ID do servidor DHCP (padrão: "lan")
- `mapping_id` (int, obrigatório): ID do mapeamento no pfSense
- `apply` (bool, opcional): Aplica as mudanças imediatamente (padrão: false)

### **Processo**
1. ✅ Exclui do **pfSense**
2. ✅ Remove do **banco de dados local**
3. ⚙️ **Apply opcional** via parâmetro `apply=true`

### **Exemplos**

#### **Sem apply automático (padrão)**
```bash
curl -X DELETE "http://localhost:8000/api/devices/dhcp/static_mapping?mapping_id=5"

# Depois, aplicar manualmente:
curl -X POST http://localhost:8000/api/devices/dhcp/apply
```

#### **Com apply automático**
```bash
curl -X DELETE "http://localhost:8000/api/devices/dhcp/static_mapping?mapping_id=5&apply=true"
```

### **Response**
```json
{
  "success": true,
  "message": "Mapeamento estático DHCP (ID: 5) excluído com sucesso no pfSense e banco de dados local",
  "parent_id": "lan",
  "mapping_id": 5,
  "applied": true,
  "local_deleted": true,
  "data": {...}
}
```

---

## ⚡ 4. APLICAR Mudanças DHCP

### **Endpoint**
```
POST /api/devices/dhcp/apply
```

### **Descrição**
Aplica **todas as mudanças pendentes** no servidor DHCP do pfSense.
Equivalente a clicar no botão "Apply Changes" na interface web após modificar configurações DHCP.

### **API do pfSense Utilizada**
```
POST /api/v2/services/dhcp_server/apply
```

### **Quando usar?**
- Após criar novos mapeamentos estáticos
- Após atualizar mapeamentos (se não usar `apply=true`)
- Após excluir mapeamentos (se não usar `apply=true`)
- Para aplicar múltiplas mudanças de uma vez (batch operations)

### **Exemplo**
```bash
curl -X POST http://localhost:8000/api/devices/dhcp/apply
```

### **Response**
```json
{
  "status": "ok",
  "message": "Mudanças DHCP aplicadas com sucesso no pfSense",
  "result": {
    "code": 200,
    "message": "Changes applied successfully"
  }
}
```

---

## 🔄 5. DIFERENÇA entre `/firewall/apply` e `/dhcp/apply`

| Endpoint | API pfSense | Finalidade |
|----------|-------------|------------|
| `POST /firewall/apply` | `POST /api/v2/firewall/apply` | Aplica mudanças em **aliases** e **regras de firewall** |
| `POST /dhcp/apply` | `POST /api/v2/services/dhcp_server/apply` | Aplica mudanças em **mapeamentos estáticos DHCP** |

⚠️ **Importante:** São endpoints **separados** e independentes!

---

## 📊 Resumo de Operações

| Operação | Endpoint | Apply Automático? | Parâmetro Apply? | Requer Apply Manual? |
|----------|----------|-------------------|------------------|----------------------|
| **CREATE** | `POST /dhcp/static_mapping` | ❌ Não | ❌ Não disponível | ✅ Sim - chamar `/dhcp/apply` |
| **UPDATE** | `PATCH /dhcp/static_mapping` | ❌ Não (padrão) | ✅ Sim (`apply=true`) | ⚙️ Opcional |
| **DELETE** | `DELETE /dhcp/static_mapping` | ❌ Não (padrão) | ✅ Sim (`apply=true`) | ⚙️ Opcional |
| **APPLY** | `POST /dhcp/apply` | ✅ Aplica tudo | N/A | N/A |

---

## 💡 Boas Práticas

### **1. Operações Individuais**
```bash
# Criar dispositivo
curl -X POST .../dhcp/static_mapping -d '{...}'

# Aplicar imediatamente
curl -X POST .../dhcp/apply
```

### **2. Operações em Lote (Batch)**
```bash
# Criar múltiplos dispositivos
curl -X POST .../dhcp/static_mapping -d '{device1}'
curl -X POST .../dhcp/static_mapping -d '{device2}'
curl -X POST .../dhcp/static_mapping -d '{device3}'

# Aplicar todas as mudanças de uma vez
curl -X POST .../dhcp/apply
```

### **3. Edição/Exclusão com Apply Imediato**
```bash
# Atualizar e aplicar em uma única operação
curl -X PATCH ".../dhcp/static_mapping?mapping_id=5&apply=true" -d '{...}'

# Excluir e aplicar em uma única operação
curl -X DELETE ".../dhcp/static_mapping?mapping_id=5&apply=true"
```

---

## 🔍 Verificação de Duplicatas

O sistema verifica automaticamente duplicatas durante a criação:

### **Verificação Automática (CREATE)**
- ✅ Verifica se IP já existe
- ✅ Verifica se MAC já existe
- ⚠️ Retorna erro 409 (Conflict) se encontrar duplicata

### **Exemplo de Erro**
```json
{
  "detail": "Já existem mapeamentos DHCP com os mesmos dados:\n- IP 192.168.1.100 já está em uso pelo dispositivo device002 (MAC: aa:bb:cc:dd:ee:ff)"
}
```

---

## 🗂️ Estrutura de Dados

### **Modelo no Banco de Dados Local**
```python
class DhcpStaticMapping:
    id: int                    # ID local (auto-incremento)
    server_id: int             # ID do servidor DHCP
    pf_id: int                 # ID no pfSense
    mac: str                   # Endereço MAC
    ipaddr: str                # Endereço IP
    cid: str                   # Client ID
    hostname: str              # Nome do host
    descr: str                 # Descrição
    is_blocked: bool           # Se está bloqueado
    reason: str                # Motivo do bloqueio
    created_at: datetime       # Data de criação
    updated_at: datetime       # Data de atualização
```

---

## 📝 Notas Importantes

1. **Sincronização Dupla**: Todas as operações mantêm o pfSense e o banco local sincronizados
2. **ID do pfSense**: O campo `pf_id` armazena o ID do mapeamento no pfSense para referência
3. **Parent ID**: Por padrão é "lan", mas pode ser alterado para outras interfaces (wan, opt1, etc.)
4. **Apply Assíncrono**: O apply pode levar alguns segundos, aguarde a resposta completa
5. **Timeout**: O timeout para apply é de 30 segundos

---

## 🛠️ Arquivos Relacionados

- **`backend/services_firewalls/pfsense_client.py`**: Funções de comunicação com pfSense
- **`backend/services_firewalls/router.py`**: Endpoints da API
- **`backend/services_firewalls/dhcp_service.py`**: Lógica de negócio DHCP
- **`backend/db/models.py`**: Modelos de dados

---

## 🚀 Exemplo de Fluxo Completo

```bash
# 1. Criar novo dispositivo
curl -X POST http://localhost:8000/api/devices/dhcp/static_mapping \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "aa:bb:cc:dd:ee:ff",
    "ipaddr": "192.168.1.150",
    "cid": "sensor-temperatura-01",
    "hostname": "sensor-temp-01",
    "descr": "Sensor de temperatura - Sala 1"
  }'

# 2. Aplicar mudanças DHCP
curl -X POST http://localhost:8000/api/devices/dhcp/apply

# 3. Atualizar descrição (com apply automático)
curl -X PATCH "http://localhost:8000/api/devices/dhcp/static_mapping?mapping_id=10&apply=true" \
  -H "Content-Type: application/json" \
  -d '{
    "descr": "Sensor de temperatura - Sala 2 (relocado)"
  }'

# 4. Excluir dispositivo (com apply automático)
curl -X DELETE "http://localhost:8000/api/devices/dhcp/static_mapping?mapping_id=10&apply=true"
```

---

**Última atualização:** 08/10/2025  
**Versão:** 2.0

