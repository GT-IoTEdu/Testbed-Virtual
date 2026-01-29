#!/bin/bash

# Script para compartilhar internet e configurar DHCP
# Interface com acesso à Internet
INTERNET_IF="eno1"

# Interface da rede interna
LAN_IF="enx000ec89f6cc0"

# Configurações da rede interna
LAN_IP="192.168.50.1"
LAN_NETWORK="192.168.50.0/24"
DHCP_START="192.168.50.10"
DHCP_END="192.168.50.100"

echo "=== Configurando compartilhamento de internet ==="
echo "Interface Internet: $INTERNET_IF"
echo "Interface LAN: $LAN_IF"
echo "IP da LAN: $LAN_IP"

# Verifica se as interfaces existem
if ! ip link show $INTERNET_IF >/dev/null 2>&1; then
    echo "ERRO: Interface $INTERNET_IF não encontrada!"
    exit 1
fi

if ! ip link show $LAN_IF >/dev/null 2>&1; then
    echo "ERRO: Interface $LAN_IF não encontrada!"
    exit 1
fi

# Remove configurações antigas do ethtool que podem causar problemas
echo "Configurando interface $LAN_IF..."
sudo ethtool -K $LAN_IF rx on tx on 2>/dev/null || true

# Configura IP da interface LAN se não estiver configurado
current_ip=$(ip addr show $LAN_IF | grep -oE "inet [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" | cut -d' ' -f2)
if [ "$current_ip" != "$LAN_IP" ]; then
    echo "Configurando IP $LAN_IP na interface $LAN_IF..."
    sudo ip addr flush dev $LAN_IF
    sudo ip addr add $LAN_IP/24 dev $LAN_IF
    sudo ip link set $LAN_IF up
fi
# Ativa IP forwarding
echo "Ativando IP forwarding..."
sudo sysctl -w net.ipv4.ip_forward=1

# Torna permanente o IP forwarding
if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo "Tornando IP forwarding permanente..."
    echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
fi

# Remove regras antigas para evitar duplicatas
echo "Limpando regras antigas do iptables..."
sudo iptables -t nat -D POSTROUTING -o $INTERNET_IF -j MASQUERADE 2>/dev/null || true
sudo iptables -D FORWARD -i $INTERNET_IF -o $LAN_IF -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true
sudo iptables -D FORWARD -i $LAN_IF -o $INTERNET_IF -j ACCEPT 2>/dev/null || true

# Configura regras de NAT e redirecionamento
echo "Configurando regras do iptables..."
sudo iptables -t nat -A POSTROUTING -o $INTERNET_IF -j MASQUERADE
sudo iptables -A FORWARD -i $INTERNET_IF -o $LAN_IF -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i $LAN_IF -o $INTERNET_IF -j ACCEPT

# Salva regras do iptables
echo "Salvando regras do iptables..."
sudo iptables-save | sudo tee /etc/iptables/rules.v4 >/dev/null 2>&1 || echo "Aviso: Não foi possível salvar regras permanentemente"

# Configura servidor DHCP
echo "Configurando servidor DHCP..."

# Verifica se o isc-dhcp-server está instalado
if ! command -v dhcpd >/dev/null 2>&1; then
    echo "Instalando servidor DHCP..."
    sudo apt update
    sudo apt install -y isc-dhcp-server
fi

# Cria configuração do DHCP
DHCP_CONF="/etc/dhcp/dhcpd.conf"
echo "Criando configuração DHCP em $DHCP_CONF..."

sudo tee $DHCP_CONF > /dev/null <<EOF
# Configuração DHCP para compartilhamento de internet
default-lease-time 600;
max-lease-time 7200;

# Configuração da rede local
subnet 192.168.50.0 netmask 255.255.255.0 {
    range $DHCP_START $DHCP_END;
    option routers $LAN_IP;
    option domain-name-servers 8.8.8.8, 8.8.4.4;
    option broadcast-address 192.168.50.255;
    default-lease-time 600;
    max-lease-time 7200;
}
EOF

# Configura interface para o DHCP
echo "Configurando interface para DHCP..."
echo "INTERFACESv4=\"$LAN_IF\"" | sudo tee /etc/default/isc-dhcp-server

# Reinicia o serviço DHCP
echo "Reiniciando servidor DHCP..."
sudo systemctl stop isc-dhcp-server 2>/dev/null || true
sudo systemctl start isc-dhcp-server
sudo systemctl enable isc-dhcp-server

# Verifica status do DHCP
if sudo systemctl is-active --quiet isc-dhcp-server; then
    echo "✓ Servidor DHCP iniciado com sucesso!"
else
    echo "⚠ Problema com o servidor DHCP. Verificando logs..."
    sudo systemctl status isc-dhcp-server --no-pager -l
    echo "Para mais detalhes: sudo journalctl -u isc-dhcp-server -f"
fi

echo
echo "=== Configuração concluída ==="
echo "Interface LAN: $LAN_IF ($LAN_IP)"
echo "Range DHCP: $DHCP_START - $DHCP_END"
echo "Gateway: $LAN_IP"
echo "DNS: 8.8.8.8, 8.8.4.4"
echo
echo "Para testar:"
echo "1. Conecte um dispositivo na interface $LAN_IF"
echo "2. Configure para obter IP automaticamente (DHCP)"
echo "3. O dispositivo deve receber IP entre $DHCP_START e $DHCP_END"
echo
echo "Para verificar clientes DHCP:"
echo "sudo dhcp-lease-list"
echo "ou"
echo "sudo cat /var/lib/dhcp/dhcpd.leases"
