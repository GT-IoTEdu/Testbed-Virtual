# 🧪 Guia de Teste - Setup Inicial de Aliases e Regras

Este guia explica como testar se o script `setup_initial_aliases_and_rules.py` funcionou corretamente.

## 📋 Pré-requisitos

Antes de testar, certifique-se de que:

1. ✅ As tabelas do banco de dados foram criadas
2. ✅ As instituições foram cadastradas no banco
3. ✅ As configurações do pfSense estão corretas nas instituições
4. ✅ O script `setup_initial_aliases_and_rules.py` foi executado

## 🚀 Executando o Script de Teste

### Teste Automatizado (Recomendado)

Execute o script de teste automatizado:

```bash
# Testar todas as instituições
python scripts/test_setup_initial_aliases_and_rules.py

# Testar uma instituição específica
python scripts/test_setup_initial_aliases_and_rules.py --institution-id 1
```

### O que o script verifica:

1. ✅ **Aliases no Banco de Dados**
   - Verifica se "Autorizados" foi criado
   - Verifica se "Bloqueados" foi criado
   - Confirma que estão associados à instituição correta

2. ✅ **Aliases no pfSense**
   - Verifica se os aliases existem no pfSense
   - Confirma que estão sincronizados

3. ✅ **Regras no Banco de Dados**
   - Verifica se regra BLOCK foi sincronizada
   - Verifica se regra PASS foi sincronizada
   - Confirma que estão associadas à instituição correta

4. ✅ **Regras no pfSense**
   - Verifica se as regras existem no pfSense
   - Confirma que estão funcionando

## 🔍 Teste Manual

Se preferir testar manualmente, siga estes passos:

### 1. Verificar Aliases no Banco de Dados

```sql
-- Conectar ao MySQL
mysql -u IoT_EDU -p iot_edu

-- Verificar aliases criados
SELECT id, name, alias_type, descr, institution_id 
FROM pfsense_aliases 
WHERE name IN ('Autorizados', 'Bloqueados')
AND institution_id = 1;
```

**Resultado esperado:**
```
+----+-------------+------------+--------------------------------+----------------+
| id | name        | alias_type | descr                          | institution_id |
+----+-------------+------------+--------------------------------+----------------+
|  1 | Autorizados | host       | Dispositivos autorizados na rede|              1 |
|  2 | Bloqueados  | host       | Dispositivos bloqueados        |              1 |
+----+-------------+------------+--------------------------------+----------------+
```

### 2. Verificar Aliases no pfSense

Via API ou interface web do pfSense:

```bash
# Via API (ajuste a URL e chave)
curl -X GET "https://seu-pfsense.local/api/v2/firewall/alias" \
  -H "X-API-Key: sua_chave_api"
```

Ou acesse: **Firewall > Aliases** na interface web do pfSense

**Resultado esperado:**
- Ver alias "Autorizados" (tipo: host, vazio inicialmente)
- Ver alias "Bloqueados" (tipo: host, vazio inicialmente)

### 3. Verificar Regras no Banco de Dados

```sql
SELECT id, pf_id, type, source, destination, descr, institution_id 
FROM pfsense_firewall_rules 
WHERE institution_id = 1
AND (source LIKE '%Bloqueados%' OR source LIKE '%Autorizados%');
```

**Resultado esperado:**
```
+----+-------+-------+-------------+-------------+--------------------------------+----------------+
| id | pf_id | type  | source      | destination | descr                          | institution_id |
+----+-------+-------+-------------+-------------+--------------------------------+----------------+
|  1 |   123 | block | Bloqueados  | any         | Bloqueio Total - Dispositivos  |              1 |
|  2 |   124 | pass  | Autorizados | any         | Liberação Total - Dispositivos |              1 |
+----+-------+-------+-------------+-------------+--------------------------------+----------------+
```

### 4. Verificar Regras no pfSense

Via API:

```bash
curl -X GET "https://seu-pfsense.local/api/v2/firewall/rule" \
  -H "X-API-Key: sua_chave_api"
```

Ou acesse: **Firewall > Rules** na interface web do pfSense

**Resultado esperado:**
- Ver regra BLOCK com source="Bloqueados"
- Ver regra PASS com source="Autorizados"

