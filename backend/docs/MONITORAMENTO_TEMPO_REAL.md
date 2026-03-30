# ⚡ Monitoramento em Tempo Real do Zeek

## 📋 Visão Geral

O sistema de monitoramento do Zeek foi atualizado para suportar **monitoramento quase em tempo real**, reduzindo drasticamente o tempo entre a detecção de um incidente e o bloqueio automático.

## ✅ O Que Mudou

### Antes (Monitoramento Periódico)
- **Intervalo**: 60 segundos
- **Desvantagem**: Até 60 segundos de atraso na detecção
- **Reprocessamento**: Buscava logs repetidamente, mesmo os já processados

### Agora (Monitoramento Quase em Tempo Real)
- **Intervalo**: 3 segundos (configurável)
- **Vantagem**: Detecção em até 3 segundos
- **Otimização**: Rastreamento de último timestamp processado, evitando reprocessamento

## 🔧 Como Funciona

### 1. Rastreamento de Timestamp

O sistema agora mantém o **último timestamp processado** para cada tipo de log:
- `notice.log`
- `http.log`
- `conn.log`
- `dns.log`

```python
# Rastreamento por tipo de log
self.last_processed_timestamp: Dict[ZeekLogType, Optional[datetime]] = {
    log_type: None for log_type in ZeekLogType
}
```

### 2. Busca Incremental

**Primeira execução:**
- Busca logs das últimas `hours_ago` horas (padrão: 1 hora)
- Processa todos os incidentes encontrados
- Marca o timestamp atual como último processado

**Execuções seguintes:**
- Busca apenas logs **depois** do último timestamp processado
- Adiciona 1 segundo ao último timestamp para evitar reprocessamento
- Atualiza o timestamp apenas se novos logs forem encontrados

### 3. Intervalo Configurável

```python
# Modo Tempo Real (recomendado)
check_interval_seconds=3  # Verifica a cada 3 segundos

# Modo Periódico (economiza recursos)
check_interval_seconds=60  # Verifica a cada 60 segundos
```

## 📊 Benefícios

### ⚡ Detecção Mais Rápida
- **Antes**: 0-60 segundos de atraso
- **Agora**: 0-3 segundos de atraso
- **Redução**: Até 95% mais rápido

### 🔄 Sem Reprocessamento
- Sistema não reprocessa logs já analisados
- Reduz carga no servidor
- Mais eficiente

### 📈 Melhor Performance
- Menos requisições HTTP desnecessárias
- Processamento mais eficiente
- Menor consumo de recursos

## 🎯 Configuração

### Configuração Atual (main.py)

```python
monitor = start_zeek_monitor(
    check_interval_seconds=3,  # Tempo real (3 segundos)
    hours_ago=1,              # Primeira busca: últimas 1 hora
    maxlines=100               # Até 100 linhas por tipo de log
)
```

### Personalizar Intervalo

Se quiser ajustar o intervalo, edite `backend/main.py`:

```python
# Para tempo real ainda mais rápido (1 segundo)
check_interval_seconds=1

# Para economizar recursos (10 segundos)
check_interval_seconds=10

# Para modo periódico (60 segundos)
check_interval_seconds=60
```

## 📊 Status do Monitor

Você pode verificar o status do monitor via código:

```python
from services_scanners.zeek_monitor import get_zeek_monitor

monitor = get_zeek_monitor()
if monitor:
    status = monitor.get_status()
    print(status)
```

**Resposta:**
```json
{
    "is_running": true,
    "check_interval_seconds": 3,
    "hours_ago": 1,
    "maxlines": 100,
    "last_check_time": "2024-01-15T10:30:45.123456",
    "last_processed_timestamps": {
        "notice.log": "2024-01-15T10:30:45.123456",
        "http.log": "2024-01-15T10:30:42.654321",
        "conn.log": "2024-01-15T10:30:40.987654",
        "dns.log": "2024-01-15T10:30:38.456789"
    },
    "monitoring_mode": "TEMPO_REAL"
}
```

## 🔍 Logs

O sistema registra logs detalhados:

### Modo Tempo Real
```
⚡ Monitor do Zeek iniciado em modo TEMPO REAL (verificação a cada 3s)
```

### Primeira Verificação
```
🆕 Primeira verificação de notice.log, buscando logs das últimas 1 hora(s)
```

### Verificações Seguintes
```
📅 Buscando logs notice.log desde 2024-01-15 10:30:45 (último processado: 2024-01-15 10:30:42)
✅ Atualizado último timestamp de notice.log para 2024-01-15 10:30:48
```

### Incidentes Detectados
```
✅ 2 incidente(s) detectado(s) em notice.log (período: 10:30:45 - 10:30:48)
📊 Total de 2 incidente(s) detectado(s) nesta verificação
```

## ⚙️ Considerações Técnicas

### Recursos do Sistema

- **CPU**: Verificação a cada 3s não impacta significativamente
- **Rede**: Apenas requisições HTTP necessárias (sem reprocessamento)
- **Memória**: Rastreamento mínimo de timestamps

### Limitações

- **Não é 100% tempo real**: Ainda há um intervalo de 3 segundos (configurável)
- **Depende da API do Zeek**: A latência da API afeta o tempo total
- **Primeira execução**: Busca logs das últimas horas (pode levar mais tempo)

### Recomendações

- **Produção**: Use intervalo de 3-5 segundos (boa relação tempo real/recursos)
- **Desenvolvimento**: Pode usar 1 segundo para testes
- **Recursos limitados**: Use 10-60 segundos se necessário

## 🚀 Resultado

Com essas mudanças, o sistema agora detecta e bloqueia atacantes em **tempo quase real**, reduzindo drasticamente o tempo de resposta a incidentes de segurança.

**Tempo Total de Detecção e Bloqueio (TtB):**
- **Antes**: 60-120 segundos
- **Agora**: 3-10 segundos
- **Melhoria**: ~90% mais rápido

