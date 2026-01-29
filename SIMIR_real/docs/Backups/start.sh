#!/bin/bash

# Script de Inicialização do SIMIR - Modo Interativo
# Suporta dois modos: Interface Física ou Rede Docker

set -e

# Detecta diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Funções de log
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Banner
clear
echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                                ║${NC}"
echo -e "${CYAN}║ ${GREEN}SIMIR${NC} - Sistema de Monitoramento de Rede   ${CYAN}║${NC}"
echo -e "${CYAN}║                                                                ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo

# Verifica se está no diretório correto
if [ ! -f "docker-compose.yml" ] || [ ! -f "Dockerfile" ]; then
    log_error "Execute este script no diretório raiz do projeto SIMIR"
    exit 1
fi

# Menu de seleção de modo
echo -e "${CYAN}Selecione o modo de operação:${NC}"
echo
echo -e "  ${GREEN}1)${NC} Modo Interface Física"
echo -e "     ${BLUE}→${NC} Monitora interface de rede física (ex: enp0s31f6)"
echo -e "     ${BLUE}→${NC} Para ambientes de produção ou teste com tráfego real"
echo -e "     ${BLUE}→${NC} Requer tráfego externo para detectar ataques"
echo
echo -e "  ${GREEN}2)${NC} Modo Rede Docker"
echo -e "     ${BLUE}→${NC} Monitora rede Docker virtual (br-simir)"
echo -e "     ${BLUE}→${NC} Tudo na mesma máquina (target + ataques)"
echo -e "     ${BLUE}→${NC} Ideal para laboratório, testes e demonstrações"
echo
echo -e "  ${GREEN}3)${NC} Apenas limpar ambiente (parar containers)"
echo
echo -e "  ${GREEN}0)${NC} Cancelar"
echo
read -p "Escolha uma opção [1-3, 0]: " MODE_CHOICE

case $MODE_CHOICE in
    1)
        MODE="physical"
        ;;
    2)
        MODE="docker"
        ;;
    3)
        MODE="clean"
        ;;
    0)
        log_info "Operação cancelada pelo usuário"
        exit 0
        ;;
    *)
        log_error "Opção inválida"
        exit 1
        ;;
esac

# Função para limpar ambiente
cleanup_environment() {
    log_info "Limpando ambiente anterior..."
    
    # Parar SIMIR se estiver rodando
    if docker ps -a | grep -q SIMIR_Z; then
        log_info "Parando container SIMIR_Z..."
        docker stop SIMIR_Z 2>/dev/null || true
        docker rm SIMIR_Z 2>/dev/null || true
    fi
    
    # Parar target server se estiver rodando
    if docker ps -a | grep -q SIMIR_TARGET; then
        log_info "Parando container SIMIR_TARGET..."
        docker stop SIMIR_TARGET 2>/dev/null || true
        docker rm SIMIR_TARGET 2>/dev/null || true
    fi
    
    # Parar containers de ataque
    for container in dos-http brute-force-ssh ping-flood dns-tunneling sql-injection; do
        if docker ps -a | grep -q "$container"; then
            docker stop "$container" 2>/dev/null || true
            docker rm "$container" 2>/dev/null || true
        fi
    done
    
    log_success "Ambiente limpo"
}

# Apenas limpar
if [ "$MODE" = "clean" ]; then
    cleanup_environment
    log_success "Containers removidos. Use './start-simir.sh' para reiniciar"
    exit 0
fi

# Limpar ambiente antes de começar
cleanup_environment

echo
log_info "Iniciando SIMIR em modo: ${GREEN}$([ "$MODE" = "physical" ] && echo "Interface Física" || echo "Rede Docker")${NC}"
echo

