
# 📋 Backlog do Projeto - API IoT-EDU

  

**Última atualização:** 10/10/2025

**Versão:** 2.0 (Completo com Funcionalidades Implementadas)

  

---

  

## 📊 Visão Geral

  

Este documento contém o backlog de funcionalidades planejadas e bugs identificados para o sistema API IoT-EDU.

  

### **Índice Rápido**

  

#### **✅ Funcionalidades Implementadas -POC-1 (v1.0)**

- [IMPL01] Gestão de Dispositivos (CRUD)- Perfil Usuário ✅

- [IMPL02] Gestão de Dispositivos (Libera, Bloqueia)- Perfil Gestor ✅

- [IMPL03] Histórico de Bloqueios - Gestor ✅

- [IMPL04] Sistema de Incidentes (Básico)- Gestor ✅

- [IMPL05] Autenticação Google ✅

- [IMPL07] Integração com pfSense ✅

- [IMPL08] Integração com Zeek (notice.log)✅

  

#### **🆕 Casos de Uso Planejados**

  

**Gestão de Dispositivos e Segurança**

- [UC01] Histórico de Dispositivos Removidos

- [UC06] Bloqueio Temporário de Dispositivo Individual

- [UC07] Bloqueio Geral (Múltiplos Dispositivos)

- [UC11] Identificação de Dispositivo via Fingerprint

  

**Autenticação e Usuários**
- [UC02] Cadastro Zero-Touch com Autenticação Google

- [UC08] Cadastro Zero-Touch com Autenticação Google

- [UC10] Portal Captive com Redirecionamento Inteligente

- [UC012] Template de Arquivo ENV (Gestor Master)
  

**Multi-tenancy e Instituições**

- [UC09] Cadastro Multi-Campus de Instituição (Unipampa-Alegrete, Uruguaiana, etc..)

  

**Analytics e Monitoramento**

- [UC03] Período de Permanência Online de Usuários

- [UC04] Número Total de Conexões por Gestor

- [UC05] Resumo Simplificado de Incidentes para Usuário

  

#### **🐛 Bugs identificados POC-01**

- [BUG01] Apply Automático em Aliases ✅ 

- [BUG02] Apply Automático em DHCP ✅

- [BUG03] Captura Automática de Incidentes 🚧

  

### **Legenda de Status**

- 🆕 **Novo** - Item recém adicionado ao backlog

- 📝 **Planejado** - Item aprovado, aguardando desenvolvimento

- 🚧 **Em Desenvolvimento** - Desenvolvimento em andamento

- ✅ **Concluído** - Implementado e testado

- ⏸️ **Pausado** - Desenvolvimento temporariamente suspenso

- ❌ **Cancelado** - Item removido do backlog

  

### **Legenda de Prioridade**

- 🔴 **Alta** - Crítico para o sistema

- 🟡 **Média** - Importante mas não urgente

- 🟢 **Baixa** - Desejável para futuras versões

  

---

  

## ✅ Funcionalidades Implementadas

  

### **[IMPL01] Gestão de Dispositivos - Perfil Usuário**

**Status:** ✅ Concluído

**Prioridade:** 🔴 Alta

**Implementado em:** Versão 1.0

  

#### **Descrição**

Sistema completo de gestão de dispositivos no perfil do usuário, permitindo cadastro, edição e exclusão de dispositivos próprios.

  

#### **Funcionalidades Implementadas**

- ✅ **Cadastro de Dispositivos**

- Cadastro manual de dispositivos (MAC, IP, descrição)

- Validação de dados (formato MAC, IP válido)

- Verificação de duplicatas automática

- Integração com pfSense para criação de mapeamento estático DHCP

- Apply automático de mudanças DHCP

- ✅ **Edição de Dispositivos**

- Atualização de informações do dispositivo

- Alteração de MAC address

- Alteração de descrição e hostname

- Sincronização automática com pfSense

- Apply automático de mudanças

- ✅ **Exclusão de Dispositivos**

- Remoção lógica e física de dispositivos

- Limpeza de mapeamentos DHCP no pfSense

- Remoção de aliases associados

- Apply automático de mudanças

- Validação de permissões (usuário só remove seus próprios dispositivos)

- ✅ **Listagem de Dispositivos**

- Visualização de todos os dispositivos do usuário

- Informações detalhadas (MAC, IP, hostname, status)

- Indicador de bloqueio/liberação

- Data de cadastro e última atualização

  

#### **Endpoints Implementados**

-  `POST /api/devices/dhcp/save` - Cadastrar dispositivo

-  `POST /api/devices/dhcp/static_mapping` - Cadastrar mapeamento estático

-  `PATCH /api/devices/dhcp/static_mapping` - Atualizar dispositivo

-  `PATCH /api/devices/dhcp/static_mapping/by_mac` - Atualizar por MAC

-  `DELETE /api/devices/dhcp/static_mapping` - Excluir dispositivo

-  `DELETE /api/devices/dhcp/static_mapping/by_mac` - Excluir por MAC

-  `GET /api/devices/dhcp/devices` - Listar dispositivos

  

#### **Arquivos Relacionados**

-  `backend/services_firewalls/router.py`

-  `backend/services_firewalls/dhcp_service.py`

-  `backend/services_firewalls/pfsense_client.py`

-  `backend/db/models.py` (DhcpStaticMapping)

  

---

  

### **[IMPL02] Gestão de Dispositivos - Perfil Gestor**

**Status:** ✅ Concluído

**Prioridade:** 🔴 Alta

**Implementado em:** Versão 1.0

  

#### **Descrição**

