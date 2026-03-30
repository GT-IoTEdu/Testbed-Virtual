# 📊 Teste de Tempos de Detecção e Bloqueio Automático

## 📋 Visão Geral

Este script permite testar os tempos de detecção (TtD) e bloqueio (TtB) em um cenário real de ataque SQL Injection usando sqlmap. O script monitora automaticamente todo o fluxo desde a geração do log do Zeek até o bloqueio efetivo do atacante.

## 🎯 Cenário de Teste

O teste simula o seguinte cenário:

1. **Atacante executa sqlmap** → Gera tráfego SQL Injection
2. **Zeek detecta e gera log** → Cria entrada em `notice.log` com tag "atacante"
3. **API detecta o log** → Salva incidente no banco de dados
4. **API processa o incidente** → Marca como processado e aplica bloqueio automático
5. **Bloqueio efetivado** → IP adicionado ao alias "Bloqueados" no pfSense

## 📈 Métricas Medidas

### TtD (Time to Detection)
Tempo desde a geração do log do Zeek até o salvamento do incidente no banco de dados.

**Fórmula**: `detected_at - zeek_log_time`

### TtP (Time to Processing)
Tempo desde o salvamento do incidente até seu processamento para bloqueio.

**Fórmula**: `processed_at - detected_at`

### TtB (Time to Block)
Tempo desde a detecção até o bloqueio efetivo (criação do feedback).

**Fórmula**: `feedback.created_at - detected_at`

### TtB desde Zeek
Tempo total desde a geração do log do Zeek até o bloqueio efetivo.

**Fórmula**: `feedback.created_at - zeek_log_time`

## 🚀 Como Usar

### Pré-requisitos

1. Sistema em execução:
   - Zeek rodando e monitorando tráfego
   - API backend em execução
   - pfSense configurado
   - Banco de dados acessível

2. Ambiente de teste preparado:
   - Máquina atacante com sqlmap instalado
   - Servidor alvo vulnerável a SQL Injection

### Execução do Teste

#### 1. Executar o Script

```bash
cd backend/scripts
python test_detection_blocking_times.py
```

**IP padrão do atacante**: O script usa por padrão o IP `192.168.59.4` (MAC: `24:0a:64:1c:73:44`) como atacante de teste.

#### 2. Opções de Linha de Comando

```bash
# Usar IP padrão do atacante (192.168.59.4)
python test_detection_blocking_times.py

# Monitorar IP específico diferente
python test_detection_blocking_times.py --target-ip 192.168.100.10

# Usar outro IP como padrão
python test_detection_blocking_times.py --attacker-ip 192.168.59.4

# Não disparar processamento automaticamente (aguardar processamento automático)
python test_detection_blocking_times.py --no-auto-process
```

#### 3. Informações do Atacante de Teste

- **IP**: `192.168.59.4`
- **MAC**: `24:0a:64:1c:73:44`
- **Tipo**: Computador na rede de teste

#### 4. Durante o Teste

1. O script iniciará e aguardará pela detecção de logs notice.log com SQL Injection - Atacante
2. Execute o ataque sqlmap **da máquina atacante** (IP: `192.168.59.4`):
   ```bash
   # Na máquina atacante (192.168.59.4)
   sqlmap -u "http://<servidor_alvo>/vulnerable.php?id=1" --batch
   ```
3. O script monitorará automaticamente:
   - Geração do log do Zeek (do IP `192.168.59.4`)
   - Criação do incidente no banco
   - Processamento e bloqueio automático
4. Ao final, exibirá todos os tempos calculados

## 📊 Exemplo de Saída

