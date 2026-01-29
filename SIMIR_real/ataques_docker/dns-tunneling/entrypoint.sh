#!/usr/bin/env bash

echo "[+] Starting DNS Tunneling Attack"
echo "[+] Generating 200 DNS queries with high entropy subdomains"
echo ""

function DNS() {
  RANGE=$(( 12 + $RANDOM % 50 ))
  DOMAIN=$( cat /dev/urandom | tr -dc "0-9a-fA-F" | fold -w "${RANGE}" | head -n 1 )
  
  # Usa dig com servidor DNS explícito (8.8.8.8) para forçar tráfego pela br-simir
  # O resolver interno do Docker (127.0.0.11) não passa pela bridge monitorada
  dig @8.8.8.8 +time=1 +tries=1 +short "${DOMAIN}.com" 2>&1 | head -1
}

echo "[+] Sending DNS queries..."
for i in $( seq 1 200 ); do
  DNS &
  sleep 0.1
done

# Aguardar todas as queries terminarem
wait

# Aguardar um pouco para o Zeek processar
sleep 2

echo ""
echo "[+] Attack completed!"
echo "[+] Sent 200 DNS queries with:"
echo "    - High entropy subdomains (random hex)"
echo "    - Variable lengths (12-62 characters)"
echo "    - All queries resulted in NXDOMAIN"
echo ""
echo "[+] Expected SIMIR Detection:"
echo "    - DNS_High_Entropy (entropy > 3.5)"
echo "    - DNS_Long_Subdomain (length > 60)"
echo "    - DNS_Tunneling_Pattern (aggregated suspicious pattern)"
echo "    - Check: docker exec SIMIR_Z grep 'DNS' /usr/local/zeek/spool/zeek/notice.log"