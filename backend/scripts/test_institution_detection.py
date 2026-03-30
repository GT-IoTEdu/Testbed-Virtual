#!/usr/bin/env python3
"""
Script para testar a detecção automática de instituição por IP.

Uso:
    python scripts/test_institution_detection.py <email_do_usuario> [ip_para_testar]
    
Exemplos:
    python scripts/test_institution_detection.py vt02joner@gmail.com
    python scripts/test_institution_detection.py vt02joner@gmail.com 192.168.59.100
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db.session import SessionLocal
from db.models import User, Institution
from services_firewalls.institution_config_service import InstitutionConfigService
import ipaddress
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ip_detection(test_ip: str):
    """Testa a detecção de instituição por IP."""
    logger.info(f"\n{'='*60}")
    logger.info(f"🧪 TESTANDO DETECÇÃO POR IP: {test_ip}")
    logger.info(f"{'='*60}")
    
    # Listar todas as instituições
    db = SessionLocal()
    try:
        institutions = db.query(Institution).filter(Institution.is_active == True).all()
        logger.info(f"\n📊 Instituições ativas encontradas: {len(institutions)}")
        
        if not institutions:
            logger.warning("⚠️ Nenhuma instituição ativa encontrada!")
            return None
        
        # Testar cada instituição
        try:
            test_ip_obj = ipaddress.ip_address(test_ip)
        except ValueError as e:
            logger.error(f"❌ IP inválido: {test_ip} - {e}")
            return None
        
        logger.info(f"\n🔍 Verificando se IP {test_ip} está em algum range...")
        
        for inst in institutions:
            try:
                range_start = ipaddress.ip_address(inst.ip_range_start)
                range_end = ipaddress.ip_address(inst.ip_range_end)
                
                logger.info(f"\n   Instituição: {inst.nome} ({inst.cidade})")
                logger.info(f"   Range: {inst.ip_range_start} a {inst.ip_range_end}")
                
                if range_start <= test_ip_obj <= range_end:
                    logger.info(f"   ✅ IP {test_ip} ESTÁ DENTRO DO RANGE!")
                    logger.info(f"   📍 Instituição detectada: {inst.nome} (ID: {inst.id})")
                    return inst.id
                else:
                    logger.info(f"   ❌ IP {test_ip} NÃO está no range")
            except (ValueError, AttributeError) as e:
                logger.warning(f"   ⚠️ Erro ao processar range: {e}")
                continue
        
        logger.warning(f"\n⚠️ IP {test_ip} não pertence a nenhuma instituição")
        logger.info(f"\n💡 Sugestões:")
        logger.info(f"   1. Verifique se o IP está correto")
        logger.info(f"   2. Se estiver em localhost (127.0.0.1), use o IP real da máquina na rede")
        logger.info(f"   3. Verifique se o range da instituição está correto")
        logger.info(f"   4. Considere expandir o range se necessário")
        return None
        
    finally:
        db.close()


def test_user_detection(user_email: str, test_ip: str = None):
    """Testa a detecção para um usuário específico."""
    logger.info(f"\n{'='*60}")
    logger.info(f"👤 TESTANDO DETECÇÃO PARA USUÁRIO: {user_email}")
    logger.info(f"{'='*60}")
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            logger.error(f"❌ Usuário {user_email} não encontrado")
            return
        
        logger.info(f"\n📋 Dados do usuário:")
        logger.info(f"   ID: {user.id}")
        logger.info(f"   Email: {user.email}")
        logger.info(f"   Nome: {user.nome}")
        logger.info(f"   Instituição atual: {user.instituicao}")
        logger.info(f"   institution_id: {user.institution_id}")
        
        if user.institution_id:
            inst = db.query(Institution).filter(Institution.id == user.institution_id).first()
            if inst:
                logger.info(f"   ✅ Já possui instituição: {inst.nome} ({inst.cidade})")
            else:
                logger.warning(f"   ⚠️ institution_id={user.institution_id} mas instituição não encontrada")
        else:
            logger.info(f"   ⚠️ Usuário NÃO possui institution_id")
            
            if test_ip:
                logger.info(f"\n🧪 Testando detecção com IP fornecido: {test_ip}")
                detected_id = test_ip_detection(test_ip)
                
                if detected_id:
                    logger.info(f"\n💾 Associando instituição {detected_id} ao usuário...")
                    user.institution_id = detected_id
                    db.commit()
                    logger.info(f"✅ Instituição associada com sucesso!")
                    
                    # Mostrar resultado
                    inst = db.query(Institution).filter(Institution.id == detected_id).first()
                    if inst:
                        logger.info(f"\n✅ Usuário agora está associado a:")
                        logger.info(f"   - Instituição: {inst.nome} ({inst.cidade})")
                        logger.info(f"   - ID: {inst.id}")
                else:
                    logger.warning(f"\n⚠️ Não foi possível detectar instituição para o IP {test_ip}")
                    logger.info(f"\n💡 Possíveis causas:")
                    logger.info(f"   1. IP {test_ip} não está dentro de nenhum range configurado")
                    logger.info(f"   2. Verifique se o IP está correto")
                    logger.info(f"   3. Verifique se os ranges das instituições estão corretos")
            else:
                logger.info(f"\n💡 Para testar com um IP específico, use:")
                logger.info(f"   python scripts/test_institution_detection.py {user_email} <IP>")
                logger.info(f"\n💡 Exemplo:")
                logger.info(f"   python scripts/test_institution_detection.py {user_email} 192.168.59.50")
                
    finally:
        db.close()


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/test_institution_detection.py <email> [ip_para_testar]")
        print("\nExemplos:")
        print("  python scripts/test_institution_detection.py vt02joner@gmail.com")
        print("  python scripts/test_institution_detection.py vt02joner@gmail.com 192.168.59.100")
        sys.exit(1)
    
    user_email = sys.argv[1]
    test_ip = sys.argv[2] if len(sys.argv) > 2 else None
    
    if test_ip:
        # Testar apenas o IP
        test_ip_detection(test_ip)
    else:
        # Testar para o usuário
        test_user_detection(user_email, test_ip)
    
    # Listar todas as instituições e ranges
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 RESUMO: INSTITUIÇÕES E RANGES CONFIGURADOS")
    logger.info(f"{'='*60}")
    
    db = SessionLocal()
    try:
        institutions = db.query(Institution).filter(Institution.is_active == True).all()
        for inst in institutions:
            logger.info(f"\n   {inst.nome} ({inst.cidade}) - ID: {inst.id}")
            logger.info(f"   Range: {inst.ip_range_start} a {inst.ip_range_end}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

