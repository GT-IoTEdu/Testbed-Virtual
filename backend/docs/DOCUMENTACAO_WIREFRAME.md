# 📋 Documentação do Wireframe - Sistema IoT-EDU

## 🎯 Visão Geral

Este wireframe representa a interface de usuário para o sistema de gerenciamento de dispositivos IoT da UNIPAMPA, com diferentes níveis de acesso (usuário comum e gestor).

## 👥 Níveis de Acesso

### **1. Usuário Comum**
- **Permissões:** Gerenciar apenas seus próprios dispositivos e visualizar suas ocorrências
- **Funcionalidades:**
  - Visualizar dashboard com estatísticas pessoais
  - Cadastrar novos dispositivos
  - Editar/remover seus dispositivos
  - Visualizar status dos dispositivos
  - Visualizar ocorrências dos seus dispositivos
  - Detalhar ocorrências (somente leitura)

### **2. Gestor**
- **Permissões:** Gerenciar todos os dispositivos e usuários
- **Funcionalidades:**
  - Todas as funcionalidades do usuário comum
  - Visualizar todos os dispositivos do sistema
  - Gerenciar usuários (criar, editar, remover)
  - Visualizar estatísticas globais
  - Atribuir dispositivos a usuários

## 🏗️ Estrutura da Interface

### **1. Header**
- **Logo:** IoT-EDU
- **Informações do usuário:** Nome e avatar
- **Design:** Gradiente azul/roxo com sombra

### **2. Sidebar de Navegação**

#### **Para Usuários Comuns:**
- **Dashboard:** Visão geral com estatísticas pessoais
- **Meus Dispositivos:** Lista de dispositivos do usuário
- **Minhas Ocorrências:** Ocorrências dos dispositivos do usuário

#### **Para Gestores:**
- **Dashboard:** Visão geral com estatísticas globais
- **Usuários:** Gerenciamento de usuários
- **Configurações:** Configurações do sistema
- **Relatórios:** Relatórios e análises

### **3. Área Principal**
- **Dashboard Grid:** Cards com estatísticas
- **Sistema de Tabs:** Organização de conteúdo
- **Tabelas:** Listagem de dados
- **Modais:** Formulários de cadastro/edição

## 📊 Dashboard

### **Cards de Estatísticas**

#### **Para Usuários Comuns:**
1. **Meus Dispositivos:** 3 (+1 este mês) - Dispositivos pessoais do usuário
2. **Dispositivos Online:** 2 (67% ativos) - Status dos dispositivos pessoais
3. **Minhas Ocorrências:** 2 (1 pendente) - Ocorrências dos dispositivos pessoais

#### **Para Gestores:**
1. **Total de Dispositivos:** 24 (+3 este mês) - Visão global de todos os dispositivos
2. **Dispositivos Online:** 18 (75% ativos) - Status global dos dispositivos
3. **Usuários Ativos:** 12 (3 gestores) - Estatísticas de usuários do sistema
4. **Ocorrências Ativas:** 3 (1 alta prioridade) - Ocorrências globais do sistema

## 🔧 Funcionalidades por Aba

### **Aba 1: Meus Dispositivos (Usuário)**
- **Busca:** Campo de busca por nome, IP, MAC
- **Tabela com colunas:**
  - Nome do dispositivo
  - Endereço IP
  - Endereço MAC
  - Status (Online/Offline)
  - Última atividade
  - Ações (Editar/Remover)
- **Botão:** "+ Novo Dispositivo"

### **Aba 2: Minhas Ocorrências (Usuário)**
- **Busca:** Campo de busca por dispositivo, tipo, severidade
- **Tabela com colunas:**
  - Dispositivo
  - Endereço IP
  - Tipo de ocorrência
  - Severidade (Baixo/Médio/Alto)
  - Descrição
  - Detectado em
  - Status (Investigando/Resolvido)
  - Ações (Detalhar - somente leitura)
- **Funcionalidade:** Apenas visualização das ocorrências dos próprios dispositivos

### **Aba 1: Todos os Dispositivos (Gestor)**
- **Busca:** Campo de busca por nome, IP, MAC
- **Tabela com colunas:**
  - Nome do dispositivo
  - Endereço IP
  - Endereço MAC
  - Proprietário
  - Status (Online/Offline)
  - Última atividade
  - Ações (Editar/Remover)
- **Botão:** "+ Novo Dispositivo"

### **Aba 2: Dispositivos Ativos (Gestor)**
- **Busca:** Campo de busca por nome, IP, MAC
- **Tabela com colunas:**
  - Nome do dispositivo
  - Endereço IP
  - Endereço MAC
  - Proprietário
  - Status (Ativo)
  - Última atividade
  - Tráfego (24h)
  - Ações (Detalhar/Bloquear)
- **Botão:** "📊 Relatório de Atividade"

