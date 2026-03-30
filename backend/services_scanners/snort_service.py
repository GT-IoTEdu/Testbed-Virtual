"""
Serviço para integração com Snort IDS/IPS
Conecta-se ao endpoint SSE do Snort para receber alertas em tempo real
"""
import json
import logging
import requests
import re
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SnortService:
    """Serviço para comunicação com API do Snort via SSE"""

    def __init__(
        self,
        snort_base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        user_id: Optional[int] = None,
        institution_id: Optional[int] = None,
    ):
        if snort_base_url and api_key:
            self.base_url = snort_base_url.rstrip("/")
            self.api_key = api_key
            logger.info(f"🔧 Snort Service configurado com parâmetros diretos - URL: {self.base_url}")
        else:
            institution_config = self._get_institution_config(user_id, institution_id)
            if institution_config:
                snort_base_url_raw = institution_config.get("snort_base_url")
                snort_key_raw = institution_config.get("snort_key")
                snort_base_url = snort_base_url_raw.strip() if snort_base_url_raw and isinstance(snort_base_url_raw, str) else None
                snort_key = snort_key_raw.strip() if snort_key_raw and isinstance(snort_key_raw, str) else None
                if snort_base_url and snort_key:
                    self.base_url = snort_base_url.rstrip("/")
                    self.api_key = snort_key
                    logger.info(f"✅ Snort Service configurado do banco (institution_id={institution_config.get('institution_id')}) - URL: {self.base_url}")
                else:
                    self.base_url = None
                    self.api_key = None
            else:
                self.base_url = None
                self.api_key = None
        self.timeout = 30

    def _get_institution_config(
        self, user_id: Optional[int] = None, institution_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        try:
            from services_firewalls.institution_config_service import InstitutionConfigService
            if user_id:
                return InstitutionConfigService.get_user_institution_config(user_id=user_id)
            if institution_id:
                return InstitutionConfigService.get_institution_config(institution_id)
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar configurações da instituição: {e}", exc_info=True)
            return None

    def get_sse_url(self) -> Optional[str]:
        """Retorna a URL do endpoint SSE do Snort (/sse/snort)."""
        if not self.base_url or not self.api_key:
            return None
        return f"{self.base_url}/sse/snort?api_key={self.api_key}"

    def test_connection(self) -> Dict[str, Any]:
        if not self.base_url or not self.api_key:
            return {
                "success": False,
                "message": "Snort não configurado para esta instituição. Configure snort_base_url e snort_key no cadastro da instituição.",
                "configured": False,
            }
        try:
            url = f"{self.base_url}/sse/snort?api_key={self.api_key}"
            response = requests.get(url, timeout=10, stream=True)
            if response.status_code == 200:
                ct = response.headers.get("Content-Type", "")
                if "text/event-stream" in ct:
                    return {
                        "success": True,
                        "message": "Conexão com Snort estabelecida com sucesso",
                        "configured": True,
                        "url": url.replace(self.api_key, "***"),
                        "server_ip": self.base_url.split("//")[1].split(":")[0] if "//" in self.base_url else "N/A",
                    }
                return {
                    "success": False,
                    "message": f"Content-Type inesperado: {ct}. Esperado: text/event-stream",
                    "configured": True,
                    "url": url.replace(self.api_key, "***"),
                }
            if response.status_code == 403:
                return {
                    "success": False,
                    "message": "Erro 403: API key inválida ou não autorizada.",
                    "configured": True,
                    "url": url.replace(self.api_key, "***"),
                }
            return {
                "success": False,
                "message": f"Erro HTTP {response.status_code}",
                "configured": True,
                "url": url.replace(self.api_key, "***"),
            }
        except requests.exceptions.Timeout:
            return {"success": False, "message": f"Timeout ao conectar com Snort em {self.base_url}", "configured": True}
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": f"Erro de conexão com Snort em {self.base_url}", "configured": True}
        except Exception as e:
            return {"success": False, "message": str(e), "configured": True}

    def _normalize_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza um alerta do Snort para formato padrão (mesmo do Suricata).
        Snort payload: timestamp (MM/DD-HH:MM:SS.microseconds sem ano), sid, message, protocol, src, dst.
        """
        src = alert.get("src", "")
        dst = alert.get("dst", "")
        src_parts = src.split(":") if src else []
        dst_parts = dst.split(":") if dst else []
        src_ip = src_parts[0] if len(src_parts) > 0 else ""
        src_port = src_parts[1] if len(src_parts) > 1 else ""
        dest_ip = dst_parts[0] if len(dst_parts) > 0 else ""
        dest_port = dst_parts[1] if len(dst_parts) > 1 else ""

        timestamp = alert.get("timestamp", "")
        try:
            if timestamp:
                # Snort: MM/DD-HH:MM:SS.microseconds (sem ano)
                year = datetime.now().year
                if "." in timestamp:
                    dt = datetime.strptime(timestamp, "%m/%d-%H:%M:%S.%f")
                else:
                    dt = datetime.strptime(timestamp, "%m/%d-%H:%M:%S")
                dt = dt.replace(year=year)
                timestamp = dt.isoformat()
        except Exception as e:
            logger.debug(f"Erro ao converter timestamp Snort {timestamp}: {e}")
            timestamp = datetime.now().isoformat()

        message = alert.get("message", "Alerta do Snort")
        signature_id = alert.get("sid", "")
        if signature_id == "**" and message:
            match = re.search(r"\[(\d+):(\d+):(\d+)\]", message)
            if match:
                signature_id = match.group(2)

        return {
            "raw": alert,
            "timestamp": timestamp,
            "src_ip": src_ip,
            "dest_ip": dest_ip,
            "src_port": src_port,
            "dest_port": dest_port,
            "protocol": alert.get("protocol", ""),
            "signature_id": signature_id,
            "signature": message,
            "category": "",
            "severity": self._determine_severity(alert),
            "message": message,
        }

    def _determine_severity(self, alert: Dict[str, Any]) -> str:
        """Determina a severidade do alerta (mesma lógica do Suricata)."""
        message = str(alert.get("message", "")).upper()
        critical_keywords = [
            "MALWARE", "EXPLOIT", "TROJAN", "VIRUS", "RANSOMWARE", "BACKDOOR",
            "COMMAND INJECTION", "CODE INJECTION", "REMOTE CODE EXECUTION", "RCE",
        ]
        high_keywords = [
            "ATTACK", "INTRUSION", "SCAN", "PROBE", "SUSPICIOUS",
            "SQL INJECTION", "SQLI", "XSS", "PATH TRAVERSAL", "FILE INCLUSION",
            "LFI", "RFI", "MYSQL", "SQL", "INJECTION", "BENCHMARK COMMAND",
            "AUTHENTICATION BYPASS", "PRIVILEGE ESCALATION",
            "BUFFER OVERFLOW", "DENIAL OF SERVICE", "DOS", "DDOS", "FLOOD",
        ]
        medium_keywords = ["POLICY", "INFO", "NOTICE", "DNS TUNNELING"]
        if "SQL" in message and ("INJECTION" in message or "MYSQL" in message or "BENCHMARK" in message):
            return "high"
        if any(k in message for k in critical_keywords):
            return "critical"
        if any(k in message for k in high_keywords):
            return "high"
        if any(k in message for k in medium_keywords):
            return "medium"
        return "medium"
