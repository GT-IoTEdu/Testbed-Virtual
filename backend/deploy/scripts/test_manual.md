# Guia de Testes Manuais - IoT-EDU

Este guia mostra como testar manualmente se a aplicação está funcionando corretamente no domínio `https://sp-python.cafeexpresso.rnp.br/`.

## 🚀 **Testes Rápidos**

### 1. **Teste Básico de Acesso**
Abra o navegador e acesse:
```
https://sp-python.cafeexpresso.rnp.br/
```

**Resultado esperado:**
- Página carrega sem erros
- Mostra informações da API IoT-EDU
- Links para documentação funcionando

### 2. **Teste de Health Check**
Acesse:
```
https://sp-python.cafeexpresso.rnp.br/health
```

**Resultado esperado:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "2.0.0"
}
```

### 3. **Teste da Documentação da API**
Acesse:
```
https://sp-python.cafeexpresso.rnp.br/docs
```

**Resultado esperado:**
- Interface Swagger/OpenAPI carrega
- Lista todos os endpoints disponíveis
- Permite testar endpoints interativamente

## 🔐 **Testes de Autenticação SAML**

### 4. **Teste de Metadados SAML**
Acesse:
```
https://sp-python.cafeexpresso.rnp.br/saml2/metadata/
```

**Resultado esperado:**
- XML com metadados SAML
- Informações do Service Provider
- Certificados e endpoints configurados

### 5. **Teste de Status de Autenticação**
Acesse:
```
https://sp-python.cafeexpresso.rnp.br/auth/status
```

**Resultado esperado (não autenticado):**
```json
{
  "status": "unauthenticated",
  "message": "Usuário não autenticado",
  "login_url": "/auth/login"
}
```

### 6. **Teste de Login SAML**
Acesse:
```
https://sp-python.cafeexpresso.rnp.br/saml2/login/
```

**Resultado esperado:**
- Redirecionamento para página de login CAFe
- Ou página de seleção de instituição (WAYF)

## 🌐 **Testes da API**

### 7. **Teste de Listagem de Dispositivos**
Acesse:
```
https://sp-python.cafeexpresso.rnp.br/api/devices/
```

**Resultado esperado:**
```json
{
  "status": "ok",
  "devices": []
}
```

### 8. **Teste de Listagem de Aliases**
Acesse:
```
https://sp-python.cafeexpresso.rnp.br/api/devices/aliases/
```

**Resultado esperado:**
```json
{
  "status": "ok",
  "aliases": [...]
}
```

### 9. **Teste de Servidores DHCP**
Acesse:
```
https://sp-python.cafeexpresso.rnp.br/api/devices/dhcp/servers
```

**Resultado esperado:**
```json
{
  "status": "ok",
  "servers": [...]
}
```

## 🛡️ **Testes de Integração pfSense**

### 10. **Teste de Alias Específico**
Acesse:
```
https://sp-python.cafeexpresso.rnp.br/api/devices/aliases/Teste_API_IoT_EDU
```

**Resultado esperado:**
```json
{
  "status": "ok",
  "alias": {
    "name": "Teste_API_IoT_EDU",
    "type": "host",
    "address": ["192.168.1.100"]
  }
}
```

### 11. **Teste de Mapeamento DHCP**
Acesse:
```
https://sp-python.cafeexpresso.rnp.br/api/devices/dhcp/static_mapping?parent_id=lan&id=6
```

**Resultado esperado:**
```json
{
  "status": "ok",
  "result": {
    "parent_id": "lan",
    "id": 6,
    "mac": "08:00:27:30:94:87",
    "ipaddr": "10.30.30.250"
  }
}
```

## 🔒 **Testes de Segurança**

### 12. **Teste de Certificado SSL**
No navegador, verifique:
- Cadeado verde na barra de endereços
- Certificado válido
- HTTPS funcionando

### 13. **Teste de Headers de Segurança**
Use o DevTools do navegador (F12) e verifique:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

## 📊 **Testes de Performance**

### 14. **Teste de Tempo de Resposta**
Use o DevTools (aba Network) e verifique:
- Tempo de carregamento < 2 segundos
- Sem timeouts
- Respostas rápidas

### 15. **Teste de Disponibilidade**
Execute várias requisições simultâneas:
```bash
# Usando curl (Linux/Mac)
for i in {1..10}; do
  curl -s -o /dev/null -w "%{http_code}" https://sp-python.cafeexpresso.rnp.br/health
  echo " - Requisição $i"