Sistema completo de gestão centralizada de dispositivos para gestores, incluindo listagem global, aprovação, bloqueio/liberação manual e automatizado.

  

#### **Funcionalidades Implementadas**

- ✅ **Listagem Global de Dispositivos**

- Visualização de todos os dispositivos da rede

- Filtros por usuário, status, ou palavra

- Busca por MAC, IP, hostname

- Paginação e ordenação

- Informações detalhadas de cada dispositivo

- ✅ **Aprovação de Dispositivos**

- Fluxo de aprovação para novos dispositivos

- Aprovação individual ou em lote

- Notificação ao usuário após aprovação

- Histórico de aprovações

- ✅ **Bloqueio Manual**

- Bloqueio imediato de dispositivo

- Bloqueio por MAC via alias no pfSense

- Motivo obrigatório para bloqueio

- Notificação ao usuário afetado

- Aplicação automática de regras no firewall

- ✅ **Liberação Manual**

- Desbloqueio de dispositivos bloqueados

- Remoção de MAC do alias de bloqueio

- Notificação ao usuário (Não implementado)

- Aplicação automática de mudanças

- ✅ **Bloqueio/Liberação Automatizada**

- Sistema de regras automáticas baseado em incidentes

- Bloqueio automático por gravidade de incidente

- Integração com sistema Zeek

- Alertas em tempo real para gestores

- Logs detalhados de ações automáticas

  

#### **Endpoints Implementados**

-  `GET /api/devices/dhcp/devices` - Listar todos dispositivos

-  `POST /api/devices/approve` - Aprovar dispositivo

-  `POST /api/devices/block` - Bloquear dispositivo

-  `POST /api/devices/unblock` - Liberar dispositivo

-  `GET /api/devices/pending` - Listar dispositivos pendentes

-  `GET /api/devices/blocked` - Listar dispositivos bloqueados

  

#### **Arquivos Relacionados**

-  `backend/services_firewalls/router.py`

-  `backend/services_firewalls/blocking_feedback_service.py`

-  `backend/services_firewalls/alias_service.py`

-  `backend/db/models.py`

  

---

  

### **[IMPL03] Histórico de Bloqueios - Gestor**

**Status:** ✅ Concluído

**Prioridade:** 🟡 Média

**Implementado em:** Versão 1.0

  

#### **Descrição**

Sistema de registro e consulta de histórico completo de bloqueios e liberações de dispositivos.

  

#### **Funcionalidades Implementadas**

- ✅ **Registro de Bloqueios**

- Armazenamento de data/hora do bloqueio

- Registro de gestor responsável

- Motivo do bloqueio

- Tipo de bloqueio (manual/automático)

- Gravidade do incidente associado

- Dispositivo afetado (MAC, IP, usuário)

- ✅ **Registro de Liberações**

- Data/hora da liberação

- Gestor que liberou

- Motivo da liberação

- Tempo total de bloqueio

- ✅ **Consulta de Histórico**

- Filtro por período

- Filtro por dispositivo (MAC/IP)

- Filtro por usuário

- Filtro por gestor responsável

- Filtro por tipo (manual/automático)

- Exportação de relatórios

- ✅ **Estatísticas**

- Total de bloqueios por período

- Média de tempo de bloqueio

- Dispositivos mais bloqueados

- Gestores mais ativos

- Gráficos de tendência

  

#### **Endpoints Implementados**

-  `GET /api/devices/blocking/history` - Histórico de bloqueios

-  `GET /api/devices/blocking/statistics` - Estatísticas de bloqueio

-  `GET /api/devices/{mac}/blocking-history` - Histórico por dispositivo

  

#### **Arquivos Relacionados**

-  `backend/services_firewalls/blocking_feedback_service.py`

-  `backend/db/models.py` (BlockingHistory, tabela de histórico)

  

---

  

### **[IMPL04] Sistema de Incidentes - Gestor**

**Status:** ✅ Concluído

**Prioridade:** 🔴 Alta

**Implementado em:** Versão 1.0

  

#### **Descrição**

Sistema completo de monitoramento, listagem e gestão de incidentes de segurança detectados pelo Zeek.

  

#### **Funcionalidades Implementadas**

- ✅ **Captura de Incidentes**

- Integração com logs do Zeek

- Parsing de logs (notice.log)

- Classificação automática por tipo

- Análise de gravidade (crítico, alto, médio, baixo)



- ✅ **Listagem de Incidentes**

- Visualização de todos os incidentes

- Filtros múltiplos:

- Por dispositivo (MAC/IP)

- Por usuário

- Por tipo de incidente

- Por gravidade

- Por período

- Por status (novo, em análise, resolvido)

- Ordenação customizável

- Paginação eficiente


#### **Endpoints Implementados**

-  `GET /api/incidents` - Listar incidentes

-  `GET /api/incidents/{id}` - Detalhe do incidente

-  `GET /api/incidents/statistics` - Estatísticas de incidentes

-  `GET /api/incidents/recent` - Incidentes recentes

-  `POST /api/incidents/{id}/mark-analyzed` - Marcar como analisado

-  `POST /api/incidents/{id}/comment` - Adicionar comentário

-  `GET /api/incidents/device/{mac}` - Incidentes por dispositivo

  

#### **Arquivos Relacionados**

-  `backend/services_scanners/incident_service.py`

-  `backend/services_scanners/zeek_service.py`

-  `backend/db/models.py` (Incident, IncidentType)

  

---

  

### **[IMPL05] Autenticação Multi-Provider**

**Status:** ✅ Concluído

**Prioridade:** 🔴 Alta

**Implementado em:** Versão 1.0

  

