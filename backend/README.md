# 🚀 API IoT-EDU Backend

Sistema de gerenciamento de dispositivos IoT para ambiente educacional com integração pfSense.

## 📁 Estrutura do Projeto

```
backend/
├── 📁 auth/                    # Autenticação SAML/CAFe
├── 📁 config/                  # Configurações do sistema
├── 📁 db/                      # Modelos e sessão do banco de dados
├── 📁 deploy/                  # Scripts de deploy e configuração
├── 📁 docs/                    # Documentação e guias
├── 📁 models/                  # Modelos de dados
├── 📁 postman/                 # Coleções Postman para testes
├── 📁 scripts/                 # Scripts utilitários
├── 📁 services_firewalls/      # Serviços de integração pfSense
├── 📁 services_scanners/       # Serviços de scanner
├── 📁 testes/                  # Testes automatizados
├── 📄 main.py                  # Aplicação FastAPI principal
├── 📄 config.py                # Configurações centralizadas
├── 📄 requirements.txt         # Dependências Python
├── 📄 start_server.py          # Script de inicialização
└── 📄 env_example.txt          # Exemplo de variáveis de ambiente
```

## 🎯 Funcionalidades Principais

### 🔐 Autenticação e Autorização
- **SAML CAFe**: Integração com sistema de autenticação federada
- **OAuth2 CAFe**: Autenticação OAuth2
- **JWT**: Tokens de acesso
- **Controle de Permissões**: Usuários (USER) e Gestores (MANAGER)

### 🌐 Integração pfSense
- **DHCP Management**: Cadastro e gerenciamento de mapeamentos estáticos
- **Alias Management**: Criação e gerenciamento de aliases de rede
- **Firewall Rules**: Configuração de regras de firewall
- **API v2**: Integração com API oficial do pfSense

### 📊 Gerenciamento de Dispositivos
- **Device Registration**: Cadastro de dispositivos IoT
- **User Assignment**: Atribuição de dispositivos a usuários
- **IP Management**: Controle de endereços IP
- **Status Monitoring**: Monitoramento de status dos dispositivos

## 🚀 Início Rápido

### 1. Configuração do Ambiente

```bash
# Clonar o repositório
git clone <repository-url>
cd API-IoT-EDU/backend

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp env_example.txt .env
# Editar .env com suas configurações
```

### 2. Configuração do Banco de Dados

```bash
# Executar migrações
python scripts/migrate_add_permission.py

# Criar usuários de teste
python scripts/create_test_users.py

# Criar aliases e regras iniciais (recomendado)
python scripts/setup_initial_aliases_and_rules.py
```

**Nota:** O script `setup_initial_aliases_and_rules.py` cria automaticamente:
- Aliases "Autorizados" e "Bloqueados" para cada instituição
- Regras de firewall básicas no pfSense
- Sincroniza regras com o banco de dados

### 3. Iniciar o Servidor

   ```bash
# Iniciar servidor de desenvolvimento
python start_server.py

# Ou usar o script de reinicialização
python scripts/restart_server.py
```

## 📚 Documentação

### 📖 Guias Disponíveis (em `docs/`)

- **📋 Guias de Endpoints**:
  - `GUIA_ENDPOINT_TODOS_DISPOSITIVOS.md` - Listagem de todos os dispositivos
  - `GUIA_DHCP_STATIC_MAPPING.md` - Mapeamentos DHCP estáticos
  - `GUIA_ENDERECOS_IP.md` - Gerenciamento de endereços IP
  - `GUIA_PERMISSOES_USUARIOS.md` - Sistema de permissões

- **🔧 Guias Postman**:
  - `GUIA_POSTMAN_DHCP_SAVE.md` - Testes de salvamento DHCP
  - `GUIA_POSTMAN_DHCP_STATIC_MAPPING.md` - Testes de mapeamentos
  - `GUIA_POSTMAN_PERMISSOES.md` - Testes de permissões
  - `GUIA_POSTMAN_ENDERECOS_IP.md` - Testes de endereços IP
  - `GUIA_ADICIONAR_IPS_ALIASES.md` - Adição de IPs em aliases

- **📊 Documentação Técnica**:
  - `README-pfsense-api-v2.md` - Documentação da API pfSense
  - `README-firewall-rules.md` - Regras de firewall
  - `DOCUMENTACAO_WIREFRAME.md` - Documentação do wireframe

### 🎨 Wireframe (em `docs/`)

- `wireframe_iot_management.html` - Interface de gerenciamento IoT

## 🧪 Testes

### 📁 Coleções Postman (em `postman/`)

- `IoT-EDU_DHCP_Save.postman_collection.json`
- `IoT-EDU_DHCP_Static_Mapping.postman_collection.json`
- `IoT-EDU_Permission_Tests.postman_collection.json`
- `POSTMAN_COLLECTION_ALIASES.json`
- `test_permissions_report.json`

### 🐍 Scripts de Teste (em `testes/`)

```bash
# Executar testes automatizados
cd testes
python test_all_devices_endpoint.py
```

## 🔧 Scripts Utilitários (em `scripts/`)

- `create_test_users.py` - Criar usuários de teste
- `migrate_add_permission.py` - Migração de permissões
- `generate_saml_certificates.py` - Gerar certificados SAML
- `restart_server.py` - Reiniciar servidor
- `sync_pfsense_ids.py` - Sincronizar IDs do pfSense
- `verify_fix.py` - Verificar e corrigir dados
- `quick_compare_ids.py` - Comparar IDs rapidamente
- `demo_ip_management.py` - Demonstração de gerenciamento IP
- `verificar_aliases.py` - Verificar aliases

