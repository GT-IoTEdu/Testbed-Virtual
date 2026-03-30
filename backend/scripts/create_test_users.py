#!/usr/bin/env python3
"""
Script para criar usuários de teste com diferentes níveis de permissão.

Este script cria:
1. Um usuário comum (user) - pode gerenciar apenas seus dispositivos
2. Um gestor (manager) - pode gerenciar todos os dispositivos
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.models import User, Base
from db.enums import UserPermission
import config

def create_test_users():
    """Cria usuários de teste no banco de dados."""
    
    # Criar engine do banco de dados
    engine = create_engine(f"mysql://{config.MYSQL_USER}:{config.MYSQL_PASSWORD}@{config.MYSQL_HOST}/{config.MYSQL_DB}")
    
    # Criar sessão
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Verificar se os usuários já existem
        existing_user = session.query(User).filter(User.email == "usuario.teste@unipampa.edu.br").first()
        existing_manager = session.query(User).filter(User.email == "gestor.teste@unipampa.edu.br").first()
        
        # Criar usuário comum
        if not existing_user:
            user = User(
                email="usuario.teste@unipampa.edu.br",
                nome="Usuário Teste",
                instituicao="UNIPAMPA",
                permission=UserPermission.USER
            )
            session.add(user)
            print("✅ Usuário comum criado:")
            print(f"   - Email: {user.email}")
            print(f"   - Nome: {user.nome}")
            print(f"   - Permissão: {user.permission.value}")
            print(f"   - Instituição: {user.instituicao}")
        else:
            print("ℹ️ Usuário comum já existe:")
            print(f"   - Email: {existing_user.email}")
            print(f"   - Nome: {existing_user.nome}")
            print(f"   - Permissão: {existing_user.permission.value}")
        
        # Criar gestor
        if not existing_manager:
            manager = User(
                email="gestor.teste@unipampa.edu.br",
                nome="Gestor Teste",
                instituicao="UNIPAMPA",
                permission=UserPermission.ADMIN
            )
            session.add(manager)
            print("\n✅ Gestor criado:")
            print(f"   - Email: {manager.email}")
            print(f"   - Nome: {manager.nome}")
            print(f"   - Permissão: {manager.permission.value}")
            print(f"   - Instituição: {manager.instituicao}")
        else:
            print("\nℹ️ Gestor já existe:")
            print(f"   - Email: {existing_manager.email}")
            print(f"   - Nome: {existing_manager.nome}")
            print(f"   - Permissão: {existing_manager.permission.value}")
        
        # Commit das alterações
        session.commit()
        
        print("\n" + "="*60)
        print("📋 RESUMO DOS USUÁRIOS DE TESTE")
        print("="*60)
        
        # Listar todos os usuários
        all_users = session.query(User).all()
        for i, user in enumerate(all_users, 1):
            print(f"{i}. {user.nome} ({user.email})")
            print(f"   - Permissão: {user.permission.value}")
            print(f"   - Instituição: {user.instituicao}")
            print(f"   - Último login: {user.ultimo_login}")
            print()
        
        print("🔐 REGRAS DE NEGÓCIO:")
        print("- Usuário comum (user): Pode gerenciar apenas seus próprios dispositivos")
        print("- Gestor (manager): Pode gerenciar todos os dispositivos de todos os usuários")
        print("\n💡 DICAS:")
        print("- Use o ID do usuário nas requisições da API")
        print("- Verifique as permissões antes de permitir operações")
        print("- Gestores têm acesso total ao sistema")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Erro ao criar usuários: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("🚀 Criando usuários de teste...")
    print("="*60)
    create_test_users()
    print("\n✅ Processo concluído!")
