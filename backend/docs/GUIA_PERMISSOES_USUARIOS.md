# 🔐 **Guia Completo - Sistema de Permissões de Usuários**

## **📋 Visão Geral**

O sistema implementa **três níveis de permissão** para usuários:

### **👤 Usuário Comum (USER)**
- **Pode**: Gerenciar apenas seus próprios dispositivos
- **Não pode**: Ver ou gerenciar dispositivos de outros usuários
- **Exemplo**: `usuario.teste@unipampa.edu.br` (ID: 1)

### **👨‍💼 Gestor (MANAGER)**
- **Pode**: Gerenciar todos os dispositivos de todos os usuários
- **Pode**: Ver atribuições de qualquer usuário
- **Exemplo**: `gestor.teste@unipampa.edu.br` (ID: 2)

### **👑 Administrador (ADMIN)**
- **Pode**: Gerenciar permissões de todos os usuários
- **Pode**: Promover usuários para MANAGER ou ADMIN
- **Pode**: Rebaixar MANAGERs para USER
- **Pode**: Fazer login com email e senha provisória
- **Exemplo**: `admin@iotedu.local` (configurado via ADMIN_ACCESS)

---

## **👥 Usuários de Teste Cadastrados**

| ID | Email | Nome | Permissão | Instituição |
|----|-------|------|-----------|-------------|
| 1 | `usuario.teste@unipampa.edu.br` | Usuário Teste | USER | UNIPAMPA |
| 2 | `gestor.teste@unipampa.edu.br` | Gestor Teste | MANAGER | UNIPAMPA |
| 3 | `admin@iotedu.local` | Administrador do Sistema | ADMIN | IoT-EDU |

---

## **🔧 Endpoints com Verificação de Permissões**

### **1. 🔗 Atribuir Dispositivo a Usuário**

**Endpoint**: `POST /api/devices/assignments`

**Regras de Permissão**:
- **Usuário comum**: Só pode atribuir dispositivos a si mesmo
- **Gestor**: Pode atribuir dispositivos a qualquer usuário

**Exemplo - Usuário comum atribuindo a si mesmo**:
```bash
curl -X POST http://127.0.0.1:8000/api/devices/assignments \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "device_id": 1,
    "notes": "Dispositivo atribuído pelo próprio usuário",
    "assigned_by": 1
  }'
```

**Exemplo - Gestor atribuindo a outro usuário**:
```bash
curl -X POST http://127.0.0.1:8000/api/devices/assignments \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "device_id": 2,
    "notes": "Dispositivo atribuído pelo gestor",
    "assigned_by": 2
  }'
```

**❌ Exemplo - Usuário comum tentando atribuir a outro usuário**:
```bash
curl -X POST http://127.0.0.1:8000/api/devices/assignments \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "device_id": 1,
    "notes": "Tentativa de atribuir a outro usuário",
    "assigned_by": 1
  }'
```
**Resposta esperada**: `403 Forbidden - Você não tem permissão para atribuir este dispositivo a este usuário`

---

### **2. 🗑️ Remover Atribuição de Dispositivo**

**Endpoint**: `DELETE /api/devices/assignments/{user_id}/{device_id}?current_user_id={id}`

**Regras de Permissão**:
- **Usuário comum**: Só pode remover suas próprias atribuições
- **Gestor**: Pode remover atribuições de qualquer usuário

**Exemplo - Usuário comum removendo sua própria atribuição**:
```bash
curl -X DELETE "http://127.0.0.1:8000/api/devices/assignments/1/1?current_user_id=1"
```

**Exemplo - Gestor removendo atribuição de outro usuário**:
```bash
curl -X DELETE "http://127.0.0.1:8000/api/devices/assignments/1/1?current_user_id=2"
```

**❌ Exemplo - Usuário comum tentando remover atribuição de outro usuário**:
```bash
curl -X DELETE "http://127.0.0.1:8000/api/devices/assignments/2/1?current_user_id=1"
```
**Resposta esperada**: `403 Forbidden - Você não tem permissão para remover esta atribuição`

---

### **3. 📋 Listar Dispositivos de um Usuário**

**Endpoint**: `GET /api/devices/users/{user_id}/devices?current_user_id={id}`

