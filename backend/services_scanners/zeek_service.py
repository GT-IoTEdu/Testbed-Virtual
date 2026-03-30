"""
Serviço para integração com Zeek NSM (Network Security Monitor)
Conecta-se ao endpoint SSE do Zeek para receber alertas em tempo real (mesmo estilo Suricata/Snort).
"""
import json
import logging
import re
import requests
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ZeekService:
    """Serviço para comunicação com API do Zeek via SSE."""

    def __init__(
        self,
        zeek_base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        user_id: Optional[int] = None,
        institution_id: Optional[int] = None,
    ):
        if zeek_base_url and api_key:
            self.base_url = zeek_base_url.rstrip("/")
            self.api_key = api_key
            logger.info(f"🔧 Zeek Service configurado com parâmetros diretos - URL: {self.base_url}")
        else:
            institution_config = self._get_institution_config(user_id, institution_id)
            if institution_config:
                zeek_base_url_raw = institution_config.get("zeek_base_url")
                zeek_key_raw = institution_config.get("zeek_key")
                zeek_base_url = zeek_base_url_raw.strip() if zeek_base_url_raw and isinstance(zeek_base_url_raw, str) else None
                zeek_key = zeek_key_raw.strip() if zeek_key_raw and isinstance(zeek_key_raw, str) else None
                if zeek_base_url and zeek_key:
                    self.base_url = zeek_base_url.rstrip("/")
                    self.api_key = zeek_key
                    logger.info(f"✅ Zeek Service configurado do banco (institution_id={institution_config.get('institution_id')}) - URL: {self.base_url}")
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
        """Retorna a URL do endpoint SSE do Zeek (IDS API: /sse/zeek)."""
        if not self.base_url or not self.api_key:
            return None
        return f"{self.base_url}/sse/zeek?api_key={self.api_key}"

    def test_connection(self) -> Dict[str, Any]:
        if not self.base_url or not self.api_key:
            return {
                "success": False,
                "message": "Zeek não configurado para esta instituição. Configure zeek_base_url e zeek_key no cadastro da instituição.",
                "configured": False,
            }
        try:
            url = f"{self.base_url}/sse/zeek?api_key={self.api_key}"
            masked_url = url.replace(self.api_key, "***")
            logger.info(f"🔍 Testando conexão com Zeek: {masked_url}")
            response = requests.get(url, timeout=10, stream=True)
            if response.status_code == 200:
                ct = response.headers.get("Content-Type", "")
                if "text/event-stream" in ct:
                    logger.info("✅ Conexão com Zeek estabelecida com sucesso")
                    return {
                        "success": True,
                        "message": "Conexão com Zeek estabelecida com sucesso",
                        "configured": True,
                        "url": masked_url,
                        "server_ip": self.base_url.split("//")[1].split(":")[0] if "//" in self.base_url else "N/A",
                    }
                return {
                    "success": False,
                    "message": f"Content-Type inesperado: {ct}. Esperado: text/event-stream",
                    "configured": True,
                    "url": masked_url,
                }
            if response.status_code == 403:
                return {
                    "success": False,
                    "message": "Erro 403: API key inválida ou não autorizada.",
                    "configured": True,
                    "url": masked_url,
                }
            return {
                "success": False,
                "message": f"Erro HTTP {response.status_code}",
                "configured": True,
                "url": masked_url,
            }
        except requests.exceptions.Timeout:
            return {"success": False, "message": f"Timeout ao conectar com Zeek em {self.base_url}", "configured": True}
        except requests.exceptions.ConnectionError as e:
            return {
                "success": False,
                "message": f"Erro de conexão com Zeek em {self.base_url}. Verifique se o servidor está acessível.",
                "configured": True,
            }
        except Exception as e:
            return {"success": False, "message": str(e), "configured": True}

    def _normalize_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza um alerta do Zeek para formato padrão (mesmo do Suricata/Snort).
        Compatível com o payload da IDS SSE API, ex.:
        {"timestamp": "2026-02-06 17:31:36", "sid": "...", "note": "...", "message": "...",
         "severity": "HIGH", "protocol": "udp", "src": "192.168.59.1", "dst": "N/A" ou "192.168.59.103", "raw": {...}}
        """
        raw_obj = alert.get("raw") or {}
        src = alert.get("src") or raw_obj.get("src") or ""
        dst = alert.get("dst") or raw_obj.get("dst") or ""
        if not src and "id_orig_h" in alert:
            src = alert.get("id_orig_h", "") or ""
            if alert.get("id_orig_p") is not None:
                src = f"{src}:{alert.get('id_orig_p', '')}"
        if not dst and "id_resp_h" in alert:
            dst = alert.get("id_resp_h", "") or ""
            if alert.get("id_resp_p") is not None:
                dst = f"{dst}:{alert.get('id_resp_p', '')}"
        src_parts = src.split(":") if src else []
        dst_parts = dst.split(":") if dst else []
        src_ip = (src_parts[0] if len(src_parts) > 0 else "") or (alert.get("id_orig_h") or raw_obj.get("src") or "")
        src_port = src_parts[1] if len(src_parts) > 1 else (str(alert.get("id_orig_p", "") or raw_obj.get("id_orig_p", "")) if (alert.get("id_orig_p") is not None or raw_obj.get("id_orig_p") is not None) else "")
        dest_ip = (dst_parts[0] if len(dst_parts) > 0 else "") or (alert.get("id_resp_h") or raw_obj.get("dst") or "")
        dest_port = dst_parts[1] if len(dst_parts) > 1 else (str(alert.get("id_resp_p", "") or raw_obj.get("p", "") or "") if (alert.get("id_resp_p") is not None or raw_obj.get("p") is not None) else "")
        if not dest_port and isinstance(raw_obj.get("p"), (int, float)):
            dest_port = str(int(raw_obj["p"]))

        if (dest_ip or "").strip().upper() == "N/A":
            dest_ip = ""
        if (src_ip or "").strip().upper() == "N/A":
            src_ip = ""

        timestamp = alert.get("timestamp", "")
        if not timestamp:
            ts = raw_obj.get("ts") or alert.get("ts")
            if ts is not None:
                if isinstance(ts, (int, float)):
                    try:
                        timestamp = datetime.fromtimestamp(float(ts)).isoformat()
                    except (ValueError, OSError):
                        timestamp = datetime.now().isoformat()
                elif isinstance(ts, dict) and "iso" in ts:
                    timestamp = ts.get("iso", datetime.now().isoformat())
        if not timestamp:
            timestamp = datetime.now().isoformat()
        try:
            if isinstance(timestamp, str) and "T" not in timestamp:
                ts_str = timestamp.strip()[:19]
                dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                timestamp = dt.isoformat()
        except Exception:
            pass

        message = alert.get("message") or alert.get("msg") or raw_obj.get("msg") or "Alerta do Zeek"
        signature_id = str(alert.get("signature_id") or alert.get("sid") or "")
        if (signature_id == "**" or not signature_id) and message:
            match = re.search(r"\[(\d+):(\d+):(\d+)\]", message)
            if match:
                signature_id = match.group(2)
        category = (alert.get("category") or alert.get("note") or raw_obj.get("note") or "")[:255]
        protocol = (alert.get("protocol") or raw_obj.get("proto") or "").lower()

        return {
            "raw": alert,
            "timestamp": timestamp,
            "src_ip": src_ip or "N/A",
            "dest_ip": dest_ip or "N/A",
            "src_port": src_port,
            "dest_port": dest_port,
            "protocol": protocol,
            "signature_id": signature_id,
            "signature": message,
            "category": category,
            "severity": self._determine_severity(alert),
            "message": message,
        }

    def _determine_severity(self, alert: Dict[str, Any]) -> str:
        """
        Determina a severidade do alerta.
        Usa o campo 'severity' da IDS SSE API (INFO, CRITICAL, HIGH, MEDIUM, LOW) quando
        presente; caso contrário aplica heurísticas por palavras-chave.
        """
        api_severity = (alert.get("severity") or "").strip().upper()
        if api_severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            return api_severity.lower()
        if api_severity == "INFO":
            return "low"

        message = str(alert.get("message", alert.get("msg", ""))).upper()
        note = str(alert.get("note", "")).upper()
        text = f"{message} {note}"
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
        if "SQL" in text and ("INJECTION" in text or "MYSQL" in text or "BENCHMARK" in text):
            return "high"
        if any(k in text for k in critical_keywords):
            return "critical"
        if any(k in text for k in high_keywords):
            return "high"
        if any(k in text for k in medium_keywords):
            return "medium"
        return "medium"
