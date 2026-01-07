# 🚀 **Guia Completo - Testando DHCP Static Mapping no Postman**

Este guia explica como testar os endpoints de mapeamento estático DHCP no pfSense usando o Postman, com o `parent_id` padrão "lan".

## 📋 **Pré-requisitos**

1. **Postman instalado** (versão gratuita ou paga)
2. **Servidor IoT-EDU rodando** em `http://127.0.0.1:8000`
3. **Coleção do Postman** importada (arquivo: `IoT-EDU_DHCP_Static_Mapping.postman_collection.json`)

## 🔧 **Configuração Inicial**

### **1. Importar a Coleção**

1. Abra o Postman
2. Clique em **"Import"** (canto superior esquerdo)
3. Selecione o arquivo `IoT-EDU_DHCP_Static_Mapping.postman_collection.json`
4. Clique em **"Import"**

### **2. Configurar Variáveis**

1. Na coleção importada, clique no ícone de **engrenagem** (⚙️)
2. Na aba **"Variables"**, configure:
   - **Variable**: `api_base`
   - **Initial Value**: `http://127.0.0.1:8000/api/devices`
   - **Current Value**: `http://127.0.0.1:8000/api/devices`
3. Clique em **"Save"**

## 🧪 **Testes Passo a Passo**

### **Etapa 1: Verificar Mapeamentos Existentes**

#### **1.1 Verificar por IP**
```
GET {{api_base}}/dhcp/static_mapping/check?ipaddr=192.168.1.100
```

**Passos:**
1. Abra a pasta **"1. Verificar Mapeamentos Existentes"**
2. Clique em **"Verificar por IP"**
3. Clique em **"Send"**

**Resposta Esperada (IP não existe):**
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

#### **1.2 Verificar por MAC**
```
GET {{api_base}}/dhcp/static_mapping/check?mac=00:11:22:33:44:55
```

**Passos:**
1. Clique em **"Verificar por MAC"**
2. Clique em **"Send"**

#### **1.3 Verificar por IP e MAC**
```
GET {{api_base}}/dhcp/static_mapping/check?ipaddr=192.168.1.100&mac=00:11:22:33:44:55
```

**Passos:**
1. Clique em **"Verificar por IP e MAC"**
2. Clique em **"Send"**

#### **1.4 Testar Erro (sem parâmetros)**
```
GET {{api_base}}/dhcp/static_mapping/check
```

**Passos:**
1. Clique em **"Verificar sem parâmetros (erro)"**
2. Clique em **"Send"**

**Resposta Esperada (Status 400):**
```json
{
  "detail": "É necessário fornecer pelo menos um endereço IP ou MAC para verificar"
}
```

### **Etapa 2: Cadastrar Mapeamentos DHCP**

#### **2.1 Cadastro Mínimo**
```
POST {{api_base}}/dhcp/static_mapping
Content-Type: application/json

{
  "mac": "00:11:22:33:44:55",
  "ipaddr": "192.168.1.100",
  "cid": "device001"
}
```

**Passos:**
1. Abra a pasta **"2. Cadastrar Mapeamentos DHCP"**
2. Clique em **"Cadastro Mínimo"**
3. Verifique se o **Body** está configurado como **"raw"** e **"JSON"**
4. Clique em **"Send"**

**Resposta Esperada (Status 200):**
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

#### **2.2 Cadastro Completo**
```
POST {{api_base}}/dhcp/static_mapping
Content-Type: application/json

{
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
}
```

**Passos:**
1. Clique em **"Cadastro Completo"**
2. Clique em **"Send"**

#### **2.3 Cadastro com parent_id Explícito**
```
POST {{api_base}}/dhcp/static_mapping
Content-Type: application/json

{
  "parent_id": "lan",
  "mac": "DE:AD:BE:EF:CA:FE",
  "ipaddr": "192.168.1.102",
  "cid": "test_explicit_parent",
  "hostname": "test-device",
  "descr": "Dispositivo de teste com parent_id explícito"
}
```

**Passos:**
1. Clique em **"Cadastro com parent_id explícito"**
2. Clique em **"Send"**

#### **2.4 Testar Proteção Contra Duplicatas**
```
POST {{api_base}}/dhcp/static_mapping
Content-Type: application/json

{
  "mac": "bc:24:11:68:fb:77",
  "ipaddr": "10.30.30.3",
  "cid": "test_duplicate"
}
```

**Passos:**
1. Clique em **"Cadastro Duplicado (erro)"**
2. Clique em **"Send"**

**Resposta Esperada (Status 409):**
```json
{
  "detail": "Já existem mapeamentos DHCP com os mesmos dados:\n- IP 10.30.30.3 já está em uso pelo dispositivo openvas (MAC: bc:24:11:68:fb:77)\n- MAC bc:24:11:68:fb:77 já está em uso pelo dispositivo openvas (IP: 10.30.30.3)"
}
```