#### **Descrição**

Sistema completo de autenticação com suporte a múltiplos provedores (Google OAuth,).

  

#### **Funcionalidades Implementadas**

-  ⚠️ **Autenticação CAFe  Esperando homologação**

- Integração com IdP SAML

- Single Sign-On (SSO)

- Logout federado

- Mapeamento de atributos

- Integração CAFe (Comunidade Acadêmica Federada)

- Autenticação para instituições de ensino

- Suporte a Shibboleth
- ✅ **Autenticação Google**

- Google OAuth 2.0

- Cadastro automático no primeiro login

- Sincronização de dados do perfil






#### **Endpoints Implementados**

-  `POST /api/auth/saml2/login` - Login CAFe

-  `POST /api/auth/saml2/metadata` - Login CAFe

-  `POST /api/auth/google/login` - Login Google

-  `POST /api/auth/logout` - Logout


  

#### **Arquivos Relacionados**

-  `backend/auth/saml_auth.py`

-  `backend/auth/google_auth.py`

-  `backend/auth/cafe_auth.py`

-  `backend/auth/base/`

  

---

  

### **[IMPL06] Sistema de Permissões e Perfis**

**Status:** ⏳Em desenvolvimento

**Prioridade:** 🔴 Alta

**Implementado em:** Versão 2.0

  

#### **Descrição**

Sistema completo de controle de acesso baseado em perfis (RBAC - Role-Based Access Control).

  

#### **Funcionalidades Implementadas**

- ✅ **Perfis de Usuário**

- Administrador (acesso total)

- Gestor (gerenciamento de dispositivos e usuários)

- Observador (visualização apenas)

- Usuário comum (gestão de próprios dispositivos)

- ✅ **Controle de Permissões**

- Permissões granulares por endpoint

- Validação automática em todas as rotas

- Middleware de autorização

- Logs de tentativas de acesso negado

- ✅ **Atribuição de Dispositivos**

- Vinculação dispositivo-usuário

- Aprovação de gestores

- Histórico de atribuições

- Transferência de propriedade

  

#### **Endpoints Implementados**

-  `GET /api/users/permissions` - Listar permissões

-  `POST /api/users/{id}/assign-role` - Atribuir perfil

-  `GET /api/users/me/permissions` - Minhas permissões

  

#### **Arquivos Relacionados**

-  `backend/services_firewalls/permission_service.py`

-  `backend/services_firewalls/user_device_service.py`

-  `backend/db/models.py` (User, UserPermission, UserDeviceAssignment)

-  `backend/db/enums.py` (UserPermission enum)

  

---

  

### **[IMPL07] Integração com pfSense**

**Status:** ✅ Concluído

**Prioridade:** 🔴 Alta

**Implementado em:** Versão 1.0

  

#### **Descrição**

Integração completa com API do pfSense para gestão de firewall, DHCP e aliases.

  

#### **Funcionalidades Implementadas**

- ✅ **Gestão de DHCP**

- Criação de mapeamentos estáticos

- Atualização de mapeamentos

- Exclusão de mapeamentos

- Listagem de servidores DHCP

- Apply automático de mudanças DHCP

- ✅ **Gestão de Aliases**

- Criação de aliases de IP

- Adição/remoção de IPs em aliases

- Atualização de aliases

- Exclusão de aliases

- Apply automático de mudanças no firewall

- ✅ **Gestão de Regras de Firewall**

- Listagem de regras

- Sincronização com banco local

- Aplicação de mudanças pendentes

- ✅ **Sincronização**

- Sincronização bidirecional (pfSense ↔ Banco)

- Resolução de conflitos

- Atualização de IDs do pfSense

  

#### **Endpoints Implementados**

-  `GET /api/devices/pfsense/aliases` - Listar aliases

-  `POST /api/devices/pfsense/aliases` - Criar alias

-  `PATCH /api/devices/pfsense/aliases/{id}` - Atualizar alias

-  `DELETE /api/devices/pfsense/aliases/{id}` - Excluir alias

-  `POST /api/devices/firewall/apply` - Aplicar mudanças firewall

-  `POST /api/devices/dhcp/apply` - Aplicar mudanças DHCP

-  `GET /api/devices/firewall/rules` - Listar regras

  

#### **Arquivos Relacionados**

-  `backend/services_firewalls/pfsense_client.py`

-  `backend/services_firewalls/alias_service.py`

-  `backend/services_firewalls/dhcp_service.py`

-  `backend/docs/GESTAO_DISPOSITIVOS_DHCP.md`

  

---

  

### **[IMPL08] Integração com Zeek (IDS/IPS)**

**Status:** ✅ Concluído

**Prioridade:** 🔴 Alta

**Implementado em:** Versão 1.0

  

#### **Descrição**

Integração completa com sistema Zeek para detecção de intrusões e análise de tráfego de rede.

  

#### **Funcionalidades Implementadas**

- ✅ **Monitoramento de Logs**

- Leitura contínua de logs Zeek

- Parsing de múltiplos tipos de log:

- conn.log (conexões)

- notice.log (alertas)

- dns.log (consultas DNS)

- http.log (tráfego HTTP)

- ssh.log (conexões SSH)

- ssl.log (certificados SSL/TLS)

- ✅ **Detecção de Anomalias**

- Identificação de padrões suspeitos

- Análise de comportamento

- Correlação de eventos

- Classificação de gravidade

- ✅ **Alertas Automáticos**

- Geração de alertas em tempo real

- Notificação para gestores

- Ações automáticas baseadas em regras

  

#### **Arquivos Relacionados**

-  `backend/services_scanners/incident_service.py`

