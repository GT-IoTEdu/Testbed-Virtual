# Deploy IoT-EDU com Apache e SAML CAFe

Este documento descreve o processo completo de deploy da aplicação IoT-EDU usando Apache, Gunicorn e FastAPI com autenticação SAML CAFe.

## 📋 **Pré-requisitos**

- Ubuntu 20.04+ ou Debian 11+
- Python 3.9+
- Apache 2.4+
- Certificados SSL válidos
- Acesso root/sudo

## 🚀 **Deploy Rápido**

### 1. Clone o repositório
```bash
git clone https://github.com/GT-IoTEdu/API_IoT_EDU.git
cd API-IoTEdu
```

### 2. Execute o script de deploy
```bash
# Para desenvolvimento
chmod +x backend/deploy/scripts/deploy.sh
./backend/deploy/scripts/deploy.sh dev

# Para produção
./backend/deploy/scripts/deploy.sh prod
```

## 📁 **Estrutura de Deploy**

```
backend/deploy/
├── apache/
│   └── iot_edu.conf          # Configuração Apache
├── systemd/
│   ├── gunicorn.service      # Serviço Django SAML
│   └── fastapi.service       # Serviço FastAPI
├── scripts/
│   ├── deploy.sh             # Script de deploy completo
│   └── setup_apache.sh       # Configuração Apache
└── README.md                 # Esta documentação
```

## ⚙️ **Configuração Manual**

### 1. **Instalar Dependências do Sistema**

```bash
# Atualizar sistema
sudo apt-get update
sudo apt-get upgrade -y

# Instalar dependências
sudo apt-get install -y python3 python3-pip python3-venv
sudo apt-get install -y apache2 apache2-utils
sudo apt-get install -y libapache2-mod-proxy-html
sudo apt-get install -y openssl
```

### 2. **Configurar Apache**

```bash
# Executar script de configuração Apache
chmod +x backend/deploy/scripts/setup_apache.sh
./backend/deploy/scripts/setup_apache.sh
```

### 3. **Configurar Certificados SSL**

```bash
# Copiar certificados para o local correto
sudo cp certificado.crt /etc/ssl/certs/cafeexpresso.rnp.br.cer
sudo cp chave_privada.key /etc/ssl/private/cafeexpresso.key
sudo cp chain.crt /etc/ssl/certs/cafeexpresso.rnp.br.chain

# Configurar permissões
sudo chmod 644 /etc/ssl/certs/cafeexpresso.rnp.br.cer
sudo chmod 600 /etc/ssl/private/cafeexpresso.key
sudo chmod 644 /etc/ssl/certs/cafeexpresso.rnp.br.chain
```

### 4. **Configurar Ambiente Python**

```bash
# Criar diretório do projeto
sudo mkdir -p /opt/iot_edu
sudo chown www-data:www-data /opt/iot_edu

# Copiar código
sudo cp -r . /opt/iot_edu/
sudo chown -R www-data:www-data /opt/iot_edu

# Criar ambiente virtual
cd /opt/iot_edu
sudo -u www-data python3 -m venv venv
sudo -u www-data venv/bin/pip install --upgrade pip
sudo -u www-data venv/bin/pip install -r backend/requirements.txt
```

### 5. **Configurar Variáveis de Ambiente**

```bash
# Copiar arquivo de exemplo
sudo -u www-data cp backend/.env.example backend/.env

# Editar configurações
sudo -u www-data nano backend/.env
```

**Exemplo de `.env`:**
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
CAFE_REDIRECT_URI=https://iot-edu.cafeexpresso.rnp.br/auth/callback

# Configurações da API do pfSense
PFSENSE_API_URL=https://iotedu.dev.ufrgs.br/api/v2/
PFSENSE_API_KEY=sua_api_key_pfsense

# Configurações JWT para SAML
JWT_SECRET_KEY=sua_chave_secreta_jwt_muito_segura
```

### 6. **Configurar Banco de Dados**

```bash
cd /opt/iot_edu/backend
sudo -u www-data venv/bin/python manage.py migrate
sudo -u www-data venv/bin/python manage.py collectstatic --noinput
```

### 7. **Gerar Certificados SAML**

```bash
cd /opt/iot_edu/backend
sudo -u www-data venv/bin/python generate_saml_certificates.py
```

### 8. **Configurar Serviços Systemd**

```bash
# Copiar arquivos de serviço
sudo cp backend/deploy/systemd/gunicorn.service /etc/systemd/system/
sudo cp backend/deploy/systemd/fastapi.service /etc/systemd/system/

# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar serviços
sudo systemctl enable gunicorn.service
sudo systemctl enable fastapi.service
```

### 9. **Iniciar Serviços**

```bash
# Iniciar serviços
sudo systemctl start gunicorn.service
sudo systemctl start fastapi.service
sudo systemctl restart apache2