done
```

## 🚨 **Testes de Erro**

### 16. **Teste de Endpoint Inexistente**
Acesse:
```
https://sp-python.cafeexpresso.rnp.br/api/endpoint-inexistente
```

**Resultado esperado:**
```json
{
  "detail": "Not Found"
}
```

### 17. **Teste de Método HTTP Inválido**
Tente fazer POST em endpoint GET:
```bash
curl -X POST https://sp-python.cafeexpresso.rnp.br/api/devices/aliases/
```

**Resultado esperado:**
```json
{
  "detail": "Method Not Allowed"
}
```

## 📱 **Testes de Compatibilidade**

### 18. **Teste em Diferentes Navegadores**
Teste em:
- Chrome
- Firefox
- Safari
- Edge

### 19. **Teste em Dispositivos Móveis**
Verifique:
- Responsividade
- Funcionamento em telas pequenas
- Touch-friendly

## 🔧 **Ferramentas de Teste**

### **Usando curl (Linux/Mac)**
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

### **Usando PowerShell (Windows)**
```powershell
# Teste básico
Invoke-WebRequest -Uri "https://sp-python.cafeexpresso.rnp.br/health" -UseBasicParsing

# Teste de performance
Measure-Command { Invoke-WebRequest -Uri "https://sp-python.cafeexpresso.rnp.br/health" -UseBasicParsing }
```

### **Usando Postman**
1. Importe a coleção: `API_IoT_EDU.postman_collection.json`
2. Configure a URL base: `https://sp-python.cafeexpresso.rnp.br`
3. Execute os testes

## 📋 **Checklist de Verificação**

- [ ] **Acesso básico** - Site carrega sem erros
- [ ] **SSL** - Certificado válido e HTTPS funcionando
- [ ] **Health check** - Endpoint `/health` retorna 200
- [ ] **Documentação** - `/docs` carrega corretamente
- [ ] **SAML metadata** - `/saml2/metadata/` retorna XML
- [ ] **API endpoints** - Todos os endpoints da API funcionam
- [ ] **pfSense integration** - Endpoints pfSense respondem
- [ ] **Headers de segurança** - Configurados corretamente
- [ ] **Performance** - Respostas rápidas (< 2s)
- [ ] **Compatibilidade** - Funciona em diferentes navegadores

## 🚨 **Problemas Comuns e Soluções**

### **Erro 502 Bad Gateway**
- Verificar se os serviços estão rodando
- Verificar logs do Apache
- Verificar conectividade entre Apache e aplicação

### **Erro 503 Service Unavailable**
- Verificar status dos serviços systemd
- Verificar recursos do servidor
- Verificar configuração do Gunicorn

### **Erro de Certificado SSL**
- Verificar se o certificado está instalado
- Verificar se o Apache está configurado para SSL
- Verificar se o domínio está correto

### **Erro de Autenticação SAML**
- Verificar configuração do CAFe
- Verificar metadados SAML
- Verificar certificados SAML

## 📞 **Suporte**

Se encontrar problemas:
1. Verifique os logs: `/var/log/apache2/` e `/var/log/gunicorn/`
2. Teste os serviços: `sudo systemctl status apache2 gunicorn.service fastapi.service`
3. Verifique a conectividade: `ping sp-python.cafeexpresso.rnp.br`
4. Consulte a documentação completa em `backend/deploy/README.md` 