-  `backend/services_scanners/zeek_service.py`

-  `api-zeek/` (diretório com logs)

  

---

  

## 🎯 Casos de Uso (User Stories)

  

### **[UC01] Histórico de Dispositivos Removidos**

**Status:** 🆕 Novo

**Prioridade:** 🟡 Média

  

#### **Descrição**

Como gestor do sistema, eu preciso visualizar o histórico completo de todos os dispositivos que foram removidos da rede, para que eu possa auditar e rastrear alterações no ambiente.

  

#### **Critérios de Aceitação**

- [ ] Sistema deve armazenar dados completos do dispositivo antes da remoção

- [ ] Histórico deve incluir: MAC, IP, hostname, descrição, usuário responsável

- [ ] Histórico deve registrar data/hora da remoção

- [ ] Histórico deve registrar motivo da remoção (se informado)

- [ ] Histórico deve registrar quem executou a remoção

- [ ] Interface deve permitir busca e filtro por período, MAC, IP ou usuário

- [ ] Dados devem ser mantidos por período configurável (padrão: 12 meses)

- [ ] Sistema deve permitir exportação do histórico em CSV/JSON

  

#### **Tarefas Técnicas**

- [ ] Criar tabela `device_removal_history` no banco de dados

- [ ] Implementar trigger/service para capturar dados antes da exclusão

- [ ] Criar endpoints REST para consulta do histórico

- [ ] Implementar filtros e paginação

- [ ] Criar interface no frontend

- [ ] Adicionar testes unitários e de integração

  

#### **Estimativa**

8-13 pontos de história

  

---

  

### **[UC02] Template de Arquivo ENV**

**Status:** 🆕 Novo

**Prioridade:** 🟢 Baixa

  

#### **Descrição**

Como desenvolvedor ou administrador, eu preciso de um arquivo template `.env.example` completo e documentado, para que eu possa configurar o sistema rapidamente sem consultar a documentação extensa.

  

#### **Critérios de Aceitação**

- [ ] Arquivo `.env.example` deve conter todas as variáveis necessárias

- [ ] Cada variável deve ter comentário explicativo

- [ ] Valores de exemplo devem ser fornecidos (sem expor dados sensíveis)

- [ ] Deve incluir seção para configuração do pfSense

- [ ] Deve incluir seção para configuração do Zeek

- [ ] Deve incluir seção para autenticação (SAML, Google, CAFe)

- [ ] Deve incluir seção para banco de dados

- [ ] Documento README deve referenciar o template

  

#### **Tarefas Técnicas**

- [ ] Criar arquivo `.env.example` na raiz do projeto backend

- [ ] Documentar todas as variáveis de ambiente usadas

- [ ] Adicionar validação de variáveis obrigatórias no startup

- [ ] Atualizar README.md com instruções de configuração

- [ ] Criar script de verificação de configuração

  

#### **Estimativa**

3-5 pontos de história

  

---

  

### **[UC03] Período de Permanência Online de Usuários**

**Status:** 🆕 Novo

**Prioridade:** 🟡 Média

  

#### **Descrição**

Como gestor, eu preciso visualizar quanto tempo cada usuário permanece online (conectado à rede), para que eu possa analisar padrões de uso e identificar comportamentos anômalos.

  

#### **Critérios de Aceitação**

- [ ] Dashboard deve exibir tempo total online por usuário

- [ ] Sistema deve registrar timestamps de conexão e desconexão

- [ ] Deve permitir filtro por período (hoje, semana, mês, customizado)

- [ ] Deve exibir estatísticas: tempo médio, mínimo, máximo

- [ ] Deve mostrar gráfico de linha temporal de conexões

- [ ] Deve identificar usuários com tempo online anormal (muito alto/baixo)

- [ ] Deve permitir exportação dos relatórios

- [ ] Atualização deve ser em tempo real ou próximo ao real

  

#### **Tarefas Técnicas**

- [ ] Criar tabela `user_session_history` para armazenar sessões

- [ ] Implementar serviço de rastreamento de sessões

- [ ] Criar endpoints para consulta de estatísticas

- [ ] Desenvolver cálculos de agregação (tempo total, médio, etc.)

- [ ] Criar componentes visuais no frontend (gráficos)

- [ ] Implementar sistema de alertas para comportamento anormal

- [ ] Adicionar testes de performance para grandes volumes de dados

  

#### **Estimativa**

13-21 pontos de história

  

---

  

### **[UC04] Número Total de Conexões por Gestor**

**Status:** 🆕 Novo

**Prioridade:** 🟡 Média

  

#### **Descrição**

Como gestor, eu preciso consultar o número total de conexões gerenciadas por cada gestor do sistema, para que eu possa avaliar a distribuição de trabalho e capacidade.

  

#### **Critérios de Aceitação**

- [ ] Dashboard deve exibir total de dispositivos por gestor

- [ ] Deve exibir total de usuários atribuídos por gestor

- [ ] Deve mostrar número de ações realizadas (aprovações, bloqueios, etc.)

- [ ] Deve permitir comparação entre gestores

- [ ] Deve incluir filtro por período

- [ ] Deve mostrar gráfico de distribuição (pizza ou barras)

- [ ] Deve identificar gestores com sobrecarga ou subutilização

- [ ] Deve permitir drill-down para detalhes de cada gestor

  

#### **Tarefas Técnicas**

- [ ] Criar queries de agregação por gestor

- [ ] Implementar endpoint `/api/statistics/managers`

- [ ] Criar serviço de estatísticas por gestor

- [ ] Desenvolver componentes visuais no frontend

