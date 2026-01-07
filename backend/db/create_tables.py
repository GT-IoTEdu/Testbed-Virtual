import os
import sys

 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Base
from session import engine


def main() -> None:
    # Criar todas as tabelas usando o mesmo engine do projeto (mysql+pymysql)
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso!")
    print("Tabelas principais:")
    print("- users")
    print("- dhcp_servers")
    print("- dhcp_static_mappings")
    print("- user_device_assignments")
    print("- pfsense_aliases")
    print("- pfsense_alias_addresses")
    print("- pfsense_firewall_rules")


if __name__ == "__main__":
    main()
