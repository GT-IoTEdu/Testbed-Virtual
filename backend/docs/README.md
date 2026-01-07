# IoT-EDU Backend

Sistema de gerenciamento seguro de dispositivos IoT para ambientes acadêmicos, com autenticação federada CAFe (SAML) e integração pfSense.

## 🚀 **Funcionalidades Principais**

- **Autenticação SAML CAFe (Federada)**
- **Autenticação OAuth2 CAFe (Legacy)**
- **Integração com pfSense API v2**
- **Gerenciamento de aliases DHCP**
- **Listagem de servidores DHCP**
- **Mapeamentos estáticos DHCP**
- **Persistência de dados DHCP no banco de dados**
- **Busca e consulta de dispositivos por IP, MAC e descrição**
- **Identificação de dispositivos duplicados**
- **Estatísticas de dispositivos cadastrados**
- **Sistema de permissões de usuários**: Controle de acesso baseado em níveis (usuário/gestor)
- **Atribuição de dispositivos a usuários**: Gerenciamento de responsabilidades por dispositivo
- **Configuração segura via variáveis de ambiente**
- **Tokens JWT para sessões seguras**

## 📋 **Requisitos**

- Python 3.9+
- MySQL
- pfSense com API REST habilitada
- OpenSSL (para certificados SAML)
- Dependências Python (ver `requirements.txt`)

## ⚙️ **Instalação**

### 1. Clone o repositório
```bash
git clone https://github.com/GT-IoTEdu/API_IoT_EDU.git
cd API-IoT-EDU
```

### 2. Instale as dependências
```bash
pip install -r backend/requirements.txt
```

### 3. Configure o arquivo `.env`
Crie um arquivo `.env` no diretório `backend/` com as seguintes variáveis:

```env
# Configurações do banco de dados MySQL
MYSQL_USER=IoT_EDU
MYSQL_PASSWORD=sua_senha_mysql
MYSQL_HOST=localhost
MYSQL_DB=iot_edu

# Configurações de autenticação CAFe (OAuth2/OpenID Connect)
CAFE_CLIENT_ID=seu_client_id_cafe
CAFE_CLIENT_SECRET=seu_client_secret_cafe
CAFE_AUTH_URL=https://sso.cafe.unipampa.edu.br/auth/realms/CAFe/protocol/openid-connect/auth
CAFE_TOKEN_URL=https://sso.cafe.unipampa.edu.br/auth/realms/CAFe/protocol/openid-connect/token
CAFE_USERINFO_URL=https://sso.cafe.unipampa.edu.br/auth/realms/CAFe/protocol/openid-connect/userinfo
CAFE_REDIRECT_URI=http://localhost:8000/auth/callback

# Configurações da API do pfSense
PFSENSE_API_URL=https://iotedu.dev.ufrgs.br/api/v2/
PFSENSE_API_KEY=sua_api_key_pfsense

# Configurações JWT para SAML
JWT_SECRET_KEY=sua_chave_secreta_jwt_muito_segura
```

### 4. Configure certificados SAML (Obrigatório para autenticação CAFe)
```bash
# Gerar certificados SAML
cd backend
python generate_saml_certificates.py
```

### 5. Configure o banco de dados
```bash
python -m backend.db.create_tables
```

### 6. Inicie o servidor
```bash
# Opção 1: Usando uvicorn diretamente
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Opção 2: Usando o script de inicialização
python backend/start_server.py
```

## 📁 **Estrutura do Projeto**

