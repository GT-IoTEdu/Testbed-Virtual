#!/bin/bash

# Script de inicialização do Snort3
# Uso: ./start_snort.sh [interface] [opções adicionais]

# Define interface padrão se não fornecida
INTERFACE=${1:-enp0s3}

# Remove o primeiro argumento (interface) para passar o resto para o snort
shift

# Exibe informações de inicialização
echo "=========================================="
echo "       Snort3 Detector Iniciando"
echo "=========================================="
echo "Interface: $INTERFACE"
echo "Config: /opt/snort3/etc/snort/snort.lua"
echo "Rules: /opt/snort3/etc/snort/rules/local.rules"
echo "Logs: /opt/snort3/logs/"
echo "=========================================="

# Verifica se a interface existe
if ! ip link show "$INTERFACE" > /dev/null 2>&1; then
    echo "ERRO: Interface '$INTERFACE' não encontrada!"
    echo "Interfaces disponíveis:"
    ip link show | grep -E '^[0-9]+:' | awk '{print $2}' | tr -d ':'
    exit 1
fi

# Testa a configuração antes de iniciar
echo "Testando configuração do Snort3..."
if ! snort -c /opt/snort3/etc/snort/snort.lua -T; then
    echo "ERRO: Configuração do Snort3 inválida!"
    exit 1
fi

echo "Configuração OK! Iniciando Snort3..."
echo "Para parar: Ctrl+C"
echo "=========================================="

# Inicia o Snort3 com os parâmetros fornecidos
exec snort -c /opt/snort3/etc/snort/snort.lua -i "$INTERFACE" -v -l /opt/snort3/logs "$@"