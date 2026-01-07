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
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
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
                # Normalizar pf_id (0 é válido no pfSense)
                raw_id = alias_data.get('id')
                normalized_pf_id = raw_id if (isinstance(raw_id, int) and raw_id >= 0) else None
                alias_name = alias_data['name']

                # 1) Procurar por nome (estável) primeiro
                record_by_name = (
                    self.db.query(PfSenseAlias)
                    .filter(PfSenseAlias.name == alias_name)
                    .first()
                )

                # 2) Procurar por pf_id (pode ter mudado de dono)
                record_by_pf_id = None
                if normalized_pf_id is not None:
                    record_by_pf_id = (
                        self.db.query(PfSenseAlias)
                        .filter(PfSenseAlias.pf_id == normalized_pf_id)
                        .first()
                    )

                if record_by_name:
                    existing_alias = record_by_name
                    # Se o pf_id atual pertence a outro registro, liberar o pf_id desse outro
                    if record_by_pf_id and record_by_pf_id.id != existing_alias.id:
                        record_by_pf_id.pf_id = None
                    # Atualizar pf_id no registro correto (por nome)
                    if normalized_pf_id is not None and existing_alias.pf_id != normalized_pf_id:
                        existing_alias.pf_id = normalized_pf_id
                    # Atualizar campos
                    existing_alias.alias_type = alias_data['type']
                    existing_alias.descr = alias_data.get('descr')
                    existing_alias.updated_at = datetime.utcnow()
                    aliases_updated += 1
                elif record_by_pf_id:
                    # Não existe por nome, mas existe por pf_id: renomear este registro para o nome atual
                    existing_alias = record_by_pf_id
                    existing_alias.name = alias_name
                    existing_alias.alias_type = alias_data['type']
                    existing_alias.descr = alias_data.get('descr')
                    existing_alias.updated_at = datetime.utcnow()
                    aliases_updated += 1
                else:
                    # Novo registro
                    new_alias = PfSenseAlias(
                        pf_id=normalized_pf_id,
                        name=alias_name,
                        alias_type=alias_data['type'],
                        descr=alias_data.get('descr')
                    )
                    self.db.add(new_alias)
                    self.db.flush()
                    aliases_saved += 1
                    existing_alias = new_alias
                
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
        
        Returns:
            Lista de aliases com endereços
        """
        try:
            aliases = self.db.query(PfSenseAlias).all()
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
        
        Args:
            name: Nome do alias
            
        Returns:
            Dados do alias ou None se não encontrado
        """
        try:
            alias = self.db.query(PfSenseAlias).filter(
                PfSenseAlias.name == name
            ).first()
            
            if not alias:
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
        
        Args:
            query: Termo de busca
            
        Returns:
            Lista de aliases encontrados
        """
        try:
            aliases = self.db.query(PfSenseAlias).filter(
                PfSenseAlias.name.contains(query) |
                PfSenseAlias.descr.contains(query)
            ).all()
            
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
        
        Returns:
            Estatísticas dos aliases
        """
        try:
            total_aliases = self.db.query(PfSenseAlias).count()
            total_addresses = self.db.query(PfSenseAliasAddress).count()
            
            # Contar por tipo
            aliases_by_type = {}
            type_counts = self.db.query(PfSenseAlias.alias_type).all()
            for alias_type in type_counts:
                type_name = alias_type[0]
                aliases_by_type[type_name] = aliases_by_type.get(type_name, 0) + 1
            
            # Contar criados hoje
            today = date.today()
            created_today = self.db.query(PfSenseAlias).filter(
                PfSenseAlias.created_at >= today
            ).count()
            
            # Contar atualizados hoje
            updated_today = self.db.query(PfSenseAlias).filter(
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
            # Verificar se já existe
            existing = self.db.query(PfSenseAlias).filter(
                PfSenseAlias.name == alias_data['name']
            ).first()
            
            if existing:
                raise ValueError(f"Alias '{alias_data['name']}' já existe")
            
            # Criar no pfSense primeiro
            pfsense_result = cadastrar_alias_pfsense(
                name=alias_data['name'],
                alias_type=alias_data['alias_type'],
                descr=alias_data['descr'],
                address=[addr['address'] for addr in alias_data['addresses']],
                detail=[addr.get('detail', '') for addr in alias_data['addresses']]
            )
            
            # Se sucesso no pfSense, salvar no banco
            if pfsense_result.get('status') == 'ok':
                # Buscar o ID do alias criado no pfSense
                pf_id = pfsense_result.get('result', {}).get('data', {}).get('id', 0)
                # Evitar colisão de índice único quando a API não retorna ID (id==0 ou ausente)
                if not pf_id or pf_id == 0:
                    pf_id = None
                
                new_alias = PfSenseAlias(
                    pf_id=pf_id,
                    name=alias_data['name'],
                    alias_type=alias_data['alias_type'],
                    descr=alias_data['descr']
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
                    aplicar_mudancas_firewall_pfsense()
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
            # Buscar o alias no banco de dados
            alias = self.db.query(PfSenseAlias).filter(
                PfSenseAlias.name == alias_name
            ).first()
            
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
                from services_firewalls.pfsense_client import atualizar_alias_pfsense
                
                # Usar o pf_id do alias para a atualização
                if alias.pf_id is None:
                    raise ValueError(f"Alias '{alias_name}' não possui pf_id válido para atualização no pfSense")
                
                pfsense_result = atualizar_alias_pfsense(
                    alias_id=alias.pf_id,
                    name=alias_name,
                    alias_type=pfsense_data.get('alias_type'),
                    descr=pfsense_data.get('descr'),
                    address=pfsense_data.get('address'),
                    detail=pfsense_data.get('detail')
                )
                
                if pfsense_result.get('status') != 'ok':
                    raise ValueError(f"Erro ao atualizar alias no pfSense: {pfsense_result}")
                
                # Aplicar mudanças no firewall do pfSense
                try:
                    from services_firewalls.pfsense_client import aplicar_mudancas_firewall_pfsense
                    aplicar_mudancas_firewall_pfsense()
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
            # Buscar o alias no banco de dados
            alias = self.db.query(PfSenseAlias).filter(
                PfSenseAlias.name == alias_name
            ).first()
            
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
                from services_firewalls.pfsense_client import atualizar_alias_pfsense
                
                # Se pf_id é None, tentar buscar o alias no pfSense pelo nome
                alias_id = alias.pf_id
                if alias_id is None:
                    logger.warning(f"Alias {alias_name} não tem pf_id, tentando buscar no pfSense pelo nome")
                    # Buscar alias no pfSense pelo nome para obter o ID
                    try:
                        from services_firewalls.pfsense_client import listar_aliases_pfsense
                        pfsense_aliases = listar_aliases_pfsense()
                        if isinstance(pfsense_aliases, dict) and 'data' in pfsense_aliases:
                            aliases_data = pfsense_aliases['data']
                        else:
                            aliases_data = pfsense_aliases
                        
                        for pfsense_alias in aliases_data:
                            if pfsense_alias.get('name') == alias_name:
                                alias_id = pfsense_alias.get('id')
                                # Atualizar pf_id no banco
                                alias.pf_id = alias_id
                                logger.info(f"pf_id {alias_id} encontrado para alias {alias_name}")
                                break
                        
                        if alias_id is None:
                            logger.error(f"Alias {alias_name} não encontrado no pfSense")
                            raise ValueError(f"Alias {alias_name} não encontrado no pfSense")
                            
                    except Exception as e:
                        logger.error(f"Erro ao buscar alias no pfSense: {e}")
                        raise ValueError(f"Erro ao buscar alias {alias_name} no pfSense: {e}")
                
                pfsense_result = atualizar_alias_pfsense(
                    alias_id=alias_id,
                    name=alias_name,
                    address=current_addresses,
                    detail=current_details
                )
                
                if pfsense_result.get('status') != 'ok':
                    raise ValueError(f"Erro ao atualizar alias no pfSense: {pfsense_result}")
                
                logger.info(f"Alias {alias_name} atualizado no pfSense com sucesso")
                
                # Aplicar mudanças no firewall do pfSense
                try:
                    from services_firewalls.pfsense_client import aplicar_mudancas_firewall_pfsense
                    aplicar_mudancas_firewall_pfsense()
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
