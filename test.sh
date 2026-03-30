#!/bin/bash
echo "=== Host Information ==="
echo "IP Forwarding: $(cat /proc/sys/net/ipv4/ip_forward)"
echo "Host IPs: $(hostname -I)"
echo ""

echo "=== Port 8001 Listening ==="
sudo netstat -tlnp | grep 8001 || echo "Port 8001 not listening"
echo ""

echo "=== Docker Bridge Info ==="
ip addr show docker0
echo ""

echo "=== Docker Network Info ==="
docker network inspect bridge | grep -A 5 "Gateway"
echo ""

echo "=== Testing localhost from host ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health || echo "Failed"
echo ""

echo "=== Testing from container ==="
docker exec -it 9cb5dd2b4410 curl -s -o /dev/null -w "%{http_code}" http://172.17.0.1:8001/health || echo "Failed"
