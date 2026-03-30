# 🚀 Guia Completo de Instalação do Zero

Este guia detalha o processo completo de instalação do sistema do zero, incluindo banco de dados vazio e pfSense sem configurações.

## 📋 Pré-requisitos

- ✅ Python 3.9+ instalado
- ✅ MySQL/MariaDB instalado e rodando
- ✅ pfSense configurado com API REST v2 habilitada
- ✅ Acesso ao banco de dados MySQL
- ✅ Acesso ao pfSense (interface web e API)

## 🔧 Passo 1: Preparar Ambiente

### 1.1. Criar Banco de Dados Vazio

```sql
-- Conectar ao MySQL como root
mysql -u root -p

-- Criar banco de dados
CREATE DATABASE iot_edu CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Criar usuário
CREATE USER 'IoT_EDU'@'localhost' IDENTIFIED BY 'sua_senha_aqui';

-- Dar permissões
GRANT ALL PRIVILEGES ON iot_edu.* TO 'IoT_EDU'@'localhost';
FLUSH PRIVILEGES;

-- Verificar
SHOW DATABASES;
USE iot_edu;
SHOW TABLES; -- Deve estar vazio
```

### 1.2. Configurar Variáveis de Ambiente

```bash
cd backend
cp env_example.txt .env
```

Edite o arquivo `.env`:

```env
# Banco de Dados
MYSQL_USER=IoT_EDU
MYSQL_PASSWORD=sua_senha_aqui
MYSQL_HOST=localhost
MYSQL_DB=iot_edu

# pfSense (será configurado depois nas instituições)
PFSENSE_API_URL=https://seu-pfsense.local/api/v2/
PFSENSE_API_KEY=sua_chave_api_aqui

# Google OAuth (para login)
GOOGLE_CLIENT_ID=seu_client_id
GOOGLE_CLIENT_SECRET=seu_client_secret

# Superusuário
SUPERUSER_ACCESS=seu_email@gmail.com
```

### 1.3. Instalar Dependências

```bash
cd backend
pip install -r requirements.txt
```

## 📊 Passo 2: Criar Estrutura do Banco de Dados

```bash
# Script unificado que detecta automaticamente se é instalação do zero
python -m db.setup_database
```

**O que este script faz:**
- ✅ Detecta se o banco está vazio (instalação do zero)
- ✅ Se for instalação do zero: cria todas as tabelas com estrutura completa (incluindo todos os campos e índices)
- ✅ Se for atualização: executa apenas as migrações necessárias
- ✅ Cria automaticamente todos os campos (`institution_id`, `permission`, `is_active`, etc.)
- ✅ Cria automaticamente todos os índices (incluindo índices únicos compostos)

**Verificar:**
```sql
USE iot_edu;
SHOW TABLES;
```

Deve mostrar todas as tabelas criadas:
- users
- institutions
- dhcp_servers
- dhcp_static_mappings
- pfsense_aliases
- pfsense_alias_addresses
- pfsense_firewall_rules
- zeek_incidents
- etc.

## 🛡️ Passo 3: Configurar pfSense

### 5.1. Habilitar API REST no pfSense

1. Acesse a interface web do pfSense
2. Vá em **System > Package Manager**
3. Instale o pacote **API** (pfsense-pkg-API)
4. Vá em **System > API**
5. Gere uma nova chave de API
6. Anote a **API Key** 



## 🚀 Passo 4: Criar Aliases e Regras Iniciais

```bash
# Para todas as instituições
python scripts/setup_initial_aliases_and_rules.py

```

**O que este script faz:**
1. ✅ Cria alias "Autorizados" no pfSense e banco
2. ✅ Cria alias "Bloqueados" no pfSense e banco
3. ✅ Cria regra BLOCK para alias "Bloqueados"
4. ✅ Cria regra PASS para alias "Autorizados"
5. ✅ Sincroniza regras com o banco de dados

**Nota:** Este script requer que a instituição já esteja cadastrada no banco de dados. Se ainda não criou a instituição, veja o Passo 5.

## 👥 Passo 5: Criar Instituição e Administrador via Interface Web

Após executar os scripts acima, você precisa:

1. **Iniciar o servidor backend:**
   ```bash
   python start_server.py
   ```

2. **Acessar a interface web** e fazer login com o email configurado em `SUPERUSER_ACCESS` no arquivo `.env`

3. **Criar Instituição:**
   - Acesse a seção de **Instituições** na interface web
   - Clique em **Nova Instituição**
   - Preencha os dados:
     - Nome (ex: "Unipampa")
     - Cidade (ex: "Alegrete")
     - URL do pfSense (ex: "https://seu-pfsense.local/api/v2/")
     - Chave API do pfSense
     - Range de IPs (ex: "192.168.1.1" a "192.168.1.254")
   - Salve a instituição

4. **Criar Usuário Administrador:**
   - Acesse a seção de **Usuários** na interface web
   - Clique em **Novo Usuário** ou atribua permissão ADMIN a um usuário existente
   - Associe o usuário à instituição criada
   - Defina a permissão como **ADMIN**

**Importante:** O script `setup_initial_aliases_and_rules.py` precisa ser executado **após** criar a instituição, pois ele cria os aliases e regras para cada instituição cadastrada.

## ✅ Passo 6: Verificações Finais

### 7.1. Verificar no Banco de Dados

