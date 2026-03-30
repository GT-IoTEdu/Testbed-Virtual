# ⏱️ Tempos de Detecção e Bloqueio (TtD e TtB)

## 📋 Visão Geral

Este documento descreve como obter os tempos de detecção (TtD - Time to Detection) e tempo até bloqueio (TtB - Time to Block) para incidentes de segurança com bloqueio automático.

## 📊 Métricas

### TtD - Time to Detection
- **Definição**: Tempo desde a detecção do incidente pelo Zeek até o processamento do incidente no sistema
- **Cálculo**: `detected_at` → `processed_at`
- **Significado**: Quanto tempo levou para o sistema processar a detecção

### TtB - Time to Block
- **Definição**: Tempo desde a detecção até o bloqueio efetivo do dispositivo no firewall
- **Cálculo**: `detected_at` → `feedback.created_at` (BlockingFeedbackHistory)
- **Significado**: Quanto tempo levou desde a detecção até o bloqueio real

## 🔗 Endpoints Disponíveis

### 1. Tempos de um Incidente Específico

**Endpoint:**
```
GET /api/incidents/{incident_id}/blocking-times
```

**Exemplo de Uso:**
```bash
curl -X GET "http://localhost:8000/api/incidents/123/blocking-times"
```

**Resposta:**
```json
{
  "incident_id": 123,
  "device_ip": "192.168.100.50",
  "incident_type": "SQL Injection - Atacante",
  "detected_at": "2024-01-15T10:00:00",
  "processed_at": "2024-01-15T10:00:05",
  "blocked_at": "2024-01-15T10:00:07",
  "ttd": {
    "seconds": 5.234,
    "readable": "5s"
  },
  "ttb": {
    "seconds": 7.456,
    "readable": "7s"
  },
  "blocked": true
}
```

### 2. Tempos de Todos os Incidentes Bloqueados

**Endpoint:**
```
GET /api/incidents/blocking-times/all?limit=100
```

**Parâmetros:**
- `limit` (opcional): Número máximo de incidentes a retornar (padrão: 100, máximo: 500)

**Exemplo de Uso:**
```bash
curl -X GET "http://localhost:8000/api/incidents/blocking-times/all?limit=50"
```

**Resposta:**
```json
[
  {
    "incident_id": 123,
    "device_ip": "192.168.100.50",
    "incident_type": "SQL Injection - Atacante",
    "detected_at": "2024-01-15T10:00:00",
    "processed_at": "2024-01-15T10:00:05",
    "blocked_at": "2024-01-15T10:00:07",
    "ttd": {
      "seconds": 5.234,
      "readable": "5s"
    },
    "ttb": {
      "seconds": 7.456,
      "readable": "7s"
    },
    "blocked": true
  },
  {
    "incident_id": 124,
    "device_ip": "192.168.100.51",
    "incident_type": "Malware - Atacante",
    "detected_at": "2024-01-15T10:15:00",
    "processed_at": "2024-01-15T10:15:08",
    "blocked_at": "2024-01-15T10:15:12",
    "ttd": {
      "seconds": 8.123,
      "readable": "8s"
    },
    "ttb": {
      "seconds": 12.789,
      "readable": "12s"
    },
    "blocked": true
  }
]
```

## 📐 Interpretação dos Valores

### TtD (Time to Detection)

- **Valor ideal**: < 5 segundos
- **Aceitável**: 5-30 segundos
- **Necessita otimização**: > 30 segundos

**Casos Especiais:**
- `ttd = null`: Incidente ainda não foi processado
- Sistema processa incidentes em lote, então pode haver atraso

### TtB (Time to Block)

- **Valor ideal**: < 10 segundos
- **Aceitável**: 10-60 segundos  
- **Necessita otimização**: > 60 segundos

**Casos Especiais:**
- `ttb = null`: Bloqueio não foi aplicado ou não há feedback
- `blocked = false`: Dispositivo não foi bloqueado ainda

## 🔍 Análise de Dados

### Estatísticas Agregadas

Para análise completa, você pode calcular:

