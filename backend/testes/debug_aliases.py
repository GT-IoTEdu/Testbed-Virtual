#!/usr/bin/env python3
"""
Script para debugar o problema com aliases.
"""

from services_firewalls.pfsense_client import listar_aliases_pfsense
from services_firewalls.alias_service import AliasService

def debug_aliases():
    """Debuga o problema com aliases."""
    print("🔍 DEBUGANDO ALIASES")
    print("="*40)
    
    # 1. Verificar resposta do pfSense
    print("\n1. RESPOSTA DO PFSENSE")
    print("-" * 30)
    
    try:
        pfsense_aliases = listar_aliases_pfsense()
        print(f"Tipo da resposta: {type(pfsense_aliases)}")
        print(f"Chaves da resposta: {list(pfsense_aliases.keys())}")
        
        if 'data' in pfsense_aliases:
            print(f"Tipo dos dados: {type(pfsense_aliases['data'])}")
            print(f"Número de aliases: {len(pfsense_aliases['data'])}")
            
            # Mostrar primeiro alias
            if pfsense_aliases['data']:
                first_alias = pfsense_aliases['data'][0]
                print(f"Primeiro alias:")
                print(f"  - ID: {first_alias.get('id')}")
                print(f"  - Nome: {first_alias.get('name')}")
                print(f"  - Tipo: {first_alias.get('type')}")
                print(f"  - Endereços: {first_alias.get('address', [])}")
        else:
            print("❌ Chave 'data' não encontrada")
            
    except Exception as e:
        print(f"❌ Erro ao buscar aliases do pfSense: {e}")
        return
    
    # 2. Testar serviço
    print("\n2. TESTANDO SERVIÇO")
    print("-" * 30)
    
    try:
        with AliasService() as alias_service:
            result = alias_service.save_aliases_data(pfsense_aliases)
            print("✅ Serviço executado com sucesso!")
            print(f"  - Aliases salvos: {result['aliases_saved']}")
            print(f"  - Aliases atualizados: {result['aliases_updated']}")
            print(f"  - Endereços salvos: {result['addresses_saved']}")
            print(f"  - Endereços atualizados: {result['addresses_updated']}")
            
    except Exception as e:
        print(f"❌ Erro no serviço: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_aliases()