```
backend/
├── main.py              # Aplicação FastAPI principal
├── config.py            # Configurações e variáveis de ambiente
├── start_server.py      # Script para iniciar o servidor
├── requirements.txt     # Dependências Python
├── .env                 # Variáveis de ambiente (criar)
├── generate_saml_certificates.py  # Gerador de certificados SAML
├── README.md           # Este arquivo
├── README-pfsense-api-v2.md  # Documentação da API pfSense
├── README-firewall-rules.md  # Documentação de regras de firewall
├── auth/               # Módulos de autenticação
│   ├── cafe_auth.py    # Autenticação OAuth2 CAFe
│   ├── saml_auth.py    # Autenticação SAML CAFe
│   └── saml_router.py  # Endpoints SAML
├── devices/            # Endpoints de dispositivos e pfSense
├── models/             # Modelos Pydantic
└── db/                # Configuração do banco de dados

# Estrutura SAML (raiz do projeto)
sp_django/             # Configuração Django SAML
├── settings.py        # Configurações SAML
└── urls.py           # URLs SAML
attribute-maps/        # Mapeamento de atributos SAML
certificates/          # Certificados SAML
base/                  # Views Django
```

## 🔗 **Endpoints Disponíveis**

### **Autenticação SAML CAFe (Recomendado)**
- `GET /auth/login` - Inicia autenticação SAML CAFe
- `GET /auth/callback` - Callback SAML CAFe
- `GET /auth/logout` - Logout SAML CAFe
- `GET /auth/verify` - Verificar token JWT
- `GET /auth/status` - Status da autenticação
- `GET /auth/metadata` - Metadados SAML

### **Autenticação OAuth2 CAFe (Legacy)**
- `GET /api/auth/login` - Inicia autenticação OAuth2 CAFe
- `GET /api/auth/callback` - Callback OAuth2 CAFe

### **Aliases pfSense**
- `POST /api/devices/alias` - Cadastrar alias no pfSense
- `GET /api/devices/aliases/` - Listar todos os aliases
- `GET /api/devices/aliases/{name}` - Obter alias específico

### **DHCP pfSense**
- `GET /api/devices/dhcp/servers` - Listar todos os servidores DHCP
- `GET /api/devices/dhcp/static_mapping?parent_id=lan&id=6` - Listar mapeamento específico DHCP

### **Gerenciamento de Dados DHCP (Novo)**
- `POST /api/devices/dhcp/save` - Salvar dados DHCP no banco de dados
- `GET /api/devices/dhcp/devices` - Listar dispositivos cadastrados (com paginação)
- `GET /api/devices/dhcp/devices/search?query=termo` - Buscar dispositivos por termo
- `GET /api/devices/dhcp/devices/ip/{ipaddr}` - Buscar dispositivo por IP
- `GET /api/devices/dhcp/devices/mac/{mac}` - Buscar dispositivo por MAC
- `GET /api/devices/dhcp/statistics` - Estatísticas de dispositivos cadastrados
- `POST /api/devices/dhcp/static_mapping` - Cadastrar mapeamento estático DHCP no pfSense (com proteção contra duplicatas)
- `GET /api/devices/dhcp/static_mapping/check` - Verificar mapeamentos DHCP existentes antes do cadastro

### **Atribuição de Usuários a Dispositivos (Novo)**
- `POST /api/devices/assignments` - Atribuir dispositivo a usuário (com verificação de permissões)
- `DELETE /api/devices/assignments/{user_id}/{device_id}` - Remover atribuição (com verificação de permissões)
- `GET /api/devices/users/{user_id}/devices` - Listar dispositivos de um usuário (com verificação de permissões)
- `GET /api/devices/devices/{device_id}/users` - Listar usuários de um dispositivo (com verificação de permissões)
- `GET /api/devices/assignments/search?query=termo` - Buscar atribuições por termo
- `GET /api/devices/assignments/statistics` - Estatísticas de atribuições

### **Dispositivos**
- `GET /api/devices/` - Listar dispositivos cadastrados

## 📝 **Exemplos de Uso**

### **Autenticação SAML CAFe**
```bash
# 1. Iniciar login SAML
curl http://127.0.0.1:8000/auth/login

# 2. Verificar status da autenticação
curl http://127.0.0.1:8000/auth/status

# 3. Verificar token (requer autenticação)
curl -H "Authorization: Bearer SEU_TOKEN_JWT" \
     http://127.0.0.1:8000/auth/verify
```

