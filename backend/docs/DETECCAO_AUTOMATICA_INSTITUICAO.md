# Detecção Automática de Instituição por IP de Origem

## Visão Geral

Este documento descreve a implementação da detecção automática de instituição/campus durante o cadastro de dispositivos. O sistema identifica automaticamente em qual rede o usuário está conectado e vincula o dispositivo à instituição correspondente.

## Funcionamento

### Fluxo de Detecção

1. **Captura do IP de Origem**: Quando o usuário cadastra um dispositivo, o sistema captura o IP de origem da requisição HTTP.

2. **Identificação da Instituição**: O IP é comparado com os ranges de IPs configurados para cada instituição na tabela `institutions`.

3. **Vinculação do Dispositivo**: O dispositivo é automaticamente vinculado à instituição identificada através do campo `institution_id` na tabela `dhcp_static_mappings`.

4. **Cadastro no pfSense Correto**: O dispositivo é cadastrado no pfSense da instituição identificada, garantindo que use a rede correta.

### Estratégia de Fallback

Se a detecção automática falhar, o sistema tenta:

1. Usar a instituição associada ao usuário (`user.institution_id`)
2. Se ainda falhar, retorna erro informativo pedindo conexão à rede do campus

## Arquivos Modificados

### 1. Modelo de Dados (`backend/db/models.py`)

- Adicionado campo `institution_id` na classe `DhcpStaticMapping`
- Criado relacionamento com a tabela `institutions`

```python
institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=True, index=True)
institution = relationship("Institution", foreign_keys=[institution_id])
```

### 2. Utilitário de Requisição (`backend/services_firewalls/request_utils.py`)

- Nova função `get_client_ip()` que captura o IP real do cliente
- Suporta headers de proxy (`X-Forwarded-For`, `X-Real-IP`)
- Fallback para `request.client.host`

### 3. Endpoint de Cadastro (`backend/services_firewalls/router.py`)

- Modificado endpoint `/dhcp/save` para:
  - Capturar IP de origem via `get_client_ip()`
  - Identificar instituição via `InstitutionConfigService.get_institution_by_ip()`
  - Passar `institution_id` para funções de cadastro
  - Usar configurações do pfSense da instituição identificada

### 4. Serviço DHCP (`backend/services_firewalls/dhcp_service.py`)

- Método `save_dhcp_data()` agora aceita `institution_id`
- Método `_save_static_mapping()` salva `institution_id` no banco

### 5. Migração de Banco de Dados

- Script SQL criado em `backend/db/migrations/add_institution_id_to_dhcp_static_mappings.sql`
- Adiciona coluna `institution_id` na tabela `dhcp_static_mappings`
- Cria índice para melhorar performance

## Como Usar

### Para Usuários

1. Conecte-se à rede WiFi do campus (ex: "Unipampa Alegrete")
2. Acesse o sistema e faça login
3. Cadastre seu dispositivo normalmente
4. O sistema detectará automaticamente o campus e cadastrará na rede correta

### Para Administradores

#### Executar Migração

```sql
-- Executar o script de migração
SOURCE backend/db/migrations/add_institution_id_to_dhcp_static_mappings.sql;
```

#### Configurar Ranges de IPs

Certifique-se de que cada instituição tenha os ranges de IPs configurados corretamente:

```sql
UPDATE institutions 
SET ip_range_start = '192.168.10.1', 
    ip_range_end = '192.168.10.254'
WHERE nome = 'Unipampa Alegrete';
```

## Exemplo de Fluxo

```
1. Usuário conecta no WiFi "Unipampa Alegrete"
   → Recebe IP: 192.168.10.50

2. Usuário acessa sistema e cadastra MAC: aa:bb:cc:dd:ee:ff
   → Requisição HTTP vem de: 192.168.10.50

3. Backend captura IP: 192.168.10.50
   → Chama get_institution_by_ip("192.168.10.50")
   → Retorna: institution_id = 1 (Unipampa Alegrete)

4. Dispositivo cadastrado com:
   - MAC: aa:bb:cc:dd:ee:ff
   - institution_id: 1
   - IP atribuído do range: 192.168.10.1-254
   - pfSense usado: pfsense.alegrete.unipampa.edu.br
```

## Tratamento de Erros

### IP não identificado

Se o IP não pertencer a nenhuma instituição:

```
Erro 400: "Não foi possível identificar a rede/campus. 
Certifique-se de estar conectado à rede do campus ou entre em contato com o administrador."
```

### Múltiplas instituições com ranges sobrepostos

Atualmente, a primeira instituição encontrada é usada. Para evitar isso:

- Configure ranges de IPs não sobrepostos
- Use ranges mais específicos quando possível

## Melhorias Futuras

1. **IPAssignmentService por Instituição**: Atualizar o serviço para considerar `institution_id` ao atribuir IPs automaticamente, usando o range específico da instituição.

2. **Validação de IP no Range**: Validar que o IP atribuído está dentro do range da instituição identificada.

3. **Detecção por SSID**: Adicionar detecção alternativa via SSID da WiFi (requer permissões do navegador).

4. **Seleção Manual como Fallback**: Permitir que o usuário escolha manualmente a instituição se a detecção automática falhar.

## Troubleshooting

### Dispositivo não está sendo vinculado à instituição

1. Verifique se a migração foi executada:
   ```sql
   DESCRIBE dhcp_static_mappings;
   -- Deve mostrar coluna institution_id
   ```

2. Verifique se os ranges de IPs estão configurados:
   ```sql
   SELECT id, nome, ip_range_start, ip_range_end FROM institutions;
   ```

3. Verifique os logs do backend para ver qual IP foi capturado:
   ```
   🔍 Detectando instituição pelo IP de origem: X.X.X.X
   ```

### IP capturado está incorreto

- Se estiver atrás de proxy/load balancer, configure os headers corretos:
  - `X-Forwarded-For`: IP original do cliente
  - `X-Real-IP`: IP real do cliente

## Segurança

- O sistema valida que o usuário está na rede do campus antes de permitir cadastro
- Dispositivos só podem ser cadastrados na rede onde o usuário está fisicamente conectado
- Previne cadastros em redes incorretas

## Referências

- `InstitutionConfigService.get_institution_by_ip()`: Identifica instituição pelo IP
- `get_client_ip()`: Captura IP de origem da requisição
- Tabela `institutions`: Armazena configurações de cada campus
- Tabela `dhcp_static_mappings`: Armazena dispositivos com vínculo à instituição

