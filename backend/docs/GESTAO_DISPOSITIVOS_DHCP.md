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
4. ✅ **Aplica as mudanças automaticamente** no pfSense

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
# As mudanças são aplicadas automaticamente! ✅
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
- `apply` (bool, opcional): Aplica as mudanças imediatamente (padrão: **true**)

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
3. ✅ **Apply automático** por padrão (pode ser desabilitado com `apply=false`)

### **Exemplos**

#### **Com apply automático (padrão)**
```bash
curl -X PATCH "http://localhost:8000/api/devices/dhcp/static_mapping?mapping_id=5" \
  -H "Content-Type: application/json" \
  -d '{
    "descr": "Nova descrição",
    "cid": "Novo CID"
  }'
# As mudanças são aplicadas automaticamente!
```

#### **Sem apply automático (usar apply=false)**
```bash
curl -X PATCH "http://localhost:8000/api/devices/dhcp/static_mapping?mapping_id=5&apply=false" \
  -H "Content-Type: application/json" \
  -d '{
    "descr": "Nova descrição",
    "cid": "Novo CID"
  }'

# Depois, aplicar manualmente:
curl -X POST http://localhost:8000/api/devices/dhcp/apply
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
- `apply` (bool, opcional): Aplica as mudanças imediatamente (padrão: **true**)

### **Processo**
1. ✅ Exclui do **pfSense**
2. ✅ Remove do **banco de dados local**
3. ✅ **Apply automático** por padrão (pode ser desabilitado com `apply=false`)

### **Exemplos**

#### **Com apply automático (padrão)**
```bash
curl -X DELETE "http://localhost:8000/api/devices/dhcp/static_mapping?mapping_id=5"
# As mudanças são aplicadas automaticamente!
```

#### **Sem apply automático (usar apply=false)**
```bash
curl -X DELETE "http://localhost:8000/api/devices/dhcp/static_mapping?mapping_id=5&apply=false"

# Depois, aplicar manualmente:
curl -X POST http://localhost:8000/api/devices/dhcp/apply
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
- **Raramente necessário** - todas as operações (CREATE, UPDATE, DELETE) aplicam automaticamente
- Pode ser útil se houver algum problema e você precisar forçar a aplicação manual
- Útil para verificar/aplicar mudanças pendentes feitas diretamente no pfSense

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
| **CREATE** | `POST /dhcp/static_mapping` | ✅ **Sim (automático)** | ❌ Não disponível | ❌ Não |
| **UPDATE** | `PATCH /dhcp/static_mapping` | ✅ **Sim (padrão)** | ✅ Sim (usar `apply=false` para desativar) | ❌ Não |
| **DELETE** | `DELETE /dhcp/static_mapping` | ✅ **Sim (padrão)** | ✅ Sim (usar `apply=false` para desativar) | ❌ Não |
| **APPLY** | `POST /dhcp/apply` | ✅ Aplica tudo | N/A | ❌ Não (só usar se necessário) |

---

## 💡 Boas Práticas

### **1. Operações Individuais (Apply Automático)**
```bash
# Criar dispositivo (apply automático)
curl -X POST .../dhcp/static_mapping -d '{...}'
# Mudanças já aplicadas automaticamente! ✅

# Atualizar dispositivo (apply automático)
curl -X PATCH ".../dhcp/static_mapping?mapping_id=5" -d '{...}'
# Mudanças já aplicadas automaticamente! ✅

# Excluir dispositivo (apply automático)
curl -X DELETE ".../dhcp/static_mapping?mapping_id=5"
# Mudanças já aplicadas automaticamente! ✅
```

### **2. Operações em Lote (Batch)**
```bash
# Criar múltiplos dispositivos (cada um aplica automaticamente)
curl -X POST .../dhcp/static_mapping -d '{device1}'  # Apply automático
curl -X POST .../dhcp/static_mapping -d '{device2}'  # Apply automático
curl -X POST .../dhcp/static_mapping -d '{device3}'  # Apply automático

# Não é mais necessário chamar /dhcp/apply manualmente!
# Mas ainda pode ser usado se preferir aplicar manualmente
```

### **3. Edição/Exclusão com Apply Automático (Padrão)**
```bash
# Atualizar (apply automático por padrão)
curl -X PATCH ".../dhcp/static_mapping?mapping_id=5" -d '{...}'

# Excluir (apply automático por padrão)
curl -X DELETE ".../dhcp/static_mapping?mapping_id=5"
```

### **4. Edição/Exclusão SEM Apply Automático**
```bash
# Atualizar sem aplicar (usar apply=false)
curl -X PATCH ".../dhcp/static_mapping?mapping_id=5&apply=false" -d '{...}'

# Excluir sem aplicar (usar apply=false)
curl -X DELETE ".../dhcp/static_mapping?mapping_id=5&apply=false"

# Depois aplicar manualmente todas as mudanças
curl -X POST .../dhcp/apply
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
2. **Apply Automático**: **TODAS** as operações (CREATE, UPDATE, DELETE) aplicam as mudanças automaticamente
3. **Apply em UPDATE/DELETE**: Use `apply=false` para desativar o apply automático se necessário
4. **ID do pfSense**: O campo `pf_id` armazena o ID do mapeamento no pfSense para referência
5. **Parent ID**: Por padrão é "lan", mas pode ser alterado para outras interfaces (wan, opt1, etc.)
6. **Apply Assíncrono**: O apply pode levar alguns segundos, aguarde a resposta completa
7. **Timeout**: O timeout para apply é de 30 segundos
8. **Erro no Apply**: Se o apply falhar, a operação continua (cadastro/atualização/exclusão é feita), apenas o apply é logado como erro

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

# 2. Mudanças já aplicadas automaticamente no passo 1! ✅

# 3. Atualizar descrição (apply automático por padrão)
curl -X PATCH "http://localhost:8000/api/devices/dhcp/static_mapping?mapping_id=10" \
  -H "Content-Type: application/json" \
  -d '{
    "descr": "Sensor de temperatura - Sala 2 (relocado)"
  }'

# 4. Excluir dispositivo (apply automático por padrão)
curl -X DELETE "http://localhost:8000/api/devices/dhcp/static_mapping?mapping_id=10"
```

---

**Última atualização:** 08/10/2025  
**Versão:** 2.0