### 5. Testar Funcionalidade

#### Teste 1: Adicionar IP ao alias "Bloqueados"

```bash
# Via API do sistema
curl -X POST "http://localhost:8000/api/devices/aliases-db/Bloqueados/add-addresses?current_user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": [
      {"address": "192.168.1.100", "detail": "Teste"}
    ]
  }'
```

**Verificar:**
- IP aparece no alias "Bloqueados" no banco
- IP aparece no alias "Bloqueados" no pfSense
- Regra BLOCK está bloqueando o IP

#### Teste 2: Adicionar IP ao alias "Autorizados"

```bash
curl -X POST "http://localhost:8000/api/devices/aliases-db/Autorizados/add-addresses?current_user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": [
      {"address": "192.168.1.101", "detail": "Teste"}
    ]
  }'
```

**Verificar:**
- IP aparece no alias "Autorizados" no banco
- IP aparece no alias "Autorizados" no pfSense
- Regra PASS está liberando o IP

## ✅ Resultado Esperado

Após executar o script de teste, você deve ver:

```
🧪 Testando configuração da instituição ID: 1
============================================================
📋 Instituição: Unipampa - Alegrete

📦 Testando aliases no banco de dados (instituição 1)...
  ✅ Alias 'Autorizados' encontrado (ID: 1)
  ✅ Alias 'Bloqueados' encontrado (ID: 2)

🌐 Testando aliases no pfSense (instituição 1)...
  ✅ Alias 'Autorizados' encontrado no pfSense
  ✅ Alias 'Bloqueados' encontrado no pfSense

🛡️  Testando regras no banco de dados (instituição 1)...
  ✅ Regra BLOCK encontrada (pf_id: 123, descr: Bloqueio Total...)
  ✅ Regra PASS encontrada (pf_id: 124, descr: Liberação Total...)
  📊 Total de regras sincronizadas: 2

🌐 Testando regras no pfSense (instituição 1)...
  ✅ Regra BLOCK encontrada no pfSense
  ✅ Regra PASS encontrada no pfSense
  📊 Total de regras no pfSense: 2

============================================================
📊 RESUMO DOS TESTES
============================================================

✅ Aliases no Banco de Dados:
   - Autorizados: ✅
   - Bloqueados: ✅

✅ Aliases no pfSense:
   - Autorizados: ✅
   - Bloqueados: ✅

✅ Regras no Banco de Dados:
   - BLOCK: ✅
   - PASS: ✅

✅ Regras no pfSense:
   - BLOCK: ✅
   - PASS: ✅

🎉 TUDO FUNCIONANDO CORRETAMENTE!
```

## ⚠️ Problemas Comuns

### Aliases não encontrados no pfSense

**Causa:** Erro de conexão ou credenciais incorretas

**Solução:**
1. Verificar configurações do pfSense na tabela `institutions`
2. Testar conexão manualmente:
   ```bash
   curl -X GET "https://seu-pfsense/api/v2/firewall/alias" \
     -H "X-API-Key: sua_chave"
   ```

### Regras não encontradas

**Causa:** Regras podem ter nomes diferentes ou não foram criadas

**Solução:**
1. Verificar manualmente no pfSense se as regras existem
2. Executar novamente o script de setup
3. Verificar logs do script para erros

### Erro de permissão

**Causa:** Usuário ADMIN não encontrado para a instituição

**Solução:**
1. Criar um usuário ADMIN para a instituição:
   ```sql
   UPDATE users SET permission = 'ADMIN', institution_id = 1 WHERE id = X;
   ```

## 📝 Próximos Passos

Após confirmar que tudo está funcionando:

1. ✅ Testar bloqueio de um dispositivo
2. ✅ Testar liberação de um dispositivo
3. ✅ Verificar sincronização automática
4. ✅ Monitorar logs do sistema

## 🔗 Links Úteis

- [Documentação da API pfSense v2](backend/docs/README-pfsense-api-v2.md)
- [Guia de Aliases](backend/docs/GUIA_ADICIONAR_IPS_ALIASES.md)
- [Sistema Multi-Institucional](backend/docs/MULTI_INSTITUCIONAL.md)

