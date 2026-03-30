"""
Script de migração para renomear permissões de usuário.

Este script atualiza as permissões no banco de dados:
- ADMIN -> SUPERUSER
- MANAGER -> ADMIN
- USER permanece igual

IMPORTANTE: Execute este script apenas UMA VEZ após atualizar o enum UserPermission.

Uso (execute do diretório backend):
    cd backend
    python -m scripts.migrate_rename_permissions

Ou diretamente:
    cd backend/scripts
    python migrate_rename_permissions.py
"""

import sys
import os

# Adicionar o diretório backend ao path (mesmo padrão dos outros scripts)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Verificar se os módulos podem ser importados
try:
    from db.session import SessionLocal
    from db.models import User
    from db.enums import UserPermission
    from sqlalchemy import text
    import logging
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print(f"📁 Diretório backend: {backend_dir}")
    print(f"📁 Diretório atual: {os.getcwd()}")
    print(f"📁 Python path: {sys.path[:3]}")
    print("\n💡 Tente executar do diretório backend:")
    print("   cd backend")
    print("   python -m scripts.migrate_rename_permissions")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_permissions():
    """
    Migra as permissões dos usuários:
    - ADMIN (antigo) -> SUPERUSER (novo)
    - MANAGER (antigo) -> ADMIN (novo)
    - USER permanece igual
    
    IMPORTANTE: Esta migração altera o ENUM do banco de dados e atualiza os dados.
    """
    db = SessionLocal()
    
    try:
        logger.info("Iniciando migração de permissões...")
        
        # Primeiro, alterar o ENUM para incluir SUPERUSER e manter ADMIN/MANAGER temporariamente
        logger.info("Passo 1: Alterando estrutura do ENUM...")
        
        # Verificar enum atual
        result = db.execute(text("""
            SELECT COLUMN_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'users' 
            AND COLUMN_NAME = 'permission'
        """))
        
        enum_info = result.fetchone()
        if enum_info:
            logger.info(f"Enum atual: {enum_info[0]}")
        
        # Adicionar SUPERUSER ao enum (mantendo valores antigos temporariamente)
        logger.info("Adicionando SUPERUSER ao enum...")
        db.execute(text("""
            ALTER TABLE users 
            MODIFY COLUMN permission ENUM('USER', 'MANAGER', 'ADMIN', 'SUPERUSER') 
            NOT NULL DEFAULT 'USER'
        """))
        db.commit()
        logger.info("✅ SUPERUSER adicionado ao enum")
        
        # Contar usuários por permissão atual
        old_admin_count = db.execute(text("SELECT COUNT(*) FROM users WHERE permission = 'ADMIN'")).scalar()
        old_manager_count = db.execute(text("SELECT COUNT(*) FROM users WHERE permission = 'MANAGER'")).scalar()
        old_user_count = db.execute(text("SELECT COUNT(*) FROM users WHERE permission = 'USER'")).scalar()
        
        logger.info(f"\nUsuários encontrados:")
        logger.info(f"  - ADMIN (antigo): {old_admin_count}")
        logger.info(f"  - MANAGER (antigo): {old_manager_count}")
        logger.info(f"  - USER: {old_user_count}")
        
        # Atualizar ADMIN -> SUPERUSER
        if old_admin_count > 0:
            logger.info("\nPasso 2: Atualizando ADMIN -> SUPERUSER...")
            db.execute(text("UPDATE users SET permission = 'SUPERUSER' WHERE permission = 'ADMIN'"))
            db.commit()
            logger.info(f"✅ {old_admin_count} usuários atualizados para SUPERUSER")
        
        # Atualizar MANAGER -> ADMIN
        if old_manager_count > 0:
            logger.info("\nPasso 3: Atualizando MANAGER -> ADMIN...")
            db.execute(text("UPDATE users SET permission = 'ADMIN' WHERE permission = 'MANAGER'"))
            db.commit()
            logger.info(f"✅ {old_manager_count} usuários atualizados para ADMIN")
        
        # Remover MANAGER do enum (agora só temos USER, ADMIN, SUPERUSER)
        logger.info("\nPasso 4: Removendo MANAGER do enum...")
        db.execute(text("""
            ALTER TABLE users 
            MODIFY COLUMN permission ENUM('USER', 'ADMIN', 'SUPERUSER') 
            NOT NULL DEFAULT 'USER'
        """))
        db.commit()
        logger.info("✅ Enum atualizado (USER, ADMIN, SUPERUSER)")
        
        # Verificar resultado
        logger.info("\nVerificando resultado da migração...")
        
        superuser_count = db.execute(text("SELECT COUNT(*) FROM users WHERE permission = 'SUPERUSER'")).scalar()
        admin_count = db.execute(text("SELECT COUNT(*) FROM users WHERE permission = 'ADMIN'")).scalar()
        user_count = db.execute(text("SELECT COUNT(*) FROM users WHERE permission = 'USER'")).scalar()
        
        logger.info(f"\nPermissões após migração:")
        logger.info(f"  - SUPERUSER: {superuser_count}")
        logger.info(f"  - ADMIN: {admin_count}")
        logger.info(f"  - USER: {user_count}")
        
        logger.info("\n✅ Migração concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro durante a migração: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        migrate_permissions()
    except Exception as e:
        logger.error(f"Falha na migração: {e}")
        sys.exit(1)

