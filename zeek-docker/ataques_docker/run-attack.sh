#!/bin/bash
set -e

# Script para executar ataques simulados com visibilidade para o Zeek

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Detectar comando docker-compose moderno (docker compose) ou antigo (docker-compose)
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    echo "[ERROR] nem 'docker compose' nem 'docker-compose' encontrados no PATH."
    exit 1
fi

# Carrega configuração do target
if [ ! -f "target.var" ]; then
    echo "[ERROR] target.var not found. Run ./start-target.sh first"
    exit 1
fi

source target.var

# Função para exibir menu
show_menu() {
    echo ""
    echo "=========================================="
    echo "  SIMIR - Attack Simulation Menu"
    echo "=========================================="
    echo ""
    echo "Target Server: $TARGET_WEB"
    echo ""
    echo "Available Attacks:"
    echo "  1) DoS HTTP         - HTTP Flood Attack"
    echo "  2) Brute Force SSH  - SSH Login Attempts"
    echo "  3) Ping Flood       - ICMP Flood"
    echo "  4) DNS Tunneling    - DNS Exfiltration"
    echo "  5) SQL Injection    - SQL Injection Attempts"
    echo ""
    echo "  0) Exit"
    echo ""
    read -p "Select attack to run: " choice
}

# Função para executar ataque
run_attack() {
    local attack=$1
    local image=$2
    
    echo ""
    echo "[+] Starting $attack attack..."
    
    # Detectar se existe rede simir-net (modo Docker)
    if docker network ls --format '{{.Name}}' | grep -q "^simir-net$"; then
        echo "[+] Running on simir-net (Docker network mode)"
        NETWORK="simir-net"
    else
        echo "[+] Running on host network (Physical interface mode)"
        NETWORK="host"
    fi
    
    echo ""
    
    # Executa no modo apropriado
    docker run --rm --network "$NETWORK" "$image"
    
    echo ""
    echo "=========================================="
    echo "  Attack Completed!"
    echo "=========================================="
    echo ""
    echo "[+] Check Zeek logs:"
    echo "    docker exec SIMIR_Z tail -20 /usr/local/zeek/spool/zeek/notice.log"
    echo ""
    echo "[+] Search for specific alerts:"
    echo "    docker exec SIMIR_Z grep 'DoS\\|DDoS' /usr/local/zeek/spool/zeek/notice.log"
    echo ""
    
    read -p "Press Enter to continue..."
}

# Loop principal
while true; do
    show_menu
    
    case $choice in
        1)
            run_attack "DoS HTTP" "dos-http"
            ;;
        2)
            run_attack "Brute Force SSH" "brute-force-ssh"
            ;;
        3)
            run_attack "Ping Flood" "ping-flood"
            ;;
        4)
            run_attack "DNS Tunneling" "dns-tunneling"
            ;;
        5)
            run_attack "SQL Injection" "sql-injection"
            ;;
        0)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "[ERROR] Invalid option"
            sleep 1
            ;;
    esac
done