**Regras de Permissão**:
- **Usuário comum**: Só pode ver seus próprios dispositivos
- **Gestor**: Pode ver dispositivos de qualquer usuário

**Exemplo - Usuário comum vendo seus próprios dispositivos**:
```bash
curl "http://127.0.0.1:8000/api/devices/users/1/devices?current_user_id=1"
```

**Exemplo - Gestor vendo dispositivos de outro usuário**:
```bash
curl "http://127.0.0.1:8000/api/devices/users/1/devices?current_user_id=2"
```

**❌ Exemplo - Usuário comum tentando ver dispositivos de outro usuário**:
```bash
curl "http://127.0.0.1:8000/api/devices/users/2/devices?current_user_id=1"
```
**Resposta esperada**: `403 Forbidden - Você não tem permissão para visualizar os dispositivos deste usuário`

---

### **4. 👥 Listar Usuários de um Dispositivo**

**Endpoint**: `GET /api/devices/devices/{device_id}/users?current_user_id={id}`

**Regras de Permissão**:
- **Usuário comum**: Só pode ver usuários de dispositivos que possui
- **Gestor**: Pode ver usuários de qualquer dispositivo

**Exemplo - Usuário comum vendo usuários de seu dispositivo**:
```bash
curl "http://127.0.0.1:8000/api/devices/devices/1/users?current_user_id=1"
```

**Exemplo - Gestor vendo usuários de qualquer dispositivo**:
```bash
curl "http://127.0.0.1:8000/api/devices/devices/1/users?current_user_id=2"
```

**❌ Exemplo - Usuário comum tentando ver usuários de dispositivo que não possui**:
```bash
curl "http://127.0.0.1:8000/api/devices/devices/2/users?current_user_id=1"
```
**Resposta esperada**: `403 Forbidden - Você não tem permissão para visualizar os usuários deste dispositivo`

---

## **🧪 Cenários de Teste Completos**

### **Cenário 1: Usuário Comum Gerenciando Seus Dispositivos**

```bash
# 1. Salvar dados DHCP primeiro
curl -X POST http://127.0.0.1:8000/api/devices/dhcp/save

# 2. Usuário comum atribui dispositivo a si mesmo
curl -X POST http://127.0.0.1:8000/api/devices/assignments \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "device_id": 1,
    "notes": "Dispositivo OpenVAS atribuído ao usuário",
    "assigned_by": 1
  }'

# 3. Usuário comum vê seus dispositivos
curl "http://127.0.0.1:8000/api/devices/users/1/devices?current_user_id=1"

# 4. Usuário comum vê usuários de seu dispositivo
curl "http://127.0.0.1:8000/api/devices/devices/1/users?current_user_id=1"
```

### **Cenário 2: Gestor Gerenciando Todos os Dispositivos**

```bash
# 1. Gestor atribui dispositivo ao usuário comum
curl -X POST http://127.0.0.1:8000/api/devices/assignments \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "device_id": 2,
    "notes": "Dispositivo atribuído pelo gestor",
    "assigned_by": 2
  }'

# 2. Gestor vê dispositivos do usuário comum
curl "http://127.0.0.1:8000/api/devices/users/1/devices?current_user_id=2"

# 3. Gestor vê usuários de qualquer dispositivo
curl "http://127.0.0.1:8000/api/devices/devices/1/users?current_user_id=2"

# 4. Gestor remove atribuição de outro usuário
curl -X DELETE "http://127.0.0.1:8000/api/devices/assignments/1/2?current_user_id=2"
```

### **Cenário 3: Testando Restrições de Permissão**

```bash
# 1. Usuário comum tenta atribuir dispositivo a outro usuário (deve falhar)
curl -X POST http://127.0.0.1:8000/api/devices/assignments \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "device_id": 1,
    "notes": "Tentativa não autorizada",
    "assigned_by": 1
  }'

# 2. Usuário comum tenta ver dispositivos de outro usuário (deve falhar)
curl "http://127.0.0.1:8000/api/devices/users/2/devices?current_user_id=1"

# 3. Usuário comum tenta remover atribuição de outro usuário (deve falhar)
curl -X DELETE "http://127.0.0.1:8000/api/devices/assignments/2/1?current_user_id=1"
```

---

## **👑 Endpoints Administrativos**

### **1. 🔐 Login Administrativo**

