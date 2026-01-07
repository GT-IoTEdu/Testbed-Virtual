# 📚 Guia: Documentação OpenAPI 3.0.0

## 📋 Visão Geral

A documentação OpenAPI 3.0.0 da API IoT-EDU foi criada com base nos endpoints testados nas coleções Postman. Este documento fornece uma especificação completa e padronizada da API.

## 📄 Arquivo da Documentação

- **Arquivo**: `docs/openapi_iot_edu.yaml`
- **Versão**: OpenAPI 3.0.0
- **Formato**: YAML
- **Endpoints Documentados**: 47 endpoints

## 🎯 Como Usar

### 🔧 Método 1: Swagger UI (Recomendado)

#### 1. Acessar Swagger UI
```
http://127.0.0.1:8000/docs
```

#### 2. Importar Especificação
1. Abra o Swagger UI
2. Clique em **Import**
3. Selecione o arquivo `docs/openapi_iot_edu.yaml`
4. Clique em **Import**

### 🔧 Método 2: SwaggerHub

#### 1. Acessar SwaggerHub
```
https://app.swaggerhub.com/
```

#### 2. Criar Nova API
1. Faça login no SwaggerHub
2. Clique em **Create New API**
3. Selecione **Import API**
4. Faça upload do arquivo `openapi_iot_edu.yaml`

#### 3. Configurar API
```yaml
# Informações da API
Name: IoT-EDU API
Version: 2.0.0
Description: API para gerenciamento de dispositivos IoT educacionais

# Configurações
Visibility: Public
Auto Mock: Enabled
```

### 🔧 Método 3: Editor Online

#### 1. Swagger Editor
```
https://editor.swagger.io/
```

#### 2. Importar Arquivo
1. Abra o Swagger Editor
2. Clique em **File > Import File**
3. Selecione `openapi_iot_edu.yaml`

## 📊 Estrutura da Documentação

### 🏷️ Tags Organizadas

#### 🏥 Health
- `GET /health` - Verificação de saúde
- `GET /` - Página inicial
- `GET /docs` - Documentação Swagger

#### 🔐 Authentication
- `GET /auth/login` - Login SAML CAFe
- `GET /auth/callback` - Callback SAML
- `GET /auth/logout` - Logout SAML
- `GET /auth/verify` - Verificar token JWT
- `GET /auth/metadata` - Metadados SAML
- `GET /auth/status` - Status da autenticação
- `GET /api/auth/login` - Login OAuth2 CAFe
- `GET /api/auth/callback` - Callback OAuth2

#### 🌐 DHCP
- `POST /api/devices/dhcp/save` - Salvar dados DHCP
- `GET /api/devices/dhcp/servers` - Listar servidores
- `GET /api/devices/dhcp/static_mapping` - Listar mapeamentos
- `POST /api/devices/dhcp/static_mapping` - Criar mapeamento
- `GET /api/devices/dhcp/static_mapping/check` - Verificar mapeamentos
- `GET /api/devices/dhcp/statistics` - Estatísticas
- `GET /api/devices/dhcp/ip-addresses` - Listar IPs

#### 📱 Devices
- `GET /api/devices/dhcp/devices` - Listar dispositivos
- `GET /api/devices/dhcp/devices/search` - Buscar dispositivos
- `GET /api/devices/dhcp/devices/ip/{ipaddr}` - Buscar por IP
- `GET /api/devices/dhcp/devices/mac/{mac}` - Buscar por MAC
- `GET /api/devices/devices` - Listar todos (Gestores)
- `GET /api/devices/devices/{device_id}/users` - Usuários do dispositivo

#### 👥 Users
- `GET /api/devices/users/{user_id}/devices` - Dispositivos do usuário

#### 🔗 Aliases
- `POST /api/devices/aliases-db/save` - Salvar aliases
- `GET /api/devices/aliases-db` - Listar aliases
- `GET /api/devices/aliases-db/search` - Buscar aliases
- `GET /api/devices/aliases-db/statistics` - Estatísticas
- `POST /api/devices/aliases-db/create` - Criar alias
- `GET /api/devices/aliases-db/{alias_name}` - Obter alias
- `PATCH /api/devices/aliases-db/{alias_name}` - Atualizar alias
- `POST /api/devices/aliases-db/{alias_name}/add-addresses` - Adicionar endereços

#### 🔗 Assignments
- `POST /api/devices/assignments` - Atribuir dispositivo
- `DELETE /api/devices/assignments/{user_id}/{device_id}` - Remover atribuição
- `GET /api/devices/assignments/search` - Buscar atribuições
- `GET /api/devices/assignments/statistics` - Estatísticas

## 🧪 Testes na Documentação

### 🔍 Testes Automáticos

#### 1. Swagger UI
- **Try it out**: Teste direto na interface
- **Execute**: Execução automática de requisições
- **Response**: Visualização das respostas

