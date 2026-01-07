# API de Gerenciamento de Regras de Firewall (pfSense)

Este documento detalha como utilizar os endpoints do backend para gerenciar regras de firewall do pfSense via API REST.

---

## Endpoints Disponíveis

### 1. Listar todas as regras de firewall
- **GET** `/api/devices/firewall/rules`
- **Descrição:** Retorna todas as regras de firewall cadastradas no pfSense.
- **Exemplo de uso (Postman/cURL):**
  ```bash
  curl -X GET http://localhost:8000/api/devices/firewall/rules
  ```
- **Resposta:**
  ```json
  {
    "status": "ok",
    "result": { ...lista de regras... }
  }
  ```

---

### 2. Criar regra de firewall por MAC
- **POST** `/api/devices/firewall/mac`
- **Descrição:** Cria uma nova regra de firewall baseada em endereço MAC.
- **Body (JSON):**
  ```json
  {
    "type": "pass", // ou "block"
    "interface": ["lan"],
    "ipprotocol": "inet",
    "protocol": "any",
    "source": "any",
    "srcmac": "00:11:22:33:44:55",
    "descr": "Liberar Notebook João",
    "disabled": false,
    "log": true
  }
  ```
- **Exemplo de uso (Postman/cURL):**
  ```bash
  curl -X POST http://localhost:8000/api/devices/firewall/mac \
    -H "Content-Type: application/json" \
    -d '{
      "type": "pass",
      "interface": ["lan"],
      "ipprotocol": "inet",
      "protocol": "any",
      "source": "any",
      "srcmac": "00:11:22:33:44:55",
      "descr": "Liberar Notebook João",
      "disabled": false,
      "log": true
    }'
  ```
- **Resposta:**
  ```json
  {
    "status": "ok",
    "result": { ...resposta do pfSense... }
  }
  ```

---

### 3. Editar uma regra de firewall
- **PATCH** `/api/devices/firewall/rule`
- **Descrição:** Edita uma regra de firewall existente.
- **Body (JSON):**
  ```json
  {
    "id": 123,
    "descr": "Nova descrição",
    "disabled": true
  }
  ```
- **Exemplo de uso (Postman/cURL):**
  ```bash
  curl -X PATCH http://localhost:8000/api/devices/firewall/rule \
    -H "Content-Type: application/json" \
    -d '{
      "id": 123,
      "descr": "Nova descrição",
      "disabled": true
    }'
  ```
- **Resposta:**
  ```json
  {
    "status": "ok",
    "result": { ...resposta do pfSense... }
  }
  ```

---

### 4. Remover uma regra de firewall
- **DELETE** `/api/devices/firewall/rule?id=123`
- **Descrição:** Remove uma regra de firewall pelo ID.
- **Exemplo de uso (Postman/cURL):**
  ```bash
  curl -X DELETE "http://localhost:8000/api/devices/firewall/rule?id=123"
  ```
- **Resposta:**
  ```json
  {
    "status": "ok",
    "result": { ...resposta do pfSense... }
  }
  ```

---

## Observações
- Todos os endpoints do backend já autenticam com o pfSense usando a chave configurada.
- Os campos aceitos para criação/edição de regras seguem o padrão da API v2 do pfSense.
- Para testar, use Postman, Insomnia, cURL ou qualquer cliente HTTP.
- Consulte a documentação oficial do pfSense para detalhes de cada campo.

--- 