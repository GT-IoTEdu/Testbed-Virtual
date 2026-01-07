# 🚀 **Guia Postman - Teste do Endpoint DHCP Save**

Este guia explica como testar o endpoint `/dhcp/save` usando o Postman, incluindo o exemplo específico que você forneceu.

## 📋 **Pré-requisitos**

1. **Postman instalado** no seu computador
2. **Servidor FastAPI rodando** em `http://127.0.0.1:8000`
3. **Conexão com pfSense** configurada no arquivo `.env`

## 📥 **Importar a Coleção**

### **1. Baixar a Coleção**
- Baixe o arquivo `IoT-EDU_DHCP_Save.postman_collection.json`
- Ou copie o conteúdo JSON da coleção

### **2. Importar no Postman**
1. Abra o Postman
2. Clique em **"Import"** (canto superior esquerdo)
3. Arraste o arquivo `IoT-EDU_DHCP_Save.postman_collection.json` ou cole o JSON
4. Clique em **"Import"**

## ⚙️ **Configurar Variáveis**

### **1. Verificar Variável `api_base`**
1. Na coleção importada, clique no ícone de **engrenagem** (⚙️)
2. Verifique se a variável `api_base` está configurada como:
   ```
   http://127.0.0.1:8000/api/devices
   ```

### **2. Se necessário, alterar a URL base**
- Se seu servidor estiver rodando em outra porta ou host, altere a variável `api_base`

## 🧪 **Executar os Testes**

### **Teste 1: Salvar Dados DHCP no Banco**

**Endpoint:** `POST {{api_base}}/dhcp/save`

**Body da Requisição:**
```json
{
  "mac": "bc:24:11:2c:0f:31",
  "ipaddr": "10.30.30.10",
  "cid": "lubuntu-live",
  "descr": "lubuntu-live-proxmox"
}
```

**Parâmetros obrigatórios:**
- `mac`: Endereço MAC do dispositivo
- `ipaddr`: Endereço IP do dispositivo
- `cid`: ID do cliente (será replicado para hostname)
- `descr`: Descrição do dispositivo

**Passos:**
1. Abra a requisição **"1. Salvar Dados DHCP no Banco"**
2. Verifique se o body está preenchido com os dados corretos
3. Clique em **"Send"**
4. **Aguarde a resposta** (pode demorar alguns segundos)

**Resposta Esperada (Sucesso):**
```json
{
  "status": "success",
  "servers_saved": 1,
  "mappings_saved": 1,
  "mappings_updated": 0,
  "timestamp": "2025-01-09T15:30:45"
}
```

**Exemplo de dados que serão salvos:**
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

### **Teste 2: Verificar Dados Salvos**

**Endpoint:** `GET {{api_base}}/dhcp/devices?page=1&per_page=10`

**Passos:**
1. Abra a requisição **"2. Verificar Dados Salvos - Listar Dispositivos"**
2. Clique em **"Send"**

**Resposta Esperada:**
```json
{
  "devices": [
    {
      "id": 1,
      "server_id": "lan",
      "pf_id": 1,
      "mac": "bc:24:11:2c:0f:31",
      "ipaddr": "10.30.30.10",
      "cid": "lubuntu-live",
      "hostname": "lubuntu-live",
      "descr": "lubuntu-live-proxmox",
      "created_at": "2025-01-09T15:30:45",
      "updated_at": "2025-01-09T15:30:45"
    }
  ],
  "total": 6,
  "page": 1,
  "per_page": 10,
  "pages": 1
}
```

### **Teste 3: Buscar Dispositivo por IP**

**Endpoint:** `GET {{api_base}}/dhcp/devices/ip/10.30.30.10`

**Passos:**
1. Abra a requisição **"3. Buscar Dispositivo Específico por IP"**
2. Clique em **"Send"**

**Resposta Esperada:**
```json
{
  "device": {
    "id": 1,
    "server_id": "lan",
    "pf_id": 1,
    "mac": "bc:24:11:2c:0f:31",
    "ipaddr": "10.30.30.10",
    "cid": "lubuntu-live",
    "hostname": "lubuntu-live",
    "descr": "lubuntu-live-proxmox",
    "created_at": "2025-01-09T15:30:45",
    "updated_at": "2025-01-09T15:30:45"
  }
}
```

### **Teste 4: Buscar Dispositivo por MAC**

**Endpoint:** `GET {{api_base}}/dhcp/devices/mac/bc:24:11:2c:0f:31`

**Passos:**
1. Abra a requisição **"4. Buscar Dispositivo Específico por MAC"**
2. Clique em **"Send"**

**Resposta Esperada:**
```json
{
  "device": {
    "id": 1,
    "server_id": "lan",
    "pf_id": 1,
    "mac": "bc:24:11:2c:0f:31",
    "ipaddr": "10.30.30.10",
    "cid": "lubuntu-live",
    "hostname": "lubuntu-live",
    "descr": "lubuntu-live-proxmox",
    "created_at": "2025-01-09T15:30:45",
    "updated_at": "2025-01-09T15:30:45"
  }
}
```

