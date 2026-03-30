# 🔧 Configuração da API do Zeek

## 📋 Problema: URL do Zeek Incorreta (404)

Se você está recebendo erro `404 Not Found` ao tentar acessar a API do Zeek, verifique a configuração da URL.

## ✅ Solução

### 1. Verificar IP do pfSense/Zeek

O Zeek está rodando no pfSense. Verifique qual é o IP correto:

```bash
# O IP padrão configurado é: 192.168.100.1
# Mas pode ser diferente no seu ambiente
```

### 2. Configurar no arquivo `.env`

Crie ou edite o arquivo `backend/.env` e adicione:

```env
# URL da API do Zeek (ajuste conforme seu ambiente)
ZEEK_API_URL=http://192.168.100.1/zeek-api

# Token de autenticação do Zeek
ZEEK_API_TOKEN=y1X6Qn8PpV9jR4kM0wBz7Tf2GhUs3Lc8NrDq5Ke1HxYi0AzF7Gv9MbX2VwJoQp
```

### 3. Verificar a URL da API

Teste se a URL está acessível:

```bash
# Teste manual (substitua o IP pelo correto)
curl "http://192.168.100.1/zeek-api/alert_data.php?logfile=notice.log&maxlines=10" \
  -H "Authorization: Bearer y1X6Qn8PpV9jR4kM0wBz7Tf2GhUs3Lc8NrDq5Ke1HxYi0AzF7Gv9MbX2VwJoQp"
```

### 4. Verificar no código

O script de teste agora mostra a configuração ao iniciar:

```bash
python backend/scripts/test_detection_blocking_times.py
```

Você verá:
```
🔧 Configuração do Zeek Service:
  - URL Base: http://192.168.100.1/zeek-api
  - Token: Configurado
  - Timeout: 30s
```

## 🔍 Troubleshooting

### Erro 404 Not Found

**Causa**: URL incorreta ou API do Zeek não está acessível

**Solução**:
1. Verifique se o pfSense está acessível no IP configurado
2. Verifique se a rota `/zeek-api/alert_data.php` existe
3. Teste a URL manualmente no navegador (com autenticação)

### Erro de Conexão

**Causa**: Firewall bloqueando ou IP incorreto

**Solução**:
1. Verifique conectividade de rede: `ping 192.168.100.1`
2. Verifique se a porta está aberta
3. Verifique regras de firewall

### Token Inválido

**Causa**: Token não configurado ou incorreto

**Solução**:
1. Verifique se `ZEEK_API_TOKEN` está no `.env`
2. Verifique se o token está correto (sem espaços extras)
3. Verifique os logs para mensagens de autenticação

## 📝 Exemplo de Arquivo .env Correto

```env
# Configurações do Zeek
ZEEK_API_URL=http://192.168.100.1/zeek-api
ZEEK_API_TOKEN=y1X6Qn8PpV9jR4kM0wBz7Tf2GhUs3Lc8NrDq5Ke1HxYi0AzF7Gv9MbX2VwJoQp

# Outras configurações...
PFSENSE_API_URL=http://192.168.100.1
PFSENSE_API_KEY=sua_key_aqui
PFSENSE_API_SECRET=seu_secret_aqui
```

## 🎯 Verificação Rápida

Execute o script de teste com debug:

```bash
cd backend/scripts
python test_detection_blocking_times.py
```

O script mostrará:
- ✅ URL configurada
- ✅ Token configurado
- ✅ Tentativas de conexão
- ❌ Erros detalhados se houver problemas