#### **2.5 Testar Validação de Dados**
```
POST {{api_base}}/dhcp/static_mapping
Content-Type: application/json

{
  "mac": "invalid-mac-address",
  "ipaddr": "invalid-ip-address"
}
```

**Passos:**
1. Clique em **"Cadastro com Dados Inválidos (erro)"**
2. Clique em **"Send"**

**Resposta Esperada (Status 422):**
```json
{
  "detail": [
    {
      "loc": ["body", "mac"],
      "msg": "string does not match pattern",
      "type": "value_error.pattern"
    },
    {
      "loc": ["body", "ipaddr"],
      "msg": "string does not match pattern",
      "type": "value_error.pattern"
    },
    {
      "loc": ["body", "cid"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### **Etapa 3: Exemplos de Uso Real**

#### **3.1 Cadastrar Sensor IoT**
```
POST {{api_base}}/dhcp/static_mapping
Content-Type: application/json

{
  "mac": "DE:AD:BE:EF:CA:FE",
  "ipaddr": "192.168.1.50",
  "cid": "sensor_umidade_01",
  "hostname": "sensor-umidade-lab1",
  "descr": "Sensor de umidade - Laboratório 1"
}
```

#### **3.2 Cadastrar Câmera IP**
```
POST {{api_base}}/dhcp/static_mapping
Content-Type: application/json

{
  "mac": "CA:FE:BA:BE:DE:AD",
  "ipaddr": "192.168.1.100",
  "cid": "camera_seguranca_01",
  "hostname": "camera-entrada",
  "gateway": "192.168.1.1",
  "dnsserver": ["8.8.8.8"],
  "descr": "Câmera de segurança - Entrada principal"
}
```

#### **3.3 Cadastrar Controlador de Automação**
```
POST {{api_base}}/dhcp/static_mapping
Content-Type: application/json

{
  "mac": "FE:ED:CA:FE:BA:BE",
  "ipaddr": "192.168.1.200",
  "cid": "controlador_automacao",
  "hostname": "controlador-lab2",
  "domain": "iot.local",
  "gateway": "192.168.1.1",
  "dnsserver": ["8.8.8.8", "1.1.1.1"],
  "ntpserver": ["pool.ntp.org"],
  "descr": "Controlador de automação - Laboratório 2"
}
```

## 🔄 **Fluxo de Teste Recomendado**

### **Sequência de Testes:**

1. **Verificar mapeamentos existentes** (Etapa 1)
2. **Cadastrar mapeamento mínimo** (Etapa 2.1)
3. **Verificar se foi cadastrado** (Etapa 1.1 com o IP usado)
4. **Cadastrar mapeamento completo** (Etapa 2.2)
5. **Testar proteção contra duplicatas** (Etapa 2.4)
6. **Testar validação de dados** (Etapa 2.5)
7. **Cadastrar exemplos reais** (Etapa 3)

## 📊 **Códigos de Status HTTP**

| Status | Significado | Quando Ocorre |
|--------|-------------|---------------|
| **200** | Sucesso | Verificação ou cadastro realizado com sucesso |
| **400** | Bad Request | Parâmetros inválidos na verificação |
| **409** | Conflict | Mapeamento já existe (proteção contra duplicatas) |
| **422** | Unprocessable Entity | Dados inválidos (validação Pydantic) |
| **500** | Internal Server Error | Erro interno do servidor |

## 🚨 **Troubleshooting**

### **Problema: Erro de Conexão**
**Solução:** Verifique se o servidor está rodando em `http://127.0.0.1:8000`

### **Problema: Erro 500**
**Solução:** Verifique os logs do servidor e a conectividade com o pfSense

### **Problema: Erro 409 (Conflito)**
**Solução:** Use um IP ou MAC diferente, ou verifique os mapeamentos existentes

### **Problema: Erro 422 (Validação)**
**Solução:** Verifique se todos os campos obrigatórios estão preenchidos corretamente

## 🎯 **Dicas Importantes**

1. **Sempre verifique antes de cadastrar** para evitar conflitos
2. **Use IPs únicos** para cada dispositivo
3. **Use MACs únicos** para cada dispositivo
4. **O campo `parent_id` é opcional** e tem valor padrão "lan"
5. **Teste com dados reais** antes de usar em produção

## 📚 **Recursos Adicionais**

- [Documentação pfSense API v2](https://docs.netgate.com/pfsense/en/latest/development/api.html)
- [Guia de Configuração DHCP](README-pfsense-api-v2.md)
- [Testes Automatizados](test_dhcp_static_mapping.py)

---

**🎯 Dica**: Use a coleção do Postman para testes rápidos e consistentes!