- [ ] Implementar cache para otimizar performance

- [ ] Adicionar filtros e paginação

- [ ] Criar relatórios exportáveis

  

#### **Estimativa**

8-13 pontos de história

  

---

  

### **[UC05] Resumo Simplificado de Incidentes para Usuário**

**Status:** 🆕 Novo

**Prioridade:** 🟡 Média

  

#### **Descrição**

Como usuário comum (não gestor), eu preciso visualizar um resumo simplificado dos incidentes relacionados aos meus dispositivos, para que eu possa entender problemas de segurança sem informações técnicas complexas.

  

#### **Critérios de Aceitação**

- [ ] Interface deve usar linguagem não-técnica

- [ ] Deve mostrar apenas incidentes dos dispositivos do usuário

- [ ] Deve categorizar incidentes por gravidade (🔴 Alto, 🟡 Médio, 🟢 Baixo)

- [ ] Deve exibir data/hora do incidente de forma amigável

- [ ] Deve fornecer descrição simplificada do problema

- [ ] Deve sugerir ações corretivas quando aplicável

- [ ] Não deve expor detalhes técnicos sensíveis

- [ ] Deve incluir ícones e cores para facilitar compreensão

  

#### **Tarefas Técnicas**

- [ ] Criar serviço de tradução de incidentes técnicos

- [ ] Implementar endpoint `/api/users/me/incidents/summary`

- [ ] Desenvolver componente visual simplificado

- [ ] Criar sistema de categorização de gravidade

- [ ] Implementar sistema de sugestões de ações

- [ ] Adicionar testes de UX/UI

- [ ] Criar documentação de ajuda para usuários

  

#### **Estimativa**

8-13 pontos de história

  

---

  

### **[UC06] Bloqueio Temporário de Dispositivo Individual**

**Status:** 🆕 Novo

**Prioridade:** 🔴 Alta

  

#### **Descrição**

Como gestor, eu preciso bloquear temporariamente um dispositivo específico com diferentes opções de tempo (imediato, 15min, 24h), para que eu possa responder rapidamente a incidentes de segurança sem bloqueio permanente.

  

#### **Critérios de Aceitação**

- [ ] Sistema deve oferecer opções de bloqueio:

- [ ] Imediato (permanente até desbloqueio manual)

- [ ] Temporário 15 minutos (desbloqueio automático)

- [ ] Temporário 24 horas (desbloqueio automático)

- [ ] Recorrente (bloqueia novamente se reconectar antes do prazo)

- [ ] Bloqueio deve ser aplicado imediatamente no pfSense

- [ ] Sistema deve registrar motivo do bloqueio

- [ ] Usuário proprietário deve ser notificado

- [ ] Gestor deve receber confirmação da ação

- [ ] Histórico de bloqueios deve ser mantido

- [ ] Sistema deve desbloquear automaticamente após o período

- [ ] Interface deve mostrar tempo restante de bloqueio

  

#### **Tarefas Técnicas**

- [ ] Criar tabela `device_blocks` para histórico

- [ ] Implementar sistema de agendamento (scheduler) para desbloqueio

- [ ] Criar endpoint `POST /api/devices/{id}/block`

- [ ] Implementar lógica de bloqueio recorrente

- [ ] Criar worker/job para processar desbloqueios agendados

- [ ] Implementar sistema de notificações

- [ ] Adicionar validações e tratamento de erros

- [ ] Criar interface de bloqueio no frontend

- [ ] Adicionar contador regressivo visual

- [ ] Implementar testes automatizados

  

#### **Estimativa**

13-21 pontos de história

  

---

  

### **[UC07] Bloqueio Geral (Múltiplos Dispositivos)**

**Status:** 🆕 Novo

**Prioridade:** 🔴 Alta

  

#### **Descrição**

Como gestor, eu preciso bloquear múltiplos dispositivos simultaneamente com diferentes opções de tempo, para que eu possa responder rapidamente a incidentes de segurança em massa.

  

#### **Critérios de Aceitação**

- [ ] Sistema deve permitir seleção múltipla de dispositivos

- [ ] Deve oferecer as mesmas opções de UC06

- [ ] Deve aplicar bloqueio em batch (lote)

- [ ] Deve exibir progresso da operação

- [ ] Deve registrar sucesso/falha por dispositivo

- [ ] Deve permitir bloqueio por critérios (ex: todos de um usuário)

- [ ] Deve gerar relatório da operação em lote

- [ ] Deve permitir rollback em caso de erro parcial

  

#### **Tarefas Técnicas**

- [ ] Criar endpoint `POST /api/devices/block/bulk`

- [ ] Implementar processamento em lote otimizado

- [ ] Criar sistema de fila para grandes volumes

- [ ] Implementar transações para garantir consistência

- [ ] Criar interface de seleção múltipla

- [ ] Adicionar barra de progresso

- [ ] Implementar sistema de rollback

- [ ] Criar logs detalhados de operações em lote

- [ ] Adicionar testes de carga e stress

  

#### **Estimativa**

13-21 pontos de história

  

---

  

### **[UC08] Cadastro Zero-Touch com Autenticação Google**

**Status:** 🆕 Novo

**Prioridade:** 🟡 Média

  

#### **Descrição**

Como usuário novo, eu preciso realizar cadastro rápido usando minha conta Google, com opção de informar CPF e celular para notificações, para que eu possa começar a usar o sistema rapidamente sem processos burocráticos.

  

#### **Critérios de Aceitação**

- [ ] Sistema deve permitir login/cadastro via Google OAuth

- [ ] Após autenticação Google, sistema deve coletar dados complementares:

- [ ] CPF (opcional, mas recomendado)

- [ ] Celular (opcional, para receber notificações SMS/WhatsApp)

- [ ] Campo CPF deve ter validação de formato

- [ ] Campo celular deve aceitar formato brasileiro (+55)

- [ ] Sistema deve criar conta automaticamente após primeiro login Google

- [ ] Usuário deve poder pular campos opcionais

- [ ] Sistema deve mostrar benefícios de informar CPF e celular

- [ ] Dados devem ser armazenados de forma segura (LGPD)

- [ ] Sistema deve permitir edição posterior dos dados

  

#### **Fluxo do Usuário**

1. Usuário clica em "Entrar com Google"

2. Autentica via Google OAuth

3. Sistema verifica se é primeiro acesso

4. Se sim: exibe tela de dados complementares

5. Usuário informa CPF (opcional) e celular (opcional)

6. Sistema cria conta e redireciona para dashboard

  

#### **Tarefas Técnicas**

- [ ] Implementar Google OAuth 2.0

- [ ] Criar tabela `user_additional_info` (cpf, celular)

- [ ] Implementar validação de CPF

- [ ] Implementar validação de celular (formato brasileiro)

- [ ] Criar endpoint `POST /api/auth/google/callback`

- [ ] Criar endpoint `PATCH /api/users/me/additional-info`

- [ ] Implementar tela de coleta de dados complementares

- [ ] Adicionar criptografia para dados sensíveis (CPF)

- [ ] Implementar consent/termo de uso LGPD

- [ ] Criar sistema de notificações SMS/WhatsApp (futuro)

- [ ] Adicionar logs de auditoria

  

#### **Estimativa**

8-13 pontos de história

  

---

  

### **[UC09] Cadastro Multi-Campus de Instituição**

**Status:** 🆕 Novo

**Prioridade:** 🟡 Média

  

#### **Descrição**

Como administrador de instituição, eu preciso cadastrar múltiplos campus da mesma instituição (ex: UNIPAMPA - Alegrete, Uruguaiana, São Borja, etc.), para que cada campus tenha sua própria configuração de pfSense e gestão independente.

  

#### **Critérios de Aceitação**

- [ ] Sistema deve permitir cadastro de instituição pai (ex: UNIPAMPA)

- [ ] Sistema deve permitir cadastro de múltiplos campus vinculados

- [ ] Cada campus deve ter:

- [ ] Nome do campus (ex: "Alegrete", "Uruguaiana")

- [ ] Configuração pfSense própria (IP, credenciais)

- [ ] Faixa de IPs específica

- [ ] Gestores específicos do campus

- [ ] Configurações de rede independentes

- [ ] Sistema deve permitir visão consolidada (todos os campus)

- [ ] Sistema deve permitir visão individual por campus

- [ ] Relatórios devem poder ser filtrados por campus

- [ ] Gestores podem ter acesso a um ou múltiplos campus

  

#### **Estrutura Hierárquica**

```

Instituição (UNIPAMPA)

├── Campus Alegrete

│ ├── pfSense: 192.168.1.1

│ ├── Rede: 192.168.1.0/24

│ └── Gestores: [gestor1, gestor2]

├── Campus Uruguaiana

│ ├── pfSense: 192.168.2.1

│ ├── Rede: 192.168.2.0/24

│ └── Gestores: [gestor3]

└── Campus São Borja

├── pfSense: 192.168.3.1

├── Rede: 192.168.3.0/24

└── Gestores: [gestor4]

```

  

#### **Tarefas Técnicas**

- [ ] Criar tabela `institutions` (nome, tipo, etc.)

- [ ] Criar tabela `campus` (institution_id, nome, config_pfsense)

- [ ] Modificar tabela `users` para incluir `campus_id`

- [ ] Criar relacionamento many-to-many entre gestores e campus

- [ ] Implementar endpoints REST para instituições e campus

- [ ] Criar interface de cadastro hierárquico

- [ ] Implementar filtros por campus em todos os endpoints

- [ ] Criar dashboard consolidado multi-campus

- [ ] Adicionar seletor de campus na interface

- [ ] Implementar permissões por campus

- [ ] Migrar dados existentes para novo modelo

  

#### **Estimativa**

21-34 pontos de história

  

---

  

### **[UC10] Portal Captive com Redirecionamento Inteligente**

**Status:** 🆕 Novo

**Prioridade:** 🔴 Alta

  

#### **Descrição**

Como visitante ou novo usuário, quando me conecto a uma rede aberta, eu preciso ser redirecionado para uma tela de boas-vindas que exibe informações do meu dispositivo e concede acesso temporário (5 minutos), para que eu possa me cadastrar ou autenticar adequadamente.

  

#### **Critérios de Aceitação**

- [ ] Sistema deve detectar conexão em faixa de IP aberta/guest

- [ ] Sistema deve redirecionar automaticamente para portal captive

- [ ] Portal deve exibir:

- [ ] Nome/hostname do dispositivo detectado

- [ ] Endereço MAC

- [ ] Endereço IP temporário

- [ ] Fabricante do dispositivo (via MAC lookup)

- [ ] Tempo restante de acesso (countdown)

- [ ] Sistema deve conceder lease DHCP de 5 minutos

- [ ] Após 5 minutos, sistema deve desconectar dispositivo

- [ ] Portal deve oferecer opções:

- [ ] Fazer login (usuário existente)

- [ ] Cadastrar-se (novo usuário)

- [ ] Login com Google

- [ ] Solicitar acesso temporário estendido

- [ ] Portal deve ser responsivo (funcionar em mobile)

