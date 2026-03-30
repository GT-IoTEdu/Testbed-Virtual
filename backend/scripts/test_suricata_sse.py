#!/usr/bin/env python3
"""
Script de teste para verificar a conexão SSE do Suricata.

Este script testa:
1. Conexão direta com o servidor Suricata
2. Conexão através do proxy da nossa API
3. Formato dos dados recebidos

Uso:
    python scripts/test_suricata_sse.py
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configurações
SURICATA_DIRECT_URL = "http://192.168.1.128:8001/sse/alerts?api_key=a8f4c2d9-1c9b-4b6f-9d6e-aaa111bbb222"
API_PROXY_URL = "http://127.0.0.1:8000/api/scanners/suricata/sse/alerts"
USER_ID = 1  # Ajuste conforme necessário
INSTITUTION_ID = 1  # Ajuste conforme necessário

def test_direct_connection():
    """Testa conexão direta com o servidor Suricata"""
    print("=" * 80)
    print("TESTE 1: Conexão Direta com Suricata")
    print("=" * 80)
    print(f"URL: {SURICATA_DIRECT_URL}")
    print()
    
    try:
        response = requests.get(
            SURICATA_DIRECT_URL,
            stream=True,
            timeout=10,
            headers={
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache'
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print()
        
        if response.status_code != 200:
            print(f"❌ Erro: Status {response.status_code}")
            print(response.text[:500])
            return False
        
        print("✅ Conexão estabelecida. Aguardando eventos (máximo 30 segundos)...")
        print()
        
        start_time = time.time()
        timeout = 30  # 30 segundos
        event_count = 0
        buffer = ""
        last_data_time = start_time
        
        try:
            for line in response.iter_lines(decode_unicode=False):
                current_time = time.time()
                
                # Timeout geral
                if current_time - start_time > timeout:
                    print(f"\n⏱️ Timeout após {timeout} segundos")
                    break
                
                # Se não receber dados por 10 segundos, considerar que não há mais eventos
                if line:
                    last_data_time = current_time
                elif current_time - last_data_time > 10:
                    print(f"\n⏱️ Sem eventos há 10 segundos, finalizando...")
                    break
                
                if line:
                    try:
                        line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                        buffer += line_str + "\n"
                        
                        # SSE termina com duas quebras de linha
                        if buffer.endswith("\n\n"):
                            event_data = buffer.strip()
                            if event_data:
                                print(f"📨 Evento {event_count + 1}:")
                                print(event_data)
                                print()
                                
                                if event_data.startswith('data: '):
                                    json_str = event_data[6:].strip()
                                    try:
                                        alert = json.loads(json_str)
                                        print(f"   ✅ JSON válido:")
                                        print(f"      - Timestamp: {alert.get('timestamp', 'N/A')}")
                                        print(f"      - SID: {alert.get('sid', 'N/A')}")
                                        print(f"      - Message: {alert.get('message', 'N/A')[:80]}...")
                                        print(f"      - Protocol: {alert.get('protocol', 'N/A')}")
                                        print(f"      - Source: {alert.get('src', 'N/A')}")
                                        print(f"      - Dest: {alert.get('dst', 'N/A')}")
                                        print()
                                    except json.JSONDecodeError as e:
                                        print(f"   ⚠️ Erro ao parsear JSON: {e}")
                                        print(f"   Dados: {json_str[:200]}")
                                        print()
                                
                                event_count += 1
                                
                                if event_count >= 5:  # Limitar a 5 eventos para teste
                                    print("\n✅ Teste concluído (5 eventos recebidos)")
                                    break
                            
                            buffer = ""
                    except Exception as e:
                        print(f"⚠️ Erro ao processar linha: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                elif buffer:
                    # Linha vazia pode indicar fim de evento
                    if buffer.endswith('\n'):
                        buffer += "\n"
                    else:
                        buffer += "\n"
        finally:
            response.close()
        
        return True
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Erro de conexão: {e}")
        print("   Verifique se o servidor Suricata está rodando em 192.168.1.128:8001")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_proxy():
    """Testa conexão através do proxy da nossa API"""
    print("=" * 80)
    print("TESTE 2: Conexão através do Proxy da API")
    print("=" * 80)
    print(f"URL: {API_PROXY_URL}?user_id={USER_ID}")
    print()
    
    try:
        url = f"{API_PROXY_URL}?user_id={USER_ID}"
        if INSTITUTION_ID:
            url += f"&institution_id={INSTITUTION_ID}"
        
        response = requests.get(
            url,
            stream=True,
            timeout=10,
            headers={
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache'
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print()
        
        if response.status_code != 200:
            print(f"❌ Erro: Status {response.status_code}")
            try:
                error_text = response.text[:500]
                print(error_text)
            except:
                pass
            return False
        
        print("✅ Conexão estabelecida. Aguardando eventos (máximo 30 segundos)...")
        print()
        
        start_time = time.time()
        timeout = 30  # 30 segundos
        event_count = 0
        buffer = ""
        last_data_time = start_time
        
        try:
            for line in response.iter_lines(decode_unicode=False):
                current_time = time.time()
                
                # Timeout geral
                if current_time - start_time > timeout:
                    print(f"\n⏱️ Timeout após {timeout} segundos")
                    break
                
                # Se não receber dados por 10 segundos, considerar que não há mais eventos
                if line:
                    last_data_time = current_time
                elif current_time - last_data_time > 10:
                    print(f"\n⏱️ Sem eventos há 10 segundos, finalizando...")
                    break
                
                if line:
                    try:
                        line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                        buffer += line_str + "\n"
                        
                        # SSE termina com duas quebras de linha
                        if buffer.endswith("\n\n"):
                            event_data = buffer.strip()
                            if event_data:
                                print(f"📨 Evento {event_count + 1}:")
                                print(event_data)
                                print()
                                
                                if event_data.startswith('data: '):
                                    json_str = event_data[6:].strip()
                                    try:
                                        data = json.loads(json_str)
                                        print(f"   ✅ JSON válido:")
                                        print(f"   Tipo: {data.get('type', 'N/A')}")
                                        
                                        if data.get('type') == 'alert' and 'alert' in data:
                                            alert = data['alert']
                                            print(f"   Alerta:")
                                            print(f"     - Timestamp: {alert.get('timestamp', 'N/A')}")
                                            print(f"     - Signature: {alert.get('signature', 'N/A')}")
                                            print(f"     - Severity: {alert.get('severity', 'N/A')}")
                                            print(f"     - Source IP: {alert.get('src_ip', 'N/A')}")
                                            print(f"     - Dest IP: {alert.get('dest_ip', 'N/A')}")
                                        elif data.get('type') == 'connected':
                                            print(f"   Mensagem: {data.get('message', 'N/A')}")
                                        elif data.get('type') == 'error':
                                            print(f"   ❌ Erro: {data.get('message', 'N/A')}")
                                        
                                        print()
                                    except json.JSONDecodeError as e:
                                        print(f"   ⚠️ Erro ao parsear JSON: {e}")
                                        print(f"   Dados: {json_str[:200]}")
                                        print()
                                
                                event_count += 1
                                
                                if event_count >= 5:  # Limitar a 5 eventos para teste
                                    print("\n✅ Teste concluído (5 eventos recebidos)")
                                    break
                            
                            buffer = ""
                    except Exception as e:
                        print(f"⚠️ Erro ao processar linha: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                elif buffer:
                    # Linha vazia pode indicar fim de evento
                    if buffer.endswith('\n'):
                        buffer += "\n"
                    else:
                        buffer += "\n"
        finally:
            response.close()
        
        return True
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Erro de conexão: {e}")
        print("   Verifique se a API está rodando em http://127.0.0.1:8000")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 80)
    print("SCRIPT DE TESTE - CONEXÃO SSE SURICATA")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Teste 1: Conexão direta
    direct_ok = test_direct_connection()
    
    print("\n")
    
    # Teste 2: Conexão via proxy
    proxy_ok = test_api_proxy()
    
    print("\n" + "=" * 80)
    print("RESUMO DOS TESTES")
    print("=" * 80)
    print(f"Conexão Direta: {'✅ PASSOU' if direct_ok else '❌ FALHOU'}")
    print(f"Conexão via Proxy: {'✅ PASSOU' if proxy_ok else '❌ FALHOU'}")
    print()
    
    if direct_ok and not proxy_ok:
        print("⚠️ CONCLUSÃO: O servidor Suricata está funcionando, mas há problema no proxy da API")
        print("   Verifique:")
        print("   1. Se a configuração do Suricata está correta no banco de dados")
        print("   2. Se o backend consegue acessar o servidor Suricata (192.168.1.128:8001)")
        print("   3. Os logs do backend para mais detalhes")
    elif not direct_ok:
        print("⚠️ CONCLUSÃO: O servidor Suricata não está acessível")
        print("   Verifique:")
        print("   1. Se o servidor Suricata está rodando")
        print("   2. Se o IP e porta estão corretos (192.168.1.128:8001)")
        print("   3. Se há firewall bloqueando a conexão")
    elif direct_ok and proxy_ok:
        print("✅ CONCLUSÃO: Tudo funcionando corretamente!")
        print("   Se os alertas não aparecem no frontend, verifique:")
        print("   1. O console do navegador para erros JavaScript")
        print("   2. Se o EventSource está conectando corretamente")
        print("   3. Se os dados estão sendo processados no frontend")
    
    print("=" * 80)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
        sys.exit(0)
