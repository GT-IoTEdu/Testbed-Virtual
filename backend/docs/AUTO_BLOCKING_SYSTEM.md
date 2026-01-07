# 🛡️ Sistema de Bloqueio Automático de Incidentes de Segurança

## 📋 Visão Geral

O sistema de bloqueio automático é uma funcionalidade que monitora incidentes de segurança em tempo real e aplica bloqueios automáticos em dispositivos identificados como **atacantes**. Quando um incidente de segurança é detectado e o dispositivo é classificado como atacante, o sistema automaticamente:

- Remove o IP do alias "Autorizados" (se existir)
- Adiciona o IP ao alias "Bloqueados" 
- Sincroniza as mudanças com o pfSense
- Atualiza o status do incidente
- Cria feedback administrativo para auditoria

## 🎯 Critérios de Bloqueio

### ✅ **Será Bloqueado Automaticamente:**
- Qualquer incidente onde `incident_type` contém a palavra **"Atacante"**
- Exemplos:
  - `"SQL Injection - Atacante"`
  - `"Malware - Atacante"`
  - `"Ataque DDoS - Atacante"`
  - `"Phishing - Atacante"`

### ❌ **NÃO Será Bloqueado:**
- Incidentes onde `incident_type` contém **"Vítima"**
- Exemplos:
  - `"SQL Injection - Vítima"`
  - `"Malware - Vítima"`
  - `"Security Notice: CaptureLoss::Too_Little_Traffic"`

## 🔧 Arquitetura do Sistema

### Componentes Principais

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Zeek/Scanner  │───▶│  IncidentService │───▶│  AliasService   │
│                 │    │                  │    │                 │
│ Detecta Ataques  │    │ Salva Incidente  │    │ Gerencia Aliases│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Auto Block      │    │    pfSense      │
                       │  Trigger         │    │                 │
                       │                  │    │ Aplica Bloqueio │
                       └──────────────────┘    └─────────────────┘
```

### Fluxo de Funcionamento

1. **Detecção**: Sistema Zeek detecta atividade suspeita
2. **Criação**: Incidente é criado no banco de dados
3. **Verificação**: Sistema verifica se `incident_type` contém "Atacante"
4. **Bloqueio**: Se for atacante, aplica bloqueio automático
5. **Sincronização**: Atualiza aliases no pfSense
6. **Auditoria**: Cria feedback administrativo

## 📁 Estrutura de Arquivos

```
backend/
├── services_scanners/
│   ├── incident_service.py      # Lógica principal de bloqueio automático
│   └── incident_router.py       # Endpoints da API
├── services_firewalls/
│   ├── alias_service.py         # Gerenciamento de aliases
│   └── blocking_feedback_service.py  # Sistema de feedback
└── scripts/
    ├── test_auto_block_on_creation.py  # Teste de criação automática
    ├── test_pfsense_blocking.py       # Teste de sincronização
    └── test_auto_block_endpoint.py    # Teste do endpoint manual
```

## 🚀 Como Usar

### 1. **Bloqueio Automático (Recomendado)**

O bloqueio automático acontece **automaticamente** quando um incidente de atacante é criado. Não é necessária nenhuma ação manual.

**Exemplo de criação de incidente que será bloqueado:**
```python
incident_data = {
    "device_ip": "192.168.100.3",
    "device_name": "Dispositivo Atacante",
    "incident_type": "SQL Injection - Atacante",  # ← Contém "Atacante"
    "severity": "critical",
    "description": "Atacante de SQL Injection detectado",
    "zeek_log_type": "notice.log"
}

# Quando este incidente é criado, o bloqueio é aplicado automaticamente
```

### 2. **Bloqueio Manual via API**

Para bloqueio manual de incidentes existentes:

```bash
curl -X POST "http://127.0.0.1:8000/api/incidents/auto-block" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": 123,
    "reason": "Bloqueio manual por administrador",
    "admin_name": "Admin"
  }'
