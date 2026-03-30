#!/usr/bin/env python3
"""
Monitor de Conexão - Log único com múltiplas sessões
Não sobrescreve, apenas adiciona novas sessões
"""

import subprocess
import time
import sys
import os
from datetime import datetime

# Configurações
URL = "http://google.com"
LOG_FILE = "acesso_log_completo.txt"

print("=" * 60)
print("MONITOR DE CONEXÃO")
print("=" * 60)
print(f"Monitorando acesso a: {URL}")
print(f"Log salvo em: {LOG_FILE}")
print("Pressione CTRL+C para parar")
print("=" * 60)

# Se arquivo não existe, criar. Se existe, adicionar nova sessão
file_exists = os.path.exists(LOG_FILE)
session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

with open(LOG_FILE, 'a', encoding='utf-8') as f:
    f.write("\n" + "=" * 60 + "\n")
    f.write(f"SESSAO: {session_id}\n")
    f.write(f"INICIO: {datetime.now()}\n")
    f.write(f"URL: {URL}\n")
    f.write("-" * 50 + "\n")

# Verificar se curl está disponível
curl_available = True
try:
    subprocess.run(["curl", "--version"], capture_output=True, check=True, shell=True)
except (subprocess.CalledProcessError, FileNotFoundError):
    curl_available = False
    print("AVISO: curl não encontrado. Usando método alternativo...")

# Função para testar conexão
def test_connection():
    if curl_available:
        try:
            result = subprocess.run(
                ["curl", "-s", "--connect-timeout", "5", "--max-time", "10", URL],
                capture_output=True,
                text=True,
                timeout=11,
                shell=True
            )
            return result.returncode == 0
        except:
            return False
    else:
        import urllib.request
        try:
            response = urllib.request.urlopen(URL, timeout=5)
            return response.getcode() == 200
        except:
            return False

# Variáveis para controle
primeiro_bloqueio = None
consecutive_failures = 0
MAX_FAILURES = 3
total_checks = 0
successful_checks = 0

try:
    while True:
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_checks += 1
        
        if test_connection():
            status = f"OK - {timestamp_str}"
            status_display = f"[OK] {timestamp_str}"
            consecutive_failures = 0
            successful_checks += 1
            primeiro_bloqueio = None
        else:
            status = f"FALHA - {timestamp_str}"
            status_display = f"[FALHA] {timestamp_str}"
            consecutive_failures += 1
            
            if primeiro_bloqueio is None:
                primeiro_bloqueio = timestamp_str
        
        # Registrar no log
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(status + "\n")
        
        # Exibir no console (sobrescrevendo a mesma linha)
        print(f"\r{status_display} | Checks: {total_checks} | OK: {successful_checks} ({successful_checks/total_checks*100:.1f}%)", end="")
        
        # Verificar se perdeu conexão completamente
        if consecutive_failures >= MAX_FAILURES:
            print(f"\n\n{'!' * 60}")
            print("CONEXAO PERDIDA - Encerrando monitoramento")
            print(f"{'!' * 60}")
            
            # Registrar fim da sessão
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write("-" * 50 + "\n")
                f.write(f"FIM DA SESSAO: {datetime.now()}\n")
                f.write(f"TOTAL CHECKS: {total_checks}\n")
                f.write(f"CHECKS OK: {successful_checks}\n")
                f.write(f"TAXA DE SUCESSO: {successful_checks/total_checks*100:.1f}%\n")
                if primeiro_bloqueio:
                    f.write(f"PRIMEIRA FALHA: {primeiro_bloqueio}\n")
                    # Calcular tempo até falha
                    primeiro_dt = datetime.strptime(primeiro_bloqueio, "%Y-%m-%d %H:%M:%S")
                    tempo_ate_falha = (datetime.now() - primeiro_dt).total_seconds()
                    f.write(f"TEMPO ATE FALHA TOTAL: {tempo_ate_falha:.1f}s\n")
                f.write("=" * 50 + "\n")
            
            print(f"\n✅ Log salvo em: {LOG_FILE}")
            print(f"📁 Sessão: {session_id}")
            print(f"📊 Estatísticas:")
            print(f"   • Total de checks: {total_checks}")
            print(f"   • Checks OK: {successful_checks}")
            print(f"   • Taxa de sucesso: {successful_checks/total_checks*100:.1f}%")
            if primeiro_bloqueio:
                print(f"   • Primeira falha: {primeiro_bloqueio}")
            sys.exit(0)
        
        time.sleep(1)
        
except KeyboardInterrupt:
    print(f"\n\n⏹️ Monitoramento interrompido pelo usuario")
    
    # Registrar interrupção
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write("-" * 50 + "\n")
        f.write(f"INTERROMPIDO: {datetime.now()}\n")
        f.write(f"TOTAL CHECKS: {total_checks}\n")
        f.write(f"CHECKS OK: {successful_checks}\n")
        f.write(f"TAXA DE SUCESSO: {successful_checks/total_checks*100:.1f}%\n")
        f.write("=" * 50 + "\n")
    
    print(f"✅ Log salvo em: {LOG_FILE}")
    print(f"📁 Sessão: {session_id}")
    
except Exception as e:
    print(f"\n❌ Erro inesperado: {e}")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"ERRO: {e}\n")