- [ ] Sistema deve registrar todas as tentativas de acesso

  

#### **Fluxo do Usuário**

1. Dispositivo conecta na rede guest/aberta

2. DHCP concede IP temporário (5 min)

3. Primeira requisição HTTP é interceptada

4. Usuário é redirecionado para portal captive

5. Portal exibe informações do dispositivo

6. Usuário escolhe uma ação (login/cadastro)

7. Após autenticação, lease é estendido

  

#### **Tarefas Técnicas**

- [ ] Configurar zona DHCP guest no pfSense

- [ ] Configurar regras de firewall para redirecionamento

- [ ] Criar endpoint de portal captive

- [ ] Implementar detecção de fabricante via MAC

- [ ] Criar sistema de lease temporário (5 min)

- [ ] Implementar interceptação de requisições HTTP

- [ ] Desenvolver interface do portal captive

- [ ] Criar contador regressivo visual

- [ ] Implementar integração com autenticação

- [ ] Criar sistema de extensão de acesso

- [ ] Adicionar logs de acesso guest

- [ ] Implementar testes de segurança

  

#### **Estimativa**

21-34 pontos de história

  

---

  

### **[UC11] Identificação de Dispositivo via Fingerprint**

**Status:** 🆕 Novo

**Prioridade:** 🟡 Média

  

#### **Descrição**

Como sistema, eu preciso identificar dispositivos através de fingerprinting (características únicas além do MAC), para que eu possa atualizar registros quando o MAC mudar e tentar identificar o MAC original em caso de spoofing.

  

#### **Critérios de Aceitação**

- [ ] Sistema deve coletar fingerprint do dispositivo:

- [ ] User-Agent HTTP

- [ ] TTL de pacotes

- [ ] Tamanho de janela TCP

- [ ] Sistema operacional (via p0f ou similar)

- [ ] Resolução de tela (se aplicável)

- [ ] Timezone

- [ ] Linguagem do navegador

- [ ] Sistema deve criar assinatura única por dispositivo

- [ ] Quando MAC mudar, sistema deve:

- [ ] Comparar fingerprint com dispositivos conhecidos

- [ ] Se match > 80%: atualizar MAC do dispositivo existente

- [ ] Se match < 80%: criar novo registro

- [ ] Sistema deve tentar identificar MAC original:

- [ ] Verificar OUI (Organizationally Unique Identifier)

- [ ] Comparar com MACs anteriores do dispositivo

- [ ] Registrar suspeita de MAC spoofing

- [ ] Sistema deve manter histórico de MACs por dispositivo

- [ ] Sistema deve alertar gestor sobre possível spoofing

  

#### **Técnicas de Fingerprinting**

1.  **Passivo**: Análise de tráfego de rede (Zeek)

2.  **Ativo**: Requisições HTTP/HTTPS

3.  **Híbrido**: Combinação de múltiplas fontes

  

#### **Tarefas Técnicas**

- [ ] Criar tabela `device_fingerprints`

- [ ] Criar tabela `device_mac_history`

- [ ] Implementar coleta de fingerprint via Zeek

- [ ] Implementar coleta de fingerprint via HTTP

- [ ] Criar algoritmo de matching de fingerprints

- [ ] Implementar cálculo de similaridade (Jaccard, Cosine)

- [ ] Criar serviço de detecção de MAC spoofing

- [ ] Implementar lookup de OUI (MAC vendor)

- [ ] Criar endpoint `/api/devices/{id}/fingerprint`

- [ ] Desenvolver interface de histórico de MACs

- [ ] Implementar sistema de alertas para spoofing

- [ ] Adicionar métricas de confiança do match

- [ ] Criar testes com dispositivos reais

  

#### **Estimativa**

21-34 pontos de história

  

---

  

## 🐛 Bugs Identificados

  

### **[BUG01] Apply Automático em Aliases**

**Status:** ✅ Concluído

**Prioridade:** 🔴 Alta

**Resolvido em:** 10/10/2025

  

#### **Descrição**

Sistema não estava aplicando automaticamente as alterações no pfSense após operações em aliases (adicionar/remover IPs).

  

#### **Solução Implementada**

- ✅ Criada função `aplicar_mudancas_firewall_pfsense()`

- ✅ Endpoint `POST /api/devices/firewall/apply` implementado

- ✅ Apply automático adicionado após operações em aliases

- ✅ Documentação atualizada

  

#### **Arquivos Alterados**

-  `backend/services_firewalls/pfsense_client.py`

-  `backend/services_firewalls/router.py`

  

---

  

### **[BUG02] Apply Automático em DHCP**

**Status:** ✅ Concluído

**Prioridade:** 🔴 Alta

**Resolvido em:** 10/10/2025

  

#### **Descrição**

Sistema não estava aplicando automaticamente as alterações no servidor DHCP do pfSense após operações de CREATE, UPDATE e DELETE de mapeamentos estáticos.

  

#### **Solução Implementada**

- ✅ Criada função `aplicar_mudancas_dhcp_pfsense()`

- ✅ Endpoint `POST /api/devices/dhcp/apply` implementado

- ✅ Apply automático adicionado em CREATE (`POST /dhcp/static_mapping`)

- ✅ Apply automático adicionado em CREATE (`POST /dhcp/save`)

- ✅ Parâmetro `apply=true` como padrão em UPDATE e DELETE

- ✅ Documentação completa criada (`GESTAO_DISPOSITIVOS_DHCP.md`)

  

#### **Comportamento Atual**

-  **CREATE**: Apply automático sempre

-  **UPDATE**: Apply automático por padrão (use `apply=false` para desativar)