**Endpoint**: `POST /api/admin/login`

**Descrição**: Permite login administrativo usando email e senha provisória.

**Exemplo**:
```bash
curl -X POST http://127.0.0.1:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@iotedu.local",
    "password": "admin123"
  }'
```

### **2. 👥 Gerenciar Usuários**

**Endpoint**: `GET /api/admin/users`

**Descrição**: Lista todos os usuários do sistema (apenas administradores).

**Exemplo**:
```bash
curl "http://127.0.0.1:8000/api/admin/users"
```

### **3. 🔄 Alterar Permissão de Usuário**

**Endpoint**: `PUT /api/admin/users/{user_id}/permission`

**Descrição**: Altera a permissão de um usuário (apenas administradores).

**Exemplo - Promover usuário para gestor**:
```bash
curl -X PUT http://127.0.0.1:8000/api/admin/users/1/permission \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "new_permission": "MANAGER"
  }'
```

**Exemplo - Rebaixar gestor para usuário**:
```bash
curl -X PUT http://127.0.0.1:8000/api/admin/users/2/permission \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "new_permission": "USER"
  }'
```

### **4. 📊 Estatísticas de Usuários**

**Endpoint**: `GET /api/admin/users/stats`

**Descrição**: Retorna estatísticas dos usuários por permissão.

**Exemplo**:
```bash
curl "http://127.0.0.1:8000/api/admin/users/stats"
```

### **5. ℹ️ Informações do Administrador**

**Endpoint**: `GET /api/admin/info`

**Descrição**: Retorna informações sobre o acesso administrativo.

**Exemplo**:
```bash
curl "http://127.0.0.1:8000/api/admin/info"
```

### **6. ✅ Validar Configuração**

**Endpoint**: `GET /api/admin/validate-config`

**Descrição**: Valida se as configurações administrativas estão corretas.

**Exemplo**:
```bash
curl "http://127.0.0.1:8000/api/admin/validate-config"
```

---

## **⚙️ Configuração do Sistema Administrativo**

### **Variáveis de Ambiente**

Adicione ao arquivo `.env`:

```env
# Configurações de acesso administrativo
ADMIN_ACCESS=admin@iotedu.local
ADMIN_PASSWORD=admin123
```

### **Scripts de Configuração**

```bash
# 1. Executar migração para adicionar perfil ADMIN
python scripts/migrate_add_admin_permission.py

# 2. Criar usuário administrador inicial
python scripts/create_initial_admin.py
```

---

## **🔒 Regras de Segurança**

### **Administradores**
- ✅ Podem promover qualquer usuário para MANAGER ou ADMIN
- ✅ Podem rebaixar qualquer MANAGER para USER
- ❌ **NÃO podem** alterar suas próprias permissões
- ❌ **NÃO podem** alterar permissões de outros administradores
- ✅ Fazem login com email e senha provisória (configurável)

### **Gestores**
- ✅ Podem gerenciar todos os dispositivos
- ✅ Podem ver atribuições de qualquer usuário
- ❌ **NÃO podem** alterar permissões de usuários
- ✅ Fazem login via CAFe/Google OAuth2

### **Usuários**
- ✅ Podem gerenciar apenas seus próprios dispositivos
- ❌ **NÃO podem** ver dispositivos de outros usuários
- ❌ **NÃO podem** alterar permissões
- ✅ Fazem login via CAFe/Google OAuth2

---

## **🧪 Testes de Permissões Administrativas**

### **Cenário 1: Login Administrativo**

```bash
# Login com credenciais corretas
curl -X POST http://127.0.0.1:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@iotedu.local",
    "password": "admin123"
  }'

# Login com credenciais incorretas (deve falhar)
curl -X POST http://127.0.0.1:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@iotedu.local",
    "password": "senha_errada"
  }'
```

### **Cenário 2: Gerenciamento de Usuários**

```bash
# 1. Listar todos os usuários
curl "http://127.0.0.1:8000/api/admin/users"

# 2. Promover usuário para gestor
curl -X PUT http://127.0.0.1:8000/api/admin/users/1/permission \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "new_permission": "MANAGER"
  }'

# 3. Verificar estatísticas
curl "http://127.0.0.1:8000/api/admin/users/stats"
```

