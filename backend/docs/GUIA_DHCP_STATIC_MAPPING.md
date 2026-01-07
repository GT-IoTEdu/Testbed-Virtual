# 🚀 **Guia Completo - Cadastro de Mapeamentos Estáticos DHCP**

Este guia explica como usar os novos endpoints para cadastrar mapeamentos estáticos DHCP no pfSense com proteção contra duplicatas.

## 📋 **Endpoints Disponíveis**

### 1. **Salvar Dados DHCP no Banco**
- **Endpoint**: `POST /api/devices/dhcp/save`
- **Descrição**: Busca dados do pfSense e salva no banco de dados
- **Exemplo de dados salvos**:
```json
{
  "parent_id": "lan",
  "id": 1,
  "mac": "bc:24:11:2c:0f:31",
  "ipaddr": "10.30.30.10",
  "cid": "lubuntu-live",
  "hostname": "lubuntu-live",
  "descr": "lubuntu-live-proxmox"
}
```

### 2. **Verificar Mapeamentos Existentes**
- **Endpoint**: `GET /api/devices/dhcp/static_mapping/check`
- **Descrição**: Verifica se já existem mapeamentos com o mesmo IP ou MAC
- **Proteção**: Evita conflitos antes do cadastro

### 3. **Cadastrar Mapeamento Estático DHCP**
- **Endpoint**: `POST /api/devices/dhcp/static_mapping`
- **Descrição**: Cadastra novo mapeamento estático DHCP no pfSense
- **Proteção**: Verificação automática de duplicatas

## 💾 **Salvamento de Dados DHCP**

### **Endpoint: POST /api/devices/dhcp/save**

Este endpoint salva dados DHCP no banco de dados com parâmetros fornecidos pelo usuário.

```bash
curl -X POST http://127.0.0.1:8000/api/devices/dhcp/save \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "bc:24:11:2c:0f:31",
    "ipaddr": "10.30.30.10",
    "cid": "lubuntu-live",
    "descr": "lubuntu-live-proxmox"
  }'
```

**Parâmetros obrigatórios:**
- `mac`: Endereço MAC do dispositivo
- `ipaddr`: Endereço IP do dispositivo
- `cid`: ID do cliente (será replicado para hostname)
- `descr`: Descrição do dispositivo

**Resposta de Sucesso:**
```json
{
  "status": "success",
  "servers_saved": 1,
  "mappings_saved": 1,
  "mappings_updated": 0,
  "timestamp": "2025-01-09T15:30:45"
}
```

**Exemplo de dados salvos:**
```json
{
  "parent_id": "lan",
  "id": 1,
  "mac": "bc:24:11:2c:0f:31",
  "ipaddr": "10.30.30.10",
  "cid": "lubuntu-live",
  "hostname": "lubuntu-live",
  "descr": "lubuntu-live-proxmox"
}
```

## 🔍 **Verificação de Mapeamentos Existentes**

### **Exemplo 1: Verificar por IP**
```bash
curl "http://127.0.0.1:8000/api/devices/dhcp/static_mapping/check?ipaddr=192.168.1.100"
```

**Resposta de Sucesso (IP não existe):**
```json
{
  "parent_id": "lan",
  "ipaddr_checked": "192.168.1.100",
  "mac_checked": null,
  "exists": false,
  "total_found": 0,
  "mappings": [],
  "message": "Verificação concluída com sucesso"
}
```

**Resposta de Conflito (IP já existe):**
```json
{
  "parent_id": "lan",
  "ipaddr_checked": "10.30.30.3",
  "mac_checked": null,
  "exists": true,
  "total_found": 1,
  "mappings": [
    {
      "type": "ip",
      "mapping": {
        "parent_id": "lan",
        "id": 0,
        "mac": "bc:24:11:68:fb:77",
        "ipaddr": "10.30.30.3",
        "cid": "openvas",
        "hostname": "openvas",
        "descr": "openvas"
      },
      "server_id": "lan"
    }
  ],
  "message": "Verificação concluída com sucesso"
}
```

