# 🔧 Processamento Automático de Bloqueio

## 📋 Problema Identificado

O sistema de bloqueio automático estava configurado para processar incidentes apenas quando o endpoint `/process-batch` era chamado manualmente. Isso significava que:

- ✅ Incidentes eram detectados e salvos no banco
- ❌ Bloqueio automático NÃO era aplicado automaticamente
- ❌ Era necessário chamar manualmente o endpoint `/process-batch`

## ✅ Solução Implementada

Foi adicionado processamento automático em background quando um incidente de **"Atacante"** é salvo:

1. **Detecção Automática**: Quando um incidente contendo "Atacante" é salvo
2. **Processamento em Background**: Thread assíncrona processa o bloqueio automaticamente
3. **Não Bloqueia**: O processamento é feito em background sem afetar a resposta da API

## 🚀 Como Funciona Agora

### Fluxo Automático

```
1. Zeek detecta ataque → Gera log notice.log
2. API recebe log → Salva incidente no banco
3. Sistema verifica se é "Atacante" → ✅ SIM
4. Thread em background inicia processamento
5. Sistema processa incidentes pendentes
6. Bloqueio automático é aplicado
7. IP é adicionado ao alias "Bloqueados"
```

### Processamento Manual (Ainda Disponível)

Se necessário, você ainda pode processar manualmente:

```bash
# Via script
python backend/scripts/check_and_process_incidents.py

# Via API
curl -X POST "http://localhost:8000/api/incidents/process-batch?limit=50" \
  -H "Authorization: Bearer <seu_token>"
```

## 📊 Verificar Status

### Verificar Incidentes Não Processados

```bash
# Via script
python backend/scripts/check_and_process_incidents.py

# Via API
curl "http://localhost:8000/api/incidents/unprocessed?limit=100" \
  -H "Authorization: Bearer <seu_token>"
```

### Verificar Estatísticas de Processamento

```bash
# Via API
curl "http://localhost:8000/api/incidents/processing-stats?hours_ago=24" \
  -H "Authorization: Bearer <seu_token>"
```

## 🔍 Troubleshooting

### Se o bloqueio não está sendo aplicado:

1. **Verifique os logs da API**:
   ```bash
   # Procure por mensagens como:
   # "🔒 Incidente de atacante detectado"
   # "Processamento automático iniciado em background"
   # "✅ Bloqueio automático aplicado"
   ```

2. **Verifique se há incidentes não processados**:
   ```bash
   python backend/scripts/check_and_process_incidents.py
   ```

3. **Processe manualmente se necessário**:
   ```bash
   python backend/scripts/check_and_process_incidents.py
   ```

4. **Verifique o incident_type**:
   - Deve conter a palavra **"Atacante"**
   - Exemplos válidos: `"SQL Injection - Atacante"`, `"Malware - Atacante"`

5. **Verifique se o dispositivo existe no DHCP**:
   - O bloqueio precisa do dispositivo no banco `dhcp_static_mappings`

## 📝 Notas Importantes

- ⚠️ O processamento automático funciona apenas para incidentes de **"Atacante"**
- ⚠️ Incidentes de **"Vítima"** NÃO são bloqueados (comportamento correto)
- ✅ O processamento em background não afeta a performance da API
- ✅ Se o processamento automático falhar, você ainda pode processar manualmente

## 🎯 Exemplo de Uso

### Testar o Sistema

1. Execute um ataque sqlmap da máquina atacante (192.168.59.4)
2. O Zeek detecta e gera log notice.log
3. A API salva o incidente automaticamente
4. O sistema processa e bloqueia automaticamente em background
5. Verifique se o IP foi bloqueado:

```bash
# Verificar incidentes
python backend/scripts/check_and_process_incidents.py

# Verificar se IP está no alias "Bloqueados" no pfSense
```