### **Cenário 3: Validação de Configuração**

```bash
# Validar configuração administrativa
curl "http://127.0.0.1:8000/api/admin/validate-config"

# Obter informações do administrador
curl "http://127.0.0.1:8000/api/admin/info"
```

---

## **📋 Resumo das Permissões**

| Ação | USER | MANAGER | ADMIN |
|------|------|---------|-------|
| Gerenciar próprios dispositivos | ✅ | ✅ | ✅ |
| Gerenciar dispositivos de outros | ❌ | ✅ | ✅ |
| Ver atribuições de outros | ❌ | ✅ | ✅ |
| Alterar permissões de usuários | ❌ | ❌ | ✅ |
| Promover usuários | ❌ | ❌ | ✅ |
| Rebaixar usuários | ❌ | ❌ | ✅ |
| Login via CAFe/Google | ✅ | ✅ | ✅ |
| Login administrativo | ❌ | ❌ | ✅ |

---

## **🚀 Próximos Passos**

1. **Configure** as variáveis `ADMIN_ACCESS` e `ADMIN_PASSWORD` no arquivo `.env`
2. **Execute** os scripts de migração e criação do administrador
3. **Teste** o login administrativo
4. **Configure** outros administradores conforme necessário
5. **Monitore** o sistema usando os endpoints administrativos

---

**🎉 O sistema agora possui controle completo de permissões com três níveis de acesso!**

## **📊 Respostas de Erro Comuns**

### **403 Forbidden - Sem Permissão**
```json
{
  "detail": "Você não tem permissão para atribuir este dispositivo a este usuário"
}
```

### **404 Not Found - Usuário Não Encontrado**
```json
{
  "detail": "Usuário com ID 999 não encontrado"
}
```

### **404 Not Found - Dispositivo Não Encontrado**
```json
{
  "detail": "Dispositivo com ID 999 não encontrado"
}
```

---

## **🔍 Verificação de Permissões no Postman**

### **Variáveis de Ambiente**
Configure no Postman:
- `base_url`: `http://127.0.0.1:8000`
- `api_base`: `{{base_url}}/api/devices`
- `user_id`: `1` (usuário comum)
- `manager_id`: `2` (gestor)

### **Collection para Testes de Permissão**
```json
{
  "info": {
    "name": "IoT-EDU Permission Tests",
    "description": "Testes de permissões do sistema"
  },
  "item": [
    {
      "name": "Usuário Comum - Atribuir a Si Mesmo",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"user_id\": {{user_id}},\n  \"device_id\": 1,\n  \"notes\": \"Teste de permissão\",\n  \"assigned_by\": {{user_id}}\n}"
        },
        "url": "{{api_base}}/assignments"
      }
    },
    {
      "name": "Usuário Comum - Tentar Atribuir a Outro (Deve Falhar)",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"user_id\": {{manager_id}},\n  \"device_id\": 1,\n  \"notes\": \"Tentativa não autorizada\",\n  \"assigned_by\": {{user_id}}\n}"
        },
        "url": "{{api_base}}/assignments"
      }
    },
    {
      "name": "Gestor - Atribuir a Qualquer Usuário",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"user_id\": {{user_id}},\n  \"device_id\": 2,\n  \"notes\": \"Atribuição pelo gestor\",\n  \"assigned_by\": {{manager_id}}\n}"
        },
        "url": "{{api_base}}/assignments"
      }
    }
  ]
}
```

---

## **💡 Dicas Importantes**

1. **Sempre execute primeiro** o endpoint de salvar dados DHCP
2. **Use os IDs corretos** dos usuários de teste
3. **Verifique as respostas** para confirmar que as permissões estão funcionando
4. **Teste tanto cenários de sucesso** quanto de falha
5. **Gestores têm acesso total** ao sistema
6. **Usuários comuns são restritos** a seus próprios recursos

---

## **🚀 Próximos Passos**

1. **Teste todos os cenários** usando os comandos acima
2. **Implemente autenticação JWT** para identificar usuários automaticamente
3. **Crie interface web** para facilitar o gerenciamento
4. **Adicione logs de auditoria** para rastrear ações dos usuários
5. **Implemente notificações** para mudanças de atribuições

O sistema de permissões está funcionando e pronto para uso! 🎉
