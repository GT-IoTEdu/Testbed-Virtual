"""
Router para integração com Suricata IDS/IPS
Fornece endpoint SSE para receber alertas em tempo real, persiste no banco
e aplica bloqueio automático para alertas de severidade alta.
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
from db.models import SuricataAlert
from db.session import SessionLocal
from services_firewalls.institution_config_service import InstitutionConfigService
from services_scanners.suricata_service import SuricataService

logger = logging.getLogger(__name__)


def _save_suricata_alert(institution_id: int, normalized_alert: dict) -> Optional[int]:
    """Persiste um alerta normalizado do Suricata na tabela suricata_alerts. Retorna o id do registro ou None."""
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

        record = SuricataAlert(
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
        db = SessionLocal()
        try:
            db.add(record)
            db.commit()
            db.refresh(record)
            logger.debug("Alerta Suricata persistido: id=%s", record.id)
            return record.id
        finally:
            db.close()
    except Exception as e:
        logger.warning("Falha ao salvar alerta Suricata no banco: %s", e, exc_info=True)
        return None


def _trigger_suricata_auto_block(alert_id: int, institution_id: int) -> None:
    """
    Executado em thread: aplica bloqueio automático para alerta Suricata de severidade alta
    (adiciona src_ip ao alias Bloqueados) e marca o alerta como processado.
    """
    try:
        time.sleep(0.5)
        from services_scanners.incident_service import IncidentService

        db = SessionLocal()
        try:
            alert = db.query(SuricataAlert).filter(SuricataAlert.id == alert_id).first()
            if not alert:
                logger.warning("Alerta Suricata %s não encontrado para bloqueio automático", alert_id)
                return
            if alert.processed_at is not None:
                logger.debug("Alerta Suricata %s já processado para bloqueio", alert_id)
                return
            if alert.severity != IncidentSeverity.HIGH:
                logger.debug("Alerta Suricata %s não é HIGH (severity=%s), bloqueio apenas para HIGH", alert_id, alert.severity)
                return
            src_ip = (alert.src_ip or "").strip()
            if not src_ip:
                logger.warning("Alerta Suricata %s sem src_ip, bloqueio ignorado", alert_id)
                return
            signature = (alert.signature or "")[:200]
            incident_service = IncidentService()
            success = incident_service.apply_auto_block_for_device(
                device_ip=src_ip,
                institution_id=institution_id,
                source_type="suricata",
                source_id=alert_id,
                description=signature,
                detected_at=alert.detected_at,
            )
            if success:
                alert.processed_at = datetime.utcnow()
                db.commit()
                logger.info("Bloqueio automático Suricata aplicado para IP %s (alerta %s)", src_ip, alert_id)
            else:
                logger.warning("Falha ao aplicar bloqueio automático Suricata para alerta %s (IP %s)", alert_id, src_ip)
        finally:
            db.close()
    except Exception as e:
        logger.error("Erro ao processar bloqueio automático Suricata para alerta %s: %s", alert_id, e, exc_info=True)

router = APIRouter(prefix="/scanners/suricata", tags=["Suricata"])


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


@router.get("/alerts", summary="Listar alertas do Suricata salvos no banco (paginado)")
async def list_suricata_alerts(
    user_id: Optional[int] = Query(None, description="ID do usuário"),
    institution_id: Optional[int] = Query(None, description="ID da instituição"),
    limit: int = Query(10, ge=1, le=100, description="Itens por página"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
):
    """Retorna alertas da tabela suricata_alerts (mais recentes primeiro), com total para paginação."""
    inst_id = _resolve_institution_id(user_id, institution_id)
    if not inst_id:
        raise HTTPException(
            status_code=400,
            detail="É necessário fornecer institution_id ou user_id para identificar a instituição.",
        )
    db = SessionLocal()
    try:
        base_q = db.query(SuricataAlert).filter(SuricataAlert.institution_id == inst_id)
        total = base_q.count()
        rows = (
            base_q.order_by(SuricataAlert.detected_at.desc())
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


@router.get("/health", summary="Verificar saúde da integração com Suricata")
async def suricata_health(
    user_id: Optional[int] = Query(None, description="ID do usuário para buscar configurações"),
    institution_id: Optional[int] = Query(None, description="ID da instituição")
):
    """
    Verifica se a integração com Suricata está funcionando.
    
    Retorna informações sobre o status da conexão e configuração.
    """
    try:
        service = SuricataService(user_id=user_id, institution_id=institution_id)
        result = service.test_connection()
        return result
    except Exception as e:
        logger.error(f"Erro ao verificar saúde do Suricata: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao verificar saúde do Suricata: {str(e)}"
        )


@router.get("/sse/alerts", summary="Stream de alertas do Suricata (SSE)")
async def stream_suricata_alerts(
    request: Request,
    user_id: Optional[int] = Query(None, description="ID do usuário para buscar configurações"),
    institution_id: Optional[int] = Query(None, description="ID da instituição")
):
    """
    Endpoint Server-Sent Events (SSE) para receber alertas do Suricata em tempo real.
    
    O cliente recebe eventos quando novos alertas são gerados pelo Suricata.
    A conexão permanece aberta e eventos são enviados conforme chegam.
    
    Uso no frontend:
    ```javascript
    const eventSource = new EventSource('/api/scanners/suricata/sse/alerts?institution_id=1');
    eventSource.onmessage = (event) => {
      const alert = JSON.parse(event.data);
      // Processar alerta
    };
    ```
    """
    try:
        # Buscar configurações da instituição
        if not institution_id and user_id:
            try:
                user_config = InstitutionConfigService.get_user_institution_config(user_id=user_id)
                if user_config:
                    institution_id = user_config.get('institution_id')
                    logger.info(f"📡 Instituição identificada para user_id {user_id}: {institution_id}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao buscar configuração do usuário {user_id}: {e}")
        
        if not institution_id:
            error_msg = "É necessário fornecer institution_id ou user_id para identificar a instituição. Verifique se o usuário está associado a uma instituição."
            logger.error(f"❌ {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        # Criar serviço Suricata
        service = SuricataService(user_id=user_id, institution_id=institution_id)
        
        logger.info(f"📡 [Suricata Router] Verificando configuração - base_url: {service.base_url}, api_key: {'***' if service.api_key else 'None'}")
        
        if not service.base_url or not service.api_key:
            logger.error(f"❌ [Suricata Router] Suricata não configurado para instituição {institution_id}")
            logger.error(f"   base_url: {repr(service.base_url)}")
            logger.error(f"   api_key: {'***' if service.api_key else 'None'}")
            raise HTTPException(
                status_code=404,
                detail="Suricata não configurado para esta instituição. Configure suricata_base_url e suricata_key no cadastro da instituição."
            )
        
        sse_url = service.get_sse_url()
        if not sse_url:
            raise HTTPException(
                status_code=500,
                detail="Erro ao construir URL do SSE do Suricata"
            )
        
        # Mascarar API key nos logs
        masked_url = sse_url.replace(service.api_key, '***') if service.api_key else sse_url
        logger.info(f"📡 Conectando ao Suricata SSE: {masked_url}")
        logger.info(f"📡 Configuração Suricata - Base URL: {service.base_url}, API Key: {'***' if service.api_key else 'NÃO CONFIGURADO'}")
        logger.info(f"📡 Instituição ID: {institution_id}, User ID: {user_id}")
        
        def event_generator():
            """Proxy simples do stream SSE do Suricata - apenas repassa os dados"""
            try:
                # Enviar evento de conexão inicial
                yield f"data: {json.dumps({'type': 'connected', 'message': 'Conectando ao stream de alertas do Suricata'})}\n\n"
                
                logger.info(f"📡 [Proxy] Conectando ao Suricata: {masked_url}")
                
                # Fazer requisição HTTP para o endpoint SSE do Suricata
                response = requests.get(
                    sse_url, 
                    stream=True, 
                    timeout=None,
                    headers={
                        'Accept': 'text/event-stream',
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive'
                    }
                )
                
                response.raise_for_status()
                logger.info(f"📡 [Proxy] Stream conectado ao Suricata (Status: {response.status_code})")
                
                # Enviar confirmação de conexão
                yield f"data: {json.dumps({'type': 'connected', 'message': 'Conectado ao stream de alertas do Suricata'})}\n\n"
                
                # Repassar o stream do Suricata
                try:
                    buffer = ""
                    
                    for raw_line in response.iter_lines(decode_unicode=False):
                        # Decodificar linha
                        try:
                            # iter_lines retorna bytes ou None para linhas vazias
                            if raw_line is None or (isinstance(raw_line, bytes) and len(raw_line) == 0):
                                # Linha vazia - adicionar ao buffer como parte do formato SSE
                                if buffer:
                                    buffer += "\n"
                                    # Se buffer termina com \n\n, temos um evento completo
                                    if buffer.endswith("\n\n"):
                                        event_data = buffer.strip()
                                        buffer = ""
                                        
                                        if event_data and event_data.startswith('data: '):
                                            json_str = event_data[6:].strip()
                                            try:
                                                alert_dict = json.loads(json_str)
                                                alert = service._normalize_alert(alert_dict)
                                                alert_id = _save_suricata_alert(institution_id, alert)
                                                if alert_id and (alert.get("severity") or "").lower() == "high" and (alert.get("src_ip") or "").strip():
                                                    threading.Thread(
                                                        target=_trigger_suricata_auto_block,
                                                        args=(alert_id, institution_id),
                                                        daemon=True,
                                                    ).start()
                                                if alert_id:
                                                    alert = {**alert, "id": alert_id}
                                                normalized_event = {
                                                    'type': 'alert',
                                                    'alert': alert,
                                                    'timestamp': alert.get('timestamp', ''),
                                                    'source': 'suricata'
                                                }
                                                yield f"data: {json.dumps(normalized_event)}\n\n"
                                            except json.JSONDecodeError as e:
                                                logger.warning(f"⚠️ [Proxy] Erro ao parsear JSON: {e}")
                                                yield f"{event_data}\n\n"
                                continue
                            
                            # Decodificar linha não vazia
                            line = raw_line.decode('utf-8') if isinstance(raw_line, bytes) else raw_line
                            
                            # Adicionar linha ao buffer
                            if line:
                                buffer += line + "\n"
                                
                                # Verificar se temos um evento completo (termina com \n\n)
                                if buffer.endswith("\n\n"):
                                    event_data = buffer.strip()
                                    buffer = ""
                                    
                                    if event_data and event_data.startswith('data: '):
                                        json_str = event_data[6:].strip()
                                        
                                        try:
                                            alert_dict = json.loads(json_str)
                                            alert = service._normalize_alert(alert_dict)
                                            alert_id = _save_suricata_alert(institution_id, alert)
                                            if alert_id and (alert.get("severity") or "").lower() == "high" and (alert.get("src_ip") or "").strip():
                                                threading.Thread(
                                                    target=_trigger_suricata_auto_block,
                                                    args=(alert_id, institution_id),
                                                    daemon=True,
                                                ).start()
                                            if alert_id:
                                                alert = {**alert, "id": alert_id}
                                            normalized_event = {
                                                'type': 'alert',
                                                'alert': alert,
                                                'timestamp': alert.get('timestamp', ''),
                                                'source': 'suricata'
                                            }
                                            yield f"data: {json.dumps(normalized_event)}\n\n"
                                        except json.JSONDecodeError as e:
                                            logger.warning(f"⚠️ [Proxy] Erro ao parsear JSON: {e}")
                                            yield f"{event_data}\n\n"
                                            
                        except (UnicodeDecodeError, AttributeError) as e:
                            logger.debug(f"⚠️ [Proxy] Erro ao decodificar linha: {e}")
                            continue
                            
                except Exception as stream_error:
                    logger.error(f"❌ [Proxy] Erro ao ler stream do Suricata: {stream_error}", exc_info=True)
                    yield f"data: {json.dumps({'type': 'error', 'message': f'Erro ao ler stream: {str(stream_error)}'})}\n\n"
                
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if hasattr(e, 'response') and e.response else 'Desconhecido'
                error_msg = f"Erro HTTP {status_code} ao conectar ao Suricata em {sse_url}"
                logger.error(f"❌ {error_msg}")
                logger.error(f"   Detalhes: {str(e)}")
                if hasattr(e, 'response') and e.response:
                    try:
                        error_body = e.response.text[:500]
                        logger.error(f"   Resposta do servidor: {error_body}")
                    except:
                        pass
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
            except requests.exceptions.ConnectionError as e:
                error_msg = f"Erro de conexão com Suricata em {sse_url}. Verifique:\n" + \
                           f"1. Se o servidor Suricata está rodando (192.168.1.128:8001)\n" + \
                           f"2. Se há firewall bloqueando a conexão\n" + \
                           f"3. Se o backend consegue acessar o IP 192.168.1.128"
                logger.error(f"❌ {error_msg}")
                logger.error(f"   Detalhes: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
            except requests.exceptions.Timeout as e:
                error_msg = f"Timeout ao conectar com Suricata em {sse_url}"
                logger.error(f"❌ {error_msg} - {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
            except requests.exceptions.RequestException as e:
                error_msg = f"Erro de requisição ao Suricata: {str(e)}"
                logger.error(f"❌ {error_msg} - {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
            except Exception as e:
                error_msg = f"Erro interno ao processar stream do Suricata: {str(e)}"
                logger.error(f"❌ {error_msg}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Desabilita buffering no nginx
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar stream SSE do Suricata: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar stream SSE: {str(e)}"
        )
