#!/bin/bash

echo "[SIMIR Target Server] Starting services..."

# Inicia SSH
echo "[+] Starting SSH server on port 22..."
/usr/sbin/sshd

# Configura e inicia FTP (se necessário)
# echo "[+] Starting FTP server on port 21..."
# vsftpd &

# Inicia Nginx
echo "[+] Starting HTTP server on port 80..."
echo "[+] Server ready for attack simulation"
echo "[+] Accessible at: http://$(hostname -i)"
echo ""
echo "Available services:"
echo "  - HTTP: port 80"
echo "  - SSH: port 22 (root/password123)"
echo ""
echo "Server is running and waiting for connections..."

# Mantém o container rodando com Nginx em foreground
nginx -g 'daemon off;'
