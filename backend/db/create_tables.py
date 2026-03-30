"""
Script para criar tabelas do banco de dados.

NOTA: Para instalação do zero, use: python -m db.setup_database
Este script ainda funciona, mas setup_database.py é recomendado pois
detecta automaticamente se é instalação do zero ou atualização.
"""
import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Base
from session import engine


def main() -> None:
    # Criar todas as tabelas usando o mesmo engine do projeto (mysql+pymysql)
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso!")
    print("\nTabelas principais:")
    print("- users")
    print("- institutions")
    print("- dhcp_servers")
    print("- dhcp_static_mappings")
    print("- user_device_assignments")
    print("- pfsense_aliases")
    print("- pfsense_alias_addresses")
    print("- pfsense_firewall_rules")
    print("- incidents")
    print("- zeek_alerts")
    print("- suricata_alerts")
    print("- snort_alerts")
    print("\nNOTA: Para instalação completa, use: python -m db.setup_database")


if __name__ == "__main__":
    main()
