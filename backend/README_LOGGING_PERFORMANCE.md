# 📊 Sistema de Logging de Performance

## 📋 Visão Geral

O sistema de logging de performance foi implementado para medir e registrar métricas técnicas de eficiência do sistema de detecção e bloqueio automático. Todos os logs são salvos no arquivo `log_test.txt` na raiz do projeto.

## 🎯 Métricas Registradas

### 1. **Tempos**
- **Tempo de Detecção (TtD)**: Tempo desde a detecção pelo Zeek até o salvamento no banco
- **Tempo de Processamento (TtP)**: Tempo desde o salvamento até o processamento
- **Tempo de Bloqueio (TtB)**: Tempo total desde a detecção até o bloqueio efetivo
- **Duração de Endpoints**: Tempo de execução de cada endpoint
- **Duração de Sincronizações**: Tempo de sincronização com pfSense

### 2. **Consumo de Recursos**
- **CPU (Processo)**: Porcentagem de CPU usada pelo processo da API
- **CPU (Sistema)**: Porcentagem de CPU do sistema
- **Memória RAM (Processo)**: MB e porcentagem de memória usada pelo processo
- **Memória RAM (Sistema)**: Porcentagem e MB disponíveis/total do sistema

### 3. **Eventos Registrados**
- **DETECTION**: Detecção de incidentes
- **BLOCKING**: Bloqueio automático
- **ENDPOINT_CALL**: Chamadas de endpoints
- **SYNC**: Sincronizações com pfSense
- **PROCESSING**: Processamento em lote
- **TIMING_SUMMARY**: Resumo de tempos

## 📍 Pontos de Logging

### Endpoints
- `POST /api/incidents/process-batch` - Processamento em lote
- `POST /api/incidents/auto-block` - Bloqueio automático manual

### Serviços
- `IncidentService.save_incident()` - Quando um incidente é salvo
- `IncidentService._apply_auto_block()` - Durante o bloqueio automático
- `IncidentService.process_incidents_for_auto_blocking()` - Processamento em lote

### Sincronizações
- `pfsense_client.atualizar_alias_pfsense()` - Atualização de aliases
- `pfsense_client.aplicar_mudancas_firewall_pfsense()` - Aplicação de mudanças no firewall

## 📄 Formato do Log

Cada evento é registrado com:

```
====================================================================================================
TIMESTAMP: 2025-11-03 16:00:00.123
TIPO: DETECTION
DESCRIÇÃO: Incidente detectado: SQL Injection - Atacante
INCIDENTE ID: 123
IP DO DISPOSITIVO: 192.168.59.4
ENDPOINT: IncidentService.save_incident
DURAÇÃO: 0.045s (45ms)

MÉTRICAS DO SISTEMA:
  CPU (Processo): 2.35%
  CPU (Sistema): 15.20%
  Memória RAM (Processo): 125.45 MB (1.25%)
  Memória RAM (Sistema): 45.20% usado (2048 MB disponíveis de 4096 MB)

METADADOS:
  detected_at: 2025-11-03T15:59:55.000
  incident_type: SQL Injection - Atacante
====================================================================================================
```

## 🔍 Como Usar

### 1. Executar um Ataque

Quando um ataque SQL Injection é executado (por exemplo, usando sqlmap):

```bash
# No computador atacante (192.168.59.4)
sqlmap -u "http://192.168.59.2/api/test" --batch
```

### 2. Verificar o Log

O arquivo `log_test.txt` será criado automaticamente e todos os eventos serão registrados:

```bash
# Ver o log em tempo real
tail -f log_test.txt

# Ver últimas 100 linhas
tail -n 100 log_test.txt
```

### 3. Analisar Métricas

O log contém:
- **Timestamps** de cada etapa
- **Durações** de cada operação
- **Consumo de recursos** em cada momento
- **Endpoints envolvidos** no processo
- **Resumo de tempos** (TtD, TtP, TtB)

## 📊 Exemplo de Fluxo Completo

```
1. DETECTION - Incidente detectado pelo Zeek
   - detected_at: 2025-11-03 15:59:55.000
   - CPU: 2.35%
   - Memória: 125.45 MB

2. PROCESSING_START - Início do processamento
   - CPU: 2.40%
   - Memória: 125.50 MB

3. BLOCKING_START - Início do bloqueio
   - CPU: 2.50%
   - Memória: 125.80 MB

4. SYNC - Atualização de alias no pfSense
   - Duração: 0.234s
   - CPU: 2.55%
   - Memória: 126.00 MB

5. SYNC - Aplicação de mudanças no firewall
   - Duração: 1.456s
   - CPU: 3.20%
   - Memória: 126.50 MB

6. BLOCKING - Bloqueio concluído
   - blocked_at: 2025-11-03 15:59:57.123
   - Duração: 2.123s
   - CPU: 2.80%
   - Memória: 126.20 MB

7. TIMING_SUMMARY - Resumo
   - TtB: 2.123s
   - TtP: 0.045s
```

## 🛠️ Configuração

O logger é configurado automaticamente. O arquivo de log padrão é `log_test.txt`, mas pode ser alterado:

```python
from services_scanners.performance_logger import get_performance_logger

# Usar arquivo customizado
perf_logger = get_performance_logger("meu_log.txt")
```

## 📝 Notas Técnicas

- O sistema usa `psutil` para medir CPU e memória
- Os logs são thread-safe (usando locks)
- Cada log é escrito imediatamente (flush)
- O arquivo é criado automaticamente se não existir
- Métricas são coletadas no momento do evento

## 🔧 Troubleshooting

### Log não está sendo criado
- Verifique permissões de escrita na raiz do projeto
- Verifique se `psutil` está instalado: `pip install psutil`

### Métricas não aparecem
- Verifique se o processo Python está rodando
- Verifique se há erros no log padrão da aplicação

### Log muito grande
- O arquivo cresce continuamente
- Considere rotacionar ou limpar periodicamente
- Use `log_test.txt` apenas para testes

## 📚 Referências

- **Tabela `zeek_incidents`**: Coluna `detected_at` - tempo de detecção
- **Tabela `blocking_feedback_history`**: Coluna `feedback_date` - tempo de bloqueio
- **Tempo de Bloqueio (TtB)**: `feedback_date - detected_at`

