# Sistema Multi-Institucional

## Visão Geral

O sistema agora suporta múltiplas instituições (campi), onde cada instituição possui suas próprias configurações de rede (pfSense e Zeek). As configurações são armazenadas no banco de dados na tabela `institutions` e não mais no arquivo `.env`.

## Estrutura

### Tabela `institutions`

Cada instituição possui os seguintes campos para configurações:
- `pfsense_base_url`: URL base da API do pfSense
- `pfsense_key`: Chave de acesso à API do pfSense
- `zeek_base_url`: URL base da API do Zeek
- `zeek_key`: Chave de acesso à API do Zeek
- `ip_range_start`: IP inicial do range da instituição
- `ip_range_end`: IP final do range da instituição

### Relacionamento com Usuários

- Cada usuário pode estar associado a uma instituição através do campo `institution_id` na tabela `users`
- Usuários `ADMIN` (administradores de campus) estão associados a uma instituição específica
- Usuários `SUPERUSER` não possuem instituição específica (podem gerenciar todas)

## Serviços Criados

### InstitutionConfigService

Serviço para buscar configurações de instituições do banco de dados:

```python
from services_firewalls.institution_config_service import InstitutionConfigService

# Buscar configurações de uma instituição
config = InstitutionConfigService.get_institution_config(institution_id=1)

# Buscar configurações da instituição de um usuário
config = InstitutionConfigService.get_user_institution_config(user_id=1)

# Listar todas as instituições
institutions = InstitutionConfigService.get_all_institutions()
```

## Modificações Realizadas

### 1. pfsense_client.py

- Função `_get_pfsense_config()` agora aceita `user_id` e `institution_id`
- Busca configurações do banco de dados automaticamente se esses parâmetros forem fornecidos
- Fallback para configurações do `.env` se não encontrar no banco

### 2. zeek_service.py

- Construtor `ZeekService.__init__()` agora aceita `user_id` e `institution_id`
- Busca configurações do banco de dados automaticamente
- Fallback para configurações do `.env` se não encontrar no banco

### 3. alias_service.py

- Construtor `AliasService.__init__()` agora aceita `institution_id` e `user_id`
- Métodos internos buscam configurações da instituição automaticamente
- Passa configurações para funções do `pfsense_client`

## Como Usar

### Em Endpoints

```python
# Exemplo de endpoint que usa configurações da instituição do usuário
@router.get("/aliases")
def list_aliases(current_user_id: int):
    # O serviço busca automaticamente as configurações da instituição do usuário
    with AliasService(user_id=current_user_id) as alias_service:
        aliases = alias_service.get_all_aliases()
        return aliases
```

### Para Superusuários

Superusuários podem precisar especificar uma instituição explicitamente:

```python
@router.get("/institutions/{institution_id}/aliases")
def list_institution_aliases(institution_id: int):
    with AliasService(institution_id=institution_id) as alias_service:
        aliases = alias_service.get_all_aliases()
        return aliases
```

### Para Zeek

```python
# Criar serviço Zeek com configurações da instituição do usuário
zeek_service = ZeekService(user_id=current_user_id)

# Ou especificar instituição diretamente
zeek_service = ZeekService(institution_id=institution_id)
```

## Migração

### De .env para Banco de Dados

1. **Criar/Atualizar Instituições no Banco**:
   - Use o endpoint `/api/admin/institutions` para criar ou atualizar instituições
   - Configure os campos `pfsense_base_url`, `pfsense_key`, `zeek_base_url`, `zeek_key`

2. **Associar Usuários às Instituições**:
   - Administradores de campus devem ter `institution_id` definido
   - Use o endpoint `/api/admin/users/{user_id}` para atualizar

3. **Remover Configurações do .env** (Opcional):
   - As configurações no `.env` ainda funcionam como fallback
   - Você pode manter como backup ou remover após migrar todas as instituições

## Prioridade de Configurações

O sistema busca configurações na seguinte ordem:

1. **Parâmetros fornecidos diretamente** (maior prioridade)
2. **Configurações da instituição do usuário** (se `user_id` fornecido)
3. **Configurações da instituição** (se `institution_id` fornecido)
4. **Configurações globais do `.env`** (fallback)

## Próximos Passos

1. Atualizar todos os endpoints para identificar a instituição do usuário
2. Atualizar serviços que ainda usam configurações do `.env` diretamente
3. Adicionar validação para garantir que usuários tenham instituição associada quando necessário
4. Criar interface administrativa para gerenciar configurações de instituições

## Exemplo Completo

```python
from services_firewalls.alias_service import AliasService
from services_scanners.zeek_service import ZeekService

# Endpoint que lista aliases da instituição do usuário
@router.get("/my-aliases")
def get_my_aliases(current_user_id: int):
    with AliasService(user_id=current_user_id) as alias_service:
        aliases = alias_service.get_all_aliases()
        return {"aliases": aliases}

# Endpoint que busca logs do Zeek da instituição do usuário
@router.get("/zeek-logs")
def get_zeek_logs(current_user_id: int):
    zeek_service = ZeekService(user_id=current_user_id)
    logs = zeek_service.get_logs(ZeekLogRequest(...))
    return logs
```

## Notas Importantes

- **Compatibilidade**: O sistema mantém compatibilidade com configurações do `.env` como fallback
- **Performance**: Configurações são buscadas do banco a cada chamada (considere cache no futuro)
- **Segurança**: Certifique-se de que apenas usuários autorizados possam acessar configurações de instituições