### **Exemplo 2: Verificar por MAC**
```bash
curl "http://127.0.0.1:8000/api/devices/dhcp/static_mapping/check?mac=bc:24:11:68:fb:77"
```

### **Exemplo 3: Verificar por IP e MAC**
```bash
curl "http://127.0.0.1:8000/api/devices/dhcp/static_mapping/check?ipaddr=192.168.1.100&mac=00:11:22:33:44:55"
```

## 📝 **Cadastro de Mapeamentos DHCP**

### **Campos Obrigatórios**
- `parent_id`: ID do servidor DHCP pai (ex: "lan", "wan", "opt1")
- `mac`: Endereço MAC do dispositivo
- `ipaddr`: Endereço IP do dispositivo
- `cid`: ID do cliente

### **Campos Opcionais**
- `hostname`: Nome do host
- `domain`: Domínio
- `domainsearchlist`: Lista de domínios para busca
- `defaultleasetime`: Tempo de lease padrão (padrão: 7200 segundos)
- `maxleasetime`: Tempo máximo de lease (padrão: 86400 segundos)
- `gateway`: Gateway
- `dnsserver`: Lista de servidores DNS
- `winsserver`: Lista de servidores WINS
- `ntpserver`: Lista de servidores NTP
- `arp_table_static_entry`: Entrada estática na tabela ARP (padrão: true)
- `descr`: Descrição do dispositivo

### **Exemplo 1: Cadastro Mínimo**
```bash
curl -X POST http://127.0.0.1:8000/api/devices/dhcp/static_mapping \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "00:11:22:33:44:55",
    "ipaddr": "192.168.1.100",
    "cid": "device001"
  }'
```

**Resposta de Sucesso:**
```json
{
  "success": true,
  "message": "Mapeamento estático DHCP cadastrado com sucesso no pfSense",
  "data": {
    "status": "ok",
    "result": {
      "code": 200,
      "status": "ok",
      "response_id": "SUCCESS",
      "message": "Static mapping created successfully"
    }
  }
}
```

### **Exemplo 2: Cadastro Completo**
```bash
curl -X POST http://127.0.0.1:8000/api/devices/dhcp/static_mapping \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "AA:BB:CC:DD:EE:FF",
    "ipaddr": "192.168.1.101",
    "cid": "iot_sensor_001",
    "hostname": "sensor-temperatura",
    "domain": "iot.local",
    "domainsearchlist": ["iot.local", "lab.local"],
    "defaultleasetime": 7200,
    "maxleasetime": 86400,
    "gateway": "192.168.1.1",
    "dnsserver": ["8.8.8.8", "8.8.4.4"],
    "winsserver": [],
    "ntpserver": ["pool.ntp.org"],
    "arp_table_static_entry": true,
    "descr": "Sensor de temperatura IoT - Laboratório A"
  }'
```

## ⚠️ **Proteção Contra Duplicatas**

### **Cenário: Tentativa de Cadastro Duplicado**
```bash
curl -X POST http://127.0.0.1:8000/api/devices/dhcp/static_mapping \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "bc:24:11:68:fb:77",
    "ipaddr": "10.30.30.3",
    "cid": "test_duplicate"
  }'
```

**Resposta de Erro (Status 409):**
```json
{
  "detail": "Já existem mapeamentos DHCP com os mesmos dados:\n- IP 10.30.30.3 já está em uso pelo dispositivo openvas (MAC: bc:24:11:68:fb:77)\n- MAC bc:24:11:68:fb:77 já está em uso pelo dispositivo openvas (IP: 10.30.30.3)"
}
```

## 🧪 **Testando com Postman**

### **1. Verificar Mapeamentos Existentes**
```
GET {{api_base}}/dhcp/static_mapping/check?parent_id=lan&ipaddr=192.168.1.100
```

