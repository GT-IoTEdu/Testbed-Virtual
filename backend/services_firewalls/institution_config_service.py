"""
Serviço para gerenciar configurações de instituições.
Busca configurações de pfSense e Zeek do banco de dados.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy import func
from db.session import SessionLocal
from db.models import Institution, User

logger = logging.getLogger(__name__)


class InstitutionConfigService:
    """Serviço para buscar configurações de instituições do banco de dados."""
    
    @staticmethod
    def get_institution_config(institution_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Busca configurações de uma instituição pelo ID.
        
        Args:
            institution_id: ID da instituição. Se None, retorna None.
            
        Returns:
            Dicionário com configurações da instituição ou None se não encontrada.
        """
        if not institution_id:
            return None
            
        try:
            with SessionLocal() as db:
                institution = db.query(Institution).filter(
                    Institution.id == institution_id,
                    Institution.is_active == True
                ).first()
                
                if not institution:
                    logger.warning(f"⚠️ [InstitutionConfigService] Instituição {institution_id} não encontrada ou inativa")
                    return None
                
                logger.info(f"✅ [InstitutionConfigService] Instituição encontrada: {institution.nome} (id={institution_id})")
                
                # Verificar valores antes de criar o dict
                # Tratar None e strings vazias
                zeek_base_url_raw = institution.zeek_base_url
                zeek_key_raw = institution.zeek_key
                
                zeek_base_url = zeek_base_url_raw.strip() if zeek_base_url_raw else ''
                zeek_key = zeek_key_raw.strip() if zeek_key_raw else ''
                
                logger.debug(f"🔍 Valores do banco para instituição {institution_id}:")
                logger.debug(f"   zeek_base_url (raw): {repr(zeek_base_url_raw)}")
                logger.debug(f"   zeek_base_url (processed): {repr(zeek_base_url)}")
                logger.debug(f"   zeek_key (raw): {'***' if zeek_key_raw else 'None/Empty'}")
                logger.debug(f"   zeek_key (processed): {'***' if zeek_key else 'None/Empty'}")
                
                # Processar configurações do Suricata
                suricata_base_url_raw = getattr(institution, 'suricata_base_url', None)
                suricata_key_raw = getattr(institution, 'suricata_key', None)
                
                # Tratar None e strings vazias
                suricata_base_url = suricata_base_url_raw.strip() if suricata_base_url_raw and isinstance(suricata_base_url_raw, str) else None
                suricata_key = suricata_key_raw.strip() if suricata_key_raw and isinstance(suricata_key_raw, str) else None
                
                logger.debug(f"🔍 Valores do Suricata do banco para instituição {institution_id}:")
                logger.debug(f"   suricata_base_url (raw): {repr(suricata_base_url_raw)}")
                logger.debug(f"   suricata_base_url (processed): {repr(suricata_base_url)}")
                logger.debug(f"   suricata_key (raw): {'***' if suricata_key_raw else 'None/Empty'}")
                logger.debug(f"   suricata_key (processed): {'***' if suricata_key else 'None/Empty'}")
                
                config = {
                    'institution_id': institution.id,
                    'nome': institution.nome,
                    'cidade': institution.cidade,
                    'pfsense_base_url': institution.pfsense_base_url,
                    'pfsense_key': institution.pfsense_key,
                    'zeek_base_url': zeek_base_url,
                    'zeek_key': zeek_key,
                    'suricata_base_url': suricata_base_url,
                    'suricata_key': suricata_key,
                    'ip_range_start': institution.ip_range_start,
                    'ip_range_end': institution.ip_range_end,
                }
                
                # Verificar se as configurações do Zeek estão presentes e não vazias
                if not zeek_base_url or not zeek_key:
                    logger.warning(f"⚠️ Instituição {institution.nome} (id={institution_id}) não tem configurações do Zeek completas:")
                    logger.warning(f"   zeek_base_url: {'✅' if zeek_base_url else '❌ NÃO CONFIGURADO OU VAZIO'} (raw: {repr(zeek_base_url_raw)})")
                    logger.warning(f"   zeek_key: {'✅' if zeek_key else '❌ NÃO CONFIGURADO OU VAZIO'} (raw: {'***' if zeek_key_raw else 'None/Empty'})")
                    logger.warning(f"   Use o endpoint PATCH /api/scanners/zeek/config/{institution_id} para configurar")
                else:
                    logger.info(f"✅ Configurações do Zeek válidas para instituição {institution.nome}: URL={zeek_base_url}, Key={'***' if zeek_key else 'NÃO CONFIGURADO'}")
                
                return config
                
        except Exception as e:
            logger.error(f"Erro ao buscar configurações da instituição {institution_id}: {e}")
            return None
    
    @staticmethod
    def get_user_institution_config(user_id: Optional[int] = None, user_email: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Busca configurações da instituição de um usuário.
        
        Args:
            user_id: ID do usuário (prioritário)
            user_email: Email do usuário (alternativa)
            
        Returns:
            Dicionário com configurações da instituição do usuário ou None.
        """
        try:
            with SessionLocal() as db:
                # Buscar usuário
                if user_id:
                    user = db.query(User).filter(User.id == user_id).first()
                elif user_email:
                    user = db.query(User).filter(User.email == user_email).first()
                else:
                    return None
                
                if not user:
                    logger.warning(f"Usuário não encontrado (id={user_id}, email={user_email})")
                    return None
                
                logger.debug(f"🔍 Usuário encontrado: {user.email} (id={user.id}, institution_id={user.institution_id})")
                
                # Se o usuário tem institution_id, buscar configurações
                if user.institution_id:
                    logger.info(f"🔍 [InstitutionConfigService] Buscando configurações da instituição {user.institution_id} para o usuário {user.email}")
                    config = InstitutionConfigService.get_institution_config(user.institution_id)
                    if config:
                        logger.info(f"✅ [InstitutionConfigService] Configurações encontradas para usuário {user.email} (instituição {user.institution_id})")
                        logger.info(f"   suricata_base_url: {repr(config.get('suricata_base_url'))}")
                        logger.info(f"   suricata_key: {'***' if config.get('suricata_key') else 'None/Empty'}")
                    else:
                        logger.warning(f"⚠️ [InstitutionConfigService] Configurações não encontradas para instituição {user.institution_id} do usuário {user.email}")
                    return config
                
                # Se é superusuário, retornar None (pode escolher instituição ou usar default)
                if user.is_superuser():
                    logger.info(f"ℹ️ Usuário {user.email} é superusuário, sem instituição específica - usando fallback do .env")
                    return None
                
                logger.warning(f"⚠️ Usuário {user.email} (id={user.id}) não possui instituição associada (institution_id=None)")
                logger.warning(f"   Para usar o Zeek, o usuário precisa ter uma instituição associada com zeek_base_url e zeek_key configurados")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar instituição do usuário: {e}")
            return None
    
    @staticmethod
    def get_all_institutions() -> list[Dict[str, Any]]:
        """
        Busca todas as instituições ativas.
        
        Returns:
            Lista de dicionários com informações básicas das instituições.
        """
        try:
            with SessionLocal() as db:
                institutions = db.query(Institution).filter(
                    Institution.is_active == True
                ).all()
                
                return [
                    {
                        'id': inst.id,
                        'nome': inst.nome,
                        'cidade': inst.cidade,
                        'is_active': inst.is_active
                    }
                    for inst in institutions
                ]
                
        except Exception as e:
            logger.error(f"Erro ao buscar instituições: {e}")
            return []
    
    @staticmethod
    def update_zeek_config(institution_id: int, zeek_base_url: str, zeek_key: str) -> Dict[str, Any]:
        """
        Atualiza as configurações do Zeek de uma instituição.
        
        Args:
            institution_id: ID da instituição
            zeek_base_url: URL base do Zeek
            zeek_key: Chave de acesso do Zeek
            
        Returns:
            Dicionário com as configurações atualizadas
            
        Raises:
            ValueError: Se a instituição não for encontrada
        """
        try:
            with SessionLocal() as db:
                institution = db.query(Institution).filter(
                    Institution.id == institution_id,
                    Institution.is_active == True
                ).first()
                
                if not institution:
                    raise ValueError(f"Instituição {institution_id} não encontrada ou inativa")
                
                # Atualizar configurações do Zeek
                institution.zeek_base_url = zeek_base_url.rstrip('/')
                institution.zeek_key = zeek_key
                institution.updated_at = func.now()
                
                db.commit()
                db.refresh(institution)
                
                logger.info(f"✅ Configurações do Zeek atualizadas para instituição {institution_id}: {institution.nome}")
                
                return {
                    'institution_id': institution.id,
                    'nome': institution.nome,
                    'zeek_base_url': institution.zeek_base_url,
                    'zeek_key': '***' if institution.zeek_key else None,
                    'updated_at': institution.updated_at.isoformat() if institution.updated_at else None
                }
                
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar configurações do Zeek da instituição {institution_id}: {e}")
            raise
    
    @staticmethod
    def get_institution_by_ip(device_ip: str) -> Optional[int]:
        """
        Identifica a instituição pelo IP do dispositivo.
        
        Verifica em qual range de IPs (ip_range_start a ip_range_end) o IP está.
        
        Args:
            device_ip: IP do dispositivo (ex: "192.168.59.4")
            
        Returns:
            ID da instituição ou None se não encontrada.
        """
        try:
            import ipaddress
            
            # Converter IP para objeto ipaddress para comparação
            try:
                ip = ipaddress.ip_address(device_ip)
            except ValueError:
                logger.warning(f"IP inválido: {device_ip}")
                return None
            
            with SessionLocal() as db:
                institutions = db.query(Institution).filter(
                    Institution.is_active == True
                ).all()
                
                for institution in institutions:
                    try:
                        # Converter ranges para objetos ipaddress
                        range_start = ipaddress.ip_address(institution.ip_range_start)
                        range_end = ipaddress.ip_address(institution.ip_range_end)
                        
                        # Verificar se o IP está no range
                        if range_start <= ip <= range_end:
                            logger.info(f"✅ IP {device_ip} identificado como pertencente à instituição {institution.nome} (ID: {institution.id}) - Range: {institution.ip_range_start} a {institution.ip_range_end}")
                            return institution.id
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Erro ao processar range da instituição {institution.id} ({institution.nome}): {e}")
                        continue
                
                logger.warning(f"⚠️ IP {device_ip} não pertence a nenhuma instituição ativa")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao identificar instituição pelo IP {device_ip}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None

