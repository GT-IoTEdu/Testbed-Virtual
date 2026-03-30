"""
Serviço para integração com Suricata IDS/IPS
Conecta-se ao endpoint SSE do Suricata para receber alertas em tempo real
"""
import json
import logging
import requests
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import config

logger = logging.getLogger(__name__)


class SuricataService:
    """Serviço para comunicação com API do Suricata via SSE"""
    
    def __init__(self, suricata_base_url: Optional[str] = None, api_key: Optional[str] = None,
                 user_id: Optional[int] = None, institution_id: Optional[int] = None):
        """Inicializa o serviço Suricata"""
        # Se configurações foram fornecidas diretamente, usar
        if suricata_base_url and api_key:
            self.base_url = suricata_base_url.rstrip('/')
            self.api_key = api_key
            logger.info(f"🔧 Suricata Service configurado com parâmetros diretos - URL: {self.base_url}")
        else:
            # Buscar do banco de dados
            institution_config = self._get_institution_config(user_id, institution_id)
            
            if institution_config:
                logger.info(f"✅ [SuricataService] Configuração da instituição encontrada")
                suricata_base_url_raw = institution_config.get('suricata_base_url')
                suricata_key_raw = institution_config.get('suricata_key')
                
                logger.info(f"🔍 [SuricataService] Valores brutos do banco:")
                logger.info(f"   suricata_base_url (raw): {repr(suricata_base_url_raw)}")
                logger.info(f"   suricata_key (raw): {'***' if suricata_key_raw else 'None/Empty'}")
                
                # Tratar None e strings vazias corretamente
                if suricata_base_url_raw and isinstance(suricata_base_url_raw, str):
                    suricata_base_url = suricata_base_url_raw.strip()
                else:
                    suricata_base_url = None
                    
                if suricata_key_raw and isinstance(suricata_key_raw, str):
                    suricata_key = suricata_key_raw.strip()
                else:
                    suricata_key = None
                
                logger.info(f"🔍 [SuricataService] Valores processados:")
                logger.info(f"   suricata_base_url (processed): {repr(suricata_base_url)}")
                logger.info(f"   suricata_key (processed): {'***' if suricata_key else 'None/Empty'}")
                
                if suricata_base_url and suricata_key:
                    self.base_url = suricata_base_url.rstrip('/')
                    self.api_key = suricata_key
                    logger.info(f"✅ Suricata Service configurado do banco (institution_id={institution_config.get('institution_id')}) - URL: {self.base_url}")
                else:
                    logger.warning(f"⚠️ Suricata não configurado para instituição {institution_config.get('institution_id')}")
                    logger.warning(f"   suricata_base_url: {'✅' if suricata_base_url else '❌ NÃO CONFIGURADO OU VAZIO'}")
                    logger.warning(f"   suricata_key: {'✅' if suricata_key else '❌ NÃO CONFIGURADO OU VAZIO'}")
                    self.base_url = None
                    self.api_key = None
            else:
                logger.warning(f"⚠️ Instituição não encontrada - Suricata não configurado (user_id={user_id}, institution_id={institution_id})")
                self.base_url = None
                self.api_key = None
        
        self.timeout = 30
        
        if not self.api_key:
            logger.warning(f"⚠️ API key do Suricata não configurada!")
    
    def _get_institution_config(self, user_id: Optional[int] = None, institution_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Busca configurações da instituição do banco de dados"""
        try:
            from services_firewalls.institution_config_service import InstitutionConfigService
            
            logger.debug(f"🔍 [SuricataService] Buscando configurações - user_id: {user_id}, institution_id: {institution_id}")
            
            if user_id:
                config = InstitutionConfigService.get_user_institution_config(user_id=user_id)
                logger.debug(f"🔍 [SuricataService] Config retornado para user_id {user_id}: {config is not None}")
                if config:
                    logger.debug(f"🔍 [SuricataService] suricata_base_url: {repr(config.get('suricata_base_url'))}")
                    logger.debug(f"🔍 [SuricataService] suricata_key: {'***' if config.get('suricata_key') else 'None/Empty'}")
                return config
            elif institution_id:
                config = InstitutionConfigService.get_institution_config(institution_id)
                logger.debug(f"🔍 [SuricataService] Config retornado para institution_id {institution_id}: {config is not None}")
                if config:
                    logger.debug(f"🔍 [SuricataService] suricata_base_url: {repr(config.get('suricata_base_url'))}")
                    logger.debug(f"🔍 [SuricataService] suricata_key: {'***' if config.get('suricata_key') else 'None/Empty'}")
                return config
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar configurações da instituição: {e}", exc_info=True)
            return None
    
    def get_sse_url(self) -> Optional[str]:
        """Retorna a URL do endpoint SSE do Suricata"""
        if not self.base_url or not self.api_key:
            logger.warning(f"⚠️ Suricata não configurado - base_url: {self.base_url}, api_key: {'***' if self.api_key else 'None'}")
            return None
        
        # URL do formato: http://192.168.1.128:8001/sse/alerts?api_key=...
        sse_url = f"{self.base_url}/sse/alerts?api_key={self.api_key}"
        logger.debug(f"🔗 URL SSE do Suricata construída: {sse_url.replace(self.api_key, '***')}")
        return sse_url
    
    def test_connection(self) -> Dict[str, Any]:
        """Testa a conexão com o Suricata"""
        if not self.base_url or not self.api_key:
            return {
                'success': False,
                'message': 'Suricata não configurado para esta instituição. Configure suricata_base_url e suricata_key no cadastro da instituição.',
                'configured': False
            }
        
        try:
            # Tentar fazer uma requisição GET simples para verificar se o servidor responde
            url = f"{self.base_url}/sse/alerts?api_key={self.api_key}"
            masked_url = url.replace(self.api_key, '***')
            logger.info(f"🔍 Testando conexão com Suricata: {masked_url}")
            
            response = requests.get(url, timeout=10, stream=True)
            
            logger.info(f"🔍 Resposta do Suricata - Status: {response.status_code}, Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            
            # Para SSE, esperamos status 200 e content-type text/event-stream
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'text/event-stream' in content_type:
                    logger.info("✅ Conexão com Suricata estabelecida com sucesso")
                    return {
                        'success': True,
                        'message': 'Conexão com Suricata estabelecida com sucesso',
                        'configured': True,
                        'url': masked_url,
                        'server_ip': self.base_url.split('//')[1].split(':')[0] if '//' in self.base_url else 'N/A'
                    }
                else:
                    logger.warning(f"⚠️ Resposta recebida mas formato incorreto. Content-Type: {content_type}")
                    return {
                        'success': False,
                        'message': f'Resposta recebida mas formato incorreto. Content-Type: {content_type}. Esperado: text/event-stream',
                        'configured': True,
                        'url': masked_url
                    }
            elif response.status_code == 403:
                logger.error("❌ Erro 403: API key inválida ou não autorizada")
                return {
                    'success': False,
                    'message': 'Erro 403: API key inválida ou não autorizada. Verifique se a chave está correta no cadastro da instituição.',
                    'configured': True,
                    'url': masked_url
                }
            else:
                logger.error(f"❌ Erro HTTP {response.status_code} ao conectar com Suricata")
                return {
                    'success': False,
                    'message': f'Erro ao conectar: Status {response.status_code}',
                    'configured': True,
                    'url': masked_url
                }
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout ao conectar com Suricata em {self.base_url}")
            return {
                'success': False,
                'message': f'Timeout ao conectar com Suricata em {self.base_url}. Verifique se o servidor está acessível e a porta 8001 está aberta.',
                'configured': True
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Erro de conexão com Suricata: {e}")
            return {
                'success': False,
                'message': f'Erro de conexão: Não foi possível conectar ao servidor Suricata em {self.base_url}. Verifique:\n' +
                          f'1. Se o servidor está rodando (uvicorn suricata_api:app --host 0.0.0.0 --port 8001)\n' +
                          f'2. Se o IP {self.base_url.split("//")[1].split(":")[0] if "//" in self.base_url else "N/A"} está acessível do backend\n' +
                          f'3. Se há firewall bloqueando a conexão na porta 8001',
                'configured': True
            }
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao testar conexão com Suricata: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Erro inesperado: {str(e)}',
                'configured': True
            }
    
    def parse_alert(self, alert_data: str) -> Optional[Dict[str, Any]]:
        """Parseia um alerta do Suricata recebido via SSE"""
        try:
            # O formato do SSE é: "data: {json}\n\n"
            # Pode vir com ou sem o prefixo "data: "
            json_str = alert_data
            
            # Remover prefixo "data: " se existir
            if json_str.startswith('data: '):
                json_str = json_str[6:].strip()
            
            # Remover quebras de linha extras
            json_str = json_str.strip()
            
            if json_str:
                alert = json.loads(json_str)
                normalized = self._normalize_alert(alert)
                logger.debug(f"Alerta parseado: {normalized.get('signature', 'N/A')}")
                return normalized
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Erro ao parsear JSON do alerta do Suricata: {e} - Dados: {alert_data[:100]}")
            return None
        except Exception as e:
            logger.error(f"Erro ao processar alerta do Suricata: {e}", exc_info=True)
            return None
    
    def _normalize_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza um alerta do Suricata para formato padrão"""
        # O formato do servidor Suricata é:
        # {
        #   "timestamp": "01/26/2026-10:30:45.123456",
        #   "sid": "**" ou "2000001",
        #   "message": "[1:2017515:8] ET INFO User-Agent (python-requests) Inbound to Webserver",
        #   "protocol": "TCP",
        #   "src": "192.168.1.122:33345",
        #   "dst": "192.168.1.128:8001"
        # }
        
        # Extrair IPs e portas de src e dst
        src = alert.get('src', '')
        dst = alert.get('dst', '')
        
        src_parts = src.split(':') if src else []
        dst_parts = dst.split(':') if dst else []
        
        src_ip = src_parts[0] if len(src_parts) > 0 else ''
        src_port = src_parts[1] if len(src_parts) > 1 else ''
        dest_ip = dst_parts[0] if len(dst_parts) > 0 else ''
        dest_port = dst_parts[1] if len(dst_parts) > 1 else ''
        
        # Normalizar timestamp (formato: 01/26/2026-10:30:45.123456)
        timestamp = alert.get('timestamp', '')
        try:
            # Converter para formato ISO se possível
            if timestamp:
                # Formato: MM/DD/YYYY-HH:MM:SS.microseconds
                from datetime import datetime
                try:
                    # Tentar com e sem microssegundos
                    if '.' in timestamp:
                        dt = datetime.strptime(timestamp, '%m/%d/%Y-%H:%M:%S.%f')
                    else:
                        dt = datetime.strptime(timestamp, '%m/%d/%Y-%H:%M:%S')
                    timestamp = dt.isoformat()
                except Exception as e:
                    logger.debug(f"Erro ao converter timestamp {timestamp}: {e}")
                    # Manter formato original se não conseguir converter
        except:
            timestamp = datetime.now().isoformat()
        
        # Extrair informações do message (pode conter signature ID)
        message = alert.get('message', 'Alerta do Suricata')
        signature_id = alert.get('sid', '')
        
        # Se sid é "**", tentar extrair do message
        if signature_id == '**' and message:
            # Formato: [1:2017515:8] ET INFO ...
            match = re.search(r'\[(\d+):(\d+):(\d+)\]', message)
            if match:
                signature_id = match.group(2)  # Pegar o ID do meio (ex: 2017515)
                logger.debug(f"📡 Signature ID extraído do message: {signature_id}")
        
        normalized = {
            'raw': alert,
            'timestamp': timestamp,
            'src_ip': src_ip,
            'dest_ip': dest_ip,
            'src_port': src_port,
            'dest_port': dest_port,
            'protocol': alert.get('protocol', ''),
            'signature_id': signature_id,
            'signature': message,
            'category': '',  # Não disponível no formato atual
            'severity': self._determine_severity(alert),
            'message': message,
        }
        
        return normalized
    
    def _determine_severity(self, alert: Dict[str, Any]) -> str:
        """Determina a severidade do alerta baseado nos dados do Suricata"""
        # No formato atual, não temos severidade explícita
        # Vamos usar heurísticas baseadas no tipo de alerta
        
        message = str(alert.get('message', '')).upper()
        sid = str(alert.get('sid', ''))
        
        # Alertas críticos comuns
        critical_keywords = ['MALWARE', 'EXPLOIT', 'TROJAN', 'VIRUS', 'RANSOMWARE', 'BACKDOOR', 
                           'COMMAND INJECTION', 'CODE INJECTION', 'REMOTE CODE EXECUTION', 'RCE']
        
        # Alertas de alta severidade - inclui SQL injection e outros ataques web
        high_keywords = ['ATTACK', 'INTRUSION', 'SCAN', 'PROBE', 'SUSPICIOUS',
                        'SQL INJECTION', 'SQLI', 'XSS', 'CROSS-SITE SCRIPTING',
                        'PATH TRAVERSAL', 'DIRECTORY TRAVERSAL', 'FILE INCLUSION',
                        'LFI', 'RFI', 'XXE', 'XML EXTERNAL ENTITY',
                        'MYSQL', 'SQL', 'INJECTION', 'BENCHMARK COMMAND',
                        'COMMAND IN URI', 'SQL COMMENTS', 'UNION SELECT',
                        'AUTHENTICATION BYPASS', 'PRIVILEGE ESCALATION',
                        'BUFFER OVERFLOW', 'STACK OVERFLOW', 'HEAP OVERFLOW',
                        'DENIAL OF SERVICE', 'DOS', 'DDOS', 'FLOOD']
        
        medium_keywords = ['POLICY', 'INFO', 'NOTICE', 'DNS TUNNELING']
        
        # Verificar se é SQL injection específico
        if 'SQL' in message and ('INJECTION' in message or 'MYSQL' in message or 'BENCHMARK' in message or 'COMMENTS' in message):
            return 'high'
        
        if any(keyword in message for keyword in critical_keywords):
            return 'critical'
        elif any(keyword in message for keyword in high_keywords):
            return 'high'
        elif any(keyword in message for keyword in medium_keywords):
            return 'medium'
        else:
            # Por padrão, considerar como médio se não conseguir determinar
            return 'medium'
