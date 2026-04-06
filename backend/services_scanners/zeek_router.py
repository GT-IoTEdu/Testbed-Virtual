"""
Router para integração com Zeek NSM
Fornece endpoint SSE para receber alertas em tempo real, persiste no banco
e aplica bloqueio automático para alertas de severidade alta (mesmo estilo Suricata/Snort).
"""
import json
import logging
import threading
import time
from datetime import datetime
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from db.enums import IncidentSeverity
from db.models import ZeekAlert
from db.session import SessionLocal
from services_firewalls.institution_config_service import InstitutionConfigService
from services_scanners.zeek_service import ZeekService

logger = logging.getLogger(__name__)


def _save_zeek_alert(institution_id: int, normalized_alert: dict) -> Optional[int]:
    """Persiste um alerta normalizado do Zeek na tabela zeek_alerts (mesmo formato Suricata/Snort)."""
    try:
        ts = normalized_alert.get("timestamp") or ""
        try:
            detected_at = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            detected_at = datetime.utcnow()

        severity_str = (normalized_alert.get("severity") or "medium").lower()
        severity_enum = (
            IncidentSeverity(severity_str)
            if severity_str in ("low", "medium", "high", "critical")
            else IncidentSeverity.MEDIUM
        )

        raw = normalized_alert.get("raw")
        raw_log_data = json.dumps(raw, ensure_ascii=False) if raw else None

        record = ZeekAlert(
            institution_id=institution_id,
            detected_at=detected_at,
            signature=(normalized_alert.get("signature") or "")[:500],
            signature_id=(str(normalized_alert.get("signature_id") or ""))[:50],
            severity=severity_enum,
            src_ip=(normalized_alert.get("src_ip") or "")[:45],
            dest_ip=(normalized_alert.get("dest_ip") or "")[:45],
            src_port=(str(normalized_alert.get("src_port") or ""))[:20],
            dest_port=(str(normalized_alert.get("dest_port") or ""))[:20],
            protocol=(normalized_alert.get("protocol") or "")[:20],
            category=(normalized_alert.get("category") or "")[:255],
            raw_log_data=raw_log_data,
        )
        print("estamos aqui")
        db = SessionLocal()
        try:
            db.add(record)
            db.commit()
            db.refresh(record)
            logger.info("Zeek alerta persistido em zeek_alerts: id=%s institution_id=%s signature=%s", record.id, institution_id, (record.signature or "")[:80])
            return record.id
        finally:
            db.close()
    except Exception as e:
        logger.warning("Falha ao salvar alerta Zeek no banco: %s", e, exc_info=True)
        return None


def _trigger_zeek_auto_block(alert_id: int, institution_id: int) -> None:
    """Executado em thread: aplica bloqueio automático para alerta Zeek de severidade alta (igual Suricata/Snort)."""
    try:
        time.sleep(0.5)
        from services_scanners.incident_service import IncidentService

        db = SessionLocal()
        try:
            alert = db.query(ZeekAlert).filter(ZeekAlert.id == alert_id).first()
            if not alert:
                logger.warning("Alerta Zeek %s não encontrado para bloqueio automático", alert_id)
                return
            if alert.processed_at is not None:
                return
            if alert.severity != IncidentSeverity.HIGH:
                return
            src_ip = (alert.src_ip or "").strip()
            if not src_ip or src_ip.upper() == "N/A":
                logger.warning("Alerta Zeek %s sem src_ip válido (vazio ou N/A), bloqueio ignorado", alert_id)
                return
            # Não bloquear se não parecer um IP (evita enviar "N/A" ou texto ao pfSense)
            if "." not in src_ip and ":" not in src_ip:
                logger.warning("Alerta Zeek %s src_ip não é um IP válido: %s", alert_id, src_ip[:50])
                return
            signature = (alert.signature or "")[:200]
            incident_service = IncidentService()
            success = incident_service.apply_auto_block_for_device(
                device_ip=src_ip,
                institution_id=institution_id,
                source_type="zeek",
                source_id=alert_id,
                description=signature,
                detected_at=alert.detected_at,
            )
            if success:
                alert.processed_at = datetime.utcnow()
                db.commit()
                logger.info("Bloqueio automático Zeek aplicado para IP %s (alerta %s)", src_ip, alert_id)
            else:
                logger.warning("Falha ao aplicar bloqueio automático Zeek para alerta %s (IP %s)", alert_id, src_ip)
        finally:
            db.close()
    except Exception as e:
        logger.error("Erro ao processar bloqueio automático Zeek para alerta %s: %s", alert_id, e, exc_info=True)


