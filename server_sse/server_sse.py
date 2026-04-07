from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
import os
import re
import json
import time

app = FastAPI(title="IDS SSE API")

# =====================================================
# SIDs IGNORADOS (FILTRO)
# =====================================================
IGNORED_SIDS = {
    "999999",
    "2017515"
}

# =====================================================
# EXTRATOR DE SID ( [gid:sid:rev] )
# =====================================================
SID_IN_MESSAGE_PATTERN = re.compile(r'\[(\d+):(\d+):(\d+)\]')

# =====================================================
# LOG FILES
# =====================================================
LOG_FILE_SURICATA = "/var/log/suricata/fast.log"
LOG_FILE_SNORT = "/var/log/snort/alert"
LOG_FILE_ZEEK = "../logs/notice.log"  # Adicionado Zeek

# =====================================================
# API KEYS
# =====================================================
API_KEYS = {
    "srv-monitoramento": "a8f4c2d9-1c9b-4b6f-9d6e-aaa111bbb222"
}

# =====================================================
# REGEX – SURICATA fast.log
# =====================================================
SURICATA_PATTERN = re.compile(
    r'(?P<timestamp>\d+/\d+/\d+-\d+:\d+:\d+\.\d+).*?'
    r'\[(?P<sid>[^\]]+)\]\s+'
    r'(?P<message>.*?)\s+\[\*\*\].*?'
    r'\{(?P<protocol>\w+)\}\s+'
    r'(?P<src>\S+)\s+->\s+(?P<dst>\S+)'
)

# =====================================================
# REGEX – SNORT alert (FAST)
# =====================================================
SNORT_PATTERN = re.compile(
    r'(?P<timestamp>\d+/\d+-\d+:\d+:\d+\.\d+)\s+'
    r'\[\*\*\]\s+'
    r'\[(?P<sid>\d+:\d+:\d+)\]\s+'
    r'(?P<message>.*?)\s+'
    r'\[\*\*\]\s+.*?'
    r'\{(?P<protocol>\w+)\}\s+'
    r'(?P<src>\S+)\s+->\s+(?P<dst>\S+)'
)

# =====================================================
# API KEY VALIDATION
# =====================================================
def validate_api_key(api_key: str):
    if api_key not in API_KEYS.values():
        raise HTTPException(status_code=403, detail="API key inválida")

# =====================================================
# PROCESSAR LINHA ZEEK (JSON)
# =====================================================
def parse_zeek_line(line: str):
    """Parse uma linha JSON do notice.log do Zeek e extrai informações relevantes."""
    try:
        data = json.loads(line.strip())
        
        # Extrair informações principais
        timestamp = data.get("ts", "")
        note = data.get("note", "")
        msg = data.get("msg", "")
        src = data.get("src", "N/A")
        dst = data.get("dst", "N/A")
        proto = data.get("proto", "N/A")
        
        # Converter timestamp UNIX para formato legível
        if timestamp:
            try:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            except:
                timestamp = str(timestamp)
        
        # Extrair severidade da mensagem
        severity = "INFO"
        if "[CRITICAL]" in msg:
            severity = "CRITICAL"
        elif "[HIGH]" in msg:
            severity = "HIGH"
        elif "[MEDIUM]" in msg:
            severity = "MEDIUM"
        elif "[LOW]" in msg:
            severity = "LOW"
        
        # Extrair SID se disponível
        sid_match = SID_IN_MESSAGE_PATTERN.search(msg)
        sid = sid_match.group(2) if sid_match else note.replace("::", "_")
        
        return {
            "timestamp": timestamp,
            "sid": sid,
            "note": note,
            "message": msg,
            "severity": severity,
            "protocol": proto,
            "src": src,
            "dst": dst,
            "raw": data
        }
    except json.JSONDecodeError:
        return None
    except Exception as e:
        print(f"Erro ao parsear linha Zeek: {e}")
        return None