### **Aba 3: Dispositivos Bloqueados (Gestor)**
- **Busca:** Campo de busca por nome, IP, MAC
- **Tabela com colunas:**
  - Nome do dispositivo
  - Endereço IP
  - Endereço MAC
  - Proprietário
  - Motivo do bloqueio
  - Bloqueado em
  - Bloqueado por
  - Ações (Detalhar/Desbloquear)
- **Botão:** "🔓 Desbloquear Selecionados"

### **Aba 4: Aguardando Acesso (Gestor)**
- **Busca:** Campo de busca por nome, IP, MAC
- **Tabela com colunas:**
  - Nome do dispositivo
  - Endereço IP
  - Endereço MAC
  - Solicitante
  - Status (Aguardando)
  - Solicitado em
  - Justificativa
  - Ações (Detalhar/Aprovar/Rejeitar)
- **Botão:** "✅ Aprovar Selecionados"

### **Aba 5: Ocorrências (Gestor)**
- **Busca:** Campo de busca por dispositivo, tipo, severidade
- **Tabela com colunas:**
  - Dispositivo
  - Endereço IP
  - Tipo de ocorrência
  - Severidade (Baixo/Médio/Alto)
  - Descrição
  - Detectado em
  - Status (Investigando/Bloqueado/Resolvido)
  - Ações (Detalhar/Bloquear/Resolver)
- **Botão:** "📄 Exportar Relatório"

### **Aba 6: Usuários (Gestor)**
- **Busca:** Campo de busca por nome, email
- **Tabela com colunas:**
  - Nome completo
  - Email
  - Instituição
  - Permissão (Usuário/Gestor)
  - Número de dispositivos
  - Último login
  - Ações (Editar/Remover)
- **Botão:** "+ Novo Usuário"

## 🎨 Design System

### **Cores**
- **Primária:** #667eea (Azul)
- **Secundária:** #764ba2 (Roxo)
- **Sucesso:** #28a745 (Verde)
- **Aviso:** #ffc107 (Amarelo)
- **Perigo:** #dc3545 (Vermelho)
- **Neutro:** #f5f5f5 (Cinza claro)

### **Tipografia**
- **Família:** Segoe UI, Tahoma, Geneva, Verdana, sans-serif
- **Tamanhos:**
  - Títulos: 1.5rem (header), 1.2rem (cards)
  - Valores: 2rem (dashboard)
  - Texto: 1rem (padrão)
  - Pequeno: 0.8rem (badges)

### **Componentes**
- **Cards:** Fundo branco, bordas arredondadas, sombra
- **Botões:** Bordas arredondadas, hover effects
- **Tabelas:** Linhas alternadas, hover effects
- **Modais:** Overlay escuro, conteúdo centralizado
- **Badges:** Bordas arredondadas, cores contextuais

## 🔄 Fluxos de Interação

### **1. Cadastro de Dispositivo**
1. Usuário clica em "+ Novo Dispositivo"
2. Modal abre com formulário
3. Campos: Nome, IP, MAC, Descrição
4. Validação em tempo real
5. Salvar → Fechar modal → Atualizar lista

### **2. Edição de Dispositivo**
1. Usuário clica em "Editar"
2. Modal abre com dados preenchidos
3. Usuário modifica campos
4. Salvar → Fechar modal → Atualizar lista

### **3. Remoção de Dispositivo**
1. Usuário clica em "Remover"
2. Confirmação (modal ou alert)
3. Dispositivo removido → Atualizar lista

### **4. Busca**
1. Usuário digita no campo de busca
2. Busca em tempo real ou ao clicar "Buscar"
3. Filtra resultados na tabela

## 📱 Responsividade

### **Desktop (>1024px)**
- Sidebar fixa à esquerda
- Layout em grid para dashboard
- Tabelas com todas as colunas

### **Tablet (768px - 1024px)**
- Sidebar colapsível
- Grid adaptativo
- Tabelas com scroll horizontal

### **Mobile (<768px)**
- Sidebar como menu hambúrguer
- Cards em coluna única
- Tabelas com scroll horizontal
- Modais em tela cheia

## 🔐 Segurança e Validação

### **Validações de Formulário**
- **IP:** Formato IPv4 válido
- **MAC:** Formato MAC válido (XX:XX:XX:XX:XX:XX)
- **Email:** Formato de email válido
- **Campos obrigatórios:** Nome, IP, MAC

### **Controle de Acesso**
- **Usuário comum:** Apenas seus dispositivos
- **Gestor:** Todos os dispositivos e usuários
- **Verificação de permissão:** No backend

## 🛡️ Funcionalidades de Segurança (Gestor)

### **Monitoramento de Dispositivos**
- **Dispositivos Ativos:** Lista todos os dispositivos conectados e funcionando
- **Tráfego em Tempo Real:** Monitoramento de dados transferidos (24h)
- **Log de Atividade:** Histórico detalhado de ações do dispositivo
- **Status de Conectividade:** Verificação de estabilidade da conexão

### **Gestão de Bloqueios**
- **Bloqueio Manual:** Gestor pode bloquear dispositivos manualmente
- **Motivos de Bloqueio:** Categorização dos motivos (suspeito, política, segurança, etc.)
- **Duração Configurável:** Bloqueio temporário ou permanente
- **Histórico de Bloqueios:** Rastreamento de quem bloqueou e quando

