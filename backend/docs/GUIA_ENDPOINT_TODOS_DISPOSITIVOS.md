# 📋 Guia do Endpoint: Listagem de Todos os Dispositivos

## 🎯 Visão Geral

Este endpoint permite que **gestores (MANAGER)** listem todos os dispositivos cadastrados no sistema, fornecendo uma visão completa com estatísticas detalhadas.

## 🔗 Endpoint

```
GET /api/devices/devices?current_user_id={manager_id}
```

## 🔐 Permissões

- **Gestores (MANAGER)**: ✅ Acesso permitido
- **Usuários comuns (USER)**: ❌ Acesso negado (403 Forbidden)

## 📝 Parâmetros

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `current_user_id` | `int` | ✅ | ID do usuário que está fazendo a consulta |

## 📊 Resposta

### Estrutura da Resposta

```json
{
  "devices": [
    {
      "id": 1,
      "server_id": "lan",
      "pf_id": 0,
      "mac": "bc:24:11:68:fb:77",
      "ipaddr": "10.30.30.3",
      "cid": "openvas",
      "hostname": "openvas",
      "descr": "openvas",
      "created_at": "2025-09-01T14:36:49",
      "updated_at": "2025-09-01T14:36:49"
    }
  ],
  "total_devices": 24,
  "online_devices": 18,
  "offline_devices": 6,
  "assigned_devices": 15,
  "unassigned_devices": 9
}
```

### Campos da Resposta

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `devices` | `array` | Lista de todos os dispositivos cadastrados |
| `total_devices` | `int` | Total de dispositivos no sistema |
| `online_devices` | `int` | Dispositivos considerados online |
| `offline_devices` | `int` | Dispositivos considerados offline |
| `assigned_devices` | `int` | Dispositivos atribuídos a usuários |
| `unassigned_devices` | `int` | Dispositivos não atribuídos |

### Estrutura do Dispositivo

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `int` | ID único do dispositivo |
| `server_id` | `string` | ID do servidor DHCP |
| `pf_id` | `int` | ID do dispositivo no pfSense |
| `mac` | `string` | Endereço MAC |
| `ipaddr` | `string` | Endereço IP |
| `cid` | `string` | ID do cliente |
| `hostname` | `string` | Nome do host |
| `descr` | `string` | Descrição do dispositivo |
| `created_at` | `datetime` | Data de criação |
| `updated_at` | `datetime` | Data da última atualização |

## 🧪 Exemplos de Uso

### Exemplo 1: Gestor acessando todos os dispositivos

```bash
curl -X GET "http://127.0.0.1:8000/api/devices/devices?current_user_id=2"
```

**Resposta de Sucesso (200):**
```json
{
  "devices": [
    {
      "id": 1,
      "server_id": "lan",
      "pf_id": 0,
      "mac": "bc:24:11:68:fb:77",
      "ipaddr": "10.30.30.3",
      "cid": "openvas",
      "hostname": "openvas",
      "descr": "openvas",
      "created_at": "2025-09-01T14:36:49",
      "updated_at": "2025-09-01T14:36:49"
    },
    {
      "id": 2,
      "server_id": "lan",
      "pf_id": 1,
      "mac": "bc:24:11:2c:0f:31",
      "ipaddr": "10.30.30.10",
      "cid": "lubuntu-live",
      "hostname": "",
      "descr": "lubuntu-live-proxmox",
      "created_at": "2025-09-01T14:36:49",
      "updated_at": "2025-09-01T14:36:49"
    }
  ],
  "total_devices": 24,
  "online_devices": 18,
  "offline_devices": 6,
  "assigned_devices": 15,
  "unassigned_devices": 9
}
```

### Exemplo 2: Usuário comum tentando acessar (negado)

```bash
curl -X GET "http://127.0.0.1:8000/api/devices/devices?current_user_id=1"
```

**Resposta de Erro (403):**
```json
{
  "detail": "Apenas gestores podem visualizar todos os dispositivos do sistema"
}
```

## 🔧 Testes

### Executar Teste Automatizado

```bash
cd testes
python test_all_devices_endpoint.py
```

### Teste Manual no Postman

1. **Nova Requisição GET**
2. **URL:** `{{api_base}}/devices`
3. **Query Params:**
   - `current_user_id`: `2` (ID do gestor)
4. **Headers:** (se necessário)
   - `Content-Type`: `application/json`

### Teste de Permissões

1. **Teste com Gestor (ID: 2)**
   - Deve retornar 200 OK com lista completa

2. **Teste com Usuário Comum (ID: 1)**
   - Deve retornar 403 Forbidden

## 📈 Estatísticas Fornecidas

O endpoint calcula automaticamente:

- **Total de Dispositivos**: Todos os dispositivos cadastrados
- **Dispositivos Online**: Simulação baseada em IP válido
- **Dispositivos Offline**: Dispositivos sem IP ou inacessíveis
- **Dispositivos Atribuídos**: Dispositivos com atribuições ativas
- **Dispositivos Não Atribuídos**: Dispositivos sem usuário responsável

## 🔄 Comparação com Outros Endpoints

| Endpoint | Descrição | Acesso |
|----------|-----------|--------|
| `GET /devices` | Todos os dispositivos | Apenas gestores |
| `GET /users/{id}/devices` | Dispositivos de um usuário | Gestores + próprio usuário |

## ⚠️ Observações Importantes

1. **Permissões**: Apenas gestores podem acessar este endpoint
2. **Performance**: Para sistemas com muitos dispositivos, considere implementar paginação
3. **Status Online**: Atualmente simulado - pode ser melhorado com ping real
4. **Dados Sensíveis**: Todos os dados de dispositivos são retornados

## 🚀 Próximos Passos

- [ ] Implementar paginação para grandes volumes
- [ ] Adicionar filtros por status, tipo, etc.
- [ ] Implementar verificação real de status online
- [ ] Adicionar cache para melhorar performance
