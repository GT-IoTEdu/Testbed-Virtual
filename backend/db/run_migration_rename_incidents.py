#!/usr/bin/env python3
"""
Executa a migration: renomeia zeek_incidents para incidents.
Uso: a partir da pasta backend: python -m db.run_migration_rename_incidents
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.session import engine


def main():
    with engine.connect() as conn:
        r = conn.execute(text("SHOW TABLES LIKE 'zeek_incidents'"))
        if r.fetchone():
            conn.execute(text("RENAME TABLE zeek_incidents TO incidents"))
            conn.commit()
            print("Migration executada: zeek_incidents renomeada para incidents.")
        else:
            r2 = conn.execute(text("SHOW TABLES LIKE 'incidents'"))
            if r2.fetchone():
                print("Tabela incidents ja existe. Nada a fazer.")
            else:
                print("Tabela zeek_incidents nao encontrada. Para instalacao nova use: python -m db.create_tables")


if __name__ == "__main__":
    main()
