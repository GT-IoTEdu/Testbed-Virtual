# Guia de Troubleshooting - IoT-EDU

## 🔍 **Problemas Identificados**

### **❌ FastAPI não está rodando**
- Todos os endpoints `/api/` retornam 404
- `/health`, `/docs` não existem
- Apenas Django SAML está funcionando

### **❌ Serviços não configurados corretamente**
- FastAPI não está sendo executado
- Proxy reverso não está configurado para FastAPI

## 🚨 **Diagnóstico Rápido**

### **1. Verificar se os serviços estão rodando**
```bash
# Verificar status dos serviços
sudo systemctl status apache2
sudo systemctl status gunicorn.service
sudo systemctl status fastapi.service

# Verificar se as portas estão em uso
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
sudo netstat -tlnp | grep :8000
```

### **2. Verificar logs dos serviços**
```bash
# Logs do Apache
sudo tail -f /var/log/apache2/iot_edu_ssl_error.log

# Logs do Gunicorn (Django)
sudo journalctl -u gunicorn.service -f

# Logs do FastAPI
sudo journalctl -u fastapi.service -f
```

## 🔧 **Soluções**

### **Solução 1: Iniciar o FastAPI**
```bash
# Verificar se o serviço existe
sudo systemctl status fastapi.service

# Se não existir, criar o serviço
sudo cp backend/deploy/systemd/fastapi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fastapi.service
sudo systemctl start fastapi.service

# Verificar se está rodando
sudo systemctl status fastapi.service
```

### **Solução 2: Verificar configuração do Apache**
```bash
# Verificar se o proxy está configurado
sudo grep -r "ProxyPass" /etc/apache2/sites-available/

# Verificar se os módulos estão habilitados
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo systemctl restart apache2
```

### **Solução 3: Testar FastAPI localmente**
```bash
# Navegar para o diretório do projeto
cd /opt/iot_edu/backend

# Ativar ambiente virtual
source venv/bin/activate

# Testar se o FastAPI funciona
python -c "
from main import app
import uvicorn
print('FastAPI app loaded successfully')
"

# Iniciar FastAPI manualmente para teste
uvicorn main:app --host 127.0.0.1 --port 8000
```

### **Solução 4: Verificar configuração do ambiente**
```bash
# Verificar se o arquivo .env existe
ls -la /opt/iot_edu/backend/.env

# Verificar se as variáveis estão carregadas
cd /opt/iot_edu/backend
source venv/bin/activate
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('PFSENSE_API_URL:', os.getenv('PFSENSE_API_URL'))
print('PFSENSE_API_KEY:', os.getenv('PFSENSE_API_KEY')[:10] + '...' if os.getenv('PFSENSE_API_KEY') else 'None')
"
```

## 🚀 **Deploy Manual (se necessário)**

### **1. Configurar ambiente**
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

### **2. Configurar variáveis de ambiente**
```bash
# Copiar arquivo de exemplo
sudo -u www-data cp backend/env_example.txt backend/.env

# Editar configurações
sudo -u www-data nano backend/.env
```

### **3. Configurar serviços**
```bash
# Copiar arquivos de serviço
sudo cp backend/deploy/systemd/gunicorn.service /etc/systemd/system/
sudo cp backend/deploy/systemd/fastapi.service /etc/systemd/system/

# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar e iniciar serviços
sudo systemctl enable gunicorn.service
sudo systemctl enable fastapi.service
sudo systemctl start gunicorn.service
sudo systemctl start fastapi.service
```

### **4. Configurar Apache**
```bash
# Copiar configuração do Apache
sudo cp backend/deploy/apache/iot_edu.conf /etc/apache2/sites-available/

# Habilitar site
sudo a2ensite iot_edu.conf

# Habilitar módulos necessários
sudo a2enmod ssl proxy proxy_http headers rewrite

# Testar configuração
sudo apache2ctl configtest

# Reiniciar Apache
sudo systemctl restart apache2
```

## 📊 **Verificação de Status**

### **Comandos para verificar se está funcionando:**
```bash
# 1. Verificar serviços
sudo systemctl status apache2 gunicorn.service fastapi.service

# 2. Verificar portas
sudo netstat -tlnp | grep -E ':(80|443|8000)'

# 3. Testar conectividade
curl -k https://sp-python.cafeexpresso.rnp.br/

# 4. Testar FastAPI localmente
curl -k http://127.0.0.1:8000/health

# 5. Verificar logs
sudo tail -f /var/log/apache2/iot_edu_ssl_error.log
```

## 🎯 **Teste Final**

Após aplicar as soluções, execute:

```bash
# Teste rápido
python backend/deploy/scripts/quick_check.py

# Teste completo
python backend/deploy/scripts/test_deployment.py
```

## 🚨 **Problemas Comuns**

### **Erro: "Unit fastapi.service not found"**
```bash
# Criar o arquivo de serviço
sudo cp backend/deploy/systemd/fastapi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fastapi.service
sudo systemctl start fastapi.service
```

### **Erro: "Module not found"**
```bash
# Verificar se o ambiente virtual está ativo
cd /opt/iot_edu/backend
source venv/bin/activate
pip install -r requirements.txt
```

### **Erro: "Permission denied"**
```bash
# Corrigir permissões
sudo chown -R www-data:www-data /opt/iot_edu
sudo chmod -R 755 /opt/iot_edu
```

### **Erro: "Address already in use"**
```bash
# Verificar o que está usando a porta
sudo netstat -tlnp | grep :8000
sudo lsof -i :8000

# Parar processo conflitante
sudo pkill -f uvicorn
sudo systemctl restart fastapi.service
```

## 📞 **Suporte**

Se os problemas persistirem:

1. **Verifique os logs** conforme mostrado acima
2. **Teste os serviços** individualmente
3. **Verifique a conectividade** de rede
4. **Consulte a documentação** em `backend/deploy/README.md`
5. **Execute o diagnóstico** detalhado: `python backend/deploy/scripts/diagnose_failures.py`

---

**A aplicação deve funcionar corretamente após aplicar estas soluções!** 🚀🔐✨ 