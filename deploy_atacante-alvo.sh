#!/bin/bash

# Limpar containers antigos
docker rm -f servidor_alvo atacante 2>/dev/null

# Criar container servidor_alvo (sem --mac-address pois será sobrescrito)
docker run -d --name servidor_alvo --hostname servidor_alvo \
    --network none \
    --cap-add NET_ADMIN --cap-add NET_RAW \
    servidor_alvo:latest sleep infinity








sleep 10
# Obter IP
SERVER_ALVO=$(docker exec servidor_alvo ip -4 addr show eth0 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}')


echo "IP do servidor: $SERVER_ALVO"

# Container atacante
docker run -d --name atacante --hostname atacante \
    --network none \
    --cap-add NET_ADMIN --cap-add NET_RAW \
    -e SERVER_IP="$SERVER_ALVO" \
    atacante:latest sleep infinity