### **Gerenciamento de Dados DHCP**
```bash
# 1. Salvar dados DHCP no banco
curl -X POST http://127.0.0.1:8000/api/devices/dhcp/save \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "bc:24:11:2c:0f:31",
    "ipaddr": "10.30.30.10",
    "cid": "lubuntu-live",
    "descr": "lubuntu-live-proxmox"
  }'

# Parâmetros obrigatórios:
# - mac: Endereço MAC do dispositivo
# - ipaddr: Endereço IP do dispositivo  
# - cid: ID do cliente (será replicado para hostname)
# - descr: Descrição do dispositivo

# 2. Listar dispositivos cadastrados
curl "http://127.0.0.1:8000/api/devices/dhcp/devices?page=1&per_page=20"

# 3. Buscar dispositivos por termo
curl "http://127.0.0.1:8000/api/devices/dhcp/devices/search?query=ubuntu"

# 4. Buscar dispositivo por IP
curl http://127.0.0.1:8000/api/devices/dhcp/devices/ip/10.30.30.3

# 5. Buscar dispositivo por MAC
curl http://127.0.0.1:8000/api/devices/dhcp/devices/mac/bc:24:11:68:fb:77

# 6. Ver estatísticas
curl http://127.0.0.1:8000/api/devices/dhcp/statistics

# 7. Verificar mapeamentos existentes antes do cadastro
curl "http://127.0.0.1:8000/api/devices/dhcp/static_mapping/check?ipaddr=192.168.1.100"

# 8. Cadastrar mapeamento estático DHCP no pfSense (com proteção automática contra duplicatas)
curl -X POST http://127.0.0.1:8000/api/devices/dhcp/static_mapping \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "00:11:22:33:44:55",
    "ipaddr": "192.168.1.100",
    "cid": "device001",
    "hostname": "device-hostname",
    "descr": "Dispositivo IoT"
  }'
```

### **Atribuição de Usuários a Dispositivos**
```bash
# 1. Atribuir dispositivo a usuário (usuário comum atribuindo a si mesmo)
curl -X POST http://127.0.0.1:8000/api/devices/assignments \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "device_id": 1,
    "notes": "Dispositivo de monitoramento atribuído ao usuário",
    "assigned_by": 1
  }'

# 2. Gestor atribuindo dispositivo a outro usuário
curl -X POST http://127.0.0.1:8000/api/devices/assignments \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "device_id": 2,
    "notes": "Dispositivo atribuído pelo gestor",
    "assigned_by": 2
  }'

# 3. Listar dispositivos de um usuário (com verificação de permissão)
curl "http://127.0.0.1:8000/api/devices/users/1/devices?current_user_id=1"

# 4. Listar usuários de um dispositivo (com verificação de permissão)
curl "http://127.0.0.1:8000/api/devices/devices/1/users?current_user_id=1"

# 5. Buscar atribuições por termo
curl "http://127.0.0.1:8000/api/devices/assignments/search?query=joner"

# 6. Ver estatísticas de atribuições
curl http://127.0.0.1:8000/api/devices/assignments/statistics

# 7. Remover atribuição (com verificação de permissão)
curl -X DELETE "http://127.0.0.1:8000/api/devices/assignments/1/1?current_user_id=1"
```

### **Cadastrar Alias no pfSense (com autenticação)**
```bash
curl -X POST http://127.0.0.1:8000/api/devices/alias \
  -H "Authorization: Bearer SEU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Teste_API_IoT_EDU",
    "type": "host",
    "descr": "Teste da API IoT EDU",
    "address": ["192.168.1.100"],
    "detail": ["Teste"]
  }'
```

### **Listar Servidores DHCP (com autenticação)**
```bash
curl -H "Authorization: Bearer SEU_TOKEN_JWT" \
     http://127.0.0.1:8000/api/devices/dhcp/servers
```

## 🔧 **Configuração do CAFe**

### **Registro no CAFe**
1. Acesse https://cafe.rnp.br
2. Registre seu Service Provider (SP)
3. Configure os metadados SAML
4. Aguarde aprovação da RNP

### **Configuração SAML**
1. Execute `python generate_saml_certificates.py`
2. Configure os certificados gerados
3. Ajuste as configurações em `sp_django/settings.py`
4. Teste a autenticação

