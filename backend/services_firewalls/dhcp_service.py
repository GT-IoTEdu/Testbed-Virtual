"""
Serviço para gerenciamento de dados DHCP no banco de dados.

Este módulo fornece funcionalidades para:
- Salvar dados de servidores DHCP do pfSense no banco
- Salvar mapeamentos estáticos DHCP
- Consultar dispositivos por IP, MAC ou descrição
- Identificar dispositivos já cadastrados
- Sincronizar IDs do pfSense com o banco local
"""
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from db.session import SessionLocal
from db.models import DhcpServer, DhcpStaticMapping
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DhcpService:
    """Serviço para gerenciamento de dados DHCP."""
    
    def __init__(self):
        self.db: Session = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def sync_pfsense_ids(self, dhcp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sincroniza os IDs do pfSense com os pf_id do banco de dados local.
        
        Args:
            dhcp_data: Dados retornados pela API do pfSense
            
        Returns:
            Dict com estatísticas da sincronização
        """
        try:
            synced_count = 0
            created_count = 0
            updated_count = 0
            
            for server_data in dhcp_data.get('data', []):
                server_id = server_data.get('id')
                
                # Buscar ou criar servidor DHCP local
                server = self.db.query(DhcpServer).filter(
                    DhcpServer.server_id == server_id
                ).first()
                
                if not server:
                    # Criar servidor se não existir
                    server = DhcpServer(
                        server_id=server_id,
                        interface=server_data.get('interface', ''),
                        enable=server_data.get('enable', False),
                        range_from=server_data.get('range_from'),
                        range_to=server_data.get('range_to'),
                        domain=server_data.get('domain'),
                        gateway=server_data.get('gateway'),
                        dnsserver=server_data.get('dnsserver')
                    )
                    self.db.add(server)
                    self.db.flush()
                    created_count += 1
                
                # Sincronizar mapeamentos estáticos
                static_maps = server_data.get('staticmap', [])
                for mapping_data in static_maps:
                    result = self._sync_static_mapping(server.id, mapping_data)
                    if result['action'] == 'synced':
                        synced_count += 1
                    elif result['action'] == 'created':
                        created_count += 1
                    elif result['action'] == 'updated':
                        updated_count += 1
            
            self.db.commit()
            
            return {
                'status': 'success',
                'servers_created': created_count,
                'mappings_synced': synced_count,
                'mappings_created': created_count,
                'mappings_updated': updated_count,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao sincronizar IDs do pfSense: {e}")
            raise
    
    def _sync_static_mapping(self, server_id: int, mapping_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Sincroniza um mapeamento estático DHCP com o ID real do pfSense.
        Usa a mesma lógica do _save_static_mapping para evitar duplicatas.
        
        Args:
            server_id: ID do servidor DHCP local
            mapping_data: Dados do mapeamento do pfSense
            
        Returns:
            Dict com ação realizada e mapeamento
        """
        # Usar a mesma lógica do _save_static_mapping para consistência
        return self._save_static_mapping(server_id, mapping_data)
    
    def save_dhcp_data(self, dhcp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Salva dados de DHCP do pfSense no banco de dados.
        
        Args:
            dhcp_data: Dados retornados pela API do pfSense
            
        Returns:
            Dict com estatísticas da operação
        """
        try:
            servers_saved = 0
            mappings_saved = 0
            mappings_updated = 0
            
            for server_data in dhcp_data.get('data', []):
                # Salvar ou atualizar servidor DHCP
                server = self._save_dhcp_server(server_data)
                servers_saved += 1
                
                # Salvar mapeamentos estáticos
                static_maps = server_data.get('staticmap', [])
                for mapping_data in static_maps:
                    result = self._save_static_mapping(server.id, mapping_data)
                    if result['action'] == 'created':
                        mappings_saved += 1
                    elif result['action'] == 'updated':
                        mappings_updated += 1
            
            self.db.commit()
            
            return {
                'status': 'success',
                'servers_saved': servers_saved,
                'mappings_saved': mappings_saved,
                'mappings_updated': mappings_updated,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao salvar dados DHCP: {e}")
            raise
    
    def _save_dhcp_server(self, server_data: Dict[str, Any]) -> DhcpServer:
        """Salva ou atualiza um servidor DHCP."""
        server_id = server_data.get('id')
        
        # Verificar se o servidor já existe
        server = self.db.query(DhcpServer).filter(DhcpServer.server_id == server_id).first()
        
        if server:
            # Atualizar servidor existente
            server.interface = server_data.get('interface', '')
            server.enable = server_data.get('enable', False)
            server.range_from = server_data.get('range_from')
            server.range_to = server_data.get('range_to')
            server.domain = server_data.get('domain')
            server.gateway = server_data.get('gateway')
            server.dnsserver = server_data.get('dnsserver')
            server.updated_at = datetime.now()
        else:
            # Criar novo servidor
            server = DhcpServer(
                server_id=server_id,
                interface=server_data.get('interface', ''),
                enable=server_data.get('enable', False),
                range_from=server_data.get('range_from'),
                range_to=server_data.get('range_to'),
                domain=server_data.get('domain'),
                gateway=server_data.get('gateway'),
                dnsserver=server_data.get('dnsserver')
            )
            self.db.add(server)
        
        self.db.flush()  # Para obter o ID
        return server
    
    def _save_static_mapping(self, server_id: int, mapping_data: Dict[str, Any]) -> Dict[str, str]:
        """Salva ou atualiza um mapeamento estático DHCP."""
        mac = mapping_data.get('mac')
        ipaddr = mapping_data.get('ipaddr')
        pf_id = mapping_data.get('id')  # ID do pfSense (não persistente, apenas para referência)
        
        # Buscar por MAC/IP (identificadores únicos e persistentes)
        existing_mapping = self.db.query(DhcpStaticMapping).filter(
            or_(
                DhcpStaticMapping.mac == mac,
                DhcpStaticMapping.ipaddr == ipaddr
            )
        ).first()
        
        if existing_mapping:
            # Atualizar mapeamento existente
            existing_mapping.pf_id = pf_id  # Atualizar pf_id atual (pode mudar)
            existing_mapping.server_id = server_id
            existing_mapping.mac = mac
            existing_mapping.ipaddr = ipaddr
            existing_mapping.cid = mapping_data.get('cid')
            existing_mapping.hostname = mapping_data.get('hostname')
            existing_mapping.descr = mapping_data.get('descr')
            existing_mapping.updated_at = datetime.now()
            action = 'updated'
            logger.info(f"Atualizando mapeamento existente: MAC={mac}, IP={ipaddr}, pf_id={pf_id}")
            mapping = existing_mapping
        else:
            # Criar novo mapeamento
            mapping = DhcpStaticMapping(
                server_id=server_id,
                pf_id=pf_id,  # Usar pf_id atual (pode ser None se não disponível)
                mac=mac,
                ipaddr=ipaddr,
                cid=mapping_data.get('cid'),
                hostname=mapping_data.get('hostname'),
                descr=mapping_data.get('descr')
            )
            self.db.add(mapping)
            action = 'created'
            logger.info(f"Criando novo mapeamento: MAC={mac}, IP={ipaddr}, pf_id={pf_id}")
        
        return {'action': action, 'mapping': mapping}
    
    def find_device_by_ip(self, ipaddr: str) -> Optional[DhcpStaticMapping]:
        """Busca dispositivo por endereço IP."""
        return self.db.query(DhcpStaticMapping).filter(
            DhcpStaticMapping.ipaddr == ipaddr
        ).first()
    
    def find_device_by_mac(self, mac: str) -> Optional[DhcpStaticMapping]:
        """Busca dispositivo por endereço MAC."""
        return self.db.query(DhcpStaticMapping).filter(
            DhcpStaticMapping.mac == mac
        ).first()
    
    def find_device_by_description(self, descr: str) -> List[DhcpStaticMapping]:
        """Busca dispositivos por descrição (busca parcial)."""
        return self.db.query(DhcpStaticMapping).filter(
            DhcpStaticMapping.descr.contains(descr)
        ).all()
    
    def get_all_devices(self) -> List[DhcpStaticMapping]:
        """Retorna todos os dispositivos cadastrados."""
        return self.db.query(DhcpStaticMapping).all()
    
    def get_devices_by_server(self, server_id: str) -> List[DhcpStaticMapping]:
        """Retorna dispositivos de um servidor específico."""
        return self.db.query(DhcpStaticMapping).join(DhcpServer).filter(
            DhcpServer.server_id == server_id
        ).all()
    
    def search_devices(self, query: str) -> List[DhcpStaticMapping]:
        """
        Busca dispositivos por IP, MAC ou descrição.
        
        Args:
            query: Termo de busca
            
        Returns:
            Lista de dispositivos encontrados
        """
        return self.db.query(DhcpStaticMapping).filter(
            or_(
                DhcpStaticMapping.ipaddr.contains(query),
                DhcpStaticMapping.mac.contains(query),
                DhcpStaticMapping.descr.contains(query),
                DhcpStaticMapping.hostname.contains(query)
            )
        ).all()
    
    def get_device_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas dos dispositivos cadastrados."""
        total_devices = self.db.query(DhcpStaticMapping).count()
        total_servers = self.db.query(DhcpServer).count()
        
        # Contar dispositivos por servidor
        devices_by_server = {}
        servers = self.db.query(DhcpServer).all()
        for server in servers:
            count = self.db.query(DhcpStaticMapping).filter(
                DhcpStaticMapping.server_id == server.id
            ).count()
            devices_by_server[server.server_id] = count
        
        return {
            'total_devices': total_devices,
            'total_servers': total_servers,
            'devices_by_server': devices_by_server,
            'last_update': datetime.now().isoformat()
        }
    
    def get_ip_address_list(self, server_id: str = "lan", range_from: str = "10.30.30.1", range_to: str = "10.30.30.100") -> Dict[str, Any]:
        """
        Lista endereços IP usados e livres em um range DHCP.
        
        Args:
            server_id: ID do servidor DHCP
            range_from: IP inicial do range
            range_to: IP final do range
            
        Returns:
            Dict com informações do range e lista de IPs
        """
        import ipaddress
        
        try:
            # Buscar servidor DHCP
            server = self.db.query(DhcpServer).filter(DhcpServer.server_id == server_id).first()
            if not server:
                # Usar range padrão se servidor não encontrado
                pass
            else:
                # Se o range do servidor for muito pequeno (apenas um IP), usar range padrão
                if server.range_from == server.range_to:
                    range_from = "10.30.30.1"
                    range_to = "10.30.30.100"
                else:
                    range_from = server.range_from or range_from
                    range_to = server.range_to or range_to
            
            # Gerar lista de IPs no range
            start_ip = ipaddress.IPv4Address(range_from)
            end_ip = ipaddress.IPv4Address(range_to)
            
            # Buscar IPs usados no banco
            used_ips = {}
            static_mappings = self.db.query(DhcpStaticMapping).filter(
                DhcpStaticMapping.server_id == server.id if server else DhcpStaticMapping.server_id == 1
            ).all()
            
            for mapping in static_mappings:
                used_ips[mapping.ipaddr] = {
                    'mac': mapping.mac,
                    'hostname': mapping.hostname,
                    'description': mapping.descr,
                    'status': 'used'
                }
            
            # Gerar lista completa de IPs
            ip_list = []
            used_count = 0
            free_count = 0
            
            current_ip = start_ip
            while current_ip <= end_ip:
                ip_str = str(current_ip)
                
                if ip_str in used_ips:
                    # IP usado
                    ip_info = used_ips[ip_str]
                    ip_list.append({
                        'ip': ip_str,
                        'status': 'used',
                        'mac': ip_info['mac'],
                        'hostname': ip_info['hostname'],
                        'description': ip_info['description'],
                        'last_seen': None
                    })
                    used_count += 1
                else:
                    # IP livre
                    ip_list.append({
                        'ip': ip_str,
                        'status': 'free',
                        'mac': None,
                        'hostname': None,
                        'description': None,
                        'last_seen': None
                    })
                    free_count += 1
                
                current_ip += 1
            
            total_ips = len(ip_list)
            
            return {
                'range_info': {
                    'server_id': server_id,
                    'interface': server.interface if server else 'lan',
                    'range_from': range_from,
                    'range_to': range_to,
                    'total_ips': total_ips,
                    'used_ips': used_count,
                    'free_ips': free_count,
                    'reserved_ips': 0
                },
                'ip_addresses': ip_list,
                'summary': {
                    'total': total_ips,
                    'used': used_count,
                    'free': free_count,
                    'reserved': 0
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar lista de IPs: {e}")
            raise
