#!/usr/bin/env python3
"""
Script para criar usuários MANAGER de teste.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import get_db_session
from db.models import User
from db.enums import UserPermission

def create_test_managers():
    """Cria usuários MANAGER de teste."""
    
    test_managers = [
        {
            "email": "gestor1@unipampa.edu.br",
            "nome": "João Silva",
            "instituicao": "Unipampa",
            "permission": UserPermission.ADMIN
        },
        {
            "email": "gestor2@unipampa.edu.br", 
            "nome": "Maria Santos",
            "instituicao": "Unipampa",
            "permission": UserPermission.ADMIN
        },
        {
            "email": "gestor3@unipampa.edu.br",
            "nome": "Pedro Costa",
            "instituicao": "Unipampa", 
            "permission": UserPermission.ADMIN
        }
    ]
    
    try:
        with get_db_session() as db:
            for manager_data in test_managers:
                # Verificar se já existe
                existing_user = db.query(User).filter(User.email == manager_data["email"]).first()
                if existing_user:
                    print(f"Usuário {manager_data['email']} já existe")
                    continue
                
                # Criar novo usuário MANAGER
                user = User(
                    email=manager_data["email"],
                    nome=manager_data["nome"],
                    instituicao=manager_data["instituicao"],
                    permission=manager_data["permission"]
                )
                
                db.add(user)
                db.commit()
                print(f"Gestor criado: {manager_data['nome']} ({manager_data['email']})")
            
            print("Gestores de teste criados com sucesso!")
            
    except Exception as e:
        print(f"Erro ao criar gestores: {e}")
        raise

if __name__ == "__main__":
    create_test_managers()
