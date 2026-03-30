#!/bin/bash
set -e

# Script para iniciar o servidor alvo SIMIR e configurar os alvos de ataque
# Usa "docker compose" quando disponível, senão cai para "docker-compose"

# Detectar comando docker-compose moderno (docker compose) ou antigo (docker-compose)
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    echo "[ERROR] nem 'docker compose' nem 'docker-compose' encontrados no PATH."
    exit 1
fi

echo "=========================================="
echo "  SIMIR - Target Server Management"
echo "=========================================="
echo ""

# Verifica se a rede simir-net existe
if ! docker network ls --format '{{.Name}}' | grep -q "^simir-net$"; then
    echo "[ERROR] Docker network 'simir-net' not found"
    echo "[INFO] Please start SIMIR with './start-simir.sh' first (Mode 2: Docker Network)"
    exit 1
fi

echo "[INFO] Using Docker network: simir-net"
echo "[INFO] Target IP will be: 172.18.0.2 (fixed)"
echo ""

# Define o IP fixo do target na rede Docker
TARGET_IP="172.18.0.2"

# Atualiza o target.var com o IP fixo do target
echo "[+] Updating target.var configuration..."
cat > target.var << EOF
TARGET_HOST="$TARGET_IP"
TARGET_WEB="$TARGET_IP:80"
TARGET_SSH="$TARGET_IP:22"
TARGET_DNS="8.8.8.8"
EOF

echo "[+] Configuration updated:"
cat target.var
echo ""

# Verifica se o container alvo já está rodando
if docker ps --format '{{.Names}}' | grep -q "^SIMIR_TARGET$"; then
    echo "[INFO] SIMIR_TARGET is already running"
    echo ""
    read -p "Do you want to restart it? (y/n): " restart
    if [ "$restart" = "y" ]; then
        echo "[+] Stopping existing container..."
        $COMPOSE_CMD -f docker-compose-target-net.yml down || true
        sleep 2
    else
        echo "[INFO] Keeping existing container"
        echo ""
        echo "=========================================="
        echo "  Target Server Information"
        echo "=========================================="
        echo "HTTP Service: http://$TARGET_IP"
        echo "SSH Service:  ssh root@$TARGET_IP (password: password123)"
        echo "Network:      simir-net (172.18.0.0/16)"
        echo ""
        echo "Container Status:"
        docker ps --format '{{.Names}}\t{{.Status}}' | grep SIMIR_TARGET || true
        exit 0
    fi
fi

# Builda e inicia o servidor alvo
echo "[+] Building target server image..."
docker build -t simir-target ./target-server

echo ""
echo "[+] Starting SIMIR Target Server (Docker Network Mode)..."
$COMPOSE_CMD -f docker-compose-target-net.yml up -d

# Aguarda o container iniciar
echo "[+] Waiting for services to start..."
sleep 5

# Verifica se está rodando
if docker ps --format '{{.Names}}' | grep -q "^SIMIR_TARGET$"; then
    echo ""
    echo "=========================================="
    echo "  Target Server Started Successfully!"
    echo "=========================================="
    echo ""
    echo "Target Server Information:"
    echo "  - Container: SIMIR_TARGET"
    echo "  - IP Address: $TARGET_IP (fixed)"
    echo "  - Network: simir-net (Docker bridge br-simir)"
    echo "  - HTTP Service: http://$TARGET_IP"
    echo "  - SSH Service:  ssh root@$TARGET_IP (password: password123)"
    echo ""
    echo "Network Monitoring:"
    echo "  - Zeek is monitoring br-simir interface"
    echo "  - All traffic between containers will be captured"
    echo ""
    echo "Testing connectivity from attack containers:"
    
    # Testa HTTP do ataque DoS
    if docker run --rm --network simir-net alpine sh -c "wget -q -O- http://$TARGET_IP" > /dev/null 2>&1; then
        echo "  [OK] HTTP server is responding on simir-net"
    else
        echo "  [WARN] HTTP server may not be ready yet"
    fi
    
    echo ""
    echo "To launch attacks, run:"
    echo "  ./run-attack.sh"
    echo ""
    echo "To view Zeek detections:"
    echo "  docker exec SIMIR_Z tail -f /usr/local/zeek/logs/current/notice.log"
    echo ""
else
    echo ""
    echo "[ERROR] Failed to start target server"
    echo "Check logs: $COMPOSE_CMD -f docker-compose-target-net.yml logs"
    exit 1
fi