## 🌐 Endpoints Implementados

### 🏠 Endpoints Principais
- `GET /` - Página inicial da API
- `GET /health` - Verificação de saúde da API
- `GET /docs` - Documentação interativa (Swagger)

### 🔐 Autenticação
- `GET /auth/login` - Iniciar login SAML CAFe
- `GET /auth/callback` - Callback SAML CAFe
- `GET /auth/logout` - Logout SAML CAFe
- `GET /auth/verify` - Verificar token JWT
- `GET /auth/metadata` - Metadados SAML
- `GET /auth/status` - Status da autenticação
- `GET /api/auth/login` - Iniciar autenticação OAuth2 CAFe
- `GET /api/auth/callback` - Callback OAuth2 CAFe

### 📱 Dispositivos e DHCP
- `GET /api/devices/` - Listar dispositivos cadastrados
- `GET /api/devices/devices` - Listar todos os dispositivos (Gestores)
- `GET /api/devices/users/{user_id}/devices` - Dispositivos de um usuário
- `GET /api/devices/devices/{device_id}/users` - Usuários de um dispositivo
- `POST /api/devices/dhcp/save` - Salvar dados DHCP no banco de dados (com rollback automático se pfSense falhar)
- `GET /api/devices/dhcp/servers` - Listar servidores DHCP
- `GET /api/devices/dhcp/static_mapping` - Listar mapeamentos estáticos DHCP
- `POST /api/devices/dhcp/static_mapping` - Cadastrar mapeamento estático DHCP
- `PATCH /api/devices/dhcp/static_mapping` - Atualizar mapeamento estático DHCP no pfSense e banco de dados local
- `DELETE /api/devices/dhcp/static_mapping` - Excluir mapeamento estático DHCP no pfSense e banco de dados local
- `POST /api/devices/dhcp/sync` - Sincronizar IDs do pfSense com o banco de dados local
- `GET /api/devices/dhcp/static_mapping/check` - Verificar mapeamentos DHCP existentes
- `GET /api/devices/dhcp/devices` - Listar dispositivos cadastrados no banco
- `GET /api/devices/dhcp/devices/search` - Buscar dispositivos por termo
- `GET /api/devices/dhcp/devices/ip/{ipaddr}` - Buscar dispositivo por IP
- `GET /api/devices/dhcp/devices/mac/{mac}` - Buscar dispositivo por MAC
- `GET /api/devices/dhcp/statistics` - Estatísticas de dispositivos
- `GET /api/devices/dhcp/ip-addresses` - Listar endereços IP usados e livres

### 👥 Usuários e Permissões
- `POST /api/devices/assignments` - Atribuir dispositivo a usuário
- `DELETE /api/devices/assignments/{user_id}/{device_id}` - Remover atribuição
- `GET /api/devices/assignments/search` - Buscar atribuições por termo
- `GET /api/devices/assignments/statistics` - Estatísticas de atribuições

### 🔗 Aliases
- `POST /api/devices/alias` - Cadastrar alias no pfSense (legado)
- `GET /api/devices/aliases` - Listar todos os aliases ou buscar por nome
- `GET /api/devices/aliases/{name}` - Obter alias específico
- `POST /api/devices/aliases-db/save` - Salvar aliases do pfSense no banco
- `GET /api/devices/aliases-db` - Listar aliases do banco de dados
- `GET /api/devices/aliases-db/search` - Buscar aliases por termo
- `GET /api/devices/aliases-db/statistics` - Estatísticas de aliases
- `POST /api/devices/aliases-db/create` - Criar novo alias
- `PATCH /api/devices/aliases-db/{alias_name}` - Atualizar alias existente
- `POST /api/devices/aliases-db/{alias_name}/add-addresses` - Adicionar endereços a um alias
- `GET /api/devices/aliases-db/{alias_name}` - Obter alias específico por nome

## 🔧 Configuração

### Variáveis de Ambiente (`.env`)

```env
# Database
DATABASE_URL=mysql+pymysql://user:pass@localhost/iot_edu

# pfSense API
PFSENSE_API_URL=https://your-pfsense.com/api/v2/
PFSENSE_API_KEY=your-api-key

# SAML CAFe
CAFE_SAML_ENTITY_ID=your-entity-id
CAFE_SAML_CERT_PATH=path/to/cert.pem
CAFE_SAML_KEY_PATH=path/to/key.pem

# Server
HOST=127.0.0.1
PORT=8000
DEBUG=true
```

## 🚀 Deploy

### 📁 Scripts de Deploy (em `deploy/`)

- `apache/` - Configurações Apache
- `systemd/` - Serviços systemd
- `scripts/` - Scripts de deploy
- `README.md` - Guia de deploy
- `SOLUTION_GUIDE.md` - Soluções de problemas
- `TESTING_GUIDE.md` - Guia de testes
- `TROUBLESHOOTING.md` - Resolução de problemas

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte e dúvidas:
- 📧 Email: suporte@iotedu.com
- 📖 Documentação: Consulte os guias em `docs/`
- 🐛 Issues: Abra uma issue no repositório

---

**Desenvolvido para o ambiente educacional IoT-EDU** 🎓
