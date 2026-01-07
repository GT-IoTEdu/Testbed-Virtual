# 📚 Documentação Completa dos Endpoints - Coleções Postman

## 📋 Visão Geral

Esta documentação descreve todos os endpoints implementados e testados através das coleções Postman:

- **IoT-EDU ALIAS CRUD.postman_collection.json** - Gerenciamento de Aliases
- **IoT-EDU DHCP CRUD.postman_collection.json** - Gerenciamento DHCP
- **IoT-EDU Permission Tests.postman_collection.json** - Sistema de Permissões

---

## 🔗 **1. ENDPOINTS DE ALIASES (pfSense)**

### **1.1 Salvar Aliases do pfSense**
- **Método:** `POST`
- **URL:** `{{api_base}}/aliases-db/save`
- **Descrição:** Sincroniza todos os aliases do pfSense com o banco de dados local
- **Body:** Não requer body
- **Resposta:** Estatísticas da sincronização

### **1.2 Listar Aliases**
- **Método:** `GET`
- **URL:** `{{api_base}}/aliases-db`
- **Descrição:** Lista todos os aliases armazenados no banco de dados local
- **Parâmetros Query:**
  - `page` (int): Número da página (padrão: 1)
  - `per_page` (int): Itens por página (padrão: 20, máximo: 100)
  - `name` (str, opcional): Filtrar por nome do alias

### **1.3 Buscar Aliases**
- **Método:** `GET`
- **URL:** `{{api_base}}/aliases-db/search`
- **Descrição:** Busca aliases por nome ou descrição
- **Parâmetros Query:**
  - `query` (str): Termo de busca

### **1.4 Estatísticas de Aliases**
- **Método:** `GET`
- **URL:** `{{api_base}}/aliases-db/statistics`
- **Descrição:** Obtém estatísticas sobre os aliases no banco de dados

### **1.5 Criar Novo Alias**
- **Método:** `POST`
- **URL:** `{{api_base}}/aliases-db/create`
- **Descrição:** Cria um novo alias no pfSense e salva no banco de dados local
- **Body (JSON):**
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

### **1.6 Atualizar Alias**
- **Método:** `PATCH`
- **URL:** `{{api_base}}/aliases-db/{alias_name}`
- **Descrição:** Atualiza um alias existente no banco de dados e no pfSense
- **Body (JSON):** Campos opcionais
```json
{
  "descr": "Nova descrição do alias",
  "addresses": [
    {
      "address": "192.168.1.200",
      "detail": "Dispositivo atualizado"
    }
  ]
}
```