### **Configuração de Segurança**
- Use HTTPS em produção
- Configure certificados válidos
- Use tokens JWT seguros
- Implemente rate limiting

## 🐳 **Docker (Opcional)**

### **Dockerfile**
```dockerfile
FROM python:3.9
WORKDIR /app
COPY backend/ .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **docker-compose.yml**
```yaml
version: '3.8'
services:
  db:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: iot_edu
      MYSQL_USER: IoT_EDU
      MYSQL_PASSWORD: root
    ports:
      - "3306:3306"
  
  backend:
    build: .
    env_file: backend/.env
    ports:
      - "8000:8000"
    depends_on:
      - db
```

### **Executar com Docker**
```bash
docker-compose up --build
```

## 🔒 **Segurança**

### **Autenticação SAML CAFe**
- Implementa SAML 2.0
- Suporte a múltiplas instituições federadas
- Tokens JWT para sessões seguras
- Certificados X.509

### **Autenticação OAuth2 CAFe**
- Implementa OAuth2/OpenID Connect
- Suporte a múltiplas instituições federadas
- Tokens JWT para sessões seguras

### **API pfSense**
- Autenticação via API Key
- Comunicação HTTPS
- Validação de certificados SSL

### **Variáveis de Ambiente**
- Todas as credenciais são carregadas do arquivo `.env`
- O arquivo `.env` não deve ser commitado no repositório
- Use `python-dotenv` para carregar variáveis automaticamente

## 🚨 **Troubleshooting**

### **Problemas Comuns**

1. **Erro de certificados SAML**
   - Verifique se os certificados foram gerados
   - Confirme as permissões dos arquivos
   - Teste a validade dos certificados

2. **Erro de autenticação CAFe**
   - Verifique o registro no CAFe
   - Confirme os metadados SAML
   - Teste a conectividade com o CAFe

3. **Erro de conexão com pfSense**
   - Verifique se a API REST está habilitada
   - Confirme as credenciais no arquivo `.env`
   - Teste a conectividade de rede

4. **Erro de banco de dados**
   - Verifique as credenciais MySQL
   - Confirme se as tabelas foram criadas
   - Teste a conexão com o banco

### **Logs e Debug**
- Use `uvicorn` com `--reload` para desenvolvimento
- Verifique os logs do servidor para erros
- Teste endpoints individualmente
- Use o endpoint `/auth/status` para verificar autenticação

## 🔐 **Sistema de Permissões**

O sistema implementa dois níveis de permissão para usuários:

### **👤 Usuário Comum (USER)**
- Pode gerenciar apenas seus próprios dispositivos
- Não pode ver ou gerenciar dispositivos de outros usuários
- Restrições aplicadas em todos os endpoints de atribuição

### **👨‍💼 Gestor (MANAGER)**
- Pode gerenciar todos os dispositivos de todos os usuários
- Acesso total ao sistema
- Pode atribuir/remover dispositivos de qualquer usuário

### **Usuários de Teste**
- **Usuário Comum**: `usuario.teste@unipampa.edu.br` (ID: 1)
- **Gestor**: `gestor.teste@unipampa.edu.br` (ID: 2)

Para mais detalhes, consulte o [Guia Completo de Permissões](GUIA_PERMISSOES_USUARIOS.md).

## 📚 **Documentação Adicional**

- `README-pfsense-api-v2.md` - Documentação completa da API pfSense
- `README-firewall-rules.md` - Guia de regras de firewall
- `GUIA_PERMISSOES_USUARIOS.md` - Guia completo do sistema de permissões
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Django SAML2 Documentation](https://djangosaml2.readthedocs.io/)
- [CAFe Documentation](https://cafe.rnp.br/documentacao)
- [pfSense API Documentation](https://docs.netgate.com/pfsense/en/latest/development/api.html)

## 🤝 **Contribuição**

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

---

**Desenvolvido para ambientes acadêmicos com foco em segurança e integração IoT.** 🎓🔐 