"""
Script para atualizar configurações do Zeek de uma instituição no banco de dados.

Uso:
    python backend/scripts/update_zeek_config.py <institution_id> <zeek_base_url> <zeek_key>

Exemplo:
    python backend/scripts/update_zeek_config.py 1 "http://192.168.59.2/zeek-api" "y1X6Qn8PpV9jR4kM0wBz7Tf2GhUs3Lc8NrDq5Ke1HxYi0AzF7Gv9MbX2VwJoQp"
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services_firewalls.institution_config_service import InstitutionConfigService

def main():
    if len(sys.argv) != 4:
        print("Uso: python update_zeek_config.py <institution_id> <zeek_base_url> <zeek_key>")
        print("\nExemplo:")
        print('  python update_zeek_config.py 1 "http://192.168.59.2/zeek-api" "y1X6Qn8PpV9jR4kM0wBz7Tf2GhUs3Lc8NrDq5Ke1HxYi0AzF7Gv9MbX2VwJoQp"')
        sys.exit(1)
    
    institution_id = int(sys.argv[1])
    zeek_base_url = sys.argv[2]
    zeek_key = sys.argv[3]
    
    try:
        result = InstitutionConfigService.update_zeek_config(
            institution_id=institution_id,
            zeek_base_url=zeek_base_url,
            zeek_key=zeek_key
        )
        
        print(f"✅ Configurações do Zeek atualizadas com sucesso!")
        print(f"   Instituição: {result['nome']} (ID: {result['institution_id']})")
        print(f"   URL: {result['zeek_base_url']}")
        print(f"   Token: {'***' if result['zeek_key'] else 'NÃO CONFIGURADO'}")
        print(f"   Atualizado em: {result['updated_at']}")
        
    except ValueError as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao atualizar configurações: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