# ============================================================================
# MODO 1: INTERFACE FÍSICA
# ============================================================================
if [ "$MODE" = "physical" ]; then
    log_info "Configurando modo Interface Física..."
    
    # Detectar interface de rede
    DEFAULT_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -1)
    
    echo
    log_info "Interface de rede padrão detectada: ${GREEN}$DEFAULT_INTERFACE${NC}"
    read -p "Usar esta interface? [S/n]: " USE_DEFAULT
    
    if [[ "$USE_DEFAULT" =~ ^[Nn]$ ]]; then
        echo
        log_info "Interfaces disponíveis:"
        ip link show | grep -E "^[0-9]+" | awk '{print "  - " $2}' | sed 's/:$//'
        echo
        read -p "Digite o nome da interface: " CUSTOM_INTERFACE
        ZEEK_INTERFACE=$CUSTOM_INTERFACE
    else
        ZEEK_INTERFACE=$DEFAULT_INTERFACE
    fi
    
    log_info "Interface selecionada: ${GREEN}$ZEEK_INTERFACE${NC}"
    
    # Usar docker-compose padrão ou criar com interface correta
    if ! grep -q "ZEEK_INTERFACE: $ZEEK_INTERFACE" docker-compose.yml; then
        log_warning "Atualizando ZEEK_INTERFACE no docker-compose.yml..."
        sed -i "s/ZEEK_INTERFACE: .*/ZEEK_INTERFACE: $ZEEK_INTERFACE/" docker-compose.yml
    fi
    
    # Construir e iniciar
    log_info "Construindo imagem Docker..."
    docker-compose build --quiet
    
    log_info "Iniciando SIMIR..."
    docker-compose up -d
    
    # Aguardar inicialização
    log_info "Aguardando inicialização do Zeek..."
    sleep 15
    
    # Verificar status
    if docker ps | grep -q SIMIR_Z; then
        log_success "SIMIR iniciado com sucesso!"
        echo
        log_info "Configuração:"
        echo "  • Interface: $ZEEK_INTERFACE"
        echo "  • Container: SIMIR_Z"
        echo "  • Logs: $SCRIPT_DIR/logs/"
        echo
        log_info "Próximos passos:"
        echo -e "  • Ver logs: ${YELLOW}docker logs -f SIMIR_Z${NC}"
        echo -e "  • Testar: ${YELLOW}./scripts/test-complete.sh${NC}"
        echo -e "  • Status: ${YELLOW}docker exec SIMIR_Z zeekctl status${NC}"
        echo
        log_warning "Ataques devem vir de ${YELLOW}outra máquina${NC} na rede"
        log_warning "Tráfego localhost não será detectado"
    else
        log_error "Falha ao iniciar SIMIR"
        docker logs SIMIR_Z 2>&1 | tail -20
        exit 1
    fi

# ============================================================================
# MODO 2: REDE DOCKER
# ============================================================================
elif [ "$MODE" = "docker" ]; then
    log_info "Configurando modo Rede Docker..."
    
    # Verificar se rede simir-net existe
    if ! docker network ls | grep -q simir-net; then
        log_info "Criando rede Docker simir-net..."
        docker network create \
            --driver bridge \
            --subnet 172.18.0.0/16 \
            --gateway 172.18.0.1 \
            --opt com.docker.network.bridge.name=br-simir \
            simir-net
        log_success "Rede simir-net criada (172.18.0.0/16)"
    else
        log_info "Rede simir-net já existe"
    fi
    
    # Backup do docker-compose.yml se necessário
    if [ ! -f "docker-compose.yml.bak" ]; then
        log_info "Criando backup do docker-compose.yml..."
        cp docker-compose.yml docker-compose.yml.bak
    fi
    
    # Usar configuração para Docker network
    if [ ! -f "docker-compose.yml.docker-net" ]; then
        log_error "Arquivo docker-compose.yml.docker-net não encontrado"
        log_info "Execute: cd ataques_docker && ./setup-docker-monitoring.sh"
        exit 1
    fi
    
    log_info "Construindo imagem Docker..."
    docker-compose -f docker-compose.yml.docker-net build --quiet
    
    log_info "Iniciando SIMIR (monitorando br-simir)..."
    docker-compose -f docker-compose.yml.docker-net up -d
    
    # Aguardar SIMIR inicializar
    log_info "Aguardando inicialização do Zeek..."
    sleep 10
    
    # Iniciar target server
    log_info "Iniciando servidor alvo na rede Docker..."
    cd ataques_docker
    
    # Verificar se imagem do target existe
    if ! docker images | grep -q simir-target; then
        log_info "Construindo imagem do target server..."
        docker build -t simir-target -f target-server/Dockerfile target-server/ --quiet
    fi
    
    docker-compose -f docker-compose-target-net.yml up -d
    
    # Aguardar target inicializar
    sleep 5
    
    # Atualizar target.var
    log_info "Atualizando configuração de alvos..."
    cat > target.var << EOF
TARGET_HOST="172.18.0.2"
TARGET_WEB="172.18.0.2"
TARGET_SSH="172.18.0.2"
TARGET_DNS="8.8.8.8"
EOF
    
    # Construir imagens de ataque
    log_info "Construindo imagens de ataque..."
    
    for attack in dos-http brute-force-ssh ping-flood dns-tunneling sql-injection; do
        if [ -d "$attack" ]; then
            log_info "  → Building $attack..."
            docker build -t "$attack" -f "$attack/Dockerfile" . --quiet 2>/dev/null || true
        fi
    done
    
    cd "$SCRIPT_DIR"
    
    # Verificar status
    if docker ps | grep -q SIMIR_Z && docker ps | grep -q SIMIR_TARGET; then
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
    else
        log_error "Falha ao iniciar ambiente Docker"
        echo
        log_info "Status dos containers:"
        docker ps -a | grep -E "SIMIR_Z|SIMIR_TARGET"
        echo
        log_info "Logs do SIMIR:"
        docker logs SIMIR_Z 2>&1 | tail -20
        exit 1
    fi
fi

echo
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  ${GREEN}SIMIR está pronto para monitoramento!${NC}${CYAN} ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo
