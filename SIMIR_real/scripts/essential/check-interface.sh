#!/bin/bash

# Script para verificar interface de rede
IFACE="${1:-enx000ec89f6cc0}"

echo "=== Verificação da Interface de Rede ==="
echo "Interface: $IFACE"
echo

# Verifica se a interface existe
if ip link show "$IFACE" >/dev/null 2>&1; then
    echo "✓ Interface $IFACE encontrada"
else
    echo "✗ Interface $IFACE não encontrada!"
    echo
    echo "Interfaces disponíveis:"
    ip link show | grep -E "^[0-9]+:" | cut -d: -f2 | sed 's/^ *//'
    exit 1
fi

# Verifica se a interface está ativa
if ip link show "$IFACE" | grep -q "state UP"; then
    echo "✓ Interface $IFACE está UP"
else
    echo "✗ Interface $IFACE está DOWN"
    echo "Tentando ativar interface..."
    if ip link set "$IFACE" up; then
        echo "✓ Interface ativada com sucesso"
    else
        echo "✗ Falha ao ativar interface"
        exit 1
    fi
fi

# Verifica se há tráfego na interface
echo
echo "Testando captura de pacotes na interface $IFACE por 5 segundos..."
if timeout 5 tcpdump -i "$IFACE" -c 1 >/dev/null 2>&1; then
    echo "✓ Captura de pacotes funcionando na interface $IFACE"
else
    echo "⚠ Não foi possível capturar pacotes ou não há tráfego na interface $IFACE"
    echo "Isso pode ser normal se não houver tráfego de rede no momento."
fi

echo
echo "=== Informações da Interface ==="
ip addr show "$IFACE" 2>/dev/null || echo "Não foi possível obter informações detalhadas"

echo
echo "=== Estatísticas da Interface ==="
cat "/sys/class/net/$IFACE/statistics/rx_packets" 2>/dev/null | awk '{print "Pacotes recebidos: " $1}' || echo "Estatísticas não disponíveis"
cat "/sys/class/net/$IFACE/statistics/tx_packets" 2>/dev/null | awk '{print "Pacotes enviados: " $1}' || echo "Estatísticas não disponíveis"