# =====================================================
# GENERIC REALTIME TAIL
# =====================================================
async def alert_stream(log_file: str, pattern: re.Pattern, log_type: str):
    """Stream de alertas para diferentes tipos de logs."""
    while not os.path.exists(log_file):
        await asyncio.sleep(1)

    with open(log_file, "r", errors="ignore") as f:
        f.seek(0, os.SEEK_END)

        while True:
            line = f.readline()
            if not line:
                await asyncio.sleep(0.3)
                continue
            
            # Processamento específico para Zeek
            if log_type == "zeek":
                parsed = parse_zeek_line(line)
                if not parsed:
                    continue
                    
                # Aplicar filtro de SIDs (usando note como SID para Zeek)
                note_as_sid = parsed["sid"]
                if note_as_sid in IGNORED_SIDS:
                    continue
                    
                yield f"data: {json.dumps(parsed)}\n\n"
                continue
            
            # Processamento original para Suricata/Snort
            match = pattern.search(line)
            if not match:
                continue

            data = match.groupdict()

            raw_sid = data.get("sid", "")
            message = data.get("message", "")

            sid_number = None

            # =================================================
            # SNORT → SID já vem no campo sid (1:2017515:3)
            # =================================================
            if raw_sid and raw_sid != "**":
                parts = raw_sid.split(":")
                if len(parts) >= 2:
                    sid_number = parts[1]

            # =================================================
            # SURICATA → SID vem dentro da message
            # =================================================
            if not sid_number:
                m = SID_IN_MESSAGE_PATTERN.search(message)
                if m:
                    sid_number = m.group(2)

            # Se não conseguiu extrair SID, ignora
            if not sid_number:
                continue

            # =================================================
            # FILTRO DE SIDs
            # =================================================
            if sid_number in IGNORED_SIDS:
                continue

            payload = {
                "timestamp": data["timestamp"],
                "sid": sid_number,
                "message": message,
                "protocol": data["protocol"],
                "src": data["src"],
                "dst": data["dst"]
            }

            yield f"data: {json.dumps(payload)}\n\n"

# =====================================================
# SSE – SURICATA (endpoint ORIGINAL)
# =====================================================
@app.get("/debug/check-zeek-logs")
async def debug_check_zeek_logs(api_key: str = Query(...)):
    """Debug endpoint to check if Zeek logs are being read correctly"""
    validate_api_key(api_key)

    results = {
        "file_exists": os.path.exists(LOG_FILE_ZEEK),
        "file_size": 0,
        "can_read": False,
        "total_lines": 0,
        "parsed_entries": [],
        "errors": []
    }

    if results["file_exists"]:
        try:
            with open(LOG_FILE_ZEEK, "r", errors="ignore") as f:
                lines = f.readlines()
                results["total_lines"] = len(lines)
                results["file_size"] = os.path.getsize(LOG_FILE_ZEEK)

                # Try to parse last 10 lines
                for i, line in enumerate(lines[-10:]):
                    parsed = parse_zeek_line(line)
                    if parsed:
                        results["parsed_entries"].append({
                            "line_number": len(lines) - 10 + i,
                            "parsed": parsed,
                            "raw": line.strip()[:100] + "..."
                        })
                    else:
                        results["errors"].append({
                            "line_number": len(lines) - 10 + i,
                            "raw": line.strip()[:100] + "...",
                            "error": "Failed to parse"
                        })
        except Exception as e:
            results["error"] = str(e)

    return results
