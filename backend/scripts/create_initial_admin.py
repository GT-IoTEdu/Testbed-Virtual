#!/usr/bin/env python3
"""
Script para criar usuário administrador inicial.

Este script:
1. Executa a migração para adicionar o perfil ADMIN
2. Cria o usuário administrador inicial
3. Valida a configuração
4. Mostra informações do sistema
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
from auth.admin_auth import admin_auth_service
import config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_initial_admin():
    """
    Cria o usuário administrador inicial.
    """
    logger.info("👑 Criando usuário administrador inicial...")
    
    try:
        # Verificar configurações
        if not config.SUPERUSER_ACCESS:
            logger.error("❌ Configuração SUPERUSER_ACCESS não definida")
            logger.error("   Configure o email do superusuário no arquivo .env")
            logger.error("   IMPORTANTE: O login administrativo é feito via Google OAuth")
            return False
        
        # Validar configuração
        if not admin_auth_service.validate_admin_access():
            logger.error("❌ Configuração administrativa inválida")
            return False
        
        # Criar usuário superusuário
        admin_user = admin_auth_service._get_or_create_admin_user(config.SUPERUSER_ACCESS)
        
        if not admin_user:
            logger.error("❌ Falha ao criar usuário administrador")
            return False
        
        logger.info(f"✅ Usuário administrador criado/encontrado:")
        logger.info(f"   📧 Email: {admin_user.email}")
        logger.info(f"   👤 Nome: {admin_user.nome}")
        logger.info(f"   🏢 Instituição: {admin_user.instituicao}")
        logger.info(f"   🔑 Permissão: {admin_user.permission.value}")
        logger.info(f"   🆔 ID: {admin_user.id}")
        
        return admin_user
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar usuário administrador: {e}")
        return False

def show_system_info():
    """
    Mostra informações do sistema de permissões.
    """
    logger.info("\n" + "="*60)
    logger.info("📊 INFORMAÇÕES DO SISTEMA")
    logger.info("="*60)
    
    try:
        with SessionLocal() as db:
            # Contar usuários por permissão
            stats = {}
            for permission in UserPermission:
                count = db.query(User).filter(User.permission == permission).count()
                stats[permission.value] = count
            
            logger.info(f"👥 Usuários cadastrados:")
            logger.info(f"   👑 Superusuários: {stats.get('SUPERUSER', 0)}")
            logger.info(f"   👨‍💼 Administradores: {stats.get('ADMIN', 0)}")
            logger.info(f"   👤 Usuários: {stats.get('USER', 0)}")
            
            # Mostrar superusuários
            admins = db.query(User).filter(User.permission == UserPermission.SUPERUSER).all()
            
            if admins:
                logger.info(f"\n👑 Lista de administradores:")
                for admin in admins:
                    logger.info(f"   - ID: {admin.id}, Email: {admin.email}, Nome: {admin.nome}")
            
            # Informações de configuração
            logger.info(f"\n⚙️ Configurações:")
            logger.info(f"   📧 SUPERUSER_ACCESS: {config.SUPERUSER_ACCESS}")
            logger.info(f"   🔐 Login: Via Google OAuth")
            
    except Exception as e:
        logger.error(f"❌ Erro ao obter informações do sistema: {e}")

def test_admin_verification():
    """
    Testa a verificação de email administrativo.
    """
    logger.info("\n" + "="*60)
    logger.info("🧪 TESTE DE VERIFICAÇÃO ADMINISTRATIVA")
    logger.info("="*60)
    
    try:
        # Testar verificação (sem senha, apenas email)
        auth_result = admin_auth_service.authenticate_admin(config.SUPERUSER_ACCESS)
        
        if auth_result:
            logger.info("✅ Verificação administrativa testada com sucesso!")
            logger.info(f"   👤 Usuário: {auth_result['nome']}")
            logger.info(f"   📧 Email: {auth_result['email']}")
            logger.info(f"   🔑 Permissão: {auth_result['permission']}")
            logger.info(f"   ✅ Email confirmado como administrador")
            logger.info(f"   ⚠️  IMPORTANTE: O login real é feito via Google OAuth")
            return True
        else:
            logger.error("❌ Falha na verificação administrativa")
            logger.error("   Verifique se o email está configurado corretamente em SUPERUSER_ACCESS")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro no teste de verificação: {e}")
        return False

def show_next_steps():
    """
    Mostra os próximos passos para usar o sistema.
    """
    logger.info("\n" + "="*60)
    logger.info("🚀 PRÓXIMOS PASSOS")
    logger.info("="*60)
    
    logger.info("1. 📝 Configure o arquivo .env:")
    logger.info(f"   SUPERUSER_ACCESS={config.SUPERUSER_ACCESS}")
    logger.info(f"   IMPORTANTE: Não é mais necessário ADMIN_PASSWORD")
    logger.info(f"   O login administrativo é feito via Google OAuth")
    
    logger.info("\n2. 🔐 Faça login administrativo:")
    logger.info(f"   - Acesse /login/admin no frontend")
    logger.info(f"   - Faça login com sua conta Google")
    logger.info(f"   - O sistema verificará se o email corresponde ao SUPERUSER_ACCESS")
    logger.info(f"   - Se corresponder, você terá acesso administrativo automaticamente")
    
    logger.info("\n3. 👥 Gerencie permissões de usuários:")
    logger.info("   GET /api/admin/users - Listar usuários")
    logger.info("   PUT /api/admin/users/{id}/permission - Alterar permissão")
    logger.info("   GET /api/admin/users/stats - Estatísticas")
    
    logger.info("\n4. 📊 Monitore o sistema:")
    logger.info("   GET /api/admin/info - Informações do administrador")
    logger.info("   GET /api/admin/validate-config - Validar configuração")
    
    logger.info("\n5. 🔧 Endpoints disponíveis:")
    logger.info("   - /api/admin/verify - Verificar se email é administrador")
    logger.info("   - /api/admin/users - Gerenciar usuários")
    logger.info("   - /api/admin/info - Informações do admin")
    logger.info("   - /api/admin/validate-config - Validar config")

def main():
    """
    Função principal do script.
    """
    logger.info("🚀 Iniciando criação do usuário administrador inicial")
    
    # Passo 1: Criar usuário administrador
    logger.info("\n" + "="*60)
    logger.info("PASSO 1: Criar usuário administrador")
    logger.info("="*60)
    
    admin_user = create_initial_admin()
    
    if not admin_user:
        logger.error("❌ Falha ao criar usuário administrador")
        sys.exit(1)
    
    # Passo 2: Mostrar informações do sistema
    show_system_info()
    
    # Passo 3: Testar verificação
    verification_success = test_admin_verification()
    
    if not verification_success:
        logger.error("❌ Falha no teste de verificação")
        sys.exit(1)
    
    # Passo 4: Mostrar próximos passos
    show_next_steps()
    
    logger.info("\n" + "="*60)
    logger.info("✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
    logger.info("="*60)
    
    logger.info("🎉 O sistema agora possui 3 perfis de usuário:")
    logger.info("   👤 USER - Usuário comum")
    logger.info("   👨‍💼 ADMIN - Administrador (gestor de instituição)")
    logger.info("   👑 SUPERUSER - Superusuário (administrador do sistema)")
    
    logger.info(f"\n🔑 Credenciais do administrador:")
    logger.info(f"   📧 Email: {config.SUPERUSER_ACCESS}")
    logger.info(f"   🔐 Login: Via Google OAuth")
    
    logger.info(f"\n⚠️ IMPORTANTE:")
    logger.info(f"   - O login administrativo é feito via Google OAuth")
    logger.info(f"   - Configure o email do superusuário em SUPERUSER_ACCESS no .env")
    logger.info(f"   - O usuário deve fazer login com a conta Google correspondente")
    logger.info(f"   - O sistema promoverá automaticamente para SUPERUSER se o email corresponder")

if __name__ == "__main__":
    main()
