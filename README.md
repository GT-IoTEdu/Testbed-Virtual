
# Sistema de Registro IoT com Autenticação CAFe e pfSense

## Diagrama de Arquitetura
![Diagrama de Arquitetura do Sistema](https://raw.githubusercontent.com/JonerMello/COVID19/refs/heads/master/APIIoTV1.png) 

*Diagrama completo dos componentes e fluxos do sistema*

## Visão Geral
Sistema integrado para gerenciamento seguro de dispositivos IoT em ambientes acadêmicos, combinando:
- ✅ Autenticação federada via CAFe
- 🔐 Gerenciamento automatizado de regras no pfSense
- 🤖 Monitoramento inteligente de tráfego com IA
- 📊 Painel administrativo de dispositivos IoTs cadastrados

## Componentes Principais

### 1. Módulo de Autenticação
- **Integração CAFe** (SAML 2.0/OAuth2)
- Fluxo JWT interno após autenticação federada
- Controle de permissões granular


### 2. Serviço da API_IoT_EDU
| Funcionalidade | Tecnologia | Detalhes |
|---------------|------------|----------|
| Autenticação CAFe | SAML/OAuth2 | Integração com federação acadêmica |
| Validação de Dispositivos | Python + NetAddr | Checagem de IP/MAC e faixas autorizadas |
| Gerenciamento pfSense | Python + Requests | Rotação automática de API Keys<br>Endpoints: `/api/v1/firewall/rule` |
| Auditoria | Definir | Log de operações com:<br>- Usuário CAFe<br>- Timestamp<br>- Ações no firewall |

### 3. Endpoints Principais:

| Endpoint | Método | Descrição | Parâmetros |
|----------|--------|-----------|------------|
| `/auth/cafe` | GET | Inicia fluxo de autenticação | `redirect_uri` |
| `/api/devices` | POST | Registra novo dispositivo IoT | ```json<br>{<br>  "ip": "string",<br>  "mac": "string",<br>  "description": "string"<br>}``` |
| `/api/firewall/rules` | GET | Lista regras ativas | `?filter=iot` |
| `/monitoring/alerts` | GET | Consulta anomalias | `?severity=high` |

## Fluxo de Operação
1. Autenticação via CAFe (SAML/OAuth2)
2. Validação de permissões no sistema
3. Cadastro do dispositivo:
   ```json
   POST /api/devices
   {
     "ip": "192.168.10.50",
     "mac": "00:1A:2B:3C:4D:5E",
     "description": "Sensor Ambiental - Lab 5A"
   }
   ```
   ### 3.1 Criação automática da regra no pfSense:
 ```json
POST /api/v1/firewall/rule
Headers: {
  "Authorization": "Bearer {api_key}",
  "X-CAFE-User": "user@university.edu.br"
}
Body: {
  "interface": "IoT_VLAN",
  "src": "192.168.10.50",
  "descr": "IoT-EDU: Sensor Lab 5A",
  "tracker": 123456789,
  "top": true
}
  ```


----------

## 🔐 **Endpoints do pfSense para Integração com Dispositivos IoT**

Estes endpoints foram selecionados para permitir:

-   ✅ Cadastro automático de regras para dispositivos IoT
    
-   🔄 Atualização dinâmica de grupos (aliases)
    
-   📡 Monitoramento de tráfego e status de rede
    
-   🧾 Consulta de logs para análise inteligente
    

----------

### 1. **Autenticação**

> Gera token JWT para autenticar nas chamadas da API do pfSense

```
POST /api/v1/access_token

```

**Parâmetros:**

Nome

Tipo

Descrição

client_id

string

ID do cliente registrado

client_secret

string

Segredo associado ao cliente

username

string

Nome de usuário

password

string

Senha

----------

### 2. **Gerenciamento de Regras de Firewall**

> Permite controlar o acesso dos dispositivos IoT à rede

-   **Listar Regras**
    

```
GET /api/v1/firewall/rule

```

-   **Criar Regra (ex: liberar IP IoT)**
    

```
POST /api/v1/firewall/rule

```

**Campos obrigatórios (exemplo IoT):**

```json
{
  "interface": "IoT_VLAN",
  "protocol": "any",
  "src": "192.168.10.50",
  "dst": "any",
  "dstport": "any",
  "descr": "IoT-EDU: Sensor Lab 5A",
  "top": true
}

```

-   **Remover Regra**
    

```
DELETE /api/v1/firewall/rule/{id}

```

----------

### 3. **Aliases (Grupos de IPs IoT)**

> Organiza dispositivos por grupos para facilitar regras e relatórios

-   **Listar Aliases**
    

```
GET /api/v1/firewall/alias

```

-   **Criar Alias**
    

```
POST /api/v1/firewall/alias

```

**Campos:**

```json
{
  "name": "Dispositivos_IoT",
  "type": "host",
  "address": "192.168.10.50 192.168.10.51"
}

```

-   **Atualizar Alias**
    

```
PUT /api/v1/firewall/alias/{name}

```

----------

### 4. **Interfaces de Rede**

> Consulta e monitoramento das interfaces onde os dispositivos estão conectados

-   **Listar Interfaces**
    

```
GET /api/v1/interface

```

-   **Status das Interfaces**
    

```
GET /api/v1/interface/status

```

----------

### 5. **Leases DHCP (IP Dinâmico dos Dispositivos IoT)**

> Permite identificar ou fixar IPs de dispositivos registrados

-   **Consultar Leases Ativos**
    

```
GET /api/v1/dhcpd/lease

```

-   **Reservar IP Estático para MAC**
    

```
POST /api/v1/dhcpd/lease

```

**Campos comuns:**

```json
{
  "mac": "00:1A:2B:3C:4D:5E",
  "ip": "192.168.10.50",
  "hostname": "sensor-lab5a"
}

```

----------

### 6. **Logs de Firewall**

> Análise de tráfego e detecção de anomalias por IA

```
GET /api/v1/system/log/firewall

```

> Retorna os logs brutos do tráfego processado pelo firewall.

----------

### 7. **Informações do Sistema**

> Detalhes úteis para diagnóstico da infraestrutura

```
GET /api/v1/system/info

```

Retorna:

```json
{
  "version": "2.7.0",
  "hostname": "fw-campus",
  "uptime": "3 days, 14:27",
  ...
}

```

----------


# Instalação
# Execução
