# Sistema de Feedback de Bloqueio

## Visão Geral

O Sistema de Feedback de Bloqueio permite que usuários forneçam feedback sobre resolução de problemas de bloqueio de dispositivos IoT. Este sistema facilita o acompanhamento e melhoria contínua do processo de segurança da rede.

## Estrutura do Banco de Dados

### Tabela: `blocking_feedback_history`

#### Valores da Coluna `problem_resolved`:
- **`NULL`**: Não respondido (padrão)
- **`1` (TRUE)**: Problema resolvido
- **`0` (FALSE)**: Problema não resolvido

```sql
CREATE TABLE `blocking_feedback_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dhcp_mapping_id` int(11) NOT NULL COMMENT 'ID do mapeamento DHCP',
  `user_feedback` text DEFAULT NULL COMMENT 'Feedback detalhado do usuário',
  `problem_resolved` tinyint(1) DEFAULT NULL COMMENT 'NULL = não respondido, 1 = resolvido, 0 = não resolvido',
  `feedback_date` datetime DEFAULT NULL COMMENT 'Data/hora do feedback',
  `feedback_by` varchar(100) DEFAULT NULL COMMENT 'Nome/identificação do usuário que forneceu o feedback',
  `admin_notes` text DEFAULT NULL COMMENT 'Anotações da equipe de rede sobre o feedback',
  `admin_review_date` datetime DEFAULT NULL COMMENT 'Data/hora da revisão administrativa',
  `admin_reviewed_by` varchar(100) DEFAULT NULL COMMENT 'Quem revisou o feedback',
  `status` enum('PENDING','REVIEWED','ACTION_REQUIRED') NOT NULL COMMENT 'Status atual do feedback',
  `created_at` datetime DEFAULT NULL COMMENT 'Data/hora de criação',
  `updated_at` datetime DEFAULT NULL COMMENT 'Data/hora da última atualização',
  PRIMARY KEY (`id`),
  KEY `idx_feedback_dhcp_mapping` (`dhcp_mapping_id`),
  KEY `idx_feedback_status` (`status`),
  KEY `idx_feedback_date` (`feedback_date`),
  KEY `idx_feedback_by` (`feedback_by`),
  KEY `idx_feedback_reviewed_by` (`admin_reviewed_by`),
  CONSTRAINT `blocking_feedback_history_ibfk_1` FOREIGN KEY (`dhcp_mapping_id`) REFERENCES `dhcp_static_mappings` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
```

## API Endpoints

### 1. Criar Feedback

**POST** `/api/feedback/`

```json
{
  "dhcp_mapping_id": 123,
  "user_feedback": "O dispositivo foi bloqueado incorretamente. Já corrigi o problema.",
  "feedback_by": "João Silva",
  "problem_resolved": true
}
```

### 2. Buscar Feedback por Mapeamento DHCP

**GET** `/api/feedback/dhcp/{dhcp_mapping_id}?limit=10&offset=0`

### 3. Buscar Feedback por Status

**GET** `/api/feedback/status/{status}?limit=50&offset=0`

Status disponíveis:
- `PENDING` - Pendente de revisão
- `REVIEWED` - Revisado
- `ACTION_REQUIRED` - Requer ação

### 4. Buscar Feedback por Usuário

**GET** `/api/feedback/user/{feedback_by}?limit=50&offset=0`

### 5. Atualizar Status do Feedback

**PUT** `/api/feedback/{feedback_id}/status`

```json
{
  "status": "REVIEWED",
  "admin_notes": "Problema resolvido. Dispositivo liberado.",
  "admin_reviewed_by": "admin@empresa.com"
}
```

### 6. Estatísticas de Feedback

**GET** `/api/feedback/stats`

Retorna:
```json
{
  "total_feedbacks": 150,
  "status_stats": {
    "pending": 25,
    "reviewed": 100,
    "action_required": 25
  },
  "resolved_stats": {
    "resolved": 80,
    "not_resolved": 20,
    "pending": 50
  },
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### 7. Feedbacks Recentes

**GET** `/api/feedback/recent?days=7`

### 8. Buscar Feedback por ID

**GET** `/api/feedback/{feedback_id}`

## Componentes Frontend

### 1. BlockingFeedbackModal

Modal para criar novo feedback:

```tsx
<BlockingFeedbackModal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  dhcpMappingId={123}
  deviceIp="192.168.1.100"
  deviceName="Sensor IoT"
/>
```

### 2. FeedbackHistory

Componente para exibir histórico de feedbacks:

```tsx
<FeedbackHistory
  dhcpMappingId={123}
  deviceIp="192.168.1.100"
  deviceName="Sensor IoT"
