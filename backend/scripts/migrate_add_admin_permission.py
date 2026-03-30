#!/usr/bin/env python3
"""
Script para adicionar o perfil ADMIN ao sistema de permissões.

Esta migração:
1. Adiciona o valor 'ADMIN' ao enum de permissões no banco de dados
2. Atualiza a estrutura da tabela users
3. Cria o primeiro usuário administrador se não existir
"""

import sys
import os
import logging
from datetime import datetime

# Adicionar o diretório backend ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import SessionLocal
from db.models import User
from db.enums import UserPermission
from sqlalchemy import text

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_admin_permission_to_enum():
    """
    Adiciona o valor 'ADMIN' ao enum de permissões no banco de dados.
    """
    db = SessionLocal()
    try:
        logger.info("🔧 Adicionando perfil ADMIN ao enum de permissões...")
        
        # Verificar se o valor ADMIN já existe no enum
        result = db.execute(text("""
            SELECT COLUMN_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'users' 
            AND COLUMN_NAME = 'permission'
        """))
        
        enum_values = result.fetchone()
        if enum_values and 'ADMIN' in enum_values[0]:
            logger.info("✅ Perfil ADMIN já existe no enum de permissões")
            return True
        
        # Adicionar ADMIN ao enum
        logger.info("📝 Adicionando 'ADMIN' ao enum de permissões...")
        
        db.execute(text("""
            ALTER TABLE users 
            MODIFY COLUMN permission ENUM('USER', 'MANAGER', 'ADMIN') 
            NOT NULL DEFAULT 'USER'
        """))
        
        db.commit()
        logger.info("✅ Perfil ADMIN adicionado com sucesso ao enum!")
        
        # Verificar a estrutura atualizada
        result = db.execute(text("""
            SELECT COLUMN_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'users' 
            AND COLUMN_NAME = 'permission'
        """))
        
        updated_enum = result.fetchone()
        logger.info(f"📋 Enum atualizado: {updated_enum[0]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar perfil ADMIN: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

def create_initial_admin_user():
    """
    Cria o usuário administrador inicial se não existir.
    """
    db = SessionLocal()
    try:
        # Verificar se já existe um administrador
        existing_admin = db.query(User).filter(User.permission == UserPermission.ADMIN).first()
        
        if existing_admin:
            logger.info(f"✅ Administrador já existe: {existing_admin.email}")
            return existing_admin
        
        # Criar usuário administrador inicial
        admin_email = os.getenv("SUPERUSER_ACCESS", "admin@iotedu.local")
        admin_name = "Administrador do Sistema"
        admin_institution = "IoT-EDU"
        
        logger.info(f"👑 Criando usuário administrador inicial: {admin_email}")
        
        admin_user = User(
            email=admin_email,
            nome=admin_name,
            instituicao=admin_institution,
            permission=UserPermission.ADMIN
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"✅ Usuário administrador criado com sucesso!")
        logger.info(f"📧 Email: {admin_user.email}")
        logger.info(f"👤 Nome: {admin_user.nome}")
        logger.info(f"🏢 Instituição: {admin_user.instituicao}")
        logger.info(f"🔑 Permissão: {admin_user.permission.value}")
        logger.info(f"🆔 ID: {admin_user.id}")
        
        return admin_user
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar usuário administrador: {e}")
        db.rollback()
        return None
        
    finally:
        db.close()

def show_user_permissions_stats():
    """
    Mostra estatísticas das permissões de usuários.
    """
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT 
                permission,
                COUNT(*) as count
            FROM users 
            GROUP BY permission
            ORDER BY 
                CASE permission
                    WHEN 'ADMIN' THEN 1
                    WHEN 'MANAGER' THEN 2
                    WHEN 'USER' THEN 3
                END
        """))
        
        stats = result.fetchall()
        
        logger.info(f"📊 Estatísticas de permissões de usuários:")
        for stat in stats:
            permission = stat[0]
            count = stat[1]
            
            if permission == 'ADMIN':
                logger.info(f"  👑 Administradores: {count}")
            elif permission == 'MANAGER':
                logger.info(f"  👨‍💼 Gestores: {count}")
            elif permission == 'USER':
                logger.info(f"  👤 Usuários: {count}")
        
        # Mostrar todos os administradores
        admins = db.query(User).filter(User.permission == UserPermission.ADMIN).all()
        
        if admins:
            logger.info(f"👑 Lista de administradores:")
            for admin in admins:
                logger.info(f"  - ID: {admin.id}, Email: {admin.email}, Nome: {admin.nome}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao mostrar estatísticas: {e}")
    finally:
        db.close()

def main():
    """
    Função principal da migração.
    """
    logger.info("🚀 Iniciando migração: Adicionar perfil ADMIN")
    
    # Passo 1: Adicionar ADMIN ao enum
    logger.info("\n" + "="*60)
    logger.info("PASSO 1: Adicionar ADMIN ao enum de permissões")
    logger.info("="*60)
    
    enum_success = add_admin_permission_to_enum()
    
    if not enum_success:
        logger.error("❌ Falha ao adicionar ADMIN ao enum")
        sys.exit(1)
    
    # Passo 2: Criar usuário administrador inicial
    logger.info("\n" + "="*60)
    logger.info("PASSO 2: Criar usuário administrador inicial")
    logger.info("="*60)
    
    admin_user = create_initial_admin_user()
    
    if not admin_user:
        logger.error("❌ Falha ao criar usuário administrador")
        sys.exit(1)
    
    # Passo 3: Mostrar estatísticas
    logger.info("\n" + "="*60)
    logger.info("PASSO 3: Estatísticas finais")
    logger.info("="*60)
    
    show_user_permissions_stats()
    
    logger.info("\n" + "="*60)
    logger.info("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    logger.info("="*60)
    
    logger.info("📋 Resumo da migração:")
    logger.info(f"  ✅ Perfil ADMIN adicionado ao enum")
    logger.info(f"  ✅ Usuário administrador criado: {admin_user.email}")
    logger.info(f"  ✅ Sistema pronto para uso com 3 perfis: USER, MANAGER, ADMIN")
    
    logger.info("\n🔧 Próximos passos:")
    logger.info("  1. Configure SUPERUSER_ACCESS no arquivo .env")
    logger.info("  2. Implemente autenticação administrativa")
    logger.info("  3. Crie endpoints para gerenciar permissões")
    logger.info("  4. Teste o sistema com os novos perfis")

if __name__ == "__main__":
    main()
