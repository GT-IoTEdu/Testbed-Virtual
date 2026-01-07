# Guia Completo de Testes - IoT-EDU

Este guia mostra como testar se a aplicação está funcionando corretamente no domínio `https://sp-python.cafeexpresso.rnp.br/`.

## 🚀 **Opções de Teste**

### **1. Teste Automatizado (Recomendado)**

#### **Linux/Mac:**
```bash
# Teste rápido
chmod +x backend/deploy/scripts/quick_test.sh
./backend/deploy/scripts/quick_test.sh

# Teste completo
python backend/deploy/scripts/test_deployment.py
```

#### **Windows:**
```powershell
# Teste rápido
.\backend\deploy\scripts\test_windows.ps1

# Teste completo
python backend\deploy\scripts\test_deployment.py
```

### **2. Teste Manual no Navegador**

Acesse os seguintes URLs no seu navegador:

#### **Testes Básicos:**
- **Página Principal**: https://sp-python.cafeexpresso.rnp.br/
- **Health Check**: https://sp-python.cafeexpresso.rnp.br/health
- **Documentação**: https://sp-python.cafeexpresso.rnp.br/docs

#### **Testes SAML:**
- **Metadados SAML**: https://sp-python.cafeexpresso.rnp.br/saml2/metadata/
- **Status de Autenticação**: https://sp-python.cafeexpresso.rnp.br/auth/status
- **Login SAML**: https://sp-python.cafeexpresso.rnp.br/saml2/login/

#### **Testes da API:**
- **Dispositivos**: https://sp-python.cafeexpresso.rnp.br/api/devices/
- **Aliases**: https://sp-python.cafeexpresso.rnp.br/api/devices/aliases/
- **Servidores DHCP**: https://sp-python.cafeexpresso.rnp.br/api/devices/dhcp/servers

### **3. Teste com curl (Linux/Mac)**

```bash
# Teste básico
curl -k https://sp-python.cafeexpresso.rnp.br/health

# Teste com headers
curl -k -H "Accept: application/json" https://sp-python.cafeexpresso.rnp.br/api/devices/

# Teste de performance
curl -k -w "@-" -o /dev/null -s https://sp-python.cafeexpresso.rnp.br/health <<'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF
```

### **4. Teste com PowerShell (Windows)**

```powershell
# Teste básico
Invoke-WebRequest -Uri "https://sp-python.cafeexpresso.rnp.br/health" -UseBasicParsing

# Teste de performance
Measure-Command { Invoke-WebRequest -Uri "https://sp-python.cafeexpresso.rnp.br/health" -UseBasicParsing }
```

### **5. Teste com Postman**

1. Importe a coleção: `API_IoT_EDU.postman_collection.json`
2. Configure a URL base: `https://sp-python.cafeexpresso.rnp.br`
3. Execute os testes

## 📋 **Checklist de Verificação**

### **✅ Testes Essenciais (Deve funcionar)**
- [ ] **Acesso básico** - Site carrega sem erros
- [ ] **SSL** - Certificado válido e HTTPS funcionando
- [ ] **Health check** - Endpoint `/health` retorna 200
- [ ] **Documentação** - `/docs` carrega corretamente
- [ ] **SAML metadata** - `/saml2/metadata/` retorna XML
- [ ] **API endpoints** - Todos os endpoints da API funcionam

### **⚠️ Testes Opcionais (Pode falhar se não configurado)**
- [ ] **pfSense integration** - Endpoints pfSense respondem
- [ ] **Autenticação SAML** - Login federado funcionando
- [ ] **Banco de dados** - Conexão com MySQL funcionando

## 🔍 **O que Verificar**

### **1. Resposta Esperada - Health Check**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "2.0.0"
}
```

### **2. Resposta Esperada - Status de Autenticação**
```json
{
  "status": "unauthenticated",
  "message": "Usuário não autenticado",
  "login_url": "/auth/login"
}
```

### **3. Resposta Esperada - Listagem de Dispositivos**
```json
{
  "status": "ok",
  "devices": []
}
```

### **4. Resposta Esperada - Listagem de Aliases**
```json
{
  "status": "ok",
  "aliases": [...]
}
```

## 🚨 **Problemas Comuns**

### **Erro 502 Bad Gateway**
**Causa:** Serviços não estão rodando
**Solução:**
```bash
sudo systemctl status apache2 gunicorn.service fastapi.service
sudo systemctl restart apache2 gunicorn.service fastapi.service
```

### **Erro 503 Service Unavailable**
**Causa:** Serviços falharam ao iniciar
**Solução:**
```bash
sudo journalctl -u gunicorn.service -f
sudo journalctl -u fastapi.service -f
```

### **Erro de Certificado SSL**
**Causa:** Certificado não configurado ou inválido
**Solução:**
```bash
sudo apache2ctl configtest
sudo systemctl status apache2
```

### **Erro de Conectividade**
**Causa:** DNS ou firewall bloqueando
**Solução:**
```bash
ping sp-python.cafeexpresso.rnp.br
nslookup sp-python.cafeexpresso.rnp.br
```

## 📊 **Interpretação dos Resultados**

### **🎉 Todos os Testes Passaram (100%)**
- Aplicação funcionando perfeitamente
- Todos os serviços operacionais
- Configuração correta

### **⚠️ Maioria dos Testes Passou (80-99%)**
- Aplicação funcionando com pequenos problemas
- Verificar endpoints que falharam
- Possíveis problemas de configuração

### **❌ Muitos Testes Falharam (< 80%)**
- Problemas significativos na configuração
- Verificar logs e status dos serviços
- Possível problema de rede ou DNS

## 🔧 **Comandos de Diagnóstico**

### **Verificar Status dos Serviços**
```bash
sudo systemctl status apache2 gunicorn.service fastapi.service
```

### **Verificar Logs**
```bash
# Logs do Apache
sudo tail -f /var/log/apache2/iot_edu_ssl_error.log

# Logs do Gunicorn
sudo journalctl -u gunicorn.service -f

# Logs do FastAPI
sudo journalctl -u fastapi.service -f
```

### **Verificar Portas**
```bash
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
sudo netstat -tlnp | grep :8000
```

### **Verificar Certificados SSL**
```bash
openssl s_client -connect sp-python.cafeexpresso.rnp.br:443 -servername sp-python.cafeexpresso.rnp.br
```

## 📞 **Suporte**

Se encontrar problemas:

1. **Verifique os logs** conforme mostrado acima
2. **Teste os serviços** individualmente
3. **Verifique a conectividade** de rede
4. **Consulte a documentação** em `backend/deploy/README.md`
5. **Execute os scripts de teste** para diagnóstico detalhado

## 🎯 **Resumo Rápido**

Para testar rapidamente se está funcionando:

1. **Abra o navegador** e acesse: https://sp-python.cafeexpresso.rnp.br/
2. **Verifique se carrega** sem erros
3. **Acesse**: https://sp-python.cafeexpresso.rnp.br/health
4. **Verifique se retorna** JSON com status "healthy"
5. **Acesse**: https://sp-python.cafeexpresso.rnp.br/docs
6. **Verifique se a documentação** carrega corretamente

Se todos esses passos funcionarem, a aplicação está operacional! 🎉

---

**Aplicação funcionando corretamente quando todos os testes essenciais passarem!** 🚀🔐✨ 