"""
Serviço para gerenciar aliases do pfSense.
"""

from db.session import SessionLocal
from db.models import PfSenseAlias, PfSenseAliasAddress
from services_firewalls.pfsense_client import listar_aliases_pfsense, cadastrar_alias_pfsense
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class AliasService:
    """Serviço para gerenciar aliases do pfSense."""
    
    def __init__(self, institution_id: Optional[int] = None, user_id: Optional[int] = None):
        """
        Inicializa o serviço de aliases.
        
        Args:
            institution_id: ID da instituição para buscar configurações (opcional)
            user_id: ID do usuário para buscar configurações da instituição (opcional)
        """
        self.db = SessionLocal()
        self.institution_id = institution_id
        self.user_id = user_id
        self._institution_config = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def _get_institution_config(self) -> Optional[Dict[str, Any]]:
        """
        Obtém configurações da instituição (cacheado).
        
        Returns:
            Dicionário com configurações ou None
        """
        if self._institution_config is not None:
            return self._institution_config
        
        try:
            from services_firewalls.institution_config_service import InstitutionConfigService
            
            if self.user_id:
                self._institution_config = InstitutionConfigService.get_user_institution_config(user_id=self.user_id)
            elif self.institution_id:
                self._institution_config = InstitutionConfigService.get_institution_config(self.institution_id)
            
            return self._institution_config
        except Exception as e:
            logger.warning(f"Erro ao buscar configurações da instituição: {e}")
            return None
    
    def _get_pfsense_config(self) -> tuple[Optional[str], Optional[str]]:
        """
        Obtém configurações do pfSense da instituição.
        
        Returns:
            Tupla (url, key) ou (None, None) se não encontrado
        """
        config = self._get_institution_config()
        if config:
            return config.get('pfsense_base_url'), config.get('pfsense_key')
        return None, None
    
    def save_aliases_data(self, aliases_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Salva dados de aliases no banco de dados.
        
        Args:
            aliases_data: Dados dos aliases vindos do pfSense
            
        Returns:
            Estatísticas da operação
        """
        try:
            aliases_saved = 0
            aliases_updated = 0
            addresses_saved = 0
            addresses_updated = 0
            
            # Verificar se os dados estão no formato correto
            if isinstance(aliases_data, dict) and 'data' in aliases_data:
                data = aliases_data['data']
            elif isinstance(aliases_data, list):
                data = aliases_data
            else:
                raise ValueError("Dados de aliases inválidos")
            
            for alias_data in data:
                # Normalizar pf_id (0 é válido no pfSense) - mas NÃO usar como identificador único
                # O pf_id é apenas uma referência, não um identificador único entre diferentes pfSenses
                raw_id = alias_data.get('id')
                normalized_pf_id = raw_id if (isinstance(raw_id, int) and raw_id >= 0) else None
                alias_name = alias_data['name']

                # Determinar institution_id ANTES de buscar (CRÍTICO para múltiplas redes)
                institution_id = self.institution_id
                if not institution_id and self.user_id:
                    config = self._get_institution_config()
                    if config:
                        institution_id = config.get('institution_id')
                
                # Garantir que o institution_id está definido
                if not institution_id:
                    logger.warning(f"⚠️ institution_id não definido ao salvar alias '{alias_name}'. Usando None.")
                    continue  # Pular aliases sem institution_id para evitar confusão
                
                logger.info(f"💾 Sincronizando alias '{alias_name}' para institution_id: {institution_id} (pf_id do pfSense: {normalized_pf_id})")

                # BUSCAR APENAS POR nome + institution_id (único identificador válido)
                # NÃO usar pf_id como identificador pois cada pfSense tem seus próprios IDs
                existing_alias = None
                if institution_id is not None:
                    existing_alias = (
                        self.db.query(PfSenseAlias)
                        .filter(
                            PfSenseAlias.name == alias_name,
                            PfSenseAlias.institution_id == institution_id
                        )
                        .first()
                    )
                    if existing_alias:
                        logger.info(f"✅ Alias '{alias_name}' encontrado por nome+institution_id (ID: {existing_alias.id}, institution_id: {institution_id}, pf_id atual: {existing_alias.pf_id})")
                    else:
                        logger.info(f"➕ Alias '{alias_name}' não encontrado para institution_id: {institution_id}, será criado")
                
                if existing_alias:
                    # Atualizar pf_id (apenas como referência, não como identificador)
                    if normalized_pf_id is not None and existing_alias.pf_id != normalized_pf_id:
                        logger.info(f"🔄 Atualizando pf_id do alias '{alias_name}' de {existing_alias.pf_id} para {normalized_pf_id}")
                        existing_alias.pf_id = normalized_pf_id
                    
                    # Atualizar campos do alias
                    existing_alias.alias_type = alias_data['type']
                    existing_alias.descr = alias_data.get('descr')
                    existing_alias.updated_at = datetime.utcnow()
                    aliases_updated += 1
                    logger.info(f"✅ Alias '{alias_name}' atualizado (ID: {existing_alias.id}, institution_id: {institution_id})")
                if not existing_alias:
                    # VERIFICAÇÃO FINAL: garantir que não existe alias com mesmo nome + institution_id
                    # (pode ter sido criado por outra thread/processo durante a sincronização)
                    final_check = None
                    if institution_id is not None:
                        final_check = (
                            self.db.query(PfSenseAlias)
                            .filter(
                                PfSenseAlias.name == alias_name,
                                PfSenseAlias.institution_id == institution_id
                            )
                            .first()
                        )
                    
                    if final_check:
                        logger.info(f"🔄 Alias '{alias_name}' encontrado na verificação final (ID: {final_check.id}), usando existente")
                        existing_alias = final_check
                        # Atualizar pf_id e campos
                        if normalized_pf_id is not None and final_check.pf_id != normalized_pf_id:
                            final_check.pf_id = normalized_pf_id
                        final_check.alias_type = alias_data['type']
                        final_check.descr = alias_data.get('descr')
                        final_check.updated_at = datetime.utcnow()
                        aliases_updated += 1
                    else:
                        # Criar novo registro APENAS se realmente não existe
                        logger.info(f"➕ Criando novo alias '{alias_name}' para institution_id: {institution_id} (pf_id: {normalized_pf_id})")
                        new_alias = PfSenseAlias(
                            pf_id=normalized_pf_id,  # Apenas como referência, não como identificador
                            name=alias_name,
                            alias_type=alias_data['type'],
                            descr=alias_data.get('descr'),
                            institution_id=institution_id
                        )
                        self.db.add(new_alias)
                        self.db.flush()
                        aliases_saved += 1
                        existing_alias = new_alias
                        logger.info(f"✅ Novo alias '{alias_name}' criado (ID: {new_alias.id}, institution_id: {institution_id}, pf_id: {normalized_pf_id})")
                
                # Processar endereços (host/network)
                if 'address' in alias_data and alias_data['address']:
                    # alias_data['address'] pode ser lista de strings; alias_data['detail'] paralela
                    details_list = alias_data.get('detail') or []
                    for i, address in enumerate(alias_data['address']):
                        detail = details_list[i] if i < len(details_list) else None

                        # Verificar se o endereço já existe
                        existing_address = self.db.query(PfSenseAliasAddress).filter(
                            PfSenseAliasAddress.alias_id == existing_alias.id,
                            PfSenseAliasAddress.address == address
                        ).first()

                        if existing_address:
                            # Atualizar endereço existente
                            if existing_address.detail != detail:
                                existing_address.detail = detail
                                addresses_updated += 1
                        else:
                            # Criar novo endereço
                            new_address = PfSenseAliasAddress(
                                alias_id=existing_alias.id,
                                address=address,
                                detail=detail
                            )
                            self.db.add(new_address)
                            addresses_saved += 1
            
            self.db.commit()
            
            return {
                'status': 'success',
                'aliases_saved': aliases_saved,
                'aliases_updated': aliases_updated,
                'addresses_saved': addresses_saved,
                'addresses_updated': addresses_updated,
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao salvar aliases: {e}")
            raise
    
    def get_all_aliases(self) -> List[Dict[str, Any]]:
        """
        Obtém todos os aliases do banco de dados.
        Filtra por instituição se institution_id ou user_id estiver configurado.
        
        Returns:
            Lista de aliases com endereços
        """
        try:
            # Determinar institution_id se não estiver definido
            institution_id = self.institution_id
            if not institution_id and self.user_id:
                config = self._get_institution_config()
                if config:
                    institution_id = config.get('institution_id')
            
            query = self.db.query(PfSenseAlias)
            if institution_id is not None:
                query = query.filter(PfSenseAlias.institution_id == institution_id)
            
            aliases = query.all()
            result = []
            
            for alias in aliases:
                addresses = self.db.query(PfSenseAliasAddress).filter(
                    PfSenseAliasAddress.alias_id == alias.id
                ).all()
                
                alias_dict = {
                    'id': alias.id,
                    'pf_id': alias.pf_id,
                    'name': alias.name,
                    'alias_type': alias.alias_type,
                    'descr': alias.descr,
                    'created_at': alias.created_at,
                    'updated_at': alias.updated_at,
                    'addresses': [
                        {
                            'id': addr.id,
                            'address': addr.address,
                            'detail': addr.detail,
                            'created_at': addr.created_at
                        }
                        for addr in addresses
                    ]
                }
                result.append(alias_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao buscar aliases: {e}")
            raise
    
    def get_alias_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Busca um alias específico por nome.
        Filtra por instituição se institution_id ou user_id estiver configurado.
        
        Args:
            name: Nome do alias
            
        Returns:
            Dados do alias ou None se não encontrado
        """
        try:
            # Determinar institution_id se não estiver definido
            institution_id = self.institution_id
            if not institution_id and self.user_id:
                config = self._get_institution_config()
                if config:
                    institution_id = config.get('institution_id')
            
            query = self.db.query(PfSenseAlias).filter(
                PfSenseAlias.name == name
            )
            if institution_id is not None:
                query = query.filter(PfSenseAlias.institution_id == institution_id)
                logger.debug(f"🔍 Buscando alias '{name}' com institution_id: {institution_id}")
            else:
                logger.warning(f"⚠️ Buscando alias '{name}' SEM institution_id (pode retornar alias de qualquer instituição)")
            
            alias = query.first()
            
            if alias:
                logger.debug(f"✅ Alias '{name}' encontrado (ID: {alias.id}, institution_id: {alias.institution_id}, pf_id: {alias.pf_id})")
            else:
                logger.warning(f"⚠️ Alias '{name}' não encontrado para institution_id: {institution_id}")
                return None
            
            addresses = self.db.query(PfSenseAliasAddress).filter(
                PfSenseAliasAddress.alias_id == alias.id
            ).all()
            
            return {
                'id': alias.id,
                'pf_id': alias.pf_id,
                'name': alias.name,
                'alias_type': alias.alias_type,
                'descr': alias.descr,
                'created_at': alias.created_at,
                'updated_at': alias.updated_at,
                'addresses': [
                    {
                        'id': addr.id,
                        'address': addr.address,
                        'detail': addr.detail,
                        'created_at': addr.created_at
                    }
                    for addr in addresses
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar alias por nome: {e}")
            raise
    
    def search_aliases(self, query: str) -> List[Dict[str, Any]]:
        """
        Busca aliases por termo.
        Filtra por instituição se institution_id ou user_id estiver configurado.
        
        Args:
            query: Termo de busca
            
        Returns:
            Lista de aliases encontrados
        """
        try:
            # Determinar institution_id se não estiver definido
            institution_id = self.institution_id
            if not institution_id and self.user_id:
                config = self._get_institution_config()
                if config:
                    institution_id = config.get('institution_id')
            
            db_query = self.db.query(PfSenseAlias).filter(
                PfSenseAlias.name.contains(query) |
                PfSenseAlias.descr.contains(query)
            )
            if institution_id is not None:
                db_query = db_query.filter(PfSenseAlias.institution_id == institution_id)
            
            aliases = db_query.all()
            
            result = []
            for alias in aliases:
                addresses = self.db.query(PfSenseAliasAddress).filter(
                    PfSenseAliasAddress.alias_id == alias.id
                ).all()
                
                alias_dict = {
                    'id': alias.id,
                    'pf_id': alias.pf_id,
                    'name': alias.name,
                    'alias_type': alias.alias_type,
                    'descr': alias.descr,
                    'created_at': alias.created_at,
                    'updated_at': alias.updated_at,
                    'addresses': [
                        {
                            'id': addr.id,
                            'address': addr.address,
                            'detail': addr.detail,
                            'created_at': addr.created_at
                        }
                        for addr in addresses
                    ]
                }
                result.append(alias_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao buscar aliases: {e}")
            raise
    
    def get_alias_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas dos aliases.
        Filtra por instituição se institution_id ou user_id estiver configurado.
        
        Returns:
            Estatísticas dos aliases
        """
        try:
            # Determinar institution_id se não estiver definido
            institution_id = self.institution_id
            if not institution_id and self.user_id:
                config = self._get_institution_config()
                if config:
                    institution_id = config.get('institution_id')
            
            query = self.db.query(PfSenseAlias)
            if institution_id is not None:
                query = query.filter(PfSenseAlias.institution_id == institution_id)
            
            total_aliases = query.count()
            
            # Contar endereços apenas dos aliases filtrados
            alias_ids = [a.id for a in query.all()]
            total_addresses = self.db.query(PfSenseAliasAddress).filter(
                PfSenseAliasAddress.alias_id.in_(alias_ids)
            ).count() if alias_ids else 0
            
            # Contar por tipo (usando query filtrada)
            aliases_by_type = {}
            type_counts = query.all()
            for alias in type_counts:
                type_name = alias.alias_type
                aliases_by_type[type_name] = aliases_by_type.get(type_name, 0) + 1
            
            # Contar criados hoje (usando query filtrada)
            today = date.today()
            created_today = query.filter(
                PfSenseAlias.created_at >= today
            ).count()
            
            # Contar atualizados hoje (usando query filtrada)
            updated_today = query.filter(
                PfSenseAlias.updated_at >= today
            ).count()
            
            return {
                'total_aliases': total_aliases,
                'aliases_by_type': aliases_by_type,
                'total_addresses': total_addresses,
                'created_today': created_today,
                'updated_today': updated_today
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            raise
    
    def create_alias(self, alias_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um novo alias no banco de dados e no pfSense.
        
        Args:
            alias_data: Dados do alias
            
        Returns:
            Dados do alias criado
        """
        try:
            # Determinar institution_id se não estiver definido
            institution_id = self.institution_id
            if not institution_id and self.user_id:
                config = self._get_institution_config()
                if config:
                    institution_id = config.get('institution_id')
            
            # Verificar se já existe (considerando instituição)
            query = self.db.query(PfSenseAlias).filter(
                PfSenseAlias.name == alias_data['name']
            )
            if institution_id is not None:
                query = query.filter(PfSenseAlias.institution_id == institution_id)
            
            existing = query.first()
            
            if existing:
                raise ValueError(f"Alias '{alias_data['name']}' já existe")
            
            # Criar no pfSense primeiro usando configurações da instituição
            pfsense_result = cadastrar_alias_pfsense(
                name=alias_data['name'],
                alias_type=alias_data['alias_type'],
                descr=alias_data['descr'],
                address=[addr['address'] for addr in alias_data['addresses']],
                detail=[addr.get('detail', '') for addr in alias_data['addresses']],
                user_id=self.user_id,
                institution_id=self.institution_id
            )
            
            # Se sucesso no pfSense, salvar no banco
            if pfsense_result.get('status') == 'ok':
                # Buscar o ID do alias criado no pfSense
                pf_id = pfsense_result.get('result', {}).get('data', {}).get('id', 0)
                # Evitar colisão de índice único quando a API não retorna ID (id==0 ou ausente)
                if not pf_id or pf_id == 0:
                    pf_id = None
                
                # Determinar institution_id se não estiver definido
                institution_id = self.institution_id
                if not institution_id and self.user_id:
                    config = self._get_institution_config()
                    if config:
                        institution_id = config.get('institution_id')
                
                new_alias = PfSenseAlias(
                    pf_id=pf_id,
                    name=alias_data['name'],
                    alias_type=alias_data['alias_type'],
                    descr=alias_data['descr'],
                    institution_id=institution_id
                )
                self.db.add(new_alias)
                self.db.flush()
                
                # Adicionar endereços
                for addr_data in alias_data['addresses']:
                    new_address = PfSenseAliasAddress(
                        alias_id=new_alias.id,
                        address=addr_data['address'],
                        detail=addr_data.get('detail')
                    )
                    self.db.add(new_address)
                
                self.db.commit()
                
                # Aplicar mudanças no firewall do pfSense
                try:
                    from services_firewalls.pfsense_client import aplicar_mudancas_firewall_pfsense
                    aplicar_mudancas_firewall_pfsense(
                        user_id=self.user_id,
                        institution_id=self.institution_id
                    )
                    logger.info(f"Mudanças aplicadas no firewall após criar alias '{alias_data['name']}'")
                except Exception as apply_error:
                    logger.error(f"Erro ao aplicar mudanças no firewall: {apply_error}")
                    # Não falha a operação se a aplicação das mudanças falhar
                
                return {
                    'success': True,
                    'message': 'Alias criado com sucesso',
                    'alias_id': new_alias.id,
                    'pf_id': pf_id
                }
            else:
                raise ValueError(f"Erro ao criar alias no pfSense: {pfsense_result}")
                
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            self.db.rollback()
            logger.error(f"Timeout/Conexão ao criar alias no pfSense: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao criar alias: {e}")
            raise

    def update_alias(self, alias_name: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza um alias existente no banco de dados e no pfSense.
        
        Args:
            alias_name: Nome do alias a ser atualizado
            update_data: Dados para atualização
            
        Returns:
            Dados do alias atualizado
        """
        try:
            # Determinar institution_id se não estiver definido
            institution_id = self.institution_id
            if not institution_id and self.user_id:
                config = self._get_institution_config()
                if config:
                    institution_id = config.get('institution_id')
            
            # Buscar o alias no banco de dados (considerando instituição)
            query = self.db.query(PfSenseAlias).filter(
                PfSenseAlias.name == alias_name
            )
            if institution_id is not None:
                query = query.filter(PfSenseAlias.institution_id == institution_id)
            
            alias = query.first()
            
            if not alias:
                raise ValueError(f"Alias '{alias_name}' não encontrado")
            
            # Preparar dados para o pfSense
            pfsense_data = {}
            
            if 'alias_type' in update_data and update_data['alias_type'] is not None:
                pfsense_data['alias_type'] = update_data['alias_type']
                alias.alias_type = update_data['alias_type']
                
            if 'descr' in update_data and update_data['descr'] is not None:
                pfsense_data['descr'] = update_data['descr']
                alias.descr = update_data['descr']
                
            if 'addresses' in update_data and update_data['addresses'] is not None:
                # Atualizar endereços no banco
                # Primeiro, remover endereços existentes
                self.db.query(PfSenseAliasAddress).filter(
                    PfSenseAliasAddress.alias_id == alias.id
                ).delete()
                
                # Adicionar novos endereços
                addresses = []
                details = []
                for addr_data in update_data['addresses']:
                    new_address = PfSenseAliasAddress(
                        alias_id=alias.id,
                        address=addr_data['address'],
                        detail=addr_data.get('detail')
                    )
                    self.db.add(new_address)
                    addresses.append(addr_data['address'])
                    details.append(addr_data.get('detail', ''))
                
                pfsense_data['address'] = addresses
                pfsense_data['detail'] = details
            
            # Atualizar timestamp
            alias.updated_at = datetime.utcnow()
            
            # Atualizar no pfSense se houver dados para atualizar
            if pfsense_data:
                from services_firewalls.pfsense_client import atualizar_alias_pfsense, obter_alias_pfsense
                
                # Garantir que temos institution_id definido
                if not institution_id:
                    raise ValueError(f"institution_id não definido. Não é possível atualizar alias no pfSense sem saber qual instituição usar.")
                
                logger.info(f"🔄 Buscando alias '{alias_name}' no pfSense da instituição {institution_id} (user_id: {self.user_id})")
                
                # Buscar o pf_id correto do alias no pfSense da instituição do usuário
                # O pf_id no banco pode estar incorreto (ex: 0 pode ser de outro alias de outra instituição)
                # SEMPRE buscar no pfSense da instituição correta para obter o ID correto
                pf_id_to_use = None
                
                try:
                    # SEMPRE buscar no pfSense da instituição do usuário para obter o ID correto
                    logger.info(f"🔍 Buscando alias '{alias_name}' no pfSense da instituição {institution_id}...")
                    pfsense_alias = obter_alias_pfsense(
                        name=alias_name,
                        user_id=self.user_id,
                        institution_id=self.institution_id
                    )
                    if pfsense_alias and isinstance(pfsense_alias, dict):
                        # Extrair o ID do alias do pfSense da instituição correta
                        pf_id_to_use = pfsense_alias.get('id')
                        pfsense_name = pfsense_alias.get('name')
                        
                        if pfsense_name == alias_name:
                            # ID 0 é válido no pfSense (primeiro alias criado)
                            if pf_id_to_use is not None:
                                logger.info(f"✅ pf_id encontrado no pfSense da instituição {institution_id}: {pf_id_to_use}")
                                # Atualizar o pf_id no banco (sempre do pfSense da instituição correta)
                                alias.pf_id = pf_id_to_use
                            else:
                                logger.warning(f"⚠️ Alias '{alias_name}' encontrado no pfSense mas sem ID")
                                # Usar 0 como fallback
                                pf_id_to_use = 0
                                alias.pf_id = 0
                        else:
                            logger.warning(f"⚠️ Alias encontrado no pfSense tem nome diferente: '{pfsense_name}' != '{alias_name}'")
                            raise ValueError(f"Alias encontrado no pfSense não corresponde ao nome esperado")
                    else:
                        # Alias não existe no pfSense da instituição, criar
                        logger.info(f"➕ Alias '{alias_name}' não encontrado no pfSense da instituição {institution_id}, será criado")
                        raise ValueError(f"Alias '{alias_name}' não encontrado no pfSense da instituição {institution_id}")
                except ValueError as ve:
                    # Se não encontrou ou tem problema, criar o alias no pfSense
                    logger.info(f"🔨 Criando alias '{alias_name}' no pfSense da instituição {institution_id}...")
                    from services_firewalls.pfsense_client import cadastrar_alias_pfsense
                    create_result = cadastrar_alias_pfsense(
                        name=alias_name,
                        alias_type=alias.alias_type,
                        descr=alias.descr or f'Alias {alias_name}',
                        address=[],  # Criar vazio, será preenchido depois
                        detail=[],
                        user_id=self.user_id,
                        institution_id=self.institution_id
                    )
                    if create_result.get('status') == 'ok':
                        new_pf_id = create_result.get('result', {}).get('data', {}).get('id')
                        if new_pf_id is not None:
                            pf_id_to_use = new_pf_id
                            alias.pf_id = new_pf_id
                            logger.info(f"✅ Alias '{alias_name}' criado no pfSense da instituição {institution_id} com ID: {pf_id_to_use}")
                        else:
                            # Se não retornou ID, usar 0 (pode ser o primeiro alias)
                            pf_id_to_use = 0
                            alias.pf_id = 0
                            logger.info(f"✅ Alias '{alias_name}' criado no pfSense (ID não retornado, usando 0)")
                    else:
                        # Se o erro for que o alias já existe, buscar novamente
                        error_msg = str(create_result)
                        if "must be unique" in error_msg or "already exists" in error_msg.lower() or "FIELD_MUST_BE_UNIQUE" in error_msg:
                            logger.info(f"ℹ️ Alias '{alias_name}' já existe no pfSense, buscando novamente...")
                            pfsense_alias = obter_alias_pfsense(
                                name=alias_name,
                                user_id=self.user_id,
                                institution_id=self.institution_id
                            )
                            if pfsense_alias and isinstance(pfsense_alias, dict):
                                pf_id_to_use = pfsense_alias.get('id', 0)
                                alias.pf_id = pf_id_to_use
                                logger.info(f"✅ Alias '{alias_name}' encontrado no pfSense com ID: {pf_id_to_use}")
                            else:
                                raise ValueError(f"Erro ao criar alias no pfSense: {create_result}")
                        else:
                            raise ValueError(f"Erro ao criar alias no pfSense: {create_result}")
                except Exception as e:
                    # Se falhou ao criar, verificar se já existe
                    error_str = str(e)
                    if "must be unique" in error_str or "already exists" in error_str.lower() or "FIELD_MUST_BE_UNIQUE" in error_str or "400" in error_str:
                        logger.info(f"ℹ️ Alias '{alias_name}' já existe no pfSense, buscando novamente...")
                        pfsense_alias = obter_alias_pfsense(
                            name=alias_name,
                            user_id=self.user_id,
                            institution_id=self.institution_id
                        )
                        if pfsense_alias and isinstance(pfsense_alias, dict):
                            pf_id_to_use = pfsense_alias.get('id', 0)
                            alias.pf_id = pf_id_to_use
                            logger.info(f"✅ Alias '{alias_name}' encontrado no pfSense com ID: {pf_id_to_use}")
                        else:
                            logger.error(f"Erro ao buscar/criar alias '{alias_name}' no pfSense da instituição {institution_id}: {e}")
                            raise ValueError(f"Não foi possível encontrar o alias '{alias_name}' no pfSense após erro de criação: {e}")
                    else:
                        logger.error(f"Erro ao buscar/criar alias '{alias_name}' no pfSense da instituição {institution_id}: {e}")
                        raise ValueError(f"Não foi possível encontrar ou criar o alias '{alias_name}' no pfSense da instituição {institution_id}: {e}")
                
                logger.info(f"🔄 Atualizando alias '{alias_name}' no pfSense usando pf_id: {pf_id_to_use}")
                pfsense_result = atualizar_alias_pfsense(
                    alias_id=pf_id_to_use,
                    name=alias_name,
                    alias_type=pfsense_data.get('alias_type'),
                    descr=pfsense_data.get('descr'),
                    address=pfsense_data.get('address'),
                    detail=pfsense_data.get('detail'),
                    user_id=self.user_id,
                    institution_id=self.institution_id
                )
                
                if pfsense_result.get('status') != 'ok':
                    raise ValueError(f"Erro ao atualizar alias no pfSense: {pfsense_result}")
                
                # Aplicar mudanças no firewall do pfSense
                try:
                    from services_firewalls.pfsense_client import aplicar_mudancas_firewall_pfsense
                    aplicar_mudancas_firewall_pfsense(
                        user_id=self.user_id,
                        institution_id=self.institution_id
                    )
                    logger.info(f"Mudanças aplicadas no firewall após atualizar alias '{alias_name}'")
                except Exception as apply_error:
                    logger.error(f"Erro ao aplicar mudanças no firewall: {apply_error}")
                    # Não falha a operação se a aplicação das mudanças falhar
            
            self.db.commit()
            
            # Retornar dados atualizados
            return {
                'success': True,
                'message': 'Alias atualizado com sucesso',
                'alias_id': alias.id,
                'name': alias.name,
                'alias_type': alias.alias_type,
                'descr': alias.descr,
                'updated_at': alias.updated_at,
                'pfsense_updated': bool(pfsense_data)
            }
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            self.db.rollback()
            logger.error(f"Timeout/Conexão ao atualizar alias no pfSense: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar alias: {e}")
            raise

    def add_addresses_to_alias(self, alias_name: str, new_addresses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Adiciona novos endereços a um alias existente sem substituir os atuais.
        
        Args:
            alias_name: Nome do alias
            new_addresses: Lista de novos endereços para adicionar
            
        Returns:
            Dados do alias atualizado
        """
        try:
            # Determinar institution_id se não estiver definido
            institution_id = self.institution_id
            if not institution_id and self.user_id:
                config = self._get_institution_config()
                if config:
                    institution_id = config.get('institution_id')
            
            # Buscar o alias no banco de dados (considerando instituição)
            query = self.db.query(PfSenseAlias).filter(
                PfSenseAlias.name == alias_name
            )
            if institution_id is not None:
                query = query.filter(PfSenseAlias.institution_id == institution_id)
            
            alias = query.first()
            
            if not alias:
                raise ValueError(f"Alias '{alias_name}' não encontrado")
            
            # Obter endereços existentes
            existing_addresses = self.db.query(PfSenseAliasAddress).filter(
                PfSenseAliasAddress.alias_id == alias.id
            ).all()
            
            # Preparar lista de endereços existentes
            current_addresses = []
            current_details = []
            for addr in existing_addresses:
                current_addresses.append(addr.address)
                current_details.append(addr.detail or '')
            
            # Adicionar novos endereços
            addresses_to_add = []
            details_to_add = []
            
            for addr_data in new_addresses:
                address = addr_data['address']
                detail = addr_data.get('detail', '')
                
                # Verificar se o endereço já existe
                if address not in current_addresses:
                    # Adicionar ao banco de dados
                    new_address = PfSenseAliasAddress(
                        alias_id=alias.id,
                        address=address,
                        detail=detail
                    )
                    self.db.add(new_address)
                    
                    # Adicionar às listas para pfSense
                    current_addresses.append(address)
                    current_details.append(detail)
                    addresses_to_add.append(address)
                    details_to_add.append(detail)
            
            # Atualizar timestamp
            alias.updated_at = datetime.utcnow()
            
            # Atualizar no pfSense se houver novos endereços
            if addresses_to_add:
                from services_firewalls.pfsense_client import atualizar_alias_pfsense, obter_alias_pfsense
                
                # Garantir que temos institution_id definido
                if not institution_id:
                    raise ValueError(f"institution_id não definido. Não é possível adicionar endereços ao alias no pfSense sem saber qual instituição usar.")
                
                logger.info(f"🔄 Buscando alias '{alias_name}' no pfSense da instituição {institution_id} (user_id: {self.user_id})")
                
                # SEMPRE buscar o pf_id no pfSense da instituição do usuário
                # Não confiar no pf_id do banco, pois pode ser de outra instituição
                alias_id = None
                
                # SEMPRE buscar no pfSense da instituição do usuário para obter o ID correto
                logger.info(f"🔍 Buscando alias '{alias_name}' no pfSense da instituição {institution_id}...")
                try:
                    pfsense_alias = obter_alias_pfsense(
                        name=alias_name,
                        user_id=self.user_id,
                        institution_id=self.institution_id
                    )
                    
                    if pfsense_alias and isinstance(pfsense_alias, dict):
                        # Extrair o ID do alias do pfSense da instituição correta
                        alias_id = pfsense_alias.get('id')
                        pfsense_name = pfsense_alias.get('name')
                        
                        if pfsense_name == alias_name:
                            # ID 0 é válido no pfSense (primeiro alias criado)
                            if alias_id is not None:
                                logger.info(f"✅ pf_id encontrado no pfSense da instituição {institution_id}: {alias_id}")
                                # Atualizar o pf_id no banco (sempre do pfSense da instituição correta)
                                alias.pf_id = alias_id
                            else:
                                logger.warning(f"⚠️ Alias '{alias_name}' encontrado no pfSense mas sem ID")
                                # Mesmo sem ID, podemos usar o alias existente
                                # Tentar obter o ID de outra forma ou usar None
                                alias_id = 0  # Usar 0 como fallback
                        else:
                            logger.warning(f"⚠️ Alias encontrado no pfSense tem nome diferente: '{pfsense_name}' != '{alias_name}'")
                            alias_id = None  # Não usar este alias
                    else:
                        # Alias não existe no pfSense da instituição, tentar criar
                        logger.info(f"➕ Alias '{alias_name}' não encontrado no pfSense da instituição {institution_id}, tentando criar...")
                        alias_id = None
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao buscar alias no pfSense: {e}")
                    alias_id = None
                
                # Se não encontrou o alias no pfSense, tentar criar
                if alias_id is None:
                    try:
                        logger.info(f"🔨 Criando alias '{alias_name}' no pfSense da instituição {institution_id}...")
                        from services_firewalls.pfsense_client import cadastrar_alias_pfsense
                        create_result = cadastrar_alias_pfsense(
                            name=alias_name,
                            alias_type=alias.alias_type,
                            descr=alias.descr or f'Alias {alias_name}',
                            address=current_addresses,  # Criar com os endereços atuais
                            detail=current_details,
                            user_id=self.user_id,
                            institution_id=self.institution_id
                        )
                        if create_result.get('status') == 'ok':
                            new_pf_id = create_result.get('result', {}).get('data', {}).get('id')
                            if new_pf_id is not None:
                                alias_id = new_pf_id
                                alias.pf_id = new_pf_id
                                logger.info(f"✅ Alias '{alias_name}' criado no pfSense da instituição {institution_id} com ID: {alias_id}")
                            else:
                                # Se não retornou ID, usar 0 (pode ser o primeiro alias)
                                alias_id = 0
                                alias.pf_id = 0
                                logger.info(f"✅ Alias '{alias_name}' criado no pfSense (ID não retornado, usando 0)")
                        else:
                            # Se o erro for que o alias já existe, buscar novamente
                            error_msg = str(create_result)
                            if "must be unique" in error_msg or "already exists" in error_msg.lower() or "FIELD_MUST_BE_UNIQUE" in error_msg:
                                logger.info(f"ℹ️ Alias '{alias_name}' já existe no pfSense, buscando novamente...")
                                pfsense_alias = obter_alias_pfsense(
                                    name=alias_name,
                                    user_id=self.user_id,
                                    institution_id=self.institution_id
                                )
                                if pfsense_alias and isinstance(pfsense_alias, dict):
                                    alias_id = pfsense_alias.get('id', 0)
                                    alias.pf_id = alias_id
                                    logger.info(f"✅ Alias '{alias_name}' encontrado no pfSense com ID: {alias_id}")
                                else:
                                    raise ValueError(f"Erro ao criar alias no pfSense: {create_result}")
                            else:
                                raise ValueError(f"Erro ao criar alias no pfSense: {create_result}")
                    except Exception as create_error:
                        # Se falhou ao criar, verificar se já existe
                        error_str = str(create_error)
                        if "must be unique" in error_str or "already exists" in error_str.lower() or "FIELD_MUST_BE_UNIQUE" in error_str or "400" in error_str:
                            logger.info(f"ℹ️ Alias '{alias_name}' já existe no pfSense, buscando novamente...")
                            pfsense_alias = obter_alias_pfsense(
                                name=alias_name,
                                user_id=self.user_id,
                                institution_id=self.institution_id
                            )
                            if pfsense_alias and isinstance(pfsense_alias, dict):
                                alias_id = pfsense_alias.get('id', 0)
                                alias.pf_id = alias_id
                                logger.info(f"✅ Alias '{alias_name}' encontrado no pfSense com ID: {alias_id}")
                            else:
                                raise ValueError(f"Não foi possível encontrar o alias '{alias_name}' no pfSense após erro de criação: {create_error}")
                        else:
                            raise ValueError(f"Erro ao criar alias no pfSense: {create_error}")
                
                pfsense_result = atualizar_alias_pfsense(
                    alias_id=alias_id,
                    name=alias_name,
                    address=current_addresses,
                    detail=current_details,
                    user_id=self.user_id,
                    institution_id=self.institution_id
                )
                
                if pfsense_result.get('status') != 'ok':
                    raise ValueError(f"Erro ao atualizar alias no pfSense: {pfsense_result}")
                
                logger.info(f"Alias {alias_name} atualizado no pfSense com sucesso")
                
                # Aplicar mudanças no firewall do pfSense
                try:
                    from services_firewalls.pfsense_client import aplicar_mudancas_firewall_pfsense
                    aplicar_mudancas_firewall_pfsense(
                        user_id=self.user_id,
                        institution_id=self.institution_id
                    )
                    logger.info(f"Mudanças aplicadas no firewall após adicionar endereços ao alias '{alias_name}'")
                except Exception as apply_error:
                    logger.error(f"Erro ao aplicar mudanças no firewall: {apply_error}")
                    # Não falha a operação se a aplicação das mudanças falhar
            
            self.db.commit()
            
            # Retornar dados atualizados
            return {
                'success': True,
                'message': f'Adicionados {len(addresses_to_add)} novos endereços ao alias',
                'alias_id': alias.id,
                'name': alias.name,
                'addresses_added': addresses_to_add,
                'total_addresses': len(current_addresses),
                'updated_at': alias.updated_at,
                'pfsense_updated': bool(addresses_to_add)
            }
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            self.db.rollback()
            logger.error(f"Timeout/Conexão ao adicionar endereços ao alias no pfSense: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao adicionar endereços ao alias: {e}")
            raise
