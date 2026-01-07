"""
Serviço para atribuição automática de endereços IP
"""
import ipaddress
import logging
from typing import List, Set, Optional, Tuple
from datetime import datetime
import config
from db.models import DhcpStaticMapping
from db.session import SessionLocal

logger = logging.getLogger(__name__)

class IPAssignmentService:
    """Serviço para gerenciar atribuição automática de IPs"""
    
    def __init__(self):
        self.range_start = config.IP_RANGE_START
        self.range_end = config.IP_RANGE_END
        self.excluded_ips = self._parse_excluded_ips(config.IP_RANGE_EXCLUDED)
        self.assigned_ips: Set[str] = set()
        self.last_assigned_ip: Optional[str] = None
        
        # Carregar IPs existentes do banco de dados
        self.load_existing_assignments_from_db()
        
    def _parse_excluded_ips(self, excluded_str: str) -> Set[str]:
        """Converte string de IPs excluídos em set"""
        if not excluded_str:
            return set()
        
        excluded = set()
        for ip_str in excluded_str.split(','):
            ip_str = ip_str.strip()
            if ip_str:
                try:
                    # Valida se é um IP válido
                    ipaddress.ip_address(ip_str)
                    excluded.add(ip_str)
                except ValueError:
                    logger.warning(f"IP excluído inválido ignorado: {ip_str}")
        
        return excluded
    
    def _ip_to_int(self, ip: str) -> int:
        """Converte IP string para inteiro"""
        return int(ipaddress.ip_address(ip))
    
    def _int_to_ip(self, ip_int: int) -> str:
        """Converte inteiro para IP string"""
        return str(ipaddress.ip_address(ip_int))
    
    def _is_ip_in_range(self, ip: str) -> bool:
        """Verifica se IP está no range configurado"""
        try:
            ip_int = self._ip_to_int(ip)
            start_int = self._ip_to_int(self.range_start)
            end_int = self._ip_to_int(self.range_end)
            return start_int <= ip_int <= end_int
        except ValueError:
            return False
    
    def _is_ip_in_range_inclusive(self, ip: str) -> bool:
        """Verifica se IP está no range configurado (incluindo IPs excluídos para validação)"""
        try:
            ip_int = self._ip_to_int(ip)
            start_int = self._ip_to_int(self.range_start)
            end_int = self._ip_to_int(self.range_end)
            return start_int <= ip_int <= end_int
        except ValueError:
            return False
    
    def _is_ip_excluded(self, ip: str) -> bool:
        """Verifica se IP está na lista de excluídos"""
        return ip in self.excluded_ips
    
    def _is_ip_assigned(self, ip: str) -> bool:
        """Verifica se IP já foi atribuído"""
        return ip in self.assigned_ips
    
    def _is_ip_available(self, ip: str) -> bool:
        """Verifica se IP está disponível para atribuição"""
        return (
            self._is_ip_in_range(ip) and
            not self._is_ip_excluded(ip) and
            not self._is_ip_assigned(ip)
        )
    
    def get_available_ips(self, count: int = 10) -> List[str]:
        """Retorna lista de IPs disponíveis no range"""
        available_ips = []
        start_int = self._ip_to_int(self.range_start)
        end_int = self._ip_to_int(self.range_end)
        
        # Se temos um último IP atribuído, começar a busca a partir dele
        if self.last_assigned_ip:
            try:
                current_int = self._ip_to_int(self.last_assigned_ip)
                # Começar do próximo IP
                current_int += 1
            except ValueError:
                current_int = start_int
        else:
            current_int = start_int
        
        # Buscar IPs disponíveis
        for i in range(end_int - start_int + 1):
            if len(available_ips) >= count:
                break
                
            # Circular no range se necessário
            check_int = start_int + ((current_int - start_int + i) % (end_int - start_int + 1))
            ip = self._int_to_ip(check_int)
            
            if self._is_ip_available(ip):
                available_ips.append(ip)
        
        return available_ips
    
    def assign_next_available_ip(self) -> Optional[str]:
        """Atribui o próximo IP disponível"""
        available_ips = self.get_available_ips(count=1)
        
        if not available_ips:
            logger.warning("Nenhum IP disponível no range configurado")
            return None
        
        assigned_ip = available_ips[0]
        self.assigned_ips.add(assigned_ip)
        self.last_assigned_ip = assigned_ip
        
        logger.info(f"IP {assigned_ip} atribuído automaticamente")
        return assigned_ip
    
    def release_ip(self, ip: str) -> bool:
        """Libera um IP que foi atribuído"""
        if ip in self.assigned_ips:
            self.assigned_ips.remove(ip)
            logger.info(f"IP {ip} liberado")
            return True
        return False
    
    def reserve_ip(self, ip: str) -> bool:
        """Reserva um IP específico (marca como atribuído)"""
        if self._is_ip_available(ip):
            self.assigned_ips.add(ip)
            self.last_assigned_ip = ip
            logger.info(f"IP {ip} reservado")
            return True
        else:
            logger.warning(f"IP {ip} não está disponível para reserva")
            return False
    
    def get_range_info(self) -> dict:
        """Retorna informações sobre o range configurado"""
        start_int = self._ip_to_int(self.range_start)
        end_int = self._ip_to_int(self.range_end)
        total_ips = end_int - start_int + 1
        available_count = len(self.get_available_ips(count=total_ips))
        assigned_count = len(self.assigned_ips)
        excluded_count = len(self.excluded_ips)
        
        return {
            "range_start": self.range_start,
            "range_end": self.range_end,
            "total_ips": total_ips,
            "assigned_ips": assigned_count,
            "excluded_ips": excluded_count,
            "available_ips": available_count,
            "excluded_list": list(self.excluded_ips),
            "assigned_list": list(self.assigned_ips)
        }
    
    def validate_ip_range(self) -> Tuple[bool, str]:
        """Valida se o range de IPs está configurado corretamente"""
        try:
            # Validar IPs de início e fim
            start_ip = ipaddress.ip_address(self.range_start)
            end_ip = ipaddress.ip_address(self.range_end)
            
            if start_ip >= end_ip:
                return False, "IP de início deve ser menor que IP de fim"
            
            # Validar IPs excluídos
            for excluded_ip in self.excluded_ips:
                try:
                    ip = ipaddress.ip_address(excluded_ip)
                    if not self._is_ip_in_range_inclusive(excluded_ip):
                        return False, f"IP excluído {excluded_ip} está fora do range"
                except ValueError:
                    return False, f"IP excluído inválido: {excluded_ip}"
            
            return True, "Range de IPs configurado corretamente"
            
        except ValueError as e:
            return False, f"Erro na configuração do range: {str(e)}"
    
    def load_existing_assignments(self, existing_ips: List[str]) -> None:
        """Carrega IPs já atribuídos (ex: do banco de dados)"""
        for ip in existing_ips:
            if self._is_ip_in_range(ip) and not self._is_ip_excluded(ip):
                self.assigned_ips.add(ip)
        
        logger.info(f"Carregados {len(existing_ips)} IPs existentes")
    
    def load_existing_assignments_from_db(self) -> None:
        """Carrega IPs já atribuídos do banco de dados (dhcp_static_mappings)"""
        try:
            db = SessionLocal()
            try:
                existing_mappings = db.query(DhcpStaticMapping).all()
                
                loaded_count = 0
                for mapping in existing_mappings:
                    if mapping.ipaddr and self._is_ip_in_range(mapping.ipaddr) and not self._is_ip_excluded(mapping.ipaddr):
                        self.assigned_ips.add(mapping.ipaddr)
                        loaded_count += 1
                
                logger.info(f"Carregados {loaded_count} IPs existentes do banco de dados")
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Erro ao carregar IPs existentes do banco: {e}")
            # Continuar sem falhar, apenas log do erro
    
    def refresh_from_db(self) -> None:
        """Recarrega IPs existentes do banco de dados"""
        self.assigned_ips.clear()
        self.load_existing_assignments_from_db()
        logger.info("IPs recarregados do banco de dados")
    
    def get_suggested_ips(self, count: int = 5) -> List[dict]:
        """Retorna sugestões de IPs com informações adicionais"""
        available_ips = self.get_available_ips(count)
        suggestions = []
        
        for ip in available_ips:
            suggestions.append({
                "ip": ip,
                "available": True,
                "reason": "Disponível no range configurado"
            })
        
        return suggestions

# Instância global do serviço
ip_assignment_service = IPAssignmentService()
