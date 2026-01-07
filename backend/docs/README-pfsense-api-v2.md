# Integração com API REST v2 do pfSense

Este documento detalha a integração completa com a API REST v2 do pfSense para gerenciamento automatizado de dispositivos IoT em ambientes acadêmicos.

## 📋 Pré-requisitos

### 1. pfSense Configurado
- Instância funcional do pfSense
- Acesso à interface web administrativa

### 2. Pacote API REST
Instalar o pacote `pfsense-pkg-API` da comunidade:
- **Interface Web:** `System > Package Manager > Available Packages` → procurar "API"
- **Linha de Comando:** Instalação manual via SSH

### 3. Configuração de Autenticação
Gerar chave de API na interface web:
- **Localização:** `System > API`
- **Anotar:** `API Key` e `API Secret`
- **Configurar:** No arquivo `backend/config.py`

### 4. Configuração do Sistema
```python
# backend/config.py
PFSENSE_API_URL = "https://192.168.0.155/api/v2/"
PFSENSE_API_KEY = "sua_api_key_aqui"
PFSENSE_API_SECRET = "seu_api_secret_aqui"
```

## 🔐 Autenticação

### Obter Token de Acesso
```bash
# Endpoint
GET /api/devices/auth/token

# Resposta
{
  "status": "ok",
  "token": "access_token_aqui"
}
```

### Uso do Token
O token deve ser incluído no cabeçalho `Authorization`:
```
Authorization: Bearer <access_token>
```

## 📡 Endpoints Disponíveis

### 1. Mapeamento Estático de DHCP

#### Criar Mapeamento DHCP
```bash
POST /api/devices/dhcp/mapping
```

**Body:**
```json
{
  "interface": "opt1",
  "mac": "00:50:56:b2:7f:d9",
  "ipaddr": "10.1.1.206",
  "hostname": "test-api",
  "descr": "machine de test pour api rest",
  "arp_table_static_entry": false
}
```

**Resposta:**
```json
{
  "status": "ok",
  "result": {
    "status": "ok",
    "return": 0
  }
}
```

### 2. Gerenciamento de Aliases

#### Criar Novo Alias
```bash
POST /api/devices/aliases
```

**Body:**
```json
{
  "name": "Dispositivos_IoT",
  "type": "host",
  "address": "192.168.1.100",
  "descr": "Dispositivos IoT da rede"
}
```

### 3. Gerenciamento de Regras de Firewall

#### Criar Regra de Firewall
```bash
POST /api/devices/firewall/rules
```

**Body:**
```json
{
  "interface": "IoT_VLAN",
  "type": "pass",
  "protocol": "tcp",
  "src": "192.168.1.0/24",
  "dst": "any",
  "descr": "Regra IoT"
}
```

## 🆕 Novas Funções DHCP (Adicionadas)

### 1. Listar Servidores DHCP

#### Função: `listar_clientes_dhcp_pfsense()`
Lista todos os servidores DHCP e suas informações.

**Endpoint:** `GET /services/dhcp_servers`

**Uso:**
```python
from backend.devices import pfsense_client

# Listar todos os servidores DHCP
result = pfsense_client.listar_clientes_dhcp_pfsense()
print(result)
```

**Resposta Esperada:**
```json
{
  "status": "ok",
  "data": [
    {
    "interface": "lan",
      "enable": true,
      "range": {
        "from": "192.168.1.100",
        "to": "192.168.1.200"
      },
      "clients": [
        {
          "mac": "00:11:22:33:44:55",
          "ip": "192.168.1.101",
          "hostname": "device1",
          "lease_time": "86400"
        }
      ]
    }
  ]
}
```

### 2. Obter Clientes DHCP por Interface

#### Função: `obter_clientes_dhcp_interface_pfsense(interface)`
Obtém os clientes DHCP ativos de uma interface específica.

**Endpoint:** `GET /services/dhcpd/{interface}/leases`

**Parâmetros:**
- `interface` (str): Nome da interface (ex: "lan", "wan", "opt1", "IoT_VLAN")

**Uso:**
```python
# Obter clientes DHCP da interface IoT_VLAN
result = pfsense_client.obter_clientes_dhcp_interface_pfsense("IoT_VLAN")
print(result)

# Obter clientes DHCP da interface LAN
result = pfsense_client.obter_clientes_dhcp_interface_pfsense("lan")
print(result)
```

**Resposta Esperada:**
```json
{
  "status": "ok",
  "data": [
    {
      "mac": "00:11:22:33:44:55",
      "ip": "192.168.1.101",
      "hostname": "device1",
      "lease_time": "86400",
      "start_time": "1640995200",
      "end_time": "1641081600"
    }
  ]
}
```

### 3. Obter Mapeamentos Estáticos por Interface

#### Função: `obter_mapeamentos_dhcp_interface_pfsense(interface)`
Obtém os mapeamentos estáticos de DHCP de uma interface específica.

**Endpoint:** `GET /services/dhcpd/{interface}/static_mapping`

**Parâmetros:**
- `interface` (str): Nome da interface (ex: "lan", "wan", "opt1", "IoT_VLAN")

**Uso:**
```python
# Obter mapeamentos estáticos da interface IoT_VLAN
result = pfsense_client.obter_mapeamentos_dhcp_interface_pfsense("IoT_VLAN")
print(result)
```