/>
```

### 3. FeedbackStats

Componente para exibir estatísticas:

```tsx
<FeedbackStats />
```

## Fluxo de Trabalho

### 1. Bloqueio Administrativo

1. Gestor de redes bloqueia dispositivo na aba "Lista de Dispositivos"
2. Informa motivo do bloqueio (obrigatório)
3. Sistema salva motivo na tabela `dhcp_static_mappings` (campo `reason`)
4. **NOVO**: Sistema também cria automaticamente um feedback administrativo na tabela `blocking_feedback_history`
5. Feedback administrativo é criado com:
   - Status `REVIEWED` (já revisado)
   - `problem_resolved = NULL` (não respondido - aguardando feedback do usuário)

### 2. Usuário Envia Feedback

1. Usuário identifica problema com dispositivo bloqueado
2. Clica no botão "📝 Feedback" na lista de incidentes
3. Preenche o modal com:
   - Nome/identificação
   - Feedback detalhado
   - Se o problema foi resolvido
4. Sistema salva feedback com status `PENDING`

### 3. Revisão Administrativa

1. Equipe de rede acessa feedbacks pendentes
2. Revisa o feedback e adiciona notas administrativas
3. Atualiza status para `REVIEWED` ou `ACTION_REQUIRED`
4. Sistema registra quem revisou e quando

### 4. Acompanhamento

1. **NOVA ABA**: "Histórico de Bloqueios" mostra todos os bloqueios (administrativos + feedbacks)
2. Filtros por tipo: Todos, Administrativos, Usuários
3. Usuários podem ver histórico de seus feedbacks
4. Administradores podem acompanhar estatísticas
5. Sistema gera relatórios de resolução de problemas

## Integração no Dashboard

### Botão de Feedback

Adicionado ao lado do botão "🚫 Bloquear" na lista de incidentes:

```tsx
<button 
  className="px-2 py-1 rounded bg-blue-600/80 hover:bg-blue-600 text-sm ml-1"
  onClick={() => showFeedbackModal(incident.id_orig_h, incident.peer_descr)}
  title="Enviar feedback sobre bloqueio"
>
  📝 Feedback
</button>
```

### Modal Integrado

O modal de feedback é exibido quando o usuário clica no botão, permitindo envio imediato de feedback sobre o dispositivo bloqueado.

## Benefícios

1. **Melhoria Contínua**: Feedback dos usuários ajuda a identificar problemas no sistema
2. **Transparência**: Usuários podem acompanhar o status de seus feedbacks
3. **Rastreabilidade**: Histórico completo de problemas e resoluções
4. **Métricas**: Estatísticas para análise de eficácia do sistema de bloqueio
5. **Comunicação**: Canal direto entre usuários e equipe de rede

## Próximos Passos

1. **Notificações**: Sistema de notificações para feedbacks pendentes
2. **Relatórios**: Relatórios automáticos de feedbacks
3. **Integração**: Integração com sistema de tickets
4. **Analytics**: Análise de padrões em feedbacks
5. **Mobile**: Interface mobile para feedback

## Exemplo de Uso

```typescript
// Enviar feedback
const response = await fetch('/api/feedback/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    dhcp_mapping_id: 123,
    user_feedback: "Dispositivo bloqueado incorretamente. Problema resolvido.",
    feedback_by: "usuario@empresa.com",
    problem_resolved: true
  })
});

// Buscar feedbacks
const feedbacks = await fetch('/api/feedback/dhcp/123?limit=10', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

## Arquivos Relacionados

### Backend
- `backend/db/models.py` - Modelo BlockingFeedbackHistory
- `backend/db/enums.py` - Enum FeedbackStatus
- `backend/services_firewalls/blocking_feedback_service.py` - Lógica de negócio
- `backend/services_firewalls/blocking_feedback_router.py` - Endpoints da API
- `backend/scripts/create_feedback_table.py` - Script de criação da tabela

### Frontend
- `frontend/components/BlockingFeedbackModal.tsx` - Modal de criação
- `frontend/components/FeedbackHistory.tsx` - Histórico de feedbacks
- `frontend/components/FeedbackStats.tsx` - Estatísticas
- `frontend/components/BlockingHistory.tsx` - **NOVO**: Histórico completo de bloqueios
- `frontend/app/dashboard/page.tsx` - Integração no dashboard com nova aba

## Documentação da API

A documentação completa da API está disponível em `/docs` quando o servidor estiver rodando.
