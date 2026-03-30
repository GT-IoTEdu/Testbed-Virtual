# Services Scanners - Integração Zeek, Suricata e Snort

Este módulo implementa a integração com **Zeek**, **Suricata** e **Snort** no mesmo estilo: configuração por instituição, health check, listagem de alertas no banco e stream SSE em tempo real com persistência e bloqueio automático para severidade alta.

## Zeek (estilo Suricata/Snort)

### `zeek_service.py`
- **ZeekService**: Configuração via `zeek_base_url` e `zeek_key` da instituição (ou parâmetros diretos).
- **get_sse_url()**: Retorna a URL do endpoint SSE do Zeek (`/sse/alerts?api_key=...`).
- **test_connection()**: Testa conectividade (retorna dict com `success`, `message`, `configured`).
- **_normalize_alert()** / **_determine_severity()**: Normalizam alertas para o formato padrão (src_ip, dest_ip, signature, severity, etc.).

### `zeek_router.py` (prefix `/scanners/zeek`)
- `GET /alerts` - Lista alertas do Zeek salvos no banco (paginado; `user_id` ou `institution_id`).
- `GET /health` - Verifica saúde da integração (aceita `user_id` ou `institution_id`).
- `GET /sse/alerts` - Stream SSE de alertas em tempo real; persiste em `zeek_alerts` e dispara bloqueio automático para severidade alta.

## Configuração

### Variáveis de Ambiente
Adicione as seguintes configurações no arquivo `.env` do backend:

```env
# Configurações do Zeek Network Security Monitor
ZEEK_API_URL=http://192.168.100.1/zeek-api
ZEEK_API_TOKEN=y1X6Qn8PpV9jR4kM0wBz7Tf2GhUs3Lc8NrDq5Ke1HxYi0AzF7Gv9MbX2VwJoQp
```

### Backend
1. O serviço acessa a API do Zeek em `http://192.168.100.1/zeek-api/alert_data.php`
2. Usa autenticação Bearer token conforme especificado na API PHP
3. Os endpoints estão disponíveis em `/api/scanners/zeek/`
4. A integração foi adicionada ao `main.py` da aplicação

### Frontend
A integração foi implementada na aba "Ocorrências" do dashboard (`frontend/app/dashboard/page.tsx`):

#### Funcionalidades
- **Filtros avançados**: Por severidade, status, tipo de log e busca textual
- **Visualização em tempo real**: Carregamento automático ao acessar a aba
- **Interface responsiva**: Tabela com informações detalhadas dos incidentes
- **Formatação inteligente**: Severidade e status com cores, timestamps relativos
- **Ações**: Botões para detalhar incidentes e alterar status

#### Estados do React
```typescript
// Estados para integração com Zeek
const [zeekIncidents, setZeekIncidents] = useState<Array<Incident>>([]);
const [zeekLoading, setZeekLoading] = useState(false);
const [zeekError, setZeekError] = useState<string | null>(null);
const [incidentSearch, setIncidentSearch] = useState("");
const [severityFilter, setSeverityFilter] = useState<string>("");
const [statusFilter, setStatusFilter] = useState<string>("");
const [logTypeFilter, setLogTypeFilter] = useState<string>("");
```

#### Funções principais
- `fetchZeekIncidents()`: Busca incidentes da API com filtros aplicados
- `formatSeverity()`: Formata níveis de severidade com cores
- `formatStatus()`: Formata status dos incidentes
- `formatDateTime()`: Converte timestamps em formato relativo

## Uso

### API Backend
```bash
# Verificar saúde da integração
curl http://localhost:8000/api/scanners/zeek/health

# Buscar logs HTTP das últimas 2 horas
curl "http://localhost:8000/api/scanners/zeek/logs?logfile=http.log&hours_ago=2&maxlines=50"

# Buscar incidentes críticos
curl "http://localhost:8000/api/scanners/zeek/incidents?severity=critical&hours_ago=24"

# Obter estatísticas
curl http://localhost:8000/api/scanners/zeek/stats
```

### Formato da API Zeek
A API do Zeek (`alert_data.php`) retorna dados no formato:

```json
{
  "success": true,
  "logfile": "http.log",
  "maxlines": 10,
  "total_lines": 5,
  "data": [
    {
      "ts": {"raw": 1640995200.123, "iso": "2021-12-31T12:00:00Z"},
      "id.orig_h": "192.168.1.100",
      "id.resp_h": "93.184.216.34",
      "method": "GET",
      "host": "example.com",
      "status_code": 200,
      "user_agent": "Mozilla/5.0..."
    }
  ]
}
```

### Frontend
1. Acesse o dashboard da aplicação
2. Clique na aba "Ocorrências"
3. Use os filtros para refinar os resultados:
   - **Buscar**: Filtra por IP, tipo ou descrição
   - **Severidade**: Baixo, Médio, Alto, Crítico
   - **Status**: Novo, Investigando, Resolvido, Falso Positivo
   - **Tipo de Log**: HTTP, DNS, Conexões
4. Clique em "Atualizar" para recarregar os dados
5. Use "Detalhar" para ver informações completas do incidente

## Detecção de Incidentes

### HTTP Logs
- Códigos de status 4xx/5xx
- User agents suspeitos (curl, wget, scanners)
- URIs maliciosas (/admin, /.env, /wp-admin)
- Redirecionamentos suspeitos

### DNS Logs
- Queries para domínios conhecidamente maliciosos
- Padrões de DGA (Domain Generation Algorithm)
- Queries anômalas (muito longas, muitos subdomínios)

### Connection Logs
- Alto volume de tráfego (>100MB)
- Conexões falhadas (REJ, RSTO, RSTR)
- Padrões de comunicação anômalos

## Extensibilidade

Para adicionar novos tipos de detecção:

1. **Backend**: Edite `zeek_service.py` e adicione lógica em `_detect_incident_in_log()`
2. **Frontend**: Adicione novos filtros ou campos na interface
3. **Modelos**: Estenda `zeek_models.py` para novos tipos de logs

## Monitoramento

O sistema inclui:
- **Health checks**: Verificação automática da conectividade
- **Tratamento de erros**: Mensagens de erro amigáveis
- **Logs**: Logging detalhado para debug
- **Timeouts**: Configurados para evitar bloqueios
- **Fallbacks**: Comportamento gracioso em caso de falha

## Segurança

- Validação de entrada com Pydantic
- Sanitização de parâmetros de URL
- Timeouts para evitar DoS
- Tratamento seguro de erros sem vazar informações sensíveis