**Resposta Esperada:**
```json
{
  "status": "ok",
  "data": [
    {
      "mac": "00:11:22:33:44:55",
      "ipaddr": "192.168.1.100",
      "hostname": "static-device1",
      "descr": "Dispositivo IoT estático",
      "arp_table_static_entry": true
    }
  ]
}
```

### 4. Obter Mapeamento DHCP Específico

#### Função: `obter_mapeamento_dhcp_especifico_pfsense(parent_id, mapping_id)`
Obtém um mapeamento DHCP específico usando o endpoint correto.

**Endpoint:** `POST /services/dhcp_server/static_mapping`

**Parâmetros:**
- `parent_id` (str): ID da interface pai (ex: "lan", "opt1")
- `mapping_id` (int): ID do mapeamento específico

**Body:**
```json
{
  "parent_id": "lan",
  "id": 0
}
```

**Uso:**
```python
# Obter mapeamento específico (ID 0 da interface LAN)
result = pfsense_client.obter_mapeamento_dhcp_especifico_pfsense("lan", 0)
print(result)

# Obter mapeamento específico (ID 1 da interface opt1)
result = pfsense_client.obter_mapeamento_dhcp_especifico_pfsense("opt1", 1)
print(result)
```

**Resposta Esperada:**
```json
{
  "status": "ok",
  "data": {
    "mac": "00:11:22:33:44:55",
    "ipaddr": "192.168.1.100",
    "hostname": "static-device1",
    "descr": "Dispositivo IoT estático",
    "arp_table_static_entry": true
  }
}
```

### 5. Listar Mapeamentos DHCP Específicos

#### Função: `listar_mapeamentos_dhcp_especificos_pfsense(parent_id)`
Lista todos os mapeamentos DHCP de uma interface específica usando o endpoint correto.

**Endpoint:** `POST /services/dhcp_server/static_mapping`

**Parâmetros:**
- `parent_id` (str): ID da interface pai (ex: "lan", "opt1")

**Body:**
```json
{
  "parent_id": "lan"
}
```

**Uso:**
```python
# Listar todos os mapeamentos da interface LAN
result = pfsense_client.listar_mapeamentos_dhcp_especificos_pfsense("lan")
print(result)

# Listar todos os mapeamentos da interface opt1
result = pfsense_client.listar_mapeamentos_dhcp_especificos_pfsense("opt1")
print(result)
```

**Resposta Esperada:**
```json
{
  "status": "ok",
  "data": [
    {
      "mac": "00:11:22:33:44:55",
      "ipaddr": "192.168.1.100",
      "hostname": "static-device1",
      "descr": "Dispositivo IoT estático",
      "arp_table_static_entry": true
    },
    {
      "mac": "00:11:22:33:44:56",
      "ipaddr": "192.168.1.101",
      "hostname": "static-device2",
      "descr": "Dispositivo IoT estático 2",
      "arp_table_static_entry": false
    }
  ]
}
```

## 🧪 Testando as Funções DHCP

Execute o script de teste para verificar se as funções estão funcionando:

```bash
cd backend
python test_dhcp_functions.py
```

## 📊 Exemplos de Uso Completo

### Exemplo 1: Monitoramento de Dispositivos IoT
```python
from backend.devices import pfsense_client

# Listar todos os servidores DHCP
servidores = pfsense_client.listar_clientes_dhcp_pfsense()

# Obter clientes ativos da VLAN IoT
clientes_iot = pfsense_client.obter_clientes_dhcp_interface_pfsense("IoT_VLAN")

# Obter mapeamentos estáticos
mapeamentos = pfsense_client.obter_mapeamentos_dhcp_interface_pfsense("IoT_VLAN")

print(f"Total de servidores DHCP: {len(servidores.get('data', []))}")
print(f"Clientes ativos na VLAN IoT: {len(clientes_iot.get('data', []))}")
print(f"Mapeamentos estáticos: {len(mapeamentos.get('data', []))}")
```

### Exemplo 2: Verificação de Interfaces
```python
interfaces = ["lan", "wan", "IoT_VLAN", "opt1", "opt2"]

for interface in interfaces:
    try:
        clientes = pfsense_client.obter_clientes_dhcp_interface_pfsense(interface)
        print(f"Interface {interface}: {len(clientes.get('data', []))} clientes")
    except Exception as e:
        print(f"Interface {interface}: Não disponível")
```

## 🔧 Tratamento de Erros

Todas as funções DHCP incluem tratamento de erros robusto:

```python
try:
    result = pfsense_client.listar_clientes_dhcp_pfsense()
    print("Sucesso:", result)
except Exception as e:
    print(f"Erro: {e}")
    # O erro inclui detalhes da resposta do pfSense
```

## 📋 Interfaces Comuns

- **lan**: Interface LAN principal
- **wan**: Interface WAN
- **opt1, opt2, opt3**: Interfaces ópticas
- **IoT_VLAN**: VLAN específica para dispositivos IoT
- **guest**: VLAN para convidados
- **management**: VLAN de gerenciamento

## 🚀 Próximos Passos

1. **Teste as funções:** Execute `python test_dhcp_functions.py`
2. **Integre com sua aplicação:** Use as funções no seu código
3. **Monitore dispositivos:** Implemente monitoramento automático
4. **Automatize configurações:** Crie scripts de automação 