```python
# Exemplo em Python
import requests
from statistics import mean, median

response = requests.get("http://localhost:8000/api/incidents/blocking-times/all?limit=100")
data = response.json()

# Filtrar apenas incidentes com bloqueio
blocked = [inc for inc in data if inc.get('blocked')]

ttd_times = [inc['ttd']['seconds'] for inc in blocked if inc['ttd']['seconds'] is not None]
ttb_times = [inc['ttb']['seconds'] for inc in blocked if inc['ttb']['seconds'] is not None]

print(f"TtD médio: {mean(ttd_times):.2f}s")
print(f"TtD mediano: {median(ttd_times):.2f}s")
print(f"TtB médio: {mean(ttb_times):.2f}s")
print(f"TtB mediano: {median(ttb_times):.2f}s")
```

### Análise por Tipo de Incidente

Para entender qual tipo de ataque leva mais tempo para ser bloqueado:

```python
from collections import defaultdict

by_type = defaultdict(list)
for inc in blocked:
    if inc['ttb']['seconds'] is not None:
        by_type[inc['incident_type']].append(inc['ttb']['seconds'])

for incident_type, times in by_type.items():
    print(f"{incident_type}: TtB médio = {mean(times):.2f}s")
```

## 🔧 Pontos de Integração no Sistema

### Fluxo de Dados

```
Zeek detecta → detected_at é registrado
     ↓
IncidentService processa → processed_at é registrado (TtD calculado aqui)
     ↓
AliasService aplica bloqueio → IP movido para alias "Bloqueados"
     ↓
BlockingFeedbackService cria feedback → created_at registrado (TtB calculado aqui)
```

### Timestamps Importantes

| Timestamp | Localização | Descrição |
|-----------|-------------|-----------|
| `detected_at` | `zeek_incidents.detected_at` | Quando o Zeek detectou o incidente |
| `processed_at` | `zeek_incidents.processed_at` | Quando o sistema processou |
| `created_at` | `blocking_feedback_history.created_at` | Quando o bloqueio foi aplicado |

## 📈 Exemplos de Uso

### 1. Verificar Performance do Sistema

```bash
# Ver todos os incidentes bloqueados com tempos
curl -X GET "http://localhost:8000/api/incidents/blocking-times/all" | jq '.[] | {id: .incident_id, ip: .device_ip, ttd: .ttd.readable, ttb: .ttb.readable}'
```

### 2. Identificar Incidentes Lentos

```bash
# Filtrar incidentes com TtB > 30 segundos
curl -X GET "http://localhost:8000/api/incidents/blocking-times/all" | jq '.[] | select(.ttb.seconds > 30)'
```

### 3. Dashboard de Métricas

```javascript
// Exemplo em JavaScript para dashboard
async function getMetrics() {
  const response = await fetch('/api/incidents/blocking-times/all?limit=100');
  const incidents = await response.json();
  
  const blocked = incidents.filter(inc => inc.blocked);
  
  const avgTtD = blocked
    .map(inc => inc.ttd.seconds)
    .filter(s => s !== null)
    .reduce((a, b) => a + b, 0) / blocked.length;
    
  const avgTtB = blocked
    .map(inc => inc.ttb.seconds)
    .filter(s => s !== null)
    .reduce((a, b) => a + b, 0) / blocked.length;
  
  console.log(`TtD médio: ${avgTtD.toFixed(2)}s`);
  console.log(`TtB médio: ${avgTtB.toFixed(2)}s`);
}
```

## 🚨 Troubleshooting

### TtD ou TtB Retornando NULL

**Possíveis Causas:**
1. **Incidente não processado**: `processed_at` é NULL
2. **Bloqueio não aplicado**: Não há feedback de bloqueio
3. **Feedback manual**: Feedback criado manualmente (não "Sistema Automático")
4. **Dispositivo não no DHCP**: IP não está em `dhcp_static_mappings`

**Solução:**
- Verificar se incidente tem `processed_at` preenchido
- Verificar se feedback foi criado pelo sistema automático
- Verificar logs do sistema para erros no processo de bloqueio

### Tempos Anormalmente Altos

**Possíveis Causas:**
1. **Processamento em lote**: Incidentes processados em lotes com delay
2. **Latência de rede**: Comunicação com pfSense lenta
3. **Carga do sistema**: Sistema sobrecarregado

**Solução:**
- Verificar configuração de processamento em lote
- Verificar conectividade com pfSense
- Monitorar recursos do servidor

## 📚 Referências

- [Sistema de Bloqueio Automático](./AUTO_BLOCKING_SYSTEM.md)
- [Solução de Bloqueio em Lote](./SOLUCAO_BLOQUEIO_AUTOMATICO_EM_LOTE.md)
- [Sistema de Feedback](./BLOCKING_FEEDBACK_SYSTEM.md)

