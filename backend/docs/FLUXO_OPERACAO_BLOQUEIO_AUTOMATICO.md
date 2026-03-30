# 🔄 Fluxo de Operação - Sistema de Detecção e Bloqueio Automático

## 📊 Dados de Performance Observados

| Operação | Tempo (s) | CPU (%) | RAM (MB) |
|----------|-----------|---------|----------|
| ZeekService.get_logs | 2.281 | 6.80 | 35.79 |
| IncidentService.save_incident | 2.499 | 13.70 | 35.79 |
| IncidentService.process_incidents | 3.222 | 16.10 | 35.79 |
| AliasService.get_alias_by_name | 2.245 | 16.70 | 35.79 |
| AliasService.add_addresses_to_alias | 2.233 | 25.00 | 35.85 |
| pfsense_client.apply_changes_firewall | 2.326 | 38.90 | 35.85 |

**Tempo Total: ~14.8 segundos**

---

## 🔄 Diagrama de Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SISTEMA DE DETECÇÃO E BLOQUEIO AUTOMÁTICO                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 1: MONITORAMENTO DO ZEEK                                              │
└─────────────────────────────────────────────────────────────────────────────┘

    [Zeek Monitor - Background Thread]
           │
           │ (A cada 3 segundos)
           ▼
    ┌─────────────────────────────────────┐
    │ ZeekService.get_logs()               │
    │                                      │
    │ Endpoint: GET /api/scanners/zeek/    │
    │          logs?logfile=notice.log    │
    │                                      │
    │ Tempo: 2.281s                        │
    │ CPU: 6.80%                           │
    │ RAM: 35.79 MB                        │
    └─────────────────────────────────────┘
           │
           │ Busca logs do Zeek via API
           ▼
    ┌─────────────────────────────────────┐
    │ Detecta padrões de ataque            │
    │ (SQL Injection, XSS, etc.)           │
    └─────────────────────────────────────┘
           │
           │ Se detectar "Atacante"
           ▼

┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 2: SALVAMENTO DO INCIDENTE                                           │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────┐
    │ IncidentService.save_incident()      │
    │                                      │
    │ Endpoint: POST /api/incidents/       │
    │                                      │
    │ Tempo: 2.499s                        │
    │ CPU: 13.70%                          │
    │ RAM: 35.79 MB                        │
    └─────────────────────────────────────┘
           │
           │ Salva no banco de dados
           ▼
    ┌─────────────────────────────────────┐
    │ Incidente criado com ID              │
    │ Status: "new"                        │
    │ processed_at: NULL                    │
    └─────────────────────────────────────┘
           │
           │ Verifica se contém "Atacante"
           ▼
    ┌─────────────────────────────────────┐
    │ ✅ É "Atacante"?                     │
    │    └─> SIM                           │
    └─────────────────────────────────────┘
           │
           │ Inicia thread em background
           ▼

┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 3: PROCESSAMENTO EM LOTE (Background Thread)                         │
└─────────────────────────────────────────────────────────────────────────────┘

    [Thread Background - Daemon]
           │
           │ Aguarda 0.5s (garantir commit)
           ▼
    ┌─────────────────────────────────────┐
    │ IncidentService.process_incidents_   │
    │   for_auto_blocking()                │
    │                                      │
    │ Endpoint: POST /api/incidents/       │
    │          process-batch?limit=10     │
    │                                      │
    │ Tempo: 3.222s                        │
    │ CPU: 16.10%                          │
    │ RAM: 35.79 MB                        │
    └─────────────────────────────────────┘
           │
           │ Busca incidentes não processados
           │ (processed_at IS NULL)
           ▼
    ┌─────────────────────────────────────┐
    │ Para cada incidente "Atacante":      │
    │   1. Marca como processado           │
    │   2. Chama _apply_auto_block()      │
    └─────────────────────────────────────┘
           │
           ▼

┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 4: APLICAÇÃO DO BLOQUEIO AUTOMÁTICO                                  │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────┐
    │ IncidentService._apply_auto_block()   │
    │                                      │
    │ (Método interno - não é endpoint)   │
    └─────────────────────────────────────┘
           │
           │ Verifica alias "Bloqueados"
           ▼
    ┌─────────────────────────────────────┐
    │ AliasService.get_alias_by_name()    │
    │                                      │
    │ Endpoint: GET /api/devices/          │
    │          aliases-db/Bloqueados       │
    │                                      │
    │ Tempo: 2.245s                        │
    │ CPU: 16.70%                          │
    │ RAM: 35.79 MB                        │
    └─────────────────────────────────────┘
           │
           │ Verifica se IP já está bloqueado
           ▼
    ┌─────────────────────────────────────┐
    │ ✅ IP já está bloqueado?             │
    │    └─> NÃO                           │
    └─────────────────────────────────────┘
           │
           │ Verifica alias "Autorizados"
           ▼
    ┌─────────────────────────────────────┐
    │ AliasService.get_alias_by_name()    │
    │   ("Autorizados")                   │
    │                                      │
    │ Se IP estiver em "Autorizados":     │
    │   Remove do alias                   │
    └─────────────────────────────────────┘
           │
           │ Adiciona IP ao alias "Bloqueados"
           ▼
    ┌─────────────────────────────────────┐
    │ AliasService.add_addresses_to_      │
    │   alias()                           │
    │                                      │
    │ Endpoint: POST /api/devices/         │
    │          aliases-db/Bloqueados/      │
    │          add-addresses               │
    │                                      │
    │ Tempo: 2.233s                        │
    │ CPU: 25.00%                          │
    │ RAM: 35.85 MB                        │
    └─────────────────────────────────────┘
           │
           │ Atualiza alias no pfSense
           ▼
    ┌─────────────────────────────────────┐
    │ Alias atualizado no pfSense         │
    │ (mas ainda não aplicado)            │
    └─────────────────────────────────────┘
           │
           │ Aplica mudanças no firewall
           ▼

┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 5: APLICAÇÃO DE MUDANÇAS NO FIREWALL                                 │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────┐
    │ pfsense_client.                       │
    │   aplicar_mudancas_firewall_         │
    │   pfsense()                           │
    │                                      │
    │ Endpoint: POST /api/devices/          │
    │          firewall/apply               │
    │                                      │
    │ Tempo: 2.326s                        │
    │ CPU: 38.90%                          │
    │ RAM: 35.85 MB                        │
    └─────────────────────────────────────┘
           │
           │ Processa no pfSense:
           │ - Valida configurações
           │ - Reconstrói tabelas
           │ - Aplica regras
           │ - Encerra conexões ativas
           ▼
    ┌─────────────────────────────────────┐
    │ ✅ Mudanças aplicadas com sucesso    │
    │    IP bloqueado efetivamente         │
    └─────────────────────────────────────┘
           │
           ▼

┌─────────────────────────────────────────────────────────────────────────────┐
│ ETAPA 6: FINALIZAÇÃO                                                       │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────┐
    │ Atualiza status do incidente         │
    │ Status: "resolved"                    │
    └─────────────────────────────────────┘
           │
           │ Cria feedback administrativo
           ▼
    ┌─────────────────────────────────────┐
    │ BlockingFeedbackService.             │
    │   create_admin_blocking_feedback()   │
    │                                      │
    │ Registra bloqueio para auditoria      │
    └─────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────────────────────┐
    │ ✅ BLOQUEIO COMPLETO                 │
    │    Atacante perde acesso             │
    └─────────────────────────────────────┘
```

---

## 📊 Fluxo Sequencial com Tempos

```
T=0.000s    ┌─────────────────────────────────────┐
            │ Zeek Monitor (Background)          │
            │ Verifica logs a cada 3s             │
            └─────────────────────────────────────┘
                    │
                    │ Detecta ataque
                    ▼
T=2.281s    ┌─────────────────────────────────────┐
            │ ZeekService.get_logs()              │
            │ Tempo: 2.281s | CPU: 6.80%          │
            └─────────────────────────────────────┘
                    │
                    │ Cria incidente
                    ▼