-  **DELETE**: Apply automático por padrão (use `apply=false` para desativar)

  

#### **Arquivos Alterados**

-  `backend/services_firewalls/pfsense_client.py`

-  `backend/services_firewalls/router.py`

-  `backend/docs/GESTAO_DISPOSITIVOS_DHCP.md`

  

---

  

### **[BUG03] Captura Automática de Incidentes pelo Observador**

**Status:** 🆕 Novo

**Prioridade:** 🔴 Alta

  

#### **Descrição**

O sistema de observação de logs Zeek não está capturando e exibindo automaticamente novos registros de incidentes em tempo real ou próximo ao real.

  

#### **Comportamento Esperado**

- Sistema deve monitorar continuamente logs do Zeek

- Novos incidentes devem ser processados automaticamente

- Interface deve atualizar em tempo real (WebSocket ou polling)

- Notificações devem ser enviadas para gestores

- Incidentes críticos devem gerar alertas imediatos

  

#### **Comportamento Atual**

- [ ] Verificar se há polling ativo

- [ ] Verificar frequência de verificação

- [ ] Verificar se há erros nos logs

- [ ] Verificar integração com Zeek

  

#### **Tarefas para Resolução**

- [ ] Investigar serviço `incident_service.py`

- [ ] Verificar cron jobs ou workers

- [ ] Implementar WebSocket para push em tempo real

- [ ] Criar sistema de fila para processamento

- [ ] Adicionar logging detalhado para debug

- [ ] Implementar health check do serviço

- [ ] Criar alertas para falhas de captura

- [ ] Adicionar métricas de performance

- [ ] Implementar testes automatizados

  

#### **Estimativa**

13-21 pontos de história

  

---

  

## 📈 Métricas do Backlog

  

### **Resumo por Status**

- 🆕 Novo: 12 items (planejados)

- ✅ Concluído: 10 items (8 funcionalidades + 2 bugs)

  

### **Resumo por Prioridade**

- 🔴 Alta: 11 items (6 implementados + 5 planejados)

- 🟡 Média: 9 items (2 implementados + 7 planejados)

- 🟢 Baixa: 1 item (planejado)

  

### **Resumo por Tipo**

- Funcionalidades Implementadas: 8 items ✅

- Casos de Uso Planejados: 11 items 🆕

- Bugs Resolvidos: 2 items ✅

- Bugs Pendentes: 1 item 🚧

  

### **Cobertura de Funcionalidades**

-  **Core do Sistema**: 100% implementado ✅

- Gestão de dispositivos (usuário e gestor)

- Autenticação multi-provider

- Bloqueio/Liberação manual e automático

- Sistema de permissões (RBAC)

- Integração pfSense e Zeek

-  **Analytics e Monitoramento**: 60% implementado

- Sistema de incidentes ✅

- Histórico de bloqueios ✅

- Período online de usuários ⏳

- Conexões por gestor ⏳

-  **UX e Aprimoramentos**: 20% implementado

- Portal captive ⏳

- Bloqueio temporário ⏳

- Fingerprinting ⏳

- Multi-campus ⏳

  

---

  

## 🗓️ Roadmap

  

### **POC-01 (Prioridade Alta - Bugs Críticos)**

- ✅ [BUG01] Apply Automático em Aliases

- ✅ [BUG02] Apply Automático em DHCP

- 🚧 [BUG03] Captura Automática de Incidentes

  

### **POC-02 (Prioridade Alta - Funcionalidades Core)**
- [UC11] Identificação de Dispositivo via Fingerprint

- [UC06] Bloqueio Temporário de Dispositivo 

- [UC07] Bloqueio (Múltiplos Dispositivos)

- [UC10] Portal Captive com Redirecionamento Inteligente

  

### **POC-02 (Prioridade Média - Autenticação e Multi-tenancy)**

- [UC08] Cadastro Zero-Touch com Autenticação Google

- [UC09] Cadastro Multi-Campus de Instituição

- [UC05] Resumo Simplificado de Incidentes

### **POC-02 (Prioridade Baixa- Analytics e Monitoramento)**

- [UC03] Período de Permanência Online de Usuários

- [UC04] Número Total de Conexões por Gestor

---

  

## 📝 Notas

  

### **Dependências Identificadas**

- UC06 e UC07 compartilham lógica de bloqueio temporário

- UC03 e UC04 compartilham infraestrutura de estatísticas

- BUG03 é pré-requisito para UC05 funcionar corretamente

- UC08 é relacionado com UC10 (cadastro via portal captive)

- UC09 impacta todos os módulos (multi-tenancy)

- UC10 depende de configuração no pfSense (captive portal)

- UC11 Possível integração com sistemas fingerprinting

  

### **Possíveis Riscos e Considerações**

- Bloqueios temporários requerem sistema de agendamento

- Portal captive (UC10) requer configuração cuidadosa de segurança

- Fingerprinting (UC11) pode ter falsos positivos

- LGPD: dados sensíveis (CPF) requerem criptografia e consentimento

  

### **Tecnologias Necessárias**
...
  

---

  

## 📊 Resumo Executivo

  

### **Estado Atual do Projeto (v1.0)**

✅ **8 Funcionalidades Core Implementadas**

✅ **100% do Core do Sistema Funcional**

✅ **2 Bugs Críticos Resolvidos**

🚧 **1 Bug em Investigação**

🆕 **11 Casos de Uso Planejados**


---

  

**Documento mantido por:** Equipe de Desenvolvimento API IoT-EDU

**Próxima revisão:** Semanal 

**Versão do Sistema:** v1.0

**Versão do Backlog:** v2.0