@app.get("/sse/alerts")
async def sse_suricata(api_key: str = Query(...)):
    validate_api_key(api_key)

    return StreamingResponse(
        alert_stream(LOG_FILE_SURICATA, SURICATA_PATTERN, "suricata"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# =====================================================
# SSE – SNORT (endpoint ORIGINAL)
# =====================================================
@app.get("/sse/snort")
async def sse_snort(api_key: str = Query(...)):
    validate_api_key(api_key)

    return StreamingResponse(
        alert_stream(LOG_FILE_SNORT, SNORT_PATTERN, "snort"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
@app.get("/sse/zeek-full")
async def sse_zeek_full(
    api_key: str = Query(...),
    batch_size: int = Query(10, description="Número de eventos por batch"),
    delay: float = Query(0.1, description="Delay entre batches em segundos")
):
    """Retorna TODOS os eventos do notice.log via SSE"""
    validate_api_key(api_key)

    if not os.path.exists(LOG_FILE_ZEEK):
        raise HTTPException(status_code=404, detail="Arquivo notice.log não encontrado")

    async def event_generator():
        try:
            # Ler todo o arquivo
            with open(LOG_FILE_ZEEK, 'r') as f:
                lines = f.readlines()

            total_events = len(lines)
            print(f"Preparando para enviar {total_events} eventos via SSE")

            # Enviar metadados primeiro
            yield f"event: metadata\ndata: {json.dumps({'total': total_events, 'start': True})}\n\n"

            # Enviar eventos em batches
            for i in range(0, total_events, batch_size):
                batch = lines[i:i+batch_size]

                for line in batch:
                    line = line.strip()
                    if line:
                        try:
                            # Tentar parsear como JSON
                            data = json.loads(line)

                            # Formatar timestamp se existir
                            if 'ts' in data and data['ts']:
                                try:
                                    data['ts_formatted'] = time.strftime(
                                        '%Y-%m-%d %H:%M:%S',
                                        time.localtime(float(data['ts']))
                                    )
                                except:
                                    pass

                            # Adicionar índice
                            data['_index'] = i
                            data['_total'] = total_events

                            yield f"event: alert\ndata: {json.dumps(data)}\n\n"

                        except json.JSONDecodeError:
                            # Se não for JSON, enviar como raw
                            yield f"event: raw\ndata: {json.dumps({'raw': line, '_index': i})}\n\n"

                # Pequeno delay entre batches para não sobrecarregar
                await asyncio.sleep(delay)

            # Finalizar
            yield f"event: complete\ndata: {json.dumps({'total': total_events, 'complete': True})}\n\n"

        except Exception as e:
            print(f"Erro no stream: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
# =====================================================
# SSE – ZEEK (NOVO ENDPOINT)
# =====================================================

@app.get("/sse/zeek")
async def sse_zeek(api_key: str = Query(...)):
    """Stream de alertas do Zeek a partir do notice.log - sends existing + new alerts"""
    validate_api_key(api_key)

    async def zeek_event_stream():
        # First, check if file exists
        if not os.path.exists(LOG_FILE_ZEEK):
            yield f"data: {json.dumps({'error': 'Zeek log file not found'})}\n\n"
            return

        try:
            # Step 1: Send existing log entries (last 100 lines)
            with open(LOG_FILE_ZEEK, "r", errors="ignore") as f:
                lines = f.readlines()

                # Send metadata about how many events we're sending
                total_existing = len(lines)
                yield f"event: metadata\ndata: {json.dumps({'type': 'history_start', 'count': min(100, total_existing)})}\n\n"

                # Send last 100 lines (or all if less than 100)
                start_line = max(0, total_existing - 100)
                for i, line in enumerate(lines[start_line:], start=start_line):
                    line = line.strip()
                    if not line:
                        continue

                    parsed = parse_zeek_line(line)
                    if parsed and parsed["sid"] not in IGNORED_SIDS:
                        # Add historical flag and index
                        parsed['_historical'] = True
                        parsed['_index'] = i
                        parsed['_total'] = total_existing
                        yield f"event: alert\ndata: {json.dumps(parsed)}\n\n"
                        await asyncio.sleep(0.01)  # Small delay to avoid overwhelming the client

                yield f"event: metadata\ndata: {json.dumps({'type': 'history_end', 'sent': min(100, total_existing)})}\n\n"

            # Step 2: Now tail for new entries
            with open(LOG_FILE_ZEEK, "r", errors="ignore") as f:
                # Go to the end of the file
                f.seek(0, os.SEEK_END)

                while True:
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.3)
                        continue

                    line = line.strip()
                    if not line:
                        continue

                    parsed = parse_zeek_line(line)
                    if parsed and parsed["sid"] not in IGNORED_SIDS:
                        parsed['_historical'] = False  # Mark as real-time
                        yield f"event: alert\ndata: {json.dumps(parsed)}\n\n"

        except Exception as e:
            logger.error(f"Error in Zeek SSE stream: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        zeek_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# =====================================================
# ENDPOINT UNIFICADO PARA TODOS OS LOGS
# =====================================================
@app.get("/sse/all")
async def sse_all(api_key: str = Query(...)):
    """Stream combinado de alertas de Suricata, Snort e Zeek"""
    validate_api_key(api_key)
    
    async def combined_stream():
        # Criar filas para cada fonte
        queues = {
            "suricata": asyncio.Queue(),
            "snort": asyncio.Queue(),
            "zeek": asyncio.Queue()
        }
        
        # Funções para consumir cada fonte
        async def consume_suricata():
            async for event in alert_stream(LOG_FILE_SURICATA, SURICATA_PATTERN, "suricata"):
                await queues["suricata"].put({"source": "suricata", "event": event})
        
        async def consume_snort():
            async for event in alert_stream(LOG_FILE_SNORT, SNORT_PATTERN, "snort"):
                await queues["snort"].put({"source": "snort", "event": event})
        
        async def consume_zeek():
            dummy_pattern = re.compile(r'.*')
            async for event in alert_stream(LOG_FILE_ZEEK, dummy_pattern, "zeek"):
                await queues["zeek"].put({"source": "zeek", "event": event})
        
        # Iniciar tasks de consumo
        tasks = [
            asyncio.create_task(consume_suricata()),
            asyncio.create_task(consume_snort()),
            asyncio.create_task(consume_zeek())
        ]
        
        # Produzir eventos combinados
        try:
            while True:
                for source in queues:
                    try:
                        item = queues[source].get_nowait()
                        yield item["event"]
                    except asyncio.QueueEmpty:
                        pass
                await asyncio.sleep(0.1)
        finally:
            for task in tasks:
                task.cancel()
    
    return StreamingResponse(
        combined_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# =====================================================
# HEALTHCHECK
# =====================================================
@app.get("/health")
def health():
    # Verificar se os arquivos de log existem
    logs_status = {
        "suricata": os.path.exists(LOG_FILE_SURICATA),
        "snort": os.path.exists(LOG_FILE_SNORT),
        "zeek": os.path.exists(LOG_FILE_ZEEK)
    }
    
    return {
        "status": "ok",
        "logs": logs_status,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    }
@app.get("/debug/zeek-check")
async def debug_zeek(api_key: str = Query(...)):
    """Endpoint de diagnóstico para o Zeek"""
    validate_api_key(api_key)

    result = {
        "file_exists": os.path.exists(LOG_FILE_ZEEK),
        "file_size": 0,
        "can_read": False,
        "sample_lines": [],
        "permissions": None,
        "error": None
    }

    try:
        if result["file_exists"]:
            result["file_size"] = os.path.getsize(LOG_FILE_ZEEK)
            result["permissions"] = oct(os.stat(LOG_FILE_ZEEK).st_mode)[-3:]

            # Tentar ler o arquivo
            with open(LOG_FILE_ZEEK, "r", errors="ignore") as f:
                lines = f.readlines()
                result["total_lines"] = len(lines)
                result["can_read"] = True

                # Pegar amostra das últimas 5 linhas
                for line in lines[-5:]:
                    parsed = parse_zeek_line(line)
                    result["sample_lines"].append({
                        "raw": line.strip(),
                        "parsed": parsed
                    })
    except Exception as e:
        result["error"] = str(e)

    return result
# =====================================================
# LISTAR ALERTAS RECENTES DO ZEEK
# =====================================================
@app.get("/zeek/recent")
async def get_recent_zeek_alerts(
    api_key: str = Query(...),
    limit: int = Query(50, ge=1, le=1000)
):
    """Retorna os alertas mais recentes do Zeek"""
    validate_api_key(api_key)
    
    if not os.path.exists(LOG_FILE_ZEEK):
        raise HTTPException(status_code=404, detail="Arquivo notice.log do Zeek não encontrado")
    
    try:
        alerts = []
        with open(LOG_FILE_ZEEK, "r", errors="ignore") as f:
            lines = f.readlines()
            
        # Processar as últimas 'limit' linhas
        for line in lines[-limit:]:
            parsed = parse_zeek_line(line)
            if parsed:
                alerts.append(parsed)
        
        return {
            "total": len(alerts),
            "alerts": alerts[::-1],  # Mais recentes primeiro
            "source": "zeek"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler logs do Zeek: {str(e)}")