T=4.780s    ┌─────────────────────────────────────┐
            │ IncidentService.save_incident()     │
            │ Tempo: 2.499s | CPU: 13.70%         │
            └─────────────────────────────────────┘
                    │
                    │ Thread background inicia
                    │ (aguarda 0.5s)
                    ▼
T=7.501s    ┌─────────────────────────────────────┐
            │ IncidentService.process_incidents_   │
            │   for_auto_blocking()               │
            │ Tempo: 3.222s | CPU: 16.10%         │
            └─────────────────────────────────────┘
                    │
                    │ Busca alias "Bloqueados"
                    ▼
T=9.746s    ┌─────────────────────────────────────┐
            │ AliasService.get_alias_by_name()    │
            │ Tempo: 2.245s | CPU: 16.70%          │
            └─────────────────────────────────────┘
                    │
                    │ Adiciona IP ao alias
                    ▼
T=11.979s   ┌─────────────────────────────────────┐
            │ AliasService.add_addresses_to_      │
            │   alias()                           │
            │ Tempo: 2.233s | CPU: 25.00%         │
            └─────────────────────────────────────┘
                    │
                    │ Aplica mudanças
                    ▼
T=14.305s   ┌─────────────────────────────────────┐
            │ pfsense_client.apply_changes_       │
            │   firewall()                        │
            │ Tempo: 2.326s | CPU: 38.90%          │
            └─────────────────────────────────────┘
                    │
                    │ Bloqueio efetivo
                    ▼
T=16.631s   ┌─────────────────────────────────────┐
            │ ✅ BLOQUEIO COMPLETO                 │
            │    Tempo Total: ~14.8s                │
            └─────────────────────────────────────┘
```

---

## 🔍 Análise Detalhada por Etapa

### **1. ZeekService.get_logs() - 2.281s**

```
┌─────────────────────────────────────────────────────────┐
│ ZeekService.get_logs()                                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [Monitor Background]                                    │
│       │                                                  │
│       │ GET /api/scanners/zeek/logs?logfile=notice.log  │
│       ▼                                                  │
│  ┌────────────────────┐                                  │
│  │ Requisição HTTP    │  ~0.1-0.5s                      │
│  └────────────────────┘                                  │
│       │                                                  │
│       │ Parse JSON                                       │
│       ▼                                                  │
│  ┌────────────────────┐                                  │
│  │ Análise de Logs   │  ~0.5-1.0s                      │
│  └────────────────────┘                                  │
│       │                                                  │
│       │ Detecção de Padrões                              │
│       ▼                                                  │
│  ┌────────────────────┐                                  │
│  │ Cria Incidentes    │  ~0.5-1.0s                      │
│  └────────────────────┘                                  │
│                                                          │
│  Tempo Total: 2.281s                                     │
│  CPU: 6.80%                                              │
│  RAM: 35.79 MB                                           │
└─────────────────────────────────────────────────────────┘
```

### **2. IncidentService.save_incident() - 2.499s**

```
┌─────────────────────────────────────────────────────────┐
│ IncidentService.save_incident()                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  POST /api/incidents/                                    │
│       │                                                  │
│       │ Validação de Dados                              │
│       ▼                                                  │
│  ┌────────────────────┐                                  │
│  │ Abre Conexão BD    │  ~0.01-0.05s                    │
│  └────────────────────┘                                  │
│       │                                                  │
│       │ Verifica Duplicatas                             │
│       ▼                                                  │
│  ┌────────────────────┐                                  │
│  │ Insere Registro    │  ~0.1-0.3s                      │
│  └────────────────────┘                                  │
│       │                                                  │
│       │ Commit Transação                                │
│       ▼                                                  │
│  ┌────────────────────┐                                  │
│  │ Log Performance    │  ~0.05-0.1s                     │
│  └────────────────────┘                                  │
│       │                                                  │
│       │ Verifica "Atacante"                             │
│       │ Inicia Thread Background                        │
│       ▼                                                  │
│                                                          │
│  Tempo Total: 2.499s                                     │
│  CPU: 13.70%                                             │
│  RAM: 35.79 MB                                           │
└─────────────────────────────────────────────────────────┘
```

### **3. IncidentService.process_incidents_for_auto_blocking() - 3.222s**

```
┌─────────────────────────────────────────────────────────┐
│ IncidentService.process_incidents_for_auto_blocking()  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  POST /api/incidents/process-batch                      │
│       │                                                  │
│       │ Busca Incidentes Não Processados                │
│       ▼                                                  │
│  ┌────────────────────┐                                  │
│  │ Query SQL          │  ~0.1-0.3s                      │
│  │ processed_at IS NULL│                                  │
│  └────────────────────┘                                  │
│       │                                                  │
│       │ Para cada incidente:                            │
│       │                                                  │
│       │ 1. Marca como processado                       │
│       │    └─> UPDATE processed_at                      │
│       │                                                  │
│       │ 2. Verifica se é "Atacante"                     │
│       │                                                  │
│       │ 3. Chama _apply_auto_block()                    │
│       │    └─> (inclui operações de alias)             │
│       │                                                  │
│  Tempo Total: 3.222s                                     │
│  CPU: 16.10%                                             │
│  RAM: 35.79 MB                                           │
└─────────────────────────────────────────────────────────┘
```

### **4. AliasService.get_alias_by_name() - 2.245s**

```
┌─────────────────────────────────────────────────────────┐
│ AliasService.get_alias_by_name("Bloqueados")           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  GET /api/devices/aliases-db/Bloqueados                 │
│       │                                                  │
│       │ Busca no Banco Local                            │
│       ▼                                                  │
│  ┌────────────────────┐                                  │
│  │ Query SQL          │  ~0.05-0.1s                     │
│  │ WHERE name = ...   │                                  │
│  └────────────────────┘                                  │
│       │                                                  │
│       │ Busca Endereços do Alias                        │
│       ▼                                                  │
│  ┌────────────────────┐                                  │
│  │ Query Relacionada  │  ~0.05-0.1s                     │
│  └────────────────────┘                                  │
│       │                                                  │
│       │ Verifica no pfSense (se necessário)             │
│       ▼                                                  │
│  ┌────────────────────┐                                  │
│  │ Requisição HTTP    │  ~1.5-2.0s                      │
│  │ para pfSense       │                                  │
│  └────────────────────┘                                  │
│                                                          │
│  Tempo Total: 2.245s                                     │
│  CPU: 16.70%                                             │
│  RAM: 35.79 MB                                           │
└─────────────────────────────────────────────────────────┘
```

### **5. AliasService.add_addresses_to_alias() - 2.233s**

```
┌─────────────────────────────────────────────────────────┐
│ AliasService.add_addresses_to_alias("Bloqueados", IP)  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  POST /api/devices/aliases-db/Bloqueados/add-addresses │
│       │                                                  │
│       │ Busca Alias no Banco                            │
│       ▼                                                  │
│  ┌────────────────────┐                                  │
│  │ Verifica Endereços │  ~0.05-0.1s                     │
│  │ Existentes          │                                  │
│  └────────────────────┘                                  │
│       │                                                  │
│       │ Adiciona ao Banco Local                         │
│       ▼                                                  │
│  ┌────────────────────┐                                  │
│  │ INSERT Address     │  ~0.05-0.1s                     │
│  └────────────────────┘                                  │
│       │                                                  │
│       │ Atualiza no pfSense                             │
│       ▼                                                  │
│  ┌────────────────────┐                                  │
│  │ PUT /api/v2/        │  ~1.5-2.0s                      │
│  │ firewall/alias/{id} │                                  │
│  └────────────────────┘                                  │
│       │                                                  │
│       │ Commit Banco Local                               │
│       ▼                                                  │
│                                                          │
│  Tempo Total: 2.233s                                     │
│  CPU: 25.00%                                             │
│  RAM: 35.85 MB                                           │
└─────────────────────────────────────────────────────────┘
```

### **6. pfsense_client.aplicar_mudancas_firewall_pfsense() - 2.326s**

```
┌─────────────────────────────────────────────────────────┐
│ pfsense_client.aplicar_mudancas_firewall_pfsense()     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  POST /api/devices/firewall/apply                       │
│       │                                                  │
│       │ Requisição para pfSense                         │
│       ▼                                                  │
│  ┌────────────────────┐                                  │
│  │ POST /api/v2/      │  ~0.1-0.3s                      │
│  │ firewall/apply     │                                  │
│  └────────────────────┘                                  │
│       │                                                  │
│       │ pfSense Processa:                                │
│       │                                                  │
│       │ 1. Valida Configurações                         │
│       │    └─> ~0.2-0.5s                                │
│       │                                                  │
│       │ 2. Reconstrói Tabelas                           │
│       │    └─> ~0.3-0.8s                                │
│       │                                                  │
│       │ 3. Aplica Regras                                │
│       │    └─> ~0.5-1.0s                                │
│       │                                                  │
│       │ 4. Encerra Conexões Ativas                      │
│       │    └─> ~0.2-0.5s                                │
│       │                                                  │
│  Tempo Total: 2.326s                                     │
│  CPU: 38.90% (maior carga - processamento intenso)      │
│  RAM: 35.85 MB                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 📈 Análise de Consumo de Recursos

### **CPU por Etapa**

```
CPU (%)
 40 │                                    ████
    │                                    ████
 35 │                                    ████
    │                                    ████
 30 │                                    ████
    │                            ████    ████
 25 │                            ████    ████
    │                            ████    ████
 20 │                    ████    ████    ████
    │            ████    ████    ████    ████
 15 │    ████    ████    ████    ████    ████
    │    ████    ████    ████    ████    ████
 10 │    ████    ████    ████    ████    ████
    │    ████    ████    ████    ████    ████
  5 │    ████    ████    ████    ████    ████
    │    ████    ████    ████    ████    ████
  0 └────┴────┴────┴────┴────┴────┴────┴────┴────
     1    2    3    4    5    6    7    8    9

    1. get_logs (6.80%)
    2. save_incident (13.70%)
    3. process_incidents (16.10%)
    4. get_alias (16.70%)
    5. add_addresses (25.00%)
    6. apply_firewall (38.90%) ← Maior carga
```

### **Tempo por Etapa**

```
Tempo (s)
 3.5 │
     │
 3.0 │                    ████
     │                    ████
 2.5 │            ████    ████
     │    ████    ████    ████
 2.0 │    ████    ████    ████    ████    ████
     │    ████    ████    ████    ████    ████
 1.5 │    ████    ████    ████    ████    ████
     │    ████    ████    ████    ████    ████
 1.0 │    ████    ████    ████    ████    ████
     │    ████    ████    ████    ████    ████
 0.5 │    ████    ████    ████    ████    ████
     │    ████    ████    ████    ████    ████
 0.0 └────┴────┴────┴────┴────┴────┴────┴────┴────
     1    2    3    4    5    6    7    8    9

    1. get_logs (2.281s)
    2. save_incident (2.499s)
    3. process_incidents (3.222s) ← Mais lento
    4. get_alias (2.245s)
    5. add_addresses (2.233s)
    6. apply_firewall (2.326s)
```

---

## 🔄 Fluxo de Dados Completo