### **Teste 5: Ver Estatísticas**

**Endpoint:** `GET {{api_base}}/dhcp/statistics`

**Passos:**
1. Abra a requisição **"5. Ver Estatísticas dos Dispositivos"**
2. Clique em **"Send"**

**Resposta Esperada:**
```json
{
  "total_devices": 6,
  "total_servers": 2,
  "devices_by_server": {
    "lan": 6,
    "wan": 0
  },
  "recent_activity": {
    "last_24h": 6,
    "last_week": 6
  }
}
```

### **Teste 6: Buscar por Termo**

**Endpoint:** `GET {{api_base}}/dhcp/devices/search?query=lubuntu`

**Passos:**
1. Abra a requisição **"6. Buscar Dispositivos por Termo"**
2. Clique em **"Send"**

**Resposta Esperada:**
```json
{
  "devices": [
    {
      "id": 1,
      "server_id": "lan",
      "pf_id": 1,
      "mac": "bc:24:11:2c:0f:31",
      "ipaddr": "10.30.30.10",
      "cid": "lubuntu-live",
      "hostname": "lubuntu-live",
      "descr": "lubuntu-live-proxmox",
      "created_at": "2025-01-09T15:30:45",
      "updated_at": "2025-01-09T15:30:45"
    }
  ],
  "total": 1,
  "query": "lubuntu"
}
```

## 🔄 **Fluxo de Teste Recomendado**

### **Sequência de Execução:**

1. **Execute o Teste 1** primeiro (Salvar Dados DHCP)
2. **Aguarde a resposta de sucesso**
3. **Execute o Teste 2** para verificar se os dados foram salvos
4. **Execute os Testes 3 e 4** para buscar o dispositivo específico
5. **Execute o Teste 5** para ver estatísticas
6. **Execute o Teste 6** para buscar por termo

## 🚨 **Códigos de Status HTTP**

- **200**: Sucesso - dados salvos/consultados com sucesso
- **500**: Erro interno - verifique logs do servidor
- **503**: Serviço indisponível - verifique conexão com pfSense

## 🔍 **Troubleshooting**

### **Problema: Erro 500 no salvamento**
**Possíveis causas:**
- Conexão com pfSense falhou
- Credenciais incorretas no `.env`
- Banco de dados não está acessível

**Soluções:**
1. Verifique se o pfSense está acessível
2. Confirme as credenciais no arquivo `.env`
3. Teste a conexão com o banco de dados

### **Problema: Nenhum dispositivo encontrado**
**Possíveis causas:**
- O salvamento não foi executado
- Não há dados DHCP no pfSense
- Erro na consulta ao banco

**Soluções:**
1. Execute primeiro o Teste 1 (Salvar Dados DHCP)
2. Verifique se há dados DHCP no pfSense
3. Confirme se o banco de dados está funcionando

### **Problema: Dispositivo específico não encontrado**
**Possíveis causas:**
- O dispositivo não foi salvo corretamente
- IP ou MAC incorretos na busca

**Soluções:**
1. Execute o Teste 2 para listar todos os dispositivos
2. Verifique o IP e MAC correto do dispositivo
3. Confirme se o salvamento foi bem-sucedido

## 📊 **Exemplo de Teste Completo**

### **Cenário: Testar Salvamento e Consulta**

1. **Salvar dados DHCP:**
   ```
   POST http://127.0.0.1:8000/api/devices/dhcp/save
   ```

2. **Verificar salvamento:**
   ```
   GET http://127.0.0.1:8000/api/devices/dhcp/devices?page=1&per_page=10
   ```

3. **Buscar dispositivo específico:**
   ```
   GET http://127.0.0.1:8000/api/devices/dhcp/devices/ip/10.30.30.10
   GET http://127.0.0.1:8000/api/devices/dhcp/devices/mac/bc:24:11:2c:0f:31
   ```

4. **Verificar estatísticas:**
   ```
   GET http://127.0.0.1:8000/api/devices/dhcp/statistics
   ```

## 🎯 **Dicas Importantes**

1. **Execute sempre o salvamento primeiro** antes de testar consultas
2. **Verifique a conectividade** com pfSense antes de testar
3. **Confirme as credenciais** no arquivo `.env`
4. **Monitore os logs** do servidor para identificar erros
5. **Use a paginação** para listar muitos dispositivos

## 📚 **Recursos Adicionais**

- [Guia Completo DHCP](GUIA_DHCP_STATIC_MAPPING.md)
- [Documentação FastAPI](https://fastapi.tiangolo.com/)
- [Coleção Postman DHCP Static Mapping](IoT-EDU_DHCP_Static_Mapping.postman_collection.json)

---

**🎯 Dica**: Use este guia para testar sistematicamente o endpoint `/dhcp/save` e verificar se os dados estão sendo salvos corretamente no banco de dados!