```sql
USE iot_edu;

-- Verificar instituições
SELECT id, nome, cidade, is_active FROM institutions;

-- Verificar usuários
SELECT id, email, nome, permission, institution_id FROM users;

-- Verificar aliases
SELECT id, name, alias_type, institution_id FROM pfsense_aliases;

-- Verificar regras
SELECT id, pf_id, type, source, descr, institution_id 
FROM pfsense_firewall_rules 
WHERE institution_id = 1;
```

### 7.2. Verificar no pfSense

**Via Interface Web:**
1. **Firewall > Aliases**
   - Deve ver "Autorizados" (tipo: host, vazio)
   - Deve ver "Bloqueados" (tipo: host, vazio)

2. **Firewall > Rules**
   - Deve ver regra BLOCK com source="Bloqueados"
   - Deve ver regra PASS com source="Autorizados"

**Via API:**
```bash
# Listar aliases
curl -X GET "https://seu-pfsense.local/api/v2/firewall/alias" \
  -H "X-API-Key: sua_chave_api"

# Listar regras
curl -X GET "https://seu-pfsense.local/api/v2/firewall/rule" \
  -H "X-API-Key: sua_chave_api"
```

### 7.3. Testar Funcionalidade

#### Teste 1: Adicionar IP ao alias "Bloqueados"

```bash
curl -X POST "http://localhost:8000/api/devices/aliases-db/Bloqueados/add-addresses?current_user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": [
      {"address": "192.168.1.100", "detail": "Teste de bloqueio"}
    ]
  }'
```

**Verificar:**
- IP aparece no alias "Bloqueados" no banco
- IP aparece no alias "Bloqueados" no pfSense
- Regra BLOCK está ativa

#### Teste 2: Adicionar IP ao alias "Autorizados"

```bash
curl -X POST "http://localhost:8000/api/devices/aliases-db/Autorizados/add-addresses?current_user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": [
      {"address": "192.168.1.101", "detail": "Teste de liberação"}
    ]
  }'
```

**Verificar:**
- IP aparece no alias "Autorizados" no banco
- IP aparece no alias "Autorizados" no pfSense
- Regra PASS está ativa

## 📝 Checklist de Instalação

Use este checklist para garantir que tudo foi configurado:

- [ ] Banco de dados criado e vazio
- [ ] Variáveis de ambiente configuradas (.env)
- [ ] Dependências Python instaladas
- [ ] Banco de dados configurado (`python -m db.setup_database`)
- [ ] pfSense API configurada e testada
- [ ] Servidor backend iniciado
- [ ] Login realizado como SUPERUSER
- [ ] Instituição criada via interface web
- [ ] Usuário ADMIN criado/atribuído via interface web
- [ ] Script de setup inicial executado (`python scripts/setup_initial_aliases_and_rules.py`)
- [ ] Aliases verificados no banco
- [ ] Aliases verificados no pfSense
- [ ] Regras verificadas no banco
- [ ] Regras verificadas no pfSense

## 🐛 Troubleshooting

### Erro: "Configurações do pfSense não encontradas"

**Solução:**
1. Verificar se a instituição foi criada no banco
2. Verificar se `pfsense_base_url` e `pfsense_key` estão corretos
3. Verificar se o usuário tem `institution_id` associado

### Erro: "Timeout ao conectar no pfSense"

**Solução:**
1. Verificar conectividade de rede
2. Verificar URL do pfSense (deve terminar com `/api/v2/`)
3. Verificar se API está habilitada no pfSense
4. Verificar certificado SSL (pode precisar `verify=False`)

### Erro: "Alias já existe"

**Solução:**
- Normal se executar o script múltiplas vezes
- O script é idempotente e não cria duplicatas
- Pode ignorar este aviso

### Erro: "Usuário ADMIN não encontrado"

**Solução:**
1. Criar usuário ADMIN via interface web:
   - Acesse a seção de Usuários
   - Atribua permissão ADMIN ao usuário
   - Associe o usuário à instituição desejada

2. Ou criar manualmente via SQL:
   ```sql
   UPDATE users SET permission = 'ADMIN', institution_id = 1 WHERE id = X;
   ```

## 📚 Resumo da Instalação

O processo de instalação foi simplificado para apenas **2 comandos principais**:

1. **Criar tabelas:** `python -m db.setup_database`
2. **Criar aliases e regras:** `python scripts/setup_initial_aliases_and_rules.py`

**Após executar os comandos:**
- Criar instituição via interface web (como SUPERUSER)
- Criar/atribuir usuário ADMIN via interface web
- Executar novamente `setup_initial_aliases_and_rules.py` se necessário

## 📚 Próximos Passos

Após instalação completa:

1. ✅ Configurar frontend
2. ✅ Testar login de usuários
3. ✅ Cadastrar dispositivos
4. ✅ Testar bloqueio/liberação
5. ✅ Configurar monitoramento Zeek (opcional)

## 🔗 Links Úteis

- [Guia de Teste](GUIA_TESTE_SETUP_INICIAL.md)
- [Sistema Multi-Institucional](MULTI_INSTITUCIONAL.md)
- [Documentação da API pfSense](README-pfsense-api-v2.md)

---

**Boa sorte com a instalação! 🚀**

Se encontrar problemas, consulte a seção de Troubleshooting ou verifique os logs do sistema.

