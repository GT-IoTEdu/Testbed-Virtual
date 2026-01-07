#!/bin/bash
# Script de Deploy para IoT-EDU com SAML CAFe
# Uso: ./deploy.sh [dev|prod]

set -e

# Configurações
PROJECT_NAME="iot_edu"
PROJECT_PATH="/opt/iot_edu"
VENV_PATH="$PROJECT_PATH/venv"
BACKEND_PATH="$PROJECT_PATH/backend"
USER="www-data"
GROUP="www-data"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Verificar se é root
if [[ $EUID -eq 0 ]]; then
   error "Este script não deve ser executado como root"
fi

# Verificar argumentos
ENVIRONMENT=${1:-prod}
if [[ ! "$ENVIRONMENT" =~ ^(dev|prod)$ ]]; then
    error "Ambiente deve ser 'dev' ou 'prod'"
fi

log "Iniciando deploy do IoT-EDU ($ENVIRONMENT)"

# 1. Criar diretórios necessários
log "Criando diretórios..."
sudo mkdir -p /opt/iot_edu
sudo mkdir -p /var/log/gunicorn
sudo mkdir -p /var/run/gunicorn
sudo mkdir -p /var/log/iot_edu

# 2. Configurar permissões
log "Configurando permissões..."
sudo chown -R $USER:$GROUP /opt/iot_edu
sudo chown -R $USER:$GROUP /var/log/gunicorn
sudo chown -R $USER:$GROUP /var/run/gunicorn
sudo chown -R $USER:$GROUP /var/log/iot_edu

# 3. Copiar arquivos do projeto
log "Copiando arquivos do projeto..."
sudo cp -r . /opt/iot_edu/backend/
sudo chown -R $USER:$GROUP /opt/iot_edu

# 4. Criar ambiente virtual
log "Configurando ambiente virtual..."
if [ ! -d "$VENV_PATH" ]; then
    sudo -u $USER python3 -m venv $VENV_PATH
fi

# 5. Instalar dependências
log "Instalando dependências..."
sudo -u $USER $VENV_PATH/bin/pip install --upgrade pip
sudo -u $USER $VENV_PATH/bin/pip install -r $BACKEND_PATH/requirements.txt

# 6. Configurar variáveis de ambiente
log "Configurando variáveis de ambiente..."
if [ ! -f "$BACKEND_PATH/.env" ]; then
    sudo -u $USER cp $BACKEND_PATH/.env.example $BACKEND_PATH/.env
    warning "Arquivo .env criado. Configure as variáveis necessárias."
fi

# 7. Configurar banco de dados
log "Configurando banco de dados..."
cd $BACKEND_PATH
sudo -u $USER $VENV_PATH/bin/python manage.py migrate
sudo -u $USER $VENV_PATH/bin/python manage.py collectstatic --noinput

# 8. Gerar certificados SAML (se necessário)
log "Verificando certificados SAML..."
if [ ! -f "../certificates/mycert.pem" ] || [ ! -f "../certificates/mykey.pem" ]; then
    log "Gerando certificados SAML..."
    cd $BACKEND_PATH
    sudo -u $USER $VENV_PATH/bin/python generate_saml_certificates.py
fi

# 9. Configurar Apache
log "Configurando Apache..."
sudo cp $BACKEND_PATH/deploy/apache/iot_edu.conf /etc/apache2/sites-available/
sudo a2ensite iot_edu.conf

# Habilitar módulos necessários
sudo a2enmod ssl
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod headers
sudo a2enmod rewrite

# 10. Configurar serviços systemd
log "Configurando serviços systemd..."

# Serviço Gunicorn (Django SAML)
sudo cp $BACKEND_PATH/deploy/systemd/gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gunicorn.service

# Serviço FastAPI (API)
sudo cp $BACKEND_PATH/deploy/systemd/fastapi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fastapi.service

# 11. Iniciar serviços
log "Iniciando serviços..."
sudo systemctl start gunicorn.service
sudo systemctl start fastapi.service
sudo systemctl restart apache2

# 12. Verificar status
log "Verificando status dos serviços..."
sleep 5

if sudo systemctl is-active --quiet gunicorn.service; then
    log "✅ Gunicorn está rodando"
else
    error "❌ Gunicorn falhou ao iniciar"
fi

if sudo systemctl is-active --quiet fastapi.service; then
    log "✅ FastAPI está rodando"
else
    error "❌ FastAPI falhou ao iniciar"
fi

if sudo systemctl is-active --quiet apache2; then
    log "✅ Apache está rodando"
else
    error "❌ Apache falhou ao iniciar"
fi

# 13. Testar endpoints
log "Testando endpoints..."
sleep 3

# Testar health check
if curl -s -f https://localhost/health > /dev/null; then
    log "✅ Health check funcionando"
else
    warning "⚠️ Health check falhou"
fi

# Testar SAML metadata
if curl -s -f https://localhost/saml2/metadata/ > /dev/null; then
    log "✅ SAML metadata funcionando"
else
    warning "⚠️ SAML metadata falhou"
fi

log "🎉 Deploy concluído com sucesso!"
log ""
log "📋 Informações importantes:"
log "   - URL: https://iot-edu.cafeexpresso.rnp.br"
log "   - API Docs: https://iot-edu.cafeexpresso.rnp.br/docs"
log "   - SAML Login: https://iot-edu.cafeexpresso.rnp.br/saml2/login/"
log "   - Admin Django: https://iot-edu.cafeexpresso.rnp.br/admin/"
log ""
log "🔧 Comandos úteis:"
log "   - Ver logs: sudo journalctl -u gunicorn.service -f"
log "   - Reiniciar: sudo systemctl restart gunicorn.service fastapi.service"
log "   - Status: sudo systemctl status gunicorn.service fastapi.service"
log ""
log "⚠️ Lembre-se de:"
log "   1. Configurar o arquivo .env com as credenciais corretas"
log "   2. Registrar o SP no CAFe (https://cafe.rnp.br)"
log "   3. Configurar os certificados SSL"
log "   4. Testar a autenticação SAML" 