#### 2. SwaggerHub
- **Auto Mock**: Geração automática de respostas
- **Test Cases**: Criação de casos de teste
- **Validation**: Validação automática de schemas

### 📋 Exemplos Incluídos

#### DHCP Save
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

#### Device Assignment
```json
{
  "user_id": 1,
  "device_id": 1,
  "notes": "Dispositivo atribuído para testes",
  "assigned_by": 2
}
```

#### Alias Creation
```json
{
  "name": "teste_api_iot_edu_v3",
  "type": "host",
  "descr": "Alias de teste criado via API v3",
  "address": ["192.168.1.200", "192.168.1.201"],
  "detail": ["Dispositivo de teste 1", "Dispositivo de teste 2"]
}
```

## 🔧 Configuração de Ambiente

### 🌐 Servers Configurados

#### Desenvolvimento
```yaml
- url: http://127.0.0.1:8000
  description: Servidor de Desenvolvimento
```

#### Produção
```yaml
- url: https://iotedu.dev.ufrgs.br
  description: Servidor de Produção
```

### 🔐 Autenticação

#### Bearer Token
```yaml
securitySchemes:
  BearerAuth:
    type: http
    scheme: bearer
    bearerFormat: JWT
    description: Token JWT obtido através da autenticação SAML ou OAuth2
```

## 📊 Schemas Definidos

### 🔍 Principais Schemas

#### HealthResponse
```yaml
HealthResponse:
  type: object
  properties:
    status:
      type: string
      enum: [healthy, unhealthy]
    timestamp:
      type: string
      format: date-time
    version:
      type: string
```

#### Device
```yaml
Device:
  type: object
  properties:
    id:
      type: integer
    mac:
      type: string
    ipaddr:
      type: string
      format: ipv4
    cid:
      type: string
    hostname:
      type: string
    descr:
      type: string
```

#### User
```yaml
User:
  type: object
  properties:
    id:
      type: integer
    email:
      type: string
      format: email
    nome:
      type: string
    permission:
      type: string
      enum: [USER, MANAGER]
```

## 🚀 Integração com Ferramentas

### 🔧 Postman

#### 1. Importar do OpenAPI
1. Abra o Postman
2. Clique em **Import**
3. Selecione **Link** ou **File**
4. Cole a URL do SwaggerHub ou faça upload do arquivo

#### 2. Gerar Coleção
```bash
# Usando openapi-generator
openapi-generator generate -i openapi_iot_edu.yaml -g postman -o postman_collection
```

### 🔧 Insomnia

#### 1. Importar Especificação
1. Abra o Insomnia
2. Clique em **Create > Import from URL**
3. Cole a URL do SwaggerHub

### 🔧 curl

#### 1. Gerar Comandos
```bash
# Exemplo de comando gerado
curl -X GET "http://127.0.0.1:8000/health" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📈 Monitoramento e Validação

### 🔍 Validação de Schemas

#### 1. Swagger Editor
- Validação automática de sintaxe
- Verificação de schemas
- Detecção de erros

#### 2. SwaggerHub
- Validação contínua
- Relatórios de qualidade
- Sugestões de melhoria

### 📊 Métricas

#### Cobertura de Endpoints
- **Total**: 47 endpoints
- **Documentados**: 47 endpoints
- **Cobertura**: 100%

#### Schemas Definidos
- **Total**: 25 schemas
- **Reutilizáveis**: 15 schemas
- **Específicos**: 10 schemas

## 🎯 Casos de Uso

### 🔍 Desenvolvimento
- **Referência**: Para desenvolvedores
- **Testes**: Validação de implementação
- **Integração**: Para clientes da API

### 📚 Documentação
- **Técnica**: Para equipe técnica
- **Usuários**: Para consumidores da API
- **Suporte**: Para troubleshooting

### 🔧 DevOps
- **CI/CD**: Validação automática
- **Monitoramento**: Verificação de contratos
- **Testes**: Geração automática de testes

## 📝 Manutenção

### 🔄 Atualizações

#### 1. Versões
- **Versionamento**: Semântico (MAJOR.MINOR.PATCH)
- **Changelog**: Documentação de mudanças
- **Deprecação**: Avisos de endpoints obsoletos

#### 2. Sincronização
- **Código**: Alinhamento com implementação
- **Testes**: Validação com Postman
- **Documentação**: Atualização de exemplos

### 🚨 Boas Práticas

#### 1. Documentação
- **Clareza**: Descrições objetivas
- **Exemplos**: Casos de uso reais
- **Validação**: Schemas precisos

#### 2. Versionamento
- **Compatibilidade**: Backward compatibility
- **Migração**: Guias de atualização
- **Deprecação**: Avisos antecipados

---

**Guia criado em**: Setembro 2025  
**Versão**: 1.0  
**Mantido por**: Equipe IoT-EDU
