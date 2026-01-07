## Fluxo de Cadastro de Dispositivo

# Casos de uso Cadastro 
![enter image description here](https://raw.githubusercontent.com/GT-IoTEdu/API_IoT_EDU/refs/heads/main/diagramas/images/casodeuso.png?token=GHSAT0AAAAAADH7PNWQVWKHSUZ2QSL4MZFS2FIUVSA)

**Pré-requisito:** Usuário autenticado.

1.  **Requisição:** Usuário envia `POST /devices` com `description` e `mac_address`.

2.  **Validação:**
    *   A API valida o formato do `mac_address`.
    *   **Se inválido:** Retorna erro `400 Bad Request` - "Formato de MAC Address inválido.".
    *   **Se válido:** Verifica se o MAC já existe no banco.
        *   **Se existir:** Retorna erro.

3.  **Processamento API:**
    *   Inicia uma transação de banco de dados.
    *   Aloca o primeiro IP disponível do `IPAddressPool`.
        *   **Se não houver IP:** Retorna erro `503 Service Unavailable`.
    *   Registra uma reserva no Servidor DHCP com os dados do dispositivo.
        *   **Se falhar:** Faz rollback da transação e retorna erro `500`.
    *   **Libera o IP no firewall** adicionando-o ao alias `authorized_devices`.
    *   Salva o novo dispositivo no banco com `status: 'active'`.
    *   Conclui (commita) a transação.

4.  **Resposta:** Retorna `201 Created` com os dados do dispositivo, incluindo o IP atribuído.

***

## Diagrama de Sequência auto cadastro

![enter image description here](https://raw.githubusercontent.com/GT-IoTEdu/API_IoT_EDU/refs/heads/main/diagramas/images/sequancia_auto_cadastro.png?token=GHSAT0AAAAAADH7PNWRKWKAO4ZMLIZI3YLY2FIUWAA)

# Fluxo de Cadastro com Aprovação Moderada

**Pré-requisito:** Usuário e gestor autenticados.

## 1. Solicitação do Usuário
**POST** `/devices`
```json
{
  "description": "string",
  "mac_address": "string"
}
```

## 2. Registro Inicial
- API salva dispositivo com:
  - `status: 'pending'`
  - `ip_address: null`
- Retorna **202 Accepted** (solicitação recebida aguardando processamento)

## 3. Processo de Aprovação
### Gestor solicita pendências:
**GET** `/admin/devices?status=pending`

### Gestor aprova dispositivo:
**POST** `/admin/devices/{deviceId}/approve`

## 4. Lógica de Aprovação
### Alocação de IP:
- Busca IP livre no pool (ou recebe IP do gestor)
  *   **Libera o IP no firewall** adicionando-o ao alias `authorized_devices`.
    *   atualiza o dispositivo no banco com `status: 'active'`.
### Reserva no DHCP:
```json
{
  "parent_id": "lan",
  "mac": "d4:5b:51:a1:0e:70",
  "ipaddr": "10.30.30.99",
  "hostname": "motog55",
  "descr": "motog55"
}
```

### Atualização no Banco:
- `status: 'active'`
- `cadastrado_por: (ID do gestor)`
- `ultimo_acesso: (timestamp)`
- `ip_address: (IP alocado)`

## 5. Notificação
- API envia notificação ao usuário:
- "Seu dispositivo '[Descrição]' foi aprovado e está ativo na rede."

***

## Diagrama de Sequência, cadastro com aprovação
![enter image description here](https://raw.githubusercontent.com/GT-IoTEdu/API_IoT_EDU/refs/heads/main/diagramas/images/sequancia_aprovacao_cadastro.png?token=GHSAT0AAAAAADH7PNWRJXBPLBUS46MEQKRE2FIUWTA)

**Principais diferenças do cenário anterior:**
- Fluxo assíncrono com duas fases distintas
- Status inicial `pending` em vez de processamento imediato
- Intervenção manual do gestor para aprovação
- Notificação ao usuário após aprovação
- Separação clara de papéis: usuário solicita, gestor aprova