# Verificar status
sudo systemctl status gunicorn.service
sudo systemctl status fastapi.service
sudo systemctl status apache2
```

## 🔧 **Configurações Específicas**

### **Configuração Gunicorn (Django SAML)**

Arquivo: `/opt/iot_edu/backend/config/gunicorn/prod.py`

```python
"""Gunicorn *production* config file"""

wsgi_app = "sp_django.wsgi:application"
loglevel = "info"
workers = 4
bind = "unix:/run/gunicorn.sock"
reload = False
accesslog = errorlog = "/var/log/gunicorn/prod.log"
capture_output = True
pidfile = "/var/run/gunicorn/prod.pid"
daemon = True
timeout = 120
max_requests = 1000
max_requests_jitter = 100
```

### **Configuração Apache**

Arquivo: `/etc/apache2/sites-available/iot_edu.conf`

```apache
# Configuração para HTTPS
<VirtualHost *:443>
    ServerName iot-edu.cafeexpresso.rnp.br
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/cafeexpresso.rnp.br.cer
    SSLCertificateKeyFile /etc/ssl/private/cafeexpresso.key
    
    # Proxy para FastAPI
    ProxyPass /api/ http://127.0.0.1:8000/api/
    ProxyPassReverse /api/ http://127.0.0.1:8000/api/
    
    # Proxy para SAML
    ProxyPass /saml2/ http://127.0.0.1:8000/saml2/
    ProxyPassReverse /saml2/ http://127.0.0.1:8000/saml2/
    
    # Proxy para autenticação
    ProxyPass /auth/ http://127.0.0.1:8000/auth/
    ProxyPassReverse /auth/ http://127.0.0.1:8000/auth/
</VirtualHost>
```

## 🚨 **Troubleshooting**

### **Problemas Comuns**

1. **Erro de permissões no banco de dados**
   ```bash
   sudo chown www-data:www-data /opt/iot_edu/db.sqlite3
   sudo chmod 664 /opt/iot_edu/db.sqlite3
   ```

2. **Erro de certificados SSL**
   ```bash
   sudo apache2ctl configtest
   sudo systemctl status apache2
   ```

3. **Erro de serviços não iniciando**
   ```bash
   sudo journalctl -u gunicorn.service -f
   sudo journalctl -u fastapi.service -f
   ```

4. **Erro de módulos Apache**
   ```bash
   sudo a2enmod ssl proxy proxy_http headers rewrite
   sudo systemctl restart apache2
   ```

### **Logs Importantes**

- **Apache**: `/var/log/apache2/iot_edu_ssl_error.log`
- **Gunicorn**: `/var/log/gunicorn/prod.log`
- **FastAPI**: `sudo journalctl -u fastapi.service -f`
- **Systemd**: `sudo journalctl -u gunicorn.service -f`

### **Comandos Úteis**

```bash
# Verificar status dos serviços
sudo systemctl status gunicorn.service fastapi.service apache2

# Reiniciar serviços
sudo systemctl restart gunicorn.service fastapi.service apache2

# Ver logs em tempo real
sudo tail -f /var/log/apache2/iot_edu_ssl_error.log
sudo journalctl -u gunicorn.service -f

# Testar configuração Apache
sudo apache2ctl configtest

# Verificar portas em uso
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

## 🔒 **Segurança**

### **Configurações de Segurança Apache**

```apache
# Headers de segurança
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"

# Configurações SSL
SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
SSLCipherSuite ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384
SSLHonorCipherOrder on
SSLCompression off
```

### **Firewall**

```bash
# Configurar UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 📊 **Monitoramento**

### **Health Checks**

```bash
# Testar endpoints
curl -k https://localhost/health
curl -k https://localhost/saml2/metadata/
curl -k https://localhost/api/devices/dhcp/servers
```

### **Métricas**

```bash
# Verificar uso de recursos
htop
df -h
free -h

# Verificar logs de acesso
sudo tail -f /var/log/apache2/iot_edu_ssl_access.log
```

## 🔄 **Atualizações**

### **Deploy de Atualizações**

```bash
# 1. Fazer backup
sudo cp -r /opt/iot_edu /opt/iot_edu_backup_$(date +%Y%m%d)

# 2. Atualizar código
cd /opt/iot_edu
sudo git pull

# 3. Atualizar dependências
sudo -u www-data venv/bin/pip install -r backend/requirements.txt

# 4. Executar migrações
cd backend
sudo -u www-data venv/bin/python manage.py migrate

# 5. Reiniciar serviços
sudo systemctl restart gunicorn.service fastapi.service apache2
```

## 📚 **Documentação Adicional**

- [Apache Documentation](https://httpd.apache.org/docs/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Django SAML2 Documentation](https://djangosaml2.readthedocs.io/)
- [CAFe Documentation](https://cafe.rnp.br/documentacao)

---

**Deploy configurado com sucesso!** 🚀🔐✨ 