### **2. Cadastrar Novo Mapeamento**
```
POST {{api_base}}/dhcp/static_mapping
Content-Type: application/json

{
  "parent_id": "lan",
  "mac": "00:11:22:33:44:55",
  "ipaddr": "192.168.1.100",
  "cid": "test_device",
  "hostname": "test-hostname",
  "descr": "Dispositivo de teste"
}
```

## 🔧 **Fluxo Recomendado**

### **1. Salvar Dados DHCP (Primeiro Passo)**
```bash
# 1. Salvar dados DHCP no banco com parâmetros do usuário
curl -X POST http://127.0.0.1:8000/api/devices/dhcp/save \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "bc:24:11:2c:0f:31",
    "ipaddr": "10.30.30.10",
    "cid": "lubuntu-live",
    "descr": "lubuntu-live-proxmox"
  }'
```

### **2. Verificação Prévia (Recomendado)**
```bash
# 2. Verificar se o IP já está em uso
curl "http://127.0.0.1:8000/api/devices/dhcp/static_mapping/check?ipaddr=192.168.1.100"

# 3. Verificar se o MAC já está em uso
curl "http://127.0.0.1:8000/api/devices/dhcp/static_mapping/check?mac=00:11:22:33:44:55"
```

### **3. Cadastro Seguro**
```bash
# 4. Se não houver conflitos, cadastrar o mapeamento
curl -X POST http://127.0.0.1:8000/api/devices/dhcp/static_mapping \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "00:11:22:33:44:55",
    "ipaddr": "192.168.1.100",
    "cid": "device001",
    "descr": "Dispositivo IoT"
  }'
```

## 🚨 **Códigos de Status HTTP**

- **200**: Sucesso na verificação ou cadastro
- **400**: Parâmetros inválidos (verificação)
- **409**: Conflito - mapeamento já existe
- **422**: Dados inválidos (validação Pydantic)
- **500**: Erro interno do servidor

## 📊 **Exemplos de Uso Real**

### **Cenário 1: Sensor IoT**
```bash
curl -X POST http://127.0.0.1:8000/api/devices/dhcp/static_mapping \
  -H "Content-Type: application/json" \
  -d '{
    "parent_id": "lan",
    "mac": "DE:AD:BE:EF:CA:FE",
    "ipaddr": "192.168.1.50",
    "cid": "sensor_umidade_01",
    "hostname": "sensor-umidade-lab1",
    "descr": "Sensor de umidade - Laboratório 1"
  }'
```

### **Cenário 2: Câmera IP**
```bash
curl -X POST http://127.0.0.1:8000/api/devices/dhcp/static_mapping \
  -H "Content-Type: application/json" \
  -d '{
    "parent_id": "lan",
    "mac": "CA:FE:BA:BE:DE:AD",
    "ipaddr": "192.168.1.100",
    "cid": "camera_seguranca_01",
    "hostname": "camera-entrada",
    "gateway": "192.168.1.1",
    "dnsserver": ["8.8.8.8"],
    "descr": "Câmera de segurança - Entrada principal"
  }'
```

## 🔍 **Troubleshooting**

### **Problema: Erro 409 (Conflito)**
**Solução**: Verifique os mapeamentos existentes e escolha um IP/MAC diferente.

### **Problema: Erro 422 (Validação)**
**Solução**: Verifique se todos os campos obrigatórios estão preenchidos corretamente.

### **Problema: Erro 500 (Servidor)**
**Solução**: Verifique a conectividade com o pfSense e as credenciais da API.

## 📚 **Recursos Adicionais**

- [Documentação pfSense API v2](https://docs.netgate.com/pfsense/en/latest/development/api.html)
- [Guia de Configuração DHCP](README-pfsense-api-v2.md)
- [Testes Automatizados](test_dhcp_static_mapping.py)

---

**🎯 Dica**: Sempre use a verificação prévia para evitar conflitos e garantir um cadastro seguro!