### **1.7 Adicionar IPs a Alias Existente**
- **Método:** `POST`
- **URL:** `{{api_base}}/aliases-db/{alias_name}/add-addresses`
- **Descrição:** Adiciona novos endereços IP a um alias existente sem substituir os atuais
- **Body (JSON):**
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
    }
  ]
}
```

---

## 🌐 **2. ENDPOINTS DHCP**

### **2.1 Salvar Dados DHCP no Banco**
- **Método:** `POST`
- **URL:** `{{api_base}}/dhcp/save`
- **Descrição:** Salva dados DHCP no banco de dados com parâmetros fornecidos pelo usuário
- **Body (JSON):**
```json
{
  "mac": "d8:e0:e1:02:c1:a6",
  "ipaddr": "10.30.30.7",
  "cid": "WEBCAM",
  "descr": "Webcam externa"
}
```

### **2.2 Listar Dispositivos DHCP**
- **Método:** `GET`
- **URL:** `{{api_base}}/dhcp/devices`
- **Descrição:** Lista os dispositivos DHCP salvos no banco de dados
- **Parâmetros Query:**
  - `page` (int): Número da página (padrão: 1)
  - `per_page` (int): Itens por página (padrão: 20, máximo: 100)
  - `server_id` (str, opcional): Filtrar por servidor DHCP

### **2.3 Buscar Dispositivo por IP**
- **Método:** `GET`
- **URL:** `{{api_base}}/dhcp/devices/ip/{ipaddr}`
- **Descrição:** Busca dispositivo específico por endereço IP
- **Parâmetros Path:**
  - `ipaddr` (str): Endereço IP do dispositivo

### **2.4 Buscar Dispositivo por MAC**
- **Método:** `GET`
- **URL:** `{{api_base}}/dhcp/devices/mac/{mac}`
- **Descrição:** Busca dispositivo específico por endereço MAC
- **Parâmetros Path:**
  - `mac` (str): Endereço MAC do dispositivo

### **2.5 Estatísticas dos Dispositivos**
- **Método:** `GET`
- **URL:** `{{api_base}}/dhcp/statistics`
- **Descrição:** Mostra estatísticas dos dispositivos DHCP salvos no banco de dados

### **2.6 Buscar Dispositivos por Termo**
- **Método:** `GET`
- **URL:** `{{api_base}}/dhcp/devices/search`
- **Descrição:** Busca dispositivos que contenham o termo especificado
- **Parâmetros Query:**
  - `query` (str): Termo de busca (IP, MAC, descrição ou hostname)

### **2.7 Excluir Mapeamento DHCP**
- **Método:** `DELETE`
- **URL:** `{{api_base}}/dhcp/static_mapping`
- **Descrição:** Exclui mapeamento estático DHCP no pfSense e banco de dados local
- **Parâmetros Query:**
  - `parent_id` (str): ID do servidor DHCP pai (padrão: "lan")
  - `mapping_id` (int): ID do mapeamento a ser excluído
  - `apply` (bool): Aplicar imediatamente (padrão: false)

### **2.8 Sincronizar IDs pfSense com Banco Local**
- **Método:** `POST`
- **URL:** `{{api_base}}/dhcp/sync`
- **Descrição:** Sincroniza os IDs do pfSense com os pf_id do banco de dados local

### **2.9 Atualizar Dados DHCP**
- **Método:** `PATCH`
- **URL:** `{{api_base}}/dhcp/static_mapping`
- **Descrição:** Atualiza mapeamento estático DHCP no pfSense e banco de dados local
- **Parâmetros Query:**
  - `parent_id` (str): ID do servidor DHCP pai (padrão: "lan")
  - `mapping_id` (int): ID do mapeamento a ser atualizado
  - `apply` (bool): Aplicar imediatamente (padrão: false)
- **Body (JSON):** Campos opcionais
```json
{
  "descr": "Teste de atualização via IoT_API"
}
```

---

## 👥 **3. ENDPOINTS DE PERMISSÕES E ATRIBUIÇÕES**

### **3.1 Atribuir Dispositivo a Usuário**
- **Método:** `POST`
- **URL:** `{{api_base}}/assignments`
- **Descrição:** Atribui um dispositivo DHCP a um usuário
- **Body (JSON):**
```json
{
  "user_id": 1,
  "device_id": 8,
  "notes": "Dispositivo Notebook atribuído ao usuário comum",
  "assigned_by": 1
}
```

### **3.2 Listar Dispositivos de um Usuário**
- **Método:** `GET`
- **URL:** `{{api_base}}/users/{user_id}/devices`
- **Descrição:** Lista dispositivos atribuídos a um usuário
- **Parâmetros Path:**
  - `user_id` (int): ID do usuário
- **Parâmetros Query:**
  - `current_user_id` (int): ID do usuário que está fazendo a consulta
  - `include_inactive` (bool): Incluir atribuições inativas (padrão: false)

### **3.3 Listar Usuários de um Dispositivo**
- **Método:** `GET`
- **URL:** `{{api_base}}/devices/{device_id}/users`
- **Descrição:** Lista usuários atribuídos a um dispositivo
- **Parâmetros Path:**
  - `device_id` (int): ID do dispositivo
- **Parâmetros Query:**
  - `current_user_id` (int): ID do usuário que está fazendo a consulta
  - `include_inactive` (bool): Incluir atribuições inativas (padrão: false)

### **3.4 Remover Atribuição de Dispositivo**
- **Método:** `DELETE`
- **URL:** `{{api_base}}/assignments/{user_id}/{device_id}`
- **Descrição:** Remove atribuição de um dispositivo de um usuário
- **Parâmetros Path:**
  - `user_id` (int): ID do usuário que tem o dispositivo
  - `device_id` (int): ID do dispositivo
- **Parâmetros Query:**
  - `current_user_id` (int): ID do usuário que está fazendo a remoção

### **3.5 Buscar Atribuições por Termo**
- **Método:** `GET`
- **URL:** `{{api_base}}/assignments/search`
- **Descrição:** Busca atribuições por termo
- **Parâmetros Query:**
  - `query` (str): Termo de busca (nome, email, IP, MAC, descrição)

### **3.6 Estatísticas de Atribuições**
- **Método:** `GET`
- **URL:** `{{api_base}}/assignments/statistics`
- **Descrição:** Retorna estatísticas das atribuições usuário-dispositivo

---

## 🔐 **4. SISTEMA DE PERMISSÕES**

### **4.1 Regras de Negócio**

#### **Usuário Comum (USER):**
- ✅ Pode atribuir dispositivos apenas a si mesmo
- ✅ Pode visualizar apenas seus próprios dispositivos
- ✅ Pode ver usuários apenas de dispositivos que possui
- ✅ Pode remover apenas suas próprias atribuições
- ❌ Não pode atribuir dispositivos a outros usuários
- ❌ Não pode visualizar dispositivos de outros usuários
- ❌ Não pode ver usuários de dispositivos que não possui
- ❌ Não pode remover atribuições de outros usuários

#### **Gestor (MANAGER):**
- ✅ Pode atribuir dispositivos a qualquer usuário
- ✅ Pode visualizar dispositivos de qualquer usuário
- ✅ Pode ver usuários de qualquer dispositivo
- ✅ Pode remover atribuições de qualquer usuário
- ✅ Pode acessar todas as funcionalidades do sistema

### **4.2 Cenários de Teste Implementados**

#### **Usuário Comum:**
1. ✅ Atribuir dispositivo a si mesmo
2. ❌ Tentar atribuir dispositivo a outro usuário (deve falhar - 403)
3. ✅ Ver seus próprios dispositivos
4. ❌ Tentar ver dispositivos de outro usuário (deve falhar - 403)
5. ✅ Ver usuários de seu dispositivo
6. ❌ Tentar ver usuários de dispositivo que não possui (deve falhar - 403)
7. ✅ Remover sua própria atribuição
8. ❌ Tentar remover atribuição de outro usuário (deve falhar - 403)

#### **Gestor:**
1. ✅ Atribuir dispositivo a outro usuário
2. ✅ Ver dispositivos de qualquer usuário
3. ✅ Ver usuários de qualquer dispositivo
4. ✅ Remover atribuição de qualquer usuário

---

## 📊 **5. VARIÁVEIS DE AMBIENTE POSTMAN**

### **Variáveis Globais:**
```json
{
  "base_url": "http://127.0.0.1:8000",
  "api_base": "{{base_url}}/api/devices",
  "user_id": "1",
  "manager_id": "2"
}
```

### **Variáveis Específicas por Coleção:**

#### **ALIAS CRUD:**
- `api_base`: URL base da API

#### **DHCP CRUD:**
- `api_base`: URL base da API

#### **Permission Tests:**
- `base_url`: URL base do servidor
- `api_base`: URL base da API
- `user_id`: ID do usuário comum para testes
- `manager_id`: ID do gestor para testes

---

## 🧪 **6. FLUXOS DE TESTE RECOMENDADOS**

### **6.1 Teste de Aliases:**
1. Salvar aliases do pfSense
2. Listar aliases
3. Buscar aliases por termo
4. Ver estatísticas
5. Criar novo alias
6. Atualizar alias existente
7. Adicionar IPs a alias existente

### **6.2 Teste de DHCP:**
1. Salvar dados DHCP no banco
2. Listar dispositivos para verificar
3. Buscar dispositivo específico por IP
4. Buscar dispositivo específico por MAC
5. Ver estatísticas dos dispositivos
6. Buscar dispositivos por termo
7. Atualizar dados DHCP
8. Excluir mapeamento DHCP
9. Sincronizar IDs pfSense

### **6.3 Teste de Permissões:**
1. Setup - Salvar dados DHCP
2. Usuário comum atribuir dispositivo a si mesmo
3. Usuário comum tentar atribuir a outro usuário (deve falhar)
4. Gestor atribuir dispositivo a outro usuário
5. Usuário comum ver seus próprios dispositivos
6. Usuário comum tentar ver dispositivos de outro usuário (deve falhar)
7. Gestor ver dispositivos de qualquer usuário
8. Testar remoção de atribuições
9. Buscar atribuições por termo
10. Ver estatísticas de atribuições

---

## 📝 **7. EXEMPLOS DE RESPOSTAS**

### **7.1 Resposta de Sucesso (200):**
```json
{
  "status": "success",
  "message": "Operação realizada com sucesso",
  "data": {
    // Dados específicos da operação
  }
}
```

### **7.2 Resposta de Erro (403 - Forbidden):**
```json
{
  "detail": "Você não tem permissão para realizar esta operação"
}
```

### **7.3 Resposta de Erro (404 - Not Found):**
```json
{
  "detail": "Recurso não encontrado"
}
```

### **7.4 Resposta de Erro (500 - Internal Server Error):**
```json
{
  "detail": "Erro interno do servidor: Descrição do erro"
}
```

---

## 🔧 **8. CONFIGURAÇÃO E DEPLOYMENT**

### **8.1 Variáveis de Ambiente:**
```bash
PFSENSE_API_URL=https://iotedu.dev.ufrgs.br/api/v2/
PFSENSE_API_KEY=sua_chave_api_aqui
```

### **8.2 Iniciar Servidor:**
```bash
python start_server.py
```

### **8.3 URL Base:**
```
http://127.0.0.1:8000/api/devices
```

---

## 📈 **9. MONITORAMENTO E LOGS**

### **9.1 Logs Importantes:**
- Operações de atribuição de dispositivos
- Tentativas de acesso não autorizado
- Sincronização com pfSense
- Erros de validação

### **9.2 Métricas a Monitorar:**
- Número de dispositivos cadastrados
- Atribuições ativas
- Taxa de sucesso das operações
- Tempo de resposta da API

---

## 🎯 **10. CONCLUSÃO**

Esta documentação cobre todos os endpoints implementados e testados através das coleções Postman. O sistema oferece:

- ✅ **Gerenciamento completo de aliases** (CRUD)
- ✅ **Gerenciamento DHCP** (salvar, listar, buscar, atualizar, excluir)
- ✅ **Sistema de permissões robusto** (usuário/gestor)
- ✅ **Sincronização com pfSense**
- ✅ **Validação e tratamento de erros**
- ✅ **Documentação completa para testes**

Todos os endpoints estão funcionais e testados, prontos para uso em produção.

---

**Última atualização:** Setembro 2025  
**Versão:** 2.0.0
