# Guia de Solução - Problema de Proxy Reverso

## 🔍 **Problema Identificado**

✅ **FastAPI está funcionando localmente** - `http://127.0.0.1:8000/health` retorna 200
❌ **Proxy reverso não está configurado** - Endpoints externos retornam 404

## 🎯 **Diagnóstico Confirmado**

O FastAPI está rodando corretamente na porta 8000, mas o Apache não está configurado para fazer proxy reverso para o FastAPI. Apenas o Django SAML está sendo servido.

## 🔧 **Soluções**

### **Solução 1: Verificar Configuração do Apache**

Execute no servidor:

```bash
# 1. Verificar se o arquivo de configuração existe
sudo ls -la /etc/apache2/sites-available/iot_edu.conf

# 2. Verificar se o site está habilitado
sudo a2query -s

# 3. Verificar se os módulos proxy estão habilitados
sudo a2query -m proxy
sudo a2query -m proxy_http

# 4. Verificar configuração do Apache
sudo apache2ctl configtest
```

### **Solução 2: Configurar Proxy Reverso**

Se o arquivo de configuração não existir ou estiver incorreto:

```bash
# 1. Copiar configuração do Apache
sudo cp backend/deploy/apache/iot_edu.conf /etc/apache2/sites-available/

# 2. Habilitar módulos necessários
sudo a2enmod ssl
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod headers
sudo a2enmod rewrite

# 3. Habilitar o site
sudo a2ensite iot_edu.conf

# 4. Desabilitar site padrão (se necessário)
sudo a2dissite 000-default.conf

# 5. Testar configuração
sudo apache2ctl configtest

# 6. Reiniciar Apache
sudo systemctl restart apache2
```

### **Solução 3: Verificar Conteúdo da Configuração**

O arquivo `/etc/apache2/sites-available/iot_edu.conf` deve conter:

```apache
<VirtualHost *:80>
    ServerName sp-python.cafeexpresso.rnp.br
    Redirect permanent / https://sp-python.cafeexpresso.rnp.br/
</VirtualHost>

<VirtualHost *:443>
    ServerName sp-python.cafeexpresso.rnp.br
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/sp-python.cafeexpresso.rnp.br.crt
    SSLCertificateKeyFile /etc/ssl/private/sp-python.cafeexpresso.rnp.br.key
    
    # Security Headers
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    
    # Django SAML (porta 8001)
    ProxyPass /saml2/ http://127.0.0.1:8001/saml2/
    ProxyPassReverse /saml2/ http://127.0.0.1:8001/saml2/
    
    # FastAPI (porta 8000)
    ProxyPass /api/ http://127.0.0.1:8000/api/
    ProxyPassReverse /api/ http://127.0.0.1:8000/api/
    
    ProxyPass /health http://127.0.0.1:8000/health
    ProxyPassReverse /health http://127.0.0.1:8000/health
    
    ProxyPass /docs http://127.0.0.1:8000/docs
    ProxyPassReverse /docs http://127.0.0.1:8000/docs
    
    ProxyPass /openapi.json http://127.0.0.1:8000/openapi.json
    ProxyPassReverse /openapi.json http://127.0.0.1:8000/openapi.json
    
    ProxyPass /auth/ http://127.0.0.1:8000/auth/
    ProxyPassReverse /auth/ http://127.0.0.1:8000/auth/
    
    # Django (porta 8001) - fallback
    ProxyPass / http://127.0.0.1:8001/
    ProxyPassReverse / http://127.0.0.1:8001/
    
    # Logs
    ErrorLog ${APACHE_LOG_DIR}/iot_edu_ssl_error.log
    CustomLog ${APACHE_LOG_DIR}/iot_edu_ssl_access.log combined
</VirtualHost>
```

### **Solução 4: Verificar Portas dos Serviços**

```bash
# Verificar se os serviços estão rodando nas portas corretas
sudo netstat -tlnp | grep -E ':(8000|8001)'

# Verificar status dos serviços
sudo systemctl status fastapi.service
sudo systemctl status gunicorn.service
```

### **Solução 5: Testar Proxy Localmente**

```bash
# Testar se o proxy está funcionando
curl -k https://sp-python.cafeexpresso.rnp.br/health
curl -k https://sp-python.cafeexpresso.rnp.br/api/devices/
curl -k https://sp-python.cafeexpresso.rnp.br/docs
```

## 🚨 **Problemas Comuns**

### **Erro: "ProxyPass not allowed here"**
```bash
# Verificar se os módulos estão habilitados
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo systemctl restart apache2
```

### **Erro: "Connection refused"**
```bash
# Verificar se o FastAPI está rodando
sudo systemctl status fastapi.service
sudo netstat -tlnp | grep :8000
```

### **Erro: "SSL certificate"**
```bash
# Verificar certificados SSL
sudo ls -la /etc/ssl/certs/sp-python.cafeexpresso.rnp.br.crt
sudo ls -la /etc/ssl/private/sp-python.cafeexpresso.rnp.br.key
```

## 📊 **Verificação de Status**

### **Comandos para verificar se está funcionando:**

```bash
# 1. Verificar serviços
sudo systemctl status apache2 fastapi.service gunicorn.service

# 2. Verificar portas
sudo netstat -tlnp | grep -E ':(80|443|8000|8001)'

# 3. Verificar configuração do Apache
sudo apache2ctl -S

# 4. Verificar logs
sudo tail -f /var/log/apache2/iot_edu_ssl_error.log

# 5. Testar endpoints
curl -k https://sp-python.cafeexpresso.rnp.br/health
curl -k https://sp-python.cafeexpresso.rnp.br/api/devices/
```

## 🎯 **Teste Final**

Após aplicar as soluções:

```bash
# Teste rápido
python backend/deploy/scripts/quick_check.py

# Teste completo
python backend/deploy/scripts/test_deployment.py
```

## 📞 **Suporte**

Se os problemas persistirem:

1. **Verifique os logs do Apache**: `sudo tail -f /var/log/apache2/iot_edu_ssl_error.log`
2. **Teste o proxy localmente**: `curl -k https://sp-python.cafeexpresso.rnp.br/health`
3. **Verifique a configuração**: `sudo apache2ctl configtest`
4. **Reinicie os serviços**: `sudo systemctl restart apache2 fastapi.service`

---

**O problema principal é que o Apache não está configurado para fazer proxy reverso para o FastAPI. Após configurar o proxy reverso corretamente, todos os endpoints devem funcionar!** 🚀🔐✨ 