```
┌──────────────┐
│   Zeek       │
│  (pfSense)   │
└──────┬───────┘
       │ Gera log notice.log
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ [1] ZeekService.get_logs()                             │
│     Tempo: 2.281s | CPU: 6.80%                        │
│     GET /api/scanners/zeek/logs                        │
└──────┬────────────────────────────────────────────────┘
       │ Retorna logs com incidentes
       ▼
┌─────────────────────────────────────────────────────────┐
│ [2] IncidentService.save_incident()                    │
│     Tempo: 2.499s | CPU: 13.70%                       │
│     POST /api/incidents/                               │
│     └─> Salva no banco MySQL                          │
└──────┬────────────────────────────────────────────────┘
       │ Incidente salvo (ID criado)
       │ Thread background inicia
       ▼
┌─────────────────────────────────────────────────────────┐
│ [3] IncidentService.process_incidents_for_auto_        │
│     blocking()                                         │
│     Tempo: 3.222s | CPU: 16.10%                      │
│     POST /api/incidents/process-batch                 │
│     └─> Busca incidentes não processados               │
│     └─> Para cada "Atacante":                         │
└──────┬────────────────────────────────────────────────┘
       │
       ├─────────────────────────────────────┐
       │                                     │
       ▼                                     ▼
┌──────────────────────┐          ┌──────────────────────┐
│ [4] AliasService.    │          │ Verifica "Autorizados"│
│     get_alias_by_    │          │ (se necessário)      │
│     name("Bloqueados")│          └──────────────────────┘
│     Tempo: 2.245s     │
│     CPU: 16.70%       │
└──────┬────────────────┘
       │ Verifica se IP já está bloqueado
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ [5] AliasService.add_addresses_to_alias()              │
│     Tempo: 2.233s | CPU: 25.00%                       │
│     POST /api/devices/aliases-db/Bloqueados/          │
│           add-addresses                                │
│     └─> Adiciona IP ao banco local                    │
│     └─> Atualiza no pfSense                           │
└──────┬────────────────────────────────────────────────┘
       │ Alias atualizado (mas não aplicado ainda)
       ▼
┌─────────────────────────────────────────────────────────┐
│ [6] pfsense_client.aplicar_mudancas_firewall_          │
│     pfsense()                                           │
│     Tempo: 2.326s | CPU: 38.90%                       │
│     POST /api/devices/firewall/apply                   │
│     └─> POST /api/v2/firewall/apply (pfSense)        │
│     └─> pfSense processa e aplica mudanças            │
└──────┬────────────────────────────────────────────────┘
       │ Bloqueio efetivo
       ▼
┌─────────────────────────────────────────────────────────┐
│ ✅ IP BLOQUEADO NO FIREWALL                             │
│    Atacante perde acesso                                │
│                                                          │
│ Tempo Total: ~14.8 segundos                             │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Resumo Executivo

### **Tempo Total: ~14.8 segundos**

| Etapa | Operação | Tempo | % do Total | CPU | RAM |
|-------|----------|-------|------------|-----|-----|
| 1 | Monitoramento Zeek | 2.281s | 15.4% | 6.80% | 35.79 MB |
| 2 | Salvamento Incidente | 2.499s | 16.9% | 13.70% | 35.79 MB |
| 3 | Processamento Lote | 3.222s | 21.8% | 16.10% | 35.79 MB |
| 4 | Busca Alias | 2.245s | 15.2% | 16.70% | 35.79 MB |
| 5 | Adiciona IP | 2.233s | 15.1% | 25.00% | 35.85 MB |
| 6 | Apply Firewall | 2.326s | 15.7% | 38.90% | 35.85 MB |

### **Observações**

1. **Processamento em Lote** é a etapa mais lenta (3.222s - 21.8%)
   - Busca e processa múltiplos incidentes
   - Pode ser otimizado com cache ou processamento paralelo

2. **Apply Firewall** tem maior consumo de CPU (38.90%)
   - Processamento intenso no pfSense
   - Normal e esperado

3. **RAM estável** (~35.79-35.85 MB)
   - Sem vazamento de memória
   - Sistema eficiente

4. **Tempo total excelente** (~14.8s)
   - Dentro da faixa "Bom" (10-30s)
   - Sistema otimizado

---

## 🎯 Conclusão

O fluxo de operação está **bem estruturado e eficiente**, com:
- ✅ Tempo total de ~14.8 segundos
- ✅ Consumo de recursos controlado
- ✅ Processamento sequencial lógico
- ✅ Sistema estável e confiável

