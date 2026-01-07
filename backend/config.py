import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
# Especifica o caminho para garantir que o arquivo seja encontrado
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Configurações de autenticação CAFe (OAuth2/OpenID Connect)
# As configurações são carregadas do arquivo .env para maior segurança
CAFE_CLIENT_ID = os.getenv("CAFE_CLIENT_ID")
CAFE_CLIENT_SECRET = os.getenv("CAFE_CLIENT_SECRET")
CAFE_AUTH_URL = os.getenv("CAFE_AUTH_URL", "https://sso.cafe.unipampa.edu.br/auth/realms/CAFe/protocol/openid-connect/auth")
CAFE_TOKEN_URL = os.getenv("CAFE_TOKEN_URL", "https://sso.cafe.unipampa.edu.br/auth/realms/CAFe/protocol/openid-connect/token")
CAFE_USERINFO_URL = os.getenv("CAFE_USERINFO_URL", "https://sso.cafe.unipampa.edu.br/auth/realms/CAFe/protocol/openid-connect/userinfo")
CAFE_REDIRECT_URI = os.getenv("CAFE_REDIRECT_URI", "http://localhost:8000/auth/callback")

# Configurações de autenticação Google OAuth2
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/callback")

# Configurações JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sua_chave_secreta_jwt_muito_segura_aqui")

# Configurações do banco de dados MySQL
MYSQL_USER = os.getenv("MYSQL_USER", "IoT_EDU")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_DB = os.getenv("MYSQL_DB", "iot_edu")

# Configurações da API do pfSense
PFSENSE_API_URL = os.getenv("PFSENSE_API_URL")
PFSENSE_API_KEY = os.getenv("PFSENSE_API_KEY")
PFSENSE_API_SECRET = os.getenv("PFSENSE_API_SECRET")

# Configurações do Zeek Network Security Monitor
ZEEK_API_URL = os.getenv("ZEEK_API_URL", "http://192.168.100.1/zeek-api")
ZEEK_API_TOKEN = os.getenv("ZEEK_API_TOKEN")

# Configurações de atribuição automática de IP
IP_RANGE_START = os.getenv("IP_RANGE_START", "192.168.100.1")
IP_RANGE_END = os.getenv("IP_RANGE_END", "192.168.100.254")
IP_RANGE_EXCLUDED = os.getenv("IP_RANGE_EXCLUDED", "192.168.100.1,192.168.100.100,192.168.100.200")



# Observação:
# Para usar este sistema, crie um arquivo .env na pasta backend/ com as configurações necessárias.
# Exemplo de arquivo .env:
# CAFE_CLIENT_ID=seu_client_id_aqui
# CAFE_CLIENT_SECRET=seu_client_secret_aqui
# MYSQL_PASSWORD=sua_senha_aqui
# PFSENSE_API_KEY=sua_api_key_aqui
# ZEEK_API_TOKEN=seu_token_zeek_aqui
# 
# O arquivo .env deve ser adicionado ao .gitignore para não ser commitado no repositório. 