router = APIRouter(prefix="/scanners/zeek", tags=["Zeek"])


def _resolve_institution_id(user_id: Optional[int], institution_id: Optional[int]) -> Optional[int]:
    if institution_id:
        return institution_id
    if user_id:
        try:
            config = InstitutionConfigService.get_user_institution_config(user_id=user_id)
            if config:
                return config.get("institution_id")
        except Exception as e:
            logger.warning("Erro ao buscar instituição do usuário %s: %s", user_id, e)
    return None


@router.get("/alerts", summary="Listar alertas do Zeek salvos no banco (paginado)")
async def list_zeek_alerts(
    user_id: Optional[int] = Query(None, description="ID do usuário"),
    institution_id: Optional[int] = Query(None, description="ID da instituição"),
    limit: int = Query(10, ge=1, le=100, description="Itens por página"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
):
    """Retorna alertas da tabela zeek_alerts (mais recentes primeiro), com total para paginação."""
    inst_id = _resolve_institution_id(user_id, institution_id)
    if not inst_id:
        raise HTTPException(
            status_code=400,
            detail="É necessário fornecer institution_id ou user_id para identificar a instituição.",
        )
    db = SessionLocal()
    try:
        base_q = db.query(ZeekAlert).filter(ZeekAlert.institution_id == inst_id)
        total = base_q.count()
        rows = (
            base_q.order_by(ZeekAlert.detected_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        items = [
            {
                "id": r.id,
                "timestamp": r.detected_at.isoformat() if r.detected_at else None,
                "signature": r.signature,
                "signature_id": r.signature_id,
                "severity": r.severity.value if r.severity else None,
                "src_ip": r.src_ip,
                "dest_ip": r.dest_ip,
                "src_port": r.src_port,
                "dest_port": r.dest_port,
                "protocol": r.protocol,
                "category": r.category,
            }
            for r in rows
        ]
        return {"items": items, "total": total}
    finally:
        db.close()


@router.get("/health", summary="Verificar saúde da integração com Zeek")
async def zeek_health(
    user_id: Optional[int] = Query(None, description="ID do usuário para buscar configurações (current_user_id)"),
    institution_id: Optional[int] = Query(None, description="ID da instituição"),
):
    """Verifica se a integração com Zeek está funcionando."""
    try:
        service = ZeekService(user_id=user_id, institution_id=institution_id)
        result = service.test_connection()
        # Compatibilidade com frontend que espera status healthy/unhealthy
        if "status" not in result and "success" in result:
            result["status"] = "healthy" if result.get("success") else "unhealthy"
        return result
    except Exception as e:
        logger.error("Erro ao verificar saúde do Zeek: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao verificar saúde do Zeek: {str(e)}")


@router.get("/sse/alerts", summary="Stream de alertas do Zeek (SSE)")
async def stream_zeek_alerts(
    request: Request,
    user_id: Optional[int] = Query(None, description="ID do usuário para buscar configurações"),
    institution_id: Optional[int] = Query(None, description="ID da instituição"),
):
    """Endpoint SSE para receber alertas do Zeek em tempo real (proxy do servidor Zeek)."""
    print("🔵 STEP 1: SSE endpoint called")
    print(f"🔵 Received params: user_id={user_id}, institution_id={institution_id}")
    logger.warning(f"🔵 SSE endpoint accessed with user_id={user_id}, institution_id={institution_id}")

    try:
        print("🔵 STEP 2: Entering try block")


        if not institution_id and user_id:
            print(f"🔵 STEP 2a: Resolving institution_id from user_id={user_id}")
            try:
                user_config = InstitutionConfigService.get_user_institution_config(user_id=user_id)
                if user_config:
                    institution_id = user_config.get("institution_id")
                    print(f"🔵 STEP 2b: Resolved institution_id={institution_id}")
                    logger.warning(f"Resolved institution_id {institution_id} from user_id {user_id}")
            except Exception as e:
                print(f"🔴 ERROR resolving institution: {e}")
                logger.warning("Erro ao buscar configuração do usuário %s: %s", user_id, e)

        if not institution_id:
            print("🔴 ERROR: No institution_id after resolution")
            raise HTTPException(
                status_code=400,
                detail="É necessário fornecer institution_id ou user_id para identificar a instituição.",
            )

        print(f"🔵 STEP 3: Creating ZeekService with institution_id={institution_id}")
        service = ZeekService(user_id=user_id, institution_id=institution_id)

        # Check Zeek configuration
        print(f"🔵 STEP 4: Checking Zeek config - base_url: {service.base_url}, has_api_key: {bool(service.api_key)}")
        if not service.base_url or not service.api_key:
            print(f"🔴 ERROR: Zeek not configured - base_url: {service.base_url}, api_key present: {bool(service.api_key)}")
            raise HTTPException(
                status_code=404,
                detail="Zeek não configurado para esta instituição. Configure zeek_base_url e zeek_key no cadastro da instituição.",
            )


        print("🔵 STEP 5: Building SSE URL")
        sse_url = service.get_sse_url()
        print(f"🔵 SSE URL built: {sse_url}")

        if not sse_url:
            print("🔴 ERROR: Failed to build SSE URL")
            raise HTTPException(status_code=500, detail="Erro ao construir URL do SSE do Zeek")

        masked_url = sse_url.replace(service.api_key, "***") if service.api_key else sse_url
        print(f"🔵 STEP 6: About to connect to: {masked_url}")
        logger.warning(f"🌐 About to connect to Zeek SSE: {masked_url}")


        def event_generator():
            print("🟢 STEP 7: INSIDE event_generator!")  # This should print if we get here
            print("🟢 Event generator started")
            logger.warning("🟢 Event generator function executing")

            try:
                print("🟢 STEP 8: Inside event_generator try block")
                yield f"data: {json.dumps({'type': 'connected', 'message': 'Conectando ao stream de alertas do Zeek'})}\n\n"

                print(f"🟢 STEP 9: Making request to: {masked_url}")
                response = requests.get(
                    sse_url,
                    stream=True,
                    timeout=None,
                    headers={"Accept": "text/event-stream", "Cache-Control": "no-cache", "Connection": "keep-alive"},
                )
                print(f"🟢 STEP 10: Request made, status: {response.status_code}")

                response.raise_for_status()
                print("🟢 STEP 11: Response OK")

                yield f"data: {json.dumps({'type': 'connected', 'message': 'Conectado ao stream de alertas do Zeek'})}\n\n"

                # Process events
                event_count = 0
                print("🟢 STEP 12: Starting to process events")

                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue

                    print(f"🟢 Received line: {line[:50]}...")

                    if line.startswith('data: '):
                        json_str = line[6:].strip()
                        print(f"🟢 Processing event #{event_count + 1}: {json_str[:100]}...")

                        try:
                            alert_dict = json.loads(json_str)
                            alert = service._normalize_alert(alert_dict)
                            alert_id = _save_zeek_alert(institution_id, alert)

                            if alert_id:
                                event_count += 1
                                print(f"🟢 Saved alert #{event_count} with ID {alert_id}")

                                normalized_event = {
                                    "type": "alert",
                                    "alert": alert,
                                    "timestamp": alert.get("timestamp", ""),
                                    "source": "zeek"
                                }
                                yield f"data: {json.dumps(normalized_event)}\n\n"

                        except Exception as e:
                            print(f"🔴 Error processing event: {e}")

            except Exception as e:
                print(f"🔴 ERROR in event_generator: {e}")
                logger.error(f"Event generator error: {e}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

            finally:
                print(f"🟢 Event generator finished. Processed {event_count if 'event_count' in locals() else 0} events")

        print("🔵 STEP 13: Returning StreamingResponse with event_generator")
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    except HTTPException:
        print("🔴 HTTPException caught, re-raising")
        raise
    except Exception as e:
        print(f"🔴 UNCAUGHT EXCEPTION: {e}")
        logger.error("Erro ao criar stream SSE do Zeek: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao criar stream SSE: {str(e)}")

def _run_zeek_collector_loop(institution_id: int, sse_url: str, service: ZeekService) -> None:
    """
    Loop do coletor em background: conecta ao SSE do Zeek, parseia eventos e persiste em zeek_alerts.
    Reconecta após erro com sleep. Deve ser executado em thread daemon.
    """
    masked = sse_url.replace(service.api_key, "***") if service.api_key else sse_url
    while True:
        try:
            logger.info("Zeek coletor em background conectando institution_id=%s url=%s", institution_id, masked)
            response = requests.get(
                sse_url,
                stream=True,
                timeout=None,
                headers={"Accept": "text/event-stream", "Cache-Control": "no-cache", "Connection": "keep-alive"},
            )
            response.raise_for_status()
            buffer = ""
            for raw_line in response.iter_lines(decode_unicode=False):
                try:
                    if raw_line is None or (isinstance(raw_line, bytes) and len(raw_line) == 0):
                        if buffer:
                            buffer += "\n"
                        if buffer.endswith("\n\n"):
                            event_data = buffer.strip()
                            buffer = ""
                            if event_data and event_data.startswith("data: "):
                                json_str = event_data[6:].strip()
                                try:
                                    alert_dict = json.loads(json_str)
                                    alert = service._normalize_alert(alert_dict)
                                    alert_id = _save_zeek_alert(institution_id, alert)
                                    if alert_id and (alert.get("severity") or "").lower() == "high" and (alert.get("src_ip") or "").strip():
                                        threading.Thread(target=_trigger_zeek_auto_block, args=(alert_id, institution_id), daemon=True).start()
                                except json.JSONDecodeError as e:
                                    logger.warning("Zeek coletor JSON decode: %s", e)
                        continue
                    line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                    if line:
                        buffer += line + "\n"
                        if buffer.endswith("\n\n"):
                            event_data = buffer.strip()
                            buffer = ""
                            if event_data and event_data.startswith("data: "):
                                json_str = event_data[6:].strip()
                                try:
                                    alert_dict = json.loads(json_str)
                                    alert = service._normalize_alert(alert_dict)
                                    alert_id = _save_zeek_alert(institution_id, alert)
                                    if alert_id and (alert.get("severity") or "").lower() == "high" and (alert.get("src_ip") or "").strip():
                                        threading.Thread(target=_trigger_zeek_auto_block, args=(alert_id, institution_id), daemon=True).start()
                                except json.JSONDecodeError as e:
                                    logger.warning("Zeek coletor JSON decode: %s", e)
                except (UnicodeDecodeError, AttributeError):
                    continue
        except Exception as e:
            logger.warning("Zeek coletor em background erro (reconectando em 30s): institution_id=%s err=%s", institution_id, e)
        time.sleep(30)


def start_zeek_background_collectors() -> None:
    """
    Inicia uma thread daemon por instituição com Zeek configurado, para persistir alertas
    em zeek_alerts mesmo sem o dashboard aberto. Chamar no startup da aplicação.
    """
    try:
        institutions = InstitutionConfigService.get_institution_config()
        if not institutions:
            logger.debug("Nenhuma instituição com Zeek configurado para coletor em background")
            return
        for cfg in institutions:
            inst_id = cfg["institution_id"]
            service = ZeekService(zeek_base_url=cfg["zeek_base_url"], api_key=cfg["zeek_key"])
            sse_url = service.get_sse_url()
            if not sse_url:
                continue
            t = threading.Thread(
                target=_run_zeek_collector_loop,
                args=(inst_id, sse_url, service),
                daemon=True,
                name=f"zeek-collector-{inst_id}",
            )
            t.start()
            logger.info("Zeek coletor em background iniciado para institution_id=%s", inst_id)
    except Exception as e:
        logger.error("Erro ao iniciar coletores Zeek em background: %s", e, exc_info=True)