```

## 🧪 Testes

### Scripts de Teste Disponíveis

#### 1. **Teste de Bloqueio Automático na Criação**
```bash
python backend/scripts/test_auto_block_on_creation.py
```
- ✅ Testa bloqueio automático quando incidente de atacante é criado
- ✅ Testa que incidentes de vítima NÃO são bloqueados
- ✅ Verifica sincronização com banco de dados

#### 2. **Teste de Sincronização com pfSense**
```bash
python backend/scripts/test_pfsense_blocking.py
```
- ✅ Testa se bloqueio é aplicado no banco de dados
- ✅ Instrui para verificar manualmente no pfSense
- ✅ Fornece relatório detalhado

#### 3. **Teste do Endpoint Manual**
```bash
python backend/scripts/test_auto_block_endpoint.py
```
- ✅ Testa endpoint de bloqueio manual
- ✅ Testa casos de erro (incidente inválido)
- ✅ Verifica diferentes tipos de incidente

### Exemplo de Saída dos Testes

```
🚀 Teste de Bloqueio Automático na Criação de Incidentes
🌐 URL base: http://127.0.0.1:8000
⏰ Timestamp: 2025-10-06 19:00:54

🧪 Testando bloqueio automático na criação de incidente
============================================================

1️⃣ Verificando estado inicial do alias Bloqueados...
📊 Endereços bloqueados inicialmente: 1

2️⃣ Criando incidente de atacante...
✅ Incidente criado com ID: 8
📊 Tipo: SQL Injection - Atacante
📊 IP: 192.168.100.99
📊 Status: resolved

3️⃣ Aguardando processamento do bloqueio automático...

4️⃣ Verificando se IP 192.168.100.99 foi bloqueado automaticamente...
✅ IP 192.168.100.99 foi bloqueado automaticamente!
📝 Detalhes do bloqueio: Bloqueado automaticamente - Incidente 8

============================================================
📊 RESULTADO DOS TESTES
============================================================
✅ Teste 1 (Bloqueio automático para atacante): PASSOU
✅ Teste 2 (Não bloquear vítima): PASSOU

🎉 TODOS OS TESTES PASSARAM!
🔒 Bloqueio automático está funcionando corretamente!
```

## 📊 Monitoramento e Logs

### Logs Importantes

Procure por estas mensagens nos logs do servidor:

#### ✅ **Logs de Sucesso:**
```
INFO: Incidente de atacante detectado (ID: 123). Aplicando bloqueio automático...
INFO: IP 192.168.100.3 adicionado ao alias Bloqueados com sucesso
INFO: Alias Bloqueados atualizado no pfSense com sucesso
INFO: Bloqueio automático concluído com sucesso para IP 192.168.100.3
```

#### ⚠️ **Logs de Warning:**
```
WARNING: IP 192.168.100.3 já está bloqueado
WARNING: Dispositivo com IP 192.168.100.3 não encontrado no banco DHCP
```

#### ❌ **Logs de Erro:**
```
ERROR: Erro ao criar alias Bloqueados no pfSense: {...}
ERROR: Erro ao aplicar bloqueio automático: {...}
```

### Verificação Manual no pfSense

1. **Acesse o pfSense**
2. **Vá em Firewall > Aliases**
3. **Procure pelo alias "Bloqueados"**
4. **Verifique se contém os IPs bloqueados**

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# URL base da API
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000

# Configurações do pfSense
PFSENSE_URL=https://seu-pfsense.local
PFSENSE_USER=admin
PFSENSE_PASSWORD=sua-senha
```

### Configuração do Banco de Dados

O sistema usa as seguintes tabelas:
- `zeek_incidents`: Armazena incidentes de segurança
- `pfsense_aliases`: Armazena aliases do pfSense
- `pfsense_alias_addresses`: Armazena endereços dos aliases
- `blocking_feedback_history`: Armazena histórico de bloqueios

