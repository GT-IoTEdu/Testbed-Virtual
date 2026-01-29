#!/bin/bash
# Script para configurar permissões e rede antes do Zeek

echo "Configurando permissões e rede..."

# Garante que o usuário zeek (se existir) tenha permissões adequadas
if id zeek >/dev/null 2>&1; then
    chown -R zeek:zeek /usr/local/zeek/spool/ 2>/dev/null || true
    chown -R zeek:zeek /usr/local/zeek/etc/ 2>/dev/null || true
fi

# Configura permissões para captura de rede
if command -v setcap >/dev/null 2>&1; then
    # Permite que binários não-root façam captura de rede
    setcap cap_net_raw,cap_net_admin=eip /usr/local/zeek/bin/zeek 2>/dev/null || true
    setcap cap_net_raw,cap_net_admin=eip /usr/bin/tcpdump 2>/dev/null || true
fi

echo "Configuração de permissões concluída."
