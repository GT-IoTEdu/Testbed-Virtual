#!/bin/bash
set -e

# Script para executar ataques simulados com visibilidade para o Zeek

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detectar comando docker-compose
detect_compose_cmd() {
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        echo "docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose"
    else
        log_error "Nem 'docker compose' nem 'docker-compose' encontrados no PATH."
        exit 1
    fi
}

COMPOSE_CMD=$(detect_compose_cmd)

# Função principal
main() {
    # Carrega configuração do target
    if [ ! -f "target.var" ]; then
        log_info "Arquivo target.var não encontrado. Criando configuração padrão..."
        create_target_config
    else
        source target.var
    fi

    setup_environment
}

create_target_config() {
    cat > target.var << EOF
TARGET_HOST="172.18.0.2"
TARGET_WEB="172.18.0.2"
TARGET_SSH="172.18.0.2"
TARGET_DNS="8.8.8.8"
EOF
    log_success "Arquivo target.var criado com configuração padrão"
}

setup_environment() {
    log_info "Configurando ambiente Docker..."

    # Verificar se a rede existe
    if ! docker network ls | grep -q "simir-net"; then
        log_info "Criando rede simir-net..."
        docker network create --subnet=172.18.0.0/16 simir-net
    fi

    build_attack_images
    check_container_status
}

build_attack_images() {
    log_info "Construindo imagens de ataque..."

    local attacks=("dos-http" "brute-force-ssh" "ping-flood" "dns-tunneling" "sql-injection")

    for attack in "${attacks[@]}"; do
        if [ -d "$attack" ]; then
            log_info "  → Building $attack..."
            if docker build -t "$attack" -f "$attack/Dockerfile" . --quiet 2>/dev/null; then
                log_success "    ✓ $attack construída com sucesso"
            else
                log_error "    ✗ Falha ao construir $attack"
            fi
        else
            log_warning "    ! Diretório $attack não encontrado"
        fi
    done
}

check_container_status() {
    log_info "Verificando status dos containers..."

    local zeek_running=false
    local target_running=false

    if docker ps --format '{{.Names}}' | grep -q "^SIMIR_Z$"; then
        zeek_running=true
    fi

    if docker ps --format '{{.Names}}' | grep -q "^SIMIR_TARGET$"; then
        target_running=true
    fi

    if $zeek_running && $target_running; then
        display_success_message
    else
        display_error_message
    fi
}

display_success_message() {
    log_success "Ambiente Docker configurado com sucesso!"
    echo
    log_info "Configuração:"
    echo "  • Rede: simir-net (172.18.0.0/16)"
    echo "  • Bridge: br-simir (monitorada pelo Zeek)"
    echo "  • Zeek Container: SIMIR_Z"
    echo "  • Target Server: SIMIR_TARGET (172.18.0.2)"
    echo "  • Logs: $SCRIPT_DIR/logs/"
    echo
    log_info "Containers de ataque disponíveis:"
    echo "  • dos-http"
    echo "  • brute-force-ssh"
    echo "  • ping-flood"
    echo "  • dns-tunneling"
    echo "  • sql-injection"
    echo
    log_info "Para executar ataques:"
    echo -e "  ${YELLOW}docker run --rm --network simir-net dos-http${NC}"
    echo -e "  ${YELLOW}docker run --rm --network simir-net brute-force-ssh${NC}"
    echo -e "  ${YELLOW}docker run --rm --network simir-net ping-flood${NC}"
    echo
    log_info "Monitorar detecções:"
    echo -e "  ${YELLOW}docker exec SIMIR_Z tail -f /usr/local/zeek/spool/zeek/notice.log${NC}"
    echo
    log_info "Menu interativo de ataques:"
    echo -e "  ${YELLOW}cd ataques_docker && ./run-attack.sh${NC}"
    echo
    log_success "Todos os ataques serão detectados pelo Zeek!"
}

display_error_message() {
    log_error "Falha ao iniciar ambiente Docker"
    echo
    log_info "Status dos containers:"
    docker ps -a | grep -E "SIMIR_Z|SIMIR_TARGET" || echo "Nenhum container encontrado"
    echo
    log_info "Tente iniciar os containers manualmente:"
    echo "  $COMPOSE_CMD up -d"
}

# Executar função principal
main "$@"
