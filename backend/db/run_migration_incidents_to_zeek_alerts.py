#!/usr/bin/env python3
"""
Executa a migration: renomeia incidents para zeek_alerts.
Uso: a partir da pasta backend: python -m db.run_migration_incidents_to_zeek_alerts
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.session import engine


def main():
    with engine.connect() as conn:
        # Verificar se incidents existe
        r = conn.execute(text("SHOW TABLES LIKE 'incidents'"))
        if r.fetchone():
            # Verificar se zeek_alerts já existe
            r2 = conn.execute(text("SHOW TABLES LIKE 'zeek_alerts'"))
            if r2.fetchone():
                print("AVISO: Tabela zeek_alerts ja existe. Nao foi possivel renomear incidents.")
                print("Execute manualmente: RENAME TABLE incidents TO zeek_alerts;")
                print("Ou faça merge dos dados antes de renomear.")
            else:
                conn.execute(text("RENAME TABLE incidents TO zeek_alerts"))
                conn.commit()
                print("Migration executada: incidents renomeada para zeek_alerts.")
        else:
            r3 = conn.execute(text("SHOW TABLES LIKE 'zeek_alerts'"))
            if r3.fetchone():
                print("Tabela zeek_alerts ja existe. Nada a fazer.")
            else:
                print("Tabela incidents nao encontrada. Para instalacao nova use: python -m db.create_tables")


if __name__ == "__main__":
    main()
