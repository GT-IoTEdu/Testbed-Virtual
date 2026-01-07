

# 📋 Backlog do Projeto - API IoT-EDU

**Última atualização:** 10/10/2025  
**Versão:** 2.0 (Completo com Funcionalidades Implementadas)


## 📊 Visão Geral
Este documento contém o backlog de funcionalidades planejadas e bugs identificados para o sistema API IoT-EDU.


----------
## 📈 Métricas do Backlog

-   **Resumo por Status:**
    
    -   🆕 Novo: 12 items
        
    -   ✅ Concluído: 10 items
        
-   **Resumo por Prioridade:**
    
    -   🔴 Alta: 11 items
        
    -   🟡 Média: 9 items
        
    -   🟢 Baixa: 1 item
        
----------




## ✅ Funcionalidades Implementadas- POC-1 (v1.0)

-   [IMPL01] Gestão de Dispositivos (CRUD) - Perfil Usuário ✅
    
-   [IMPL02] Gestão de Dispositivos (Libera/Bloqueia) - Perfil Gestor ✅
    
-   [IMPL03] Histórico de Bloqueios - Gestor/Usuário ✅
    
-   [IMPL04] Sistema de Incidentes (Básico) - Gestor/Usuário ✅
    
-   [IMPL05] Autenticação Google ✅
    
-   [IMPL07] Integração com pfSense ✅
    
-   [IMPL08] Integração com Zeek (notice.log) ✅
    
#### 🐛 Bugs identificados POC-01

-   [BUG01] Apply Automático em Aliases ✅
    
-   [BUG02] Apply Automático em DHCP ✅
    
-   [BUG03] Captura Automática de Incidentes 🚧
    
## 🆕 Próximos Casos de Uso Planejados -POC-02

**Gestão de Dispositivos e Segurança**

-   [🔴UC06] Bloqueio Temporário de Dispositivo Individual
    
-   [🔴UC07] Bloqueio Geral (Múltiplos Dispositivos)
    
-   [🔴UC11] Identificação de Dispositivo via Fingerprint 
    

**Autenticação e Usuários**

-   [🔴UC02] Sistema completo de controle de acesso baseado em perfis
    
-   [🟡UC08] Cadastro Zero-Touch com Autenticação Google
    
-   [🔴UC10] Portal Captive com Redirecionamento Inteligente (MAC Randon)
    

**Multi-tenancy e Instituições**

-   [🟡UC09] Cadastro Multi-Campus de Instituição (Unipampa-Alegrete, Uruguaiana, tec...)
    

**Analytics e Monitoramento**

-   [🟢UC03] Período de Permanência Online de Usuários
    
-   [🟢UC04] Número Total de Conexões por Gestor
    
-   [🟡UC05] Resumo Simplificado de Incidentes para Usuário
    

----------

## 🐛 Bugs Identificados POC-02

   



## 🗓️ Roadmap

**POC-01 (Prioridade Alta - Bugs Críticos)**
    
-   🚧 [BUG03] Captura Automática de Incidentes
    

**POC-02 (Prioridade Alta - Funcionalidades Core)**
-   [UC02] Sistema completo de controle de acesso baseado em perfis

-   [UC06] Bloqueio Temporário de Dispositivo Individual
    
-   [UC07] Bloqueio Geral (Múltiplos Dispositivos)
    
-   [UC10] Portal Captive com Redirecionamento Inteligente
    
-   [UC11] Identificação de Dispositivo via Fingerprint
    

**POC-02 (Prioridade Média - Autenticação e Multi-tenancy)**

-   [UC08] Cadastro Zero-Touch com Autenticação Google
    
-   [UC09] Cadastro Multi-Campus de Instituição
    
-   [UC05] Resumo Simplificado de Incidentes
    

**POC-02 (Prioridade Baixa - Analytics e Monitoramento)**

-   [UC03] Período de Permanência Online de Usuários
    
-   [UC04] Número Total de Conexões por Gestor
    

----------

## 📝 Notas

**Dependências Identificadas**

-   UC06 e UC07 compartilham lógica de bloqueio temporário
    
-   UC03 e UC04 compartilham infraestrutura de estatísticas
    
-   BUG03 é pré-requisito para UC05 funcionar corretamente
    
-   UC08 é relacionado com UC10 (cadastro via portal captive)
    
-   UC09 impacta todos os módulos (multi-tenancy)
    
-   UC10 depende de configuração no pfSense (captive portal)
    
-   UC11 Possível integração com sistemas fingerprinting
    

**Possíveis Riscos e Considerações**

-   Bloqueios temporários requerem sistema de agendamento
    
-   Portal captive (UC10) requer configuração cuidadosa de segurança
    
-   Fingerprinting (UC11) pode ter falsos positivos
    
-   LGPD: dados sensíveis (CPF) requerem criptografia e consentimento
    

----------

## 📊 Resumo Executivo

**Estado Atual do Projeto (v1.0)**  
✅ 8 Funcionalidades Core Implementadas  
✅ 100% do Core do Sistema Funcional  
✅ 2 Bugs Críticos Resolvidos  
🚧 1 Bug em Investigação  
🆕 11 Casos de Uso Planejados

----------