## 🛠️ Troubleshooting

### Problemas Comuns

#### 1. **Bloqueio não está sendo aplicado**

**Sintomas:**
- Incidente é criado mas IP não é bloqueado
- Status do incidente não muda para "resolved"

**Soluções:**
- Verifique se `incident_type` contém "Atacante"
- Verifique logs do servidor para erros
- Execute script de teste para diagnóstico

#### 2. **Sincronização com pfSense falha**

**Sintomas:**
- IP é bloqueado no banco mas não no pfSense
- Erro "pfSense indisponível" nos logs

**Soluções:**
- Verifique conectividade com pfSense
- Verifique credenciais do pfSense
- Execute script de teste de sincronização

#### 3. **Alias "Bloqueados" não existe**

**Sintomas:**
- Erro ao criar alias "Bloqueados"
- Falha na sincronização

**Soluções:**
- Sistema criará automaticamente o alias
- Verifique permissões no pfSense
- Execute teste para verificar criação

### Comandos de Diagnóstico

```bash
# Verificar incidentes recentes
curl "http://127.0.0.1:8000/api/incidents?hours_ago=1"

# Verificar alias Bloqueados
curl "http://127.0.0.1:8000/api/devices/aliases-db/Bloqueados"

# Executar teste completo
python backend/scripts/test_auto_block_on_creation.py
```

## 📈 Métricas e Estatísticas

### Endpoints de Monitoramento

```bash
# Estatísticas de incidentes
GET /api/incidents/stats/summary

# Estatísticas de aliases
GET /api/devices/aliases-db/statistics

# Histórico de bloqueios
GET /api/devices/blocking-feedback/history
```

### Exemplo de Resposta de Estatísticas

```json
{
  "total_incidents": 150,
  "incidents_by_severity": {
    "critical": 25,
    "high": 45,
    "medium": 60,
    "low": 20
  },
  "incidents_by_status": {
    "new": 10,
    "investigating": 5,
    "resolved": 130,
    "false_positive": 5
  },
  "auto_blocked_incidents": 45,
  "manual_blocked_incidents": 5
}
```

## 🔒 Segurança

### Considerações de Segurança

- ✅ **Verificação dupla**: Só bloqueia dispositivos identificados como atacantes
- ✅ **Logs de auditoria**: Todas as ações são registradas
- ✅ **Feedback administrativo**: Cria histórico para revisão
- ✅ **Rollback automático**: Em caso de erro, operação é revertida
- ✅ **Validação de dados**: Todos os dados são validados antes do processamento

### Permissões Necessárias

- **Leitura**: Incidentes, aliases existentes
- **Escrita**: Criação/atualização de aliases, feedback administrativo
- **Sincronização**: Comunicação com pfSense

## 📚 Referências

### Documentação Relacionada

- [Sistema de Incidentes de Segurança](./INCIDENTS.md)
- [Gerenciamento de Aliases](./ALIASES.md)
- [Sistema de Feedback de Bloqueio](./BLOCKING_FEEDBACK.md)
- [Integração com pfSense](./PFSENSE_INTEGRATION.md)

### APIs Relacionadas

- `POST /api/incidents/` - Criar incidente (dispara bloqueio automático)
- `POST /api/incidents/auto-block` - Bloqueio manual
- `GET /api/devices/aliases-db/Bloqueados` - Verificar IPs bloqueados
- `GET /api/incidents/stats/summary` - Estatísticas de incidentes

---

## 📞 Suporte

Para dúvidas ou problemas:

1. **Verifique os logs** do servidor para mensagens de erro
2. **Execute os scripts de teste** para diagnóstico
3. **Consulte a documentação** relacionada
4. **Entre em contato** com a equipe de desenvolvimento

---

**Versão**: 1.0  
**Última atualização**: 2025-10-06  
**Autor**: Sistema IoT-EDU
