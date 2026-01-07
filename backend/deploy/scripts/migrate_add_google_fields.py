import os
import sys
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy import text
from db.session import engine

"""
Migração simples para adicionar colunas google_sub e picture na tabela users.
Executa ALTER TABLE apenas se a coluna não existir.
Uso (na raiz do backend):
  python backend/deploy/scripts/migrate_add_google_fields.py
"""

def column_exists(table: str, column: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(text(
            """
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = :table AND COLUMN_NAME = :column
            """
        ), {"table": table, "column": column}).scalar()
        return bool(result)

def add_column_if_missing(ddl: str):
    with engine.connect() as conn:
        conn.execute(text(ddl))

def main():
    # google_sub
    if not column_exists("users", "google_sub"):
        add_column_if_missing(
            "ALTER TABLE users ADD COLUMN google_sub VARCHAR(255) NULL UNIQUE"
        )
        print("[OK] Coluna google_sub adicionada.")
    else:
        print("[SKIP] Coluna google_sub já existe.")

    # picture
    if not column_exists("users", "picture"):
        add_column_if_missing(
            "ALTER TABLE users ADD COLUMN picture VARCHAR(512) NULL"
        )
        print("[OK] Coluna picture adicionada.")
    else:
        print("[SKIP] Coluna picture já existe.")

if __name__ == "__main__":
    main()


