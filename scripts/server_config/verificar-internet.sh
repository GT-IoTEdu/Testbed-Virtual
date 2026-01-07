#!/bin/bash

# Script para verificar status do compartilhamento de internet

echo "=== Status do Compartilhamento de Internet ==="
echo

# Verifica IP forwarding
echo "1. IP Forwarding:"
if [ "$(cat /proc/sys/net/ipv4/ip_forward)" = "1" ]; then
    echo "✓ IP forwarding está ATIVO"
else
    echo "✗ IP forwarding está INATIVO"
fi

echo

# Verifica interfaces
echo "2. Interfaces de rede:"
echo "Interface Internet (eno1):"
ip addr show eno1 2>/dev/null | grep "inet " || echo "  Não configurada"

echo "Interface LAN (enx000ec89f6cc0):"
ip addr show enx000ec89f6cc0 2>/dev/null | grep "inet " || echo "  Não configurada"

echo

# Verifica regras iptables
echo "3. Regras iptables:"
echo "NAT (MASQUERADE):"
if sudo iptables -t nat -L POSTROUTING | grep -q MASQUERADE; then
    echo "✓ Regra NAT configurada"
    sudo iptables -t nat -L POSTROUTING | grep MASQUERADE
else
    echo "✗ Regra NAT não encontrada"
fi

echo "FORWARD:"
if sudo iptables -L FORWARD | grep -q "enx000ec89f6cc0"; then
    echo "✓ Regras FORWARD configuradas"
    sudo iptables -L FORWARD | grep "enx000ec89f6cc0"
else
    echo "✗ Regras FORWARD não encontradas"
fi

echo

# Verifica servidor DHCP
echo "4. Servidor DHCP:"
if command -v dhcpd >/dev/null 2>&1; then
    echo "✓ DHCP server instalado"
    
    if sudo systemctl is-active --quiet isc-dhcp-server; then
        echo "✓ DHCP server está RODANDO"
        
        # Mostra clientes conectados
        echo
        echo "Clientes DHCP ativos:"
        if command -v dhcp-lease-list >/dev/null 2>&1; then
            sudo dhcp-lease-list 2>/dev/null || echo "  Nenhum cliente ativo"
        else
            echo "  (dhcp-lease-list não instalado)"
            echo "  Use: sudo cat /var/lib/dhcp/dhcpd.leases"
        fi
    else
        echo "✗ DHCP server está PARADO"
        echo "  Status: $(sudo systemctl is-failed isc-dhcp-server 2>/dev/null || echo 'unknown')"
    fi
else
    echo "✗ DHCP server não está instalado"
fi

echo

# Verifica conectividade
echo "5. Teste de conectividade:"
echo "Ping para gateway da interface eno1:"
gateway=$(ip route | grep eno1 | grep default | awk '{print $3}')
if [ -n "$gateway" ]; then
    if ping -c 1 -W 2 "$gateway" >/dev/null 2>&1; then
        echo "✓ Gateway ($gateway) acessível"
    else
        echo "✗ Gateway ($gateway) não acessível"
    fi
else
    echo "✗ Gateway não encontrado"
fi

echo

# Instruções para troubleshooting
echo "=== Troubleshooting ==="
echo "Se houver problemas:"
echo "1. Verificar logs DHCP: sudo journalctl -u isc-dhcp-server -f"
echo "2. Reiniciar DHCP: sudo systemctl restart isc-dhcp-server"
echo "3. Verificar config DHCP: sudo cat /etc/dhcp/dhcpd.conf"
echo "4. Verificar leases: sudo cat /var/lib/dhcp/dhcpd.leases"
echo "5. Reexecutar script: sudo ./compartilhar-internet.sh"
