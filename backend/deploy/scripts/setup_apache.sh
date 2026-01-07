#!/bin/bash
# Script para configurar Apache para IoT-EDU
# Uso: ./setup_apache.sh

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

log "Configurando Apache para IoT-EDU..."

# 1. Instalar Apache e módulos necessários
log "Instalando Apache e módulos..."
sudo apt-get update
sudo apt-get install -y apache2 apache2-utils

# 2. Habilitar módulos necessários
log "Habilitando módulos Apache..."
sudo a2enmod ssl
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod headers
sudo a2enmod rewrite
sudo a2enmod socache_shmcb

# 3. Desabilitar site padrão
log "Desabilitando site padrão..."
sudo a2dissite 000-default.conf

# 4. Configurar SSL
log "Configurando SSL..."
sudo mkdir -p /etc/ssl/private
sudo mkdir -p /etc/ssl/certs

# Verificar se os certificados existem
if [ ! -f "/etc/ssl/certs/cafeexpresso.rnp.br.cer" ]; then
    warning "Certificado SSL não encontrado. Configure os certificados SSL:"
    warning "   - /etc/ssl/certs/cafeexpresso.rnp.br.cer"
    warning "   - /etc/ssl/private/cafeexpresso.key"
    warning "   - /etc/ssl/certs/cafeexpresso.rnp.br.chain"
fi

# 5. Configurar virtual host
log "Configurando virtual host..."
sudo cp backend/deploy/apache/iot_edu.conf /etc/apache2/sites-available/
sudo a2ensite iot_edu.conf

# 6. Configurar segurança
log "Configurando segurança Apache..."

# Criar arquivo de configuração de segurança
sudo tee /etc/apache2/conf-available/security.conf > /dev/null <<EOF
# Configurações de segurança Apache
ServerTokens Prod
ServerSignature Off
TraceEnable Off

# Headers de segurança
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
Header always set Referrer-Policy "strict-origin-when-cross-origin"

# Configurações SSL
SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
SSLCipherSuite ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384
SSLHonorCipherOrder on
SSLCompression off
SSLUseStapling on
SSLStaplingCache shmcb:/var/run/ocsp(128000)
EOF

sudo a2enconf security

# 7. Configurar logs
log "Configurando logs..."
sudo mkdir -p /var/log/iot_edu
sudo chown www-data:www-data /var/log/iot_edu

# 8. Testar configuração
log "Testando configuração Apache..."
if sudo apache2ctl configtest; then
    log "✅ Configuração Apache válida"
else
    error "❌ Configuração Apache inválida"
fi

# 9. Reiniciar Apache
log "Reiniciando Apache..."
sudo systemctl restart apache2

# 10. Verificar status
log "Verificando status Apache..."
if sudo systemctl is-active --quiet apache2; then
    log "✅ Apache está rodando"
else
    error "❌ Apache falhou ao iniciar"
fi

# 11. Configurar firewall (se necessário)
log "Configurando firewall..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    log "✅ Regras de firewall configuradas"
fi

log "🎉 Configuração Apache concluída!"
log ""
log "📋 Próximos passos:"
log "   1. Configure os certificados SSL"
log "   2. Teste o acesso HTTPS"
log "   3. Configure o DNS para apontar para este servidor"
log "   4. Teste a autenticação SAML"
log ""
log "🔧 Comandos úteis:"
log "   - Ver logs: sudo tail -f /var/log/apache2/iot_edu_ssl_error.log"
log "   - Reiniciar: sudo systemctl restart apache2"
log "   - Status: sudo systemctl status apache2" 