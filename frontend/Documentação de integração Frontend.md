### Documentação de integração Frontend ↔ Backend (funcionalidades utilizadas)

- Base do backend: `http://127.0.0.1:8000/api/devices` (ou `NEXT_PUBLIC_API_BASE`)
- Frontend usa `NEXT_PUBLIC_API_BASE` para montar URLs
- Tratamento de indisponibilidade do pfSense: respostas 504 são exibidas com mensagem amigável “pfSense indisponível. Tente novamente mais tarde.”

## Autenticação (Google)
- Front lê `auth:user` no `localStorage` para nome, email, picture, permission e user_id.
- Logout: `POST http://localhost:8000/api/auth/logout` (fora do escopo deste doc, mas usado no header).

## Dispositivos (DHCP)
- Usuário (aba “Meus Dispositivos”)
  - Listar dispositivos do usuário:
    - GET `/users/{user_id}/devices?current_user_id={user_id}`
    - Resposta: `user`, `devices[]`, `total_devices`, `active_assignments`
    - Front exibe colunas: Nome, IP, MAC, Status (LIBERADO/BLOQUEADO), Última Atividade, Ações
    - Status é calculado no backend (ver “Status de acesso”)
  - Buscar por termo: GET `/dhcp/devices/search?query={ip|mac|hostname|descr}`
  - Adicionar dispositivo:
    - POST `/dhcp/save`
    - Body: `{ mac, ipaddr, cid, descr }`
    - 504 → mostra mensagem amigável
    - Em sucesso: sincroniza, tenta atribuir ao usuário, recarrega lista
  - Remover dispositivo:
    - Primeiro remove atribuição: DELETE `/assignments/{user_id}/{device_id}?current_user_id={user_id}`
    - Depois remove no pfSense: DELETE `/dhcp/static_mapping?parent_id=lan&mapping_id={pf_id}&apply=true`
    - Em seguida: POST `/dhcp/sync` para sincronizar `pf_id`

- Gestor (aba “Lista de Dispositivos”)
  - GET `/dhcp/devices?page={n}&per_page={m}`
  - Resposta: `devices[]` (com `assigned_users[]`), `total`, paginação
  - Front exibe: Nome, IP, MAC, Usuário, Status (LIBERADO/BLOQUEADO), Descrição, Última Atividade

- Sincronizar IDs DHCP (quando `pf_id` muda):
  - POST `/dhcp/sync`

## Aliases (pfSense)
- Sincronizar aliases do pfSense com banco local:
  - POST `/aliases-db/save`
  - Backend resolve duplicidades por `name` e muda `pf_id` quando o pfSense desloca IDs (inclui `pf_id=0`)

- Listar aliases do banco local (com paginação):
  - GET `/aliases-db?page={n}&per_page={m}`
  - Front exibe: Nome, Tipo, Ação (PASS/BLOCK quando mapeado em regras), Descrição, Itens (contador) e “Ver detalhes”
  - “Ver detalhes”: GET `/aliases-db/{alias_name}` (mostra endereços e detalhes)

- Criar novo alias:
  - POST `/aliases-db/create`
  - Body:
    - `{ name, alias_type: "host"|"network", descr, addresses: [{ address, detail }] }`
  - 504 → mensagem amigável
  - Depois: POST `/aliases-db/save` e recarregar

- Adicionar IPs a um alias:
  - POST `/aliases-db/{alias_name}/add-addresses`
  - Body: `{ addresses: [{ address, detail }] }`
  - 504 → mensagem amigável
  - Depois: POST `/aliases-db/save` e recarregar

## Regras de Firewall (pfSense)
- Ler regras diretamente do pfSense:
  - GET `/firewall/rules`
  - Usado internamente para salvar no banco

- Salvar/atualizar regras no banco:
  - POST `/firewall/rules/save`
  - Salva em `pfsense_firewall_rules` (mantém atualização quando IDs mudam no pfSense)

- Listar regras do banco:
  - GET `/firewall/rules-db`
  - Front (aba “Regras de Firewall”) exibe: Ação (type PASS/BLOCK), Interface, IP Proto, Protocolo, Origem, Destino, Porta Destino, Descrição
  - Aliases negados (“!alias”) são considerados

## Status de acesso (LIBERADO/BLOQUEADO)
- Backend enriquece dispositivos com `status_acesso` (em:
  - GET `/users/{user_id}/devices`
  - GET `/dhcp/devices`
)
- Regra de cálculo (no backend):
  - Procura aliases que contenham o IP do dispositivo (`pfsense_alias_addresses` → `pfsense_aliases`)
  - Cruzamento com `pfsense_firewall_rules`:
    - Verifica `source` / `destination` contendo o alias como token:
      - Aceita formatos CSV e variações: `=alias`, `=!alias`, `LIKE 'alias,%'`, `LIKE '%,alias'`, `LIKE '%,alias,%'` (idem para `!alias`)
    - Se encontrar qualquer `block` → BLOQUEADO (prioritário)
    - Senão, se encontrar `pass` → LIBERADO
    - Caso contrário → indefinido (frontend exibe “-”)

## Padrões de erro e UX
- pfSense indisponível (timeouts/conexão): retorna 504 com detalhe “pfSense indisponível: …”; frontend mostra mensagem amigável e não quebra fluxo
- Conflitos de alias/id (duplicatas): backend resolve por nome e ajusta `pf_id` quando IDs mudam no pfSense (inclui `pf_id=0`)

## Variáveis e configuração no Frontend
- `NEXT_PUBLIC_API_BASE` (ex.: `http://127.0.0.1:8000/api/devices`)
- Front organiza as abas:
  - Usuário: “Meus Dispositivos” (Status LIBERADO/BLOQUEADO)
  - Gestor: “Lista de Dispositivos”, “Mapeamento Aliases”, “Regras”

## Fluxos principais do Front
- Adição de dispositivo:
  1) POST `/dhcp/save` → 2) (se sucesso) POST `/dhcp/sync` → 3) atribuição (POST `/assignments`) → 4) recarregar lista

- Remoção de dispositivo:
  1) DELETE `/assignments/{user_id}/{device_id}` → 2) DELETE `/dhcp/static_mapping?parent_id=lan&mapping_id={pf_id}&apply=true` → 3) POST `/dhcp/sync` → 4) recarregar lista

- Manutenção de aliases:
  - Criar: POST `/aliases-db/create` → POST `/aliases-db/save` → recarregar
  - Adicionar IPs: POST `/aliases-db/{alias}/add-addresses` → POST `/aliases-db/save` → recarregar
  - Ver detalhes: GET `/aliases-db/{alias}`

- Sincronizar regras:
  - POST `/firewall/rules/save` → GET `/firewall/rules-db` para exibir


