# 📚 Índice da Documentação

## 🎯 Visão Geral

Este diretório contém toda a documentação do sistema IoT-EDU Backend, organizada por categorias para facilitar a navegação.

## 📋 Categorias

### 🔧 Guias de Endpoints
Documentação detalhada dos endpoints da API:

- **[GUIA_ENDPOINT_TODOS_DISPOSITIVOS.md](GUIA_ENDPOINT_TODOS_DISPOSITIVOS.md)** - Listagem de todos os dispositivos (Gestores)
- **[GUIA_DHCP_STATIC_MAPPING.md](GUIA_DHCP_STATIC_MAPPING.md)** - Mapeamentos DHCP estáticos
- **[GUIA_ENDERECOS_IP.md](GUIA_ENDERECOS_IP.md)** - Gerenciamento de endereços IP
- **[GUIA_PERMISSOES_USUARIOS.md](GUIA_PERMISSOES_USUARIOS.md)** - Sistema de permissões

### 🧪 Guias Postman
Guias para testes e validação usando Postman:

- **[GUIA_POSTMAN_DHCP_SAVE.md](GUIA_POSTMAN_DHCP_SAVE.md)** - Testes de salvamento DHCP
- **[GUIA_POSTMAN_DHCP_STATIC_MAPPING.md](GUIA_POSTMAN_DHCP_STATIC_MAPPING.md)** - Testes de mapeamentos
- **[GUIA_POSTMAN_PERMISSOES.md](GUIA_POSTMAN_PERMISSOES.md)** - Testes de permissões
- **[GUIA_POSTMAN_ENDERECOS_IP.md](GUIA_POSTMAN_ENDERECOS_IP.md)** - Testes de endereços IP
- **[GUIA_ADICIONAR_IPS_ALIASES.md](GUIA_ADICIONAR_IPS_ALIASES.md)** - Adição de IPs em aliases
- **[POSTMAN_TESTES_ALIASES.md](POSTMAN_TESTES_ALIASES.md)** - Testes de aliases
- **[POSTMAN_USER_DEVICE_ASSIGNMENTS.md](POSTMAN_USER_DEVICE_ASSIGNMENTS.md)** - Atribuições usuário-dispositivo

### 📊 Documentação Técnica
Documentação técnica e arquitetural:

- **[README-pfsense-api-v2.md](README-pfsense-api-v2.md)** - Documentação da API pfSense
- **[README-firewall-rules.md](README-firewall-rules.md)** - Regras de firewall
- **[DOCUMENTACAO_WIREFRAME.md](DOCUMENTACAO_WIREFRAME.md)** - Documentação do wireframe

### 📈 Resumos e Relatórios
Resumos de implementações e relatórios de testes:

- **[RESUMO_ENDPOINT_TODOS_DISPOSITIVOS.md](RESUMO_ENDPOINT_TODOS_DISPOSITIVOS.md)** - Resumo da implementação do endpoint de todos os dispositivos
- **[RESUMO_TESTES_PERMISSOES.md](RESUMO_TESTES_PERMISSOES.md)** - Resumo dos testes de permissões

### 🎨 Interface
Arquivos de interface e wireframes:

- **[wireframe_iot_management.html](wireframe_iot_management.html)** - Interface de gerenciamento IoT

## 🔍 Como Usar

### Para Desenvolvedores
1. **Implementação**: Consulte os guias de endpoints para entender a API
2. **Testes**: Use os guias Postman para validar funcionalidades
3. **Integração**: Leia a documentação técnica para integração com pfSense

### Para Administradores
1. **Configuração**: Consulte a documentação técnica para configuração
2. **Deploy**: Use os guias de deploy em `../deploy/`
3. **Monitoramento**: Utilize os scripts em `../scripts/`

### Para Usuários Finais
1. **Interface**: Acesse o wireframe para entender a interface
2. **Funcionalidades**: Leia os guias de endpoints para entender as funcionalidades

## 📝 Convenções

- **Guias de Endpoints**: Documentação completa de cada endpoint
- **Guias Postman**: Instruções passo a passo para testes
- **Documentação Técnica**: Arquitetura e integrações
- **Resumos**: Visão geral de implementações
- **Interface**: Wireframes e mockups

## 🔗 Links Relacionados

- **[README Principal](../README.md)** - Visão geral do projeto
- **[Scripts Utilitários](../scripts/)** - Scripts de manutenção
- **[Coleções Postman](../postman/)** - Arquivos de teste
- **[Testes Automatizados](../testes/)** - Testes Python

---

**Última atualização**: Setembro 2025  
**Versão**: 2.0  
**Mantido por**: Equipe IoT-EDU
