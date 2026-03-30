# Estrutura de Relacionamentos: pfsense_aliases e pfsense_alias_addresses

## Problema Identificado

A confusão entre os IDs das tabelas `pfsense_aliases` e `pfsense_alias_addresses` causava problemas em ambientes multi-rede onde cada instituição tem seu próprio pfSense.

## Estrutura Correta

### Tabela: `pfsense_aliases`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER (PK) | **ID primário do banco de dados** - ÚNICO em todo o banco |
| `pf_id` | INTEGER | **ID do alias no pfSense** - Pode ser o mesmo valor em diferentes pfSenses |
| `name` | VARCHAR(255) | Nome do alias (ex: "Autorizados", "Bloqueados") |
| `institution_id` | INTEGER (FK) | ID da instituição/campus |
| `alias_type` | VARCHAR(50) | Tipo do alias (host, network, port, etc.) |
| `descr` | TEXT | Descrição do alias |

**IMPORTANTE:**
- `id` é o identificador único no banco de dados
- `pf_id` é apenas uma referência ao ID no pfSense (pode ser NULL ou 0)
- A combinação `(name, institution_id)` deve ser única (índice único composto)

### Tabela: `pfsense_alias_addresses`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER (PK) | ID primário do banco de dados |
| `alias_id` | INTEGER (FK) | **DEVE referenciar `pfsense_aliases.id`** (ID do banco, NÃO pf_id) |
| `address` | VARCHAR(255) | Endereço IP, rede ou porta |
| `detail` | TEXT | Detalhes do endereço |

**IMPORTANTE:**
- `alias_id` **SEMPRE** referencia `pfsense_aliases.id` (ID do banco)
- **NUNCA** usar `pf_id` para relacionar com `pfsense_alias_addresses`

## Exemplo Correto

```python
# 1. Buscar ou criar alias
alias = db.query(PfSenseAlias).filter(
    PfSenseAlias.name == "Autorizados",
    PfSenseAlias.institution_id == institution_id
).first()

if not alias:
    alias = PfSenseAlias(
        name="Autorizados",
        institution_id=institution_id,
        alias_type="host",
        pf_id=None  # Será preenchido depois ao sincronizar com pfSense
    )
    db.add(alias)
    db.flush()  # Importante: flush para obter o ID

# 2. Adicionar endereço ao alias
# ✅ CORRETO: usar alias.id (ID do banco)
new_address = PfSenseAliasAddress(
    alias_id=alias.id,  # ✅ ID do banco
    address="192.168.1.100",
    detail="Dispositivo autorizado"
)
db.add(new_address)

# ❌ ERRADO: usar alias.pf_id
# new_address = PfSenseAliasAddress(
#     alias_id=alias.pf_id,  # ❌ NUNCA fazer isso!
#     address="192.168.1.100"
# )
```

## Regras de Ouro

1. **Sempre usar `alias.id`** (ID do banco) ao criar `PfSenseAliasAddress`
2. **Nunca usar `alias.pf_id`** para relacionar com `pfsense_alias_addresses`
3. **Sempre filtrar por `name + institution_id`** ao buscar aliases
4. **Validar que o IP pertence à instituição** antes de adicionar ao alias
5. **Sempre usar `db.flush()`** após criar um alias antes de criar endereços

## Script de Diagnóstico e Correção

Execute o script para diagnosticar e corrigir problemas:

```bash
# Apenas diagnosticar
python backend/scripts/fix_alias_addresses_relationships.py

# Aplicar correções
python backend/scripts/fix_alias_addresses_relationships.py --fix --apply
```

O script identifica:
- Endereços órfãos (alias_id não existe)
- IPs em aliases de instituições erradas
- Aliases duplicados (mesmo name + institution_id)

## Ambiente Multi-Rede

Em ambientes com múltiplas instituições, cada uma tem:
- Seu próprio pfSense (URL e chave API diferentes)
- Seus próprios aliases "Autorizados" e "Bloqueados"
- Seu próprio range de IPs

**Exemplo:**
- Instituição 1 (Alegrete): 
  - Alias "Autorizados" (id=3, institution_id=1, pf_id=0)
  - Range: 192.168.59.3 - 192.168.59.99
  
- Instituição 3 (Uruguaiana):
  - Alias "Autorizados" (id=1, institution_id=3, pf_id=0)
  - Range: 192.168.56.3 - 192.168.56.99

Note que ambos têm `pf_id=0`, mas IDs diferentes no banco (`id=3` vs `id=1`).