```
================================================================================
INÍCIO DO TESTE: Detecção e Bloqueio Automático
================================================================================

Instruções:
1. Execute um ataque sqlmap contra o servidor alvo
2. O script irá monitorar a detecção e bloqueio automático

Aguardando ataque sqlmap...

================================================================================
MONITORAMENTO: Procurando por logs notice.log com SQL Injection - Atacante
================================================================================

✅ LOG DETECTADO:
  - IP: 192.168.100.10
  - Tipo: SQL::SQL_Injection_Attacker
  - Mensagem: SQL injection attack detected
  - Timestamp Zeek: 2024-01-15 14:30:25.123456

================================================================================
MONITORAMENTO: Aguardando criação do incidente no banco de dados
================================================================================

✅ INCIDENTE CRIADO:
  - ID: 123
  - IP: 192.168.100.10
  - Tipo: SQL Injection - Atacante
  - Detectado em: 2024-01-15 14:30:26.456789
  - Processado em: None

================================================================================
PROCESSAMENTO: Disparando processamento de incidentes pendentes
================================================================================

📊 RESULTADO DO PROCESSAMENTO:
  - Processados: 1
  - Bloqueados: 1
  - Ignorados: 0
  - Erros: 0

================================================================================
MONITORAMENTO: Aguardando bloqueio efetivo
================================================================================

✅ BLOQUEIO EFETIVADO:
  - Feedback ID: 45
  - Criado em: 2024-01-15 14:30:28.789012
  - Motivo: Bloqueio automático por incidente de segurança - Incidente 123: SQL Injection - Atacante

================================================================================
RESULTADOS DO TESTE
================================================================================

📊 TEMPOS CALCULADOS:

⏱️  TtD (Time to Detection):
  - Tempo: 1.333s (1.333s)
  - Zeek log: 2024-01-15T14:30:25.123456
  - Detectado: 2024-01-15T14:30:26.456789

⏱️  TtP (Time to Processing):
  - Tempo: 2.123s (2.123s)
  - Detectado: 2024-01-15T14:30:26.456789
  - Processado: 2024-01-15T14:30:28.579789

⏱️  TtB (Time to Block):
  - Tempo: 2.332s (2.332s)
  - Detectado: 2024-01-15T14:30:26.456789
  - Bloqueado: 2024-01-15T14:30:28.789012

⏱️  TtB (desde log Zeek):
  - Tempo: 3.666s (3.666s)
  - Zeek log: 2024-01-15T14:30:25.123456
  - Bloqueado: 2024-01-15T14:30:28.789012

================================================================================

✅ TESTE CONCLUÍDO COM SUCESSO!
```

## 🔍 Logs Detalhados

O sistema agora inclui logs detalhados com prefixo `⏱️ [TIMING]` em todos os pontos críticos:

### Pontos de Medição

1. **Detecção em Log Zeek** (`zeek_service.py`)
   - Timestamp do log do Zeek
   - Tempo desde geração do log até detecção pela API

2. **Salvamento do Incidente** (`incident_service.py`)
   - Timestamp de salvamento
   - Tempo desde detecção até salvamento

3. **Processamento** (`incident_service.py`)
   - Timestamp de início do processamento
   - Timestamp de marcação como processado
   - Duração do processamento

4. **Aplicação do Bloqueio** (`incident_service.py`)
   - Timestamp de início do bloqueio
   - Timestamp de criação do feedback (bloqueio efetivo)
   - TtB calculado

### Visualizando Logs

Os logs podem ser visualizados em:

- **Console**: Saída padrão do script
- **Logs da API**: Arquivos de log do backend (se configurados)
- **Banco de dados**: Campos `detected_at`, `processed_at` e `BlockingFeedbackHistory.created_at`

## 📝 Notas Importantes

1. **Tempo de Espera**: O script aguarda até 10 minutos por logs do Zeek e 5 minutos para cada etapa subsequente

2. **Processamento Automático**: Por padrão, o script dispara o processamento automaticamente. Use `--no-auto-process` se quiser aguardar o processamento automático do sistema

3. **Múltiplos Ataques**: Se houver múltiplos ataques simultâneos, o script detectará o primeiro que corresponder aos critérios

4. **IP Específico**: Use `--target-ip` para monitorar apenas um IP específico (útil para testes controlados)

## 🛠️ Troubleshooting

### Nenhum log detectado
- Verifique se o Zeek está rodando e monitorando tráfego
- Confirme que o ataque sqlmap foi executado
- Verifique conectividade com a API do Zeek

### Incidente não criado
- Verifique se a API está processando logs do Zeek
- Confira logs da API para erros
- Verifique conectividade com o banco de dados

### Bloqueio não efetivado
- Verifique se o processamento foi executado (`/incidents/process-batch`)
- Confira se o dispositivo existe no banco DHCP
- Verifique logs do AliasService para erros

## 📚 Arquivos Relacionados

- `test_detection_blocking_times.py`: Script principal de teste
- `test_blocking_times_average.py`: Script para calcular médias entre múltiplas execuções
- `backend/services_scanners/incident_service.py`: Serviço de incidentes com logs de timing
- `backend/services_scanners/zeek_service.py`: Serviço Zeek com logs de timing