### **Aprovação de Dispositivos**
- **Fila de Aprovação:** Dispositivos aguardando autorização para acesso
- **Justificativa Obrigatória:** Usuário deve explicar o motivo da solicitação
- **Aprovação/Rejeição:** Gestor pode aprovar ou rejeitar com observações
- **Notificação Automática:** Usuário é notificado sobre a decisão

### **Sistema de Ocorrências**
- **Detecção Automática:** Sistema identifica comportamentos suspeitos
- **Classificação por Severidade:** Baixo, Médio, Alto
- **Tipos de Ocorrência:**
  - Comportamento Suspeito
  - Ameaça Detectada
  - Violação de Política
  - Tentativas de Acesso Não Autorizado
- **Evidências Detalhadas:** Logs e timestamps das atividades suspeitas
- **Workflow de Resolução:** Investigação → Ação → Resolução

### **Ações de Segurança Disponíveis**
- **Detalhar:** Visualizar informações completas do dispositivo/ocorrência
- **Bloquear:** Bloquear dispositivo por comportamento suspeito
- **Desbloquear:** Remover bloqueio após resolução
- **Aprovar:** Autorizar acesso de novo dispositivo
- **Rejeitar:** Negar acesso com justificativa
- **Resolver:** Marcar ocorrência como resolvida
- **Arquivar:** Mover ocorrências antigas para arquivo
- **Exportar:** Gerar relatórios de segurança

### **Indicadores Visuais de Status**
- **🟢 Ativo:** Dispositivo funcionando normalmente
- **🔴 Bloqueado:** Dispositivo bloqueado por segurança
- **🟡 Aguardando:** Dispositivo aguardando aprovação
- **🟠 Suspeito:** Comportamento suspeito detectado
- **🔴 Ameaça:** Ameaça de segurança identificada
- **🔵 Investigando:** Ocorrência em análise
- **✅ Resolvido:** Problema resolvido

## 🚀 Integração com API

### **Endpoints Utilizados**

#### **Dispositivos e DHCP**
- `GET /api/devices/dhcp/servers` - Listar dispositivos
- `POST /api/devices/dhcp/save` - Cadastrar dispositivo
- `GET /api/devices/users/{id}/devices` - Dispositivos do usuário
- `GET /api/devices/assignments` - Atribuições
- `POST /api/devices/assignments` - Atribuir dispositivo

#### **Segurança e Monitoramento**
- `GET /api/devices/security/active` - Dispositivos ativos
- `GET /api/devices/security/blocked` - Dispositivos bloqueados
- `GET /api/devices/security/pending` - Dispositivos aguardando aprovação
- `GET /api/devices/security/incidents` - Listar ocorrências
- `POST /api/devices/security/block` - Bloquear dispositivo
- `POST /api/devices/security/unblock` - Desbloquear dispositivo
- `POST /api/devices/security/approve` - Aprovar dispositivo
- `POST /api/devices/security/reject` - Rejeitar dispositivo
- `GET /api/devices/security/incidents/{id}` - Detalhes da ocorrência
- `POST /api/devices/security/incidents/{id}/resolve` - Resolver ocorrência
- `GET /api/devices/security/reports` - Relatórios de segurança

### **Autenticação**
- Token JWT no header
- Verificação de permissões
- Refresh token automático

## 📈 Métricas e Analytics

### **Dashboard Metrics**
- Total de dispositivos por usuário
- Taxa de dispositivos online
- Crescimento mensal
- Distribuição por instituição

### **Relatórios**
- Dispositivos por período
- Atividade de usuários
- Status de dispositivos
- Exportação em PDF/Excel

## 🎯 Próximos Passos

### **Fase 1: Implementação Básica**
- [ ] Desenvolver frontend React/Vue.js
- [ ] Integrar com API existente
- [ ] Implementar autenticação
- [ ] Testes de usabilidade

### **Fase 2: Funcionalidades Avançadas**
- [ ] Notificações em tempo real
- [ ] Gráficos interativos
- [ ] Exportação de relatórios
- [ ] Configurações avançadas

### **Fase 3: Otimizações**
- [ ] Performance e cache
- [ ] PWA (Progressive Web App)
- [ ] Integração com mobile
- [ ] Analytics avançados

## 📝 Notas de Implementação

### **Tecnologias Sugeridas**
- **Frontend:** React.js ou Vue.js
- **UI Framework:** Material-UI ou Vuetify
- **Estado:** Redux ou Vuex
- **HTTP Client:** Axios
- **Charts:** Chart.js ou D3.js

### **Considerações de Performance**
- Lazy loading de componentes
- Paginação de tabelas
- Cache de dados
- Debounce na busca
- Otimização de imagens

### **Acessibilidade**
- Navegação por teclado
- Screen readers
- Contraste adequado
- Textos alternativos
- ARIA labels
