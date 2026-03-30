#!/usr/bin/env python3
"""
Script para adicionar relação entre users e institutions.
Adiciona campo institution_id na tabela users para vincular gestores aos campus.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import engine
from sqlalchemy import text

def add_institution_relation():
    """Adiciona campo institution_id na tabela users."""
    
    try:
        with engine.connect() as conn:
            # Verificar se a coluna já existe
            result = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'iot_edu' 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'institution_id'
            """))
            
            if result.fetchone():
                print("Coluna institution_id já existe na tabela users")
                return
            
            # Adicionar coluna institution_id
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN institution_id INT(11) NULL 
                COMMENT 'ID da instituição/campus que o usuário gerencia'
            """))
            
            # Adicionar índice para performance
            conn.execute(text("""
                CREATE INDEX idx_users_institution_id ON users(institution_id)
            """))
            
            # Adicionar chave estrangeira
            conn.execute(text("""
                ALTER TABLE users 
                ADD CONSTRAINT fk_users_institution 
                FOREIGN KEY (institution_id) REFERENCES institutions(id) 
                ON DELETE SET NULL ON UPDATE CASCADE
            """))
            
            conn.commit()
            print("Relacao entre users e institutions criada com sucesso!")
            
    except Exception as e:
        print(f"Erro ao criar relacao: {e}")
        raise

if __name__ == "__main__":
    add_institution_relation()
