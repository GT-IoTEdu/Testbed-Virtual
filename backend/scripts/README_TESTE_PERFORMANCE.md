# 🔧 Script de Teste de Performance - Sistema de Detecção e Bloqueio Automático

## 📋 Descrição

Script que monitora e mede o desempenho de todos os endpoints envolvidos no processo de detecção e bloqueio automático, registrando:

- ⏰ Timestamp de cada operação
- ⏱️ Tempo de execução de cada endpoint
- 💻 Consumo de CPU (processo e sistema)
- 🧠 Consumo de RAM (processo e sistema)
- 📊 Relatório detalhado de performance

## 🚀 Como Usar

### Pré-requisitos

1. Ter o ambiente Python configurado
2. Ter as dependências instaladas (`pip install -r requirements.txt`)
3. Ter a API rodando (ou configurar `API_URL` no `.env`)
4. Ter token de autenticação configurado (`API_TOKEN` no `.env`)

### Execução

```bash
# Executar teste com IP padrão (192.168.59.4)
python backend/scripts/test_blocking_performance.py

# Executar teste com IP personalizado
python backend/scripts/test_blocking_performance.py 192.168.100.10
```

### Configuração

O script usa variáveis de ambiente do arquivo `.env`:

```env
API_URL=http://localhost:8000
API_TOKEN=seu_token_aqui
```

## 📊 Endpoints Testados

O script testa os seguintes endpoints no processo de bloqueio automático:

1. **GET /api/scanners/zeek/logs**
   - Função: `ZeekService.get_logs`
   - Simula busca de logs do Zeek (monitoramento)

2. **POST /api/incidents/**
   - Função: `IncidentService.save_incident`
   - Cria incidente de teste

3. **POST /api/incidents/process-batch**
   - Função: `IncidentService.process_incidents_for_auto_blocking`
   - Processa incidentes em lote

4. **GET /api/devices/aliases-db/{name}**
   - Função: `AliasService.get_alias_by_name`
   - Busca alias "Bloqueados"

5. **POST /api/devices/aliases-db/{name}/add-addresses**
   - Função: `AliasService.add_addresses_to_alias`
   - Adiciona IP ao alias "Bloqueados"

6. **POST /api/devices/firewall/apply**
   - Função: `pfsense_client.aplicar_mudancas_firewall_pfsense`
   - Aplica mudanças no firewall

## 📈 Relatório Gerado

O script gera um relatório completo com:

### **1. Tabela Resumida**
```
Nº  Função                              Endpoint                          Rota                              Tempo (s)     CPU%     RAM (MB)     Status    
--------------------------------------------------------------------------------------------------------------------
1   ZeekService.get_logs                GET /api/scanners/zeek/logs        /api/scanners/zeek/logs?logfile...  0.123       5.20     121.50       ✅ OK
...
```

### **2. Detalhes de Cada Endpoint**
- Timestamp da operação
- Tempo de execução
- Consumo de CPU e RAM
- Status (sucesso/falha)
- Resultado da operação

### **3. Resumo de Recursos**
- Média e máximo de CPU
- Média e máximo de RAM
- Recursos finais do sistema

### **4. Distribuição de Tempo**
- Gráfico visual de tempo por etapa
- Percentual de cada etapa

### **5. Arquivo JSON**
Relatório completo salvo em `backend/performance_test_report.json`

## 📄 Exemplo de Saída

```
================================================================================
📊 RELATÓRIO FINAL DE PERFORMANCE - SISTEMA DE DETECÇÃO E BLOQUEIO AUTOMÁTICO
================================================================================

⏱️ TEMPO TOTAL DE EXECUÇÃO: 15.234 segundos
📅 Timestamp Início: 2025-11-05T16:30:00.123456
📅 Timestamp Fim: 2025-11-05T16:30:15.357890

================================================================================
📋 ENDPOINTS ENVOLVIDOS NO PROCESSO DE DETECÇÃO E BLOQUEIO AUTOMÁTICO
================================================================================

Nº  Função                              Endpoint                          Rota                              Tempo (s)     CPU%     RAM (MB)     Status    
--------------------------------------------------------------------------------------------------------------------
1   ZeekService.get_logs                GET /api/scanners/zeek/logs        /api/scanners/zeek/logs?logfile...  0.123       5.20     121.50       ✅ OK
2   IncidentService.save_incident        POST /api/incidents/               /api/incidents/                      0.456       8.30     122.10       ✅ OK
...
```

## 🔍 Interpretação dos Resultados

### **Tempos Esperados**

- **Busca de logs Zeek:** 0.1-0.5s
- **Salvamento de incidente:** 0.2-0.5s
- **Processamento em lote:** 1-5s
- **Operações de alias:** 0.1-2s cada
- **Apply do firewall:** 0.5-5s

### **Consumo de Recursos**

- **CPU (Processo):** Normalmente < 20% por operação
- **RAM (Processo):** Estável em torno de 120-130 MB
- **CPU (Sistema):** Varia com carga do sistema
- **RAM (Sistema):** Depende do sistema

## ⚠️ Observações

- O script cria um incidente de teste real no banco de dados
- O IP de teste será bloqueado no pfSense
- Certifique-se de usar um IP de teste apropriado
- O script pode ser interrompido com `Ctrl+C`

## 📝 Notas Técnicas

- O script mede métricas no momento da execução
- Timestamps são capturados com precisão de microssegundos
- Métricas de CPU são amostradas durante a execução
- Métricas de RAM são instantâneas no início e fim

