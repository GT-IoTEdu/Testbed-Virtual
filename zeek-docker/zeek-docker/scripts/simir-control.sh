#!/bin/bash

# SIMIR - Sistema Inteligente de Monitoramento de Rede
# Script principal de gerenciamento

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="/tmp/simir_config.json"
EMAIL_CONFIG_FILE="/tmp/simir_email_config.env"
PID_FILE="/tmp/simir_monitor.pid"

# Funções utilitárias
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_banner() {
    echo -e "${PURPLE}"
    cat << "EOF"
   _____ _____ __  __ _____ _____  
  / ____|_   _|  \/  |_   _|  __ \ 
 | (___   | | | \  / | | | | |__) |
  \___ \  | | | |\/| | | | |  _  / 
  ____) |_| |_| |  | |_| |_| | \ \ 
 |_____/|_____|_|  |_|_____|_|  \_\
                                  
 Sistema Inteligente de Monitoramento
 de Rede com Detecção de Port Scan
EOF
    echo -e "${NC}"
    echo -e "${BLUE}Versão 2.0 - Monitor Avançado${NC}"
    echo
}

# Verificar dependências
check_dependencies() {
    log_info "Verificando dependências..."
    
    local missing_deps=()
    
    # Python 3
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Docker
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    # Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Dependências faltando: ${missing_deps[*]}"
        log_info "Instale as dependências e tente novamente"
        exit 1
    fi
    
    log_success "Todas as dependências estão disponíveis"
}

# Configurar email
configure_email() {
    log_info "Configuração de Email para Alertas"
    echo "======================================"
    echo
    echo "Para receber alertas por email, configure:"
    echo "1. Conta Gmail (recomendado)"
    echo "2. App Password do Gmail (não a senha normal)"
    echo
    echo -e "${YELLOW}Como obter App Password:${NC}"
    echo "1. Acesse https://myaccount.google.com/"
    echo "2. Segurança > Verificação em duas etapas (ative se necessário)"
    echo "3. Senhas de app > Selecionar app: Mail"
    echo "4. Copie a senha de 16 caracteres gerada"
    echo
    
    read -p "Email remetente [simir.alerts@gmail.com]: " sender_email
    sender_email=${sender_email:-simir.alerts@gmail.com}
    
    read -p "Email destinatário [rafaelbartorres@gmail.com]: " recipient_email
    recipient_email=${recipient_email:-rafaelbartorres@gmail.com}
    
    echo
    read -s -p "App Password do Gmail: " email_password
    echo
    
    if [ -z "$email_password" ]; then
        log_warning "Email não configurado. Alertas serão apenas logados."
        email_password=""
    else
        log_success "Email configurado!"
    fi
    
    # Salva configuração
    cat > "$EMAIL_CONFIG_FILE" <<EOF
export SIMIR_SENDER_EMAIL="$sender_email"
export SIMIR_EMAIL_PASSWORD="$email_password"
export SIMIR_RECIPIENT_EMAIL="$recipient_email"
EOF
    
    # Cria configuração JSON completa
    cat > "$CONFIG_FILE" <<EOF
{
    "email": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "$sender_email",
        "sender_password": "$email_password",
        "recipient_email": "$recipient_email"
    },
    "monitoring": {
        "zeek_log_dir": "/usr/local/zeek/spool/zeek",
        "check_interval": 5,
        "max_alerts_per_hour": 10,
        "alert_cooldown": 300,
        "log_retention_days": 7
    },
    "detection": {
        "port_scan_threshold": 10,
        "time_window_minutes": 5,
        "suspicious_ports": [22, 23, 80, 443, 3389, 445, 135, 139],
        "whitelist_ips": ["127.0.0.1", "::1"]
    }
}
EOF
    
    log_success "Configuração salva em $CONFIG_FILE"
}

# Testar email
test_email() {
    log_info "Testando configuração de email..."
    
    if [ ! -f "$EMAIL_CONFIG_FILE" ]; then
        log_error "Configuração de email não encontrada. Execute '$0 configure' primeiro."
        exit 1
    fi
    
    source "$EMAIL_CONFIG_FILE"
    
    python3 "$SCRIPT_DIR/simir-monitor.py" --config "$CONFIG_FILE" --test-email
    
    if [ $? -eq 0 ]; then
        log_success "Email de teste enviado com sucesso!"
    else
        log_error "Falha no envio do email de teste"
        exit 1
    fi
}

# Iniciar container Zeek
start_zeek() {
    log_info "Iniciando container Zeek..."
    
    cd "$PROJECT_ROOT"
    
    # Verifica se container já está rodando
    if docker-compose ps | grep -q "Up"; then
        log_warning "Container já está rodando"
        return
    fi
    
    # Configura permissões se necessário
    if [ -f "$SCRIPT_DIR/setup-permissions.sh" ]; then
        log_info "Configurando permissões..."
        sudo "$SCRIPT_DIR/setup-permissions.sh"
    fi
    
    # Inicia container
    docker-compose up -d
    
    # Aguarda container estar pronto
    log_info "Aguardando container inicializar..."
    sleep 10
    
    # Verifica se está funcionando
    if docker-compose ps | grep -q "Up"; then
        log_success "Container Zeek iniciado com sucesso!"
        
        # Mostra logs iniciais
        log_info "Logs do container:"
        docker-compose logs --tail=20
    else
        log_error "Falha ao iniciar container Zeek"
        docker-compose logs
        exit 1
    fi
}

# Parar container Zeek
stop_zeek() {
    log_info "Parando container Zeek..."
    
    cd "$PROJECT_ROOT"
    docker-compose down
    
    log_success "Container Zeek parado"
}

# Iniciar monitor de port scan
start_monitor() {
    log_info "Iniciando monitor de port scan..."
    
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        log_warning "Monitor já está rodando (PID: $(cat "$PID_FILE"))"
        return
    fi
    
    if [ ! -f "$EMAIL_CONFIG_FILE" ]; then
        log_warning "Email não configurado. Execute '$0 configure' primeiro."
        log_info "Iniciando monitor apenas com logs..."
    else
        source "$EMAIL_CONFIG_FILE"
    fi
    
    # Inicia monitor em background
    nohup python3 "$SCRIPT_DIR/simir-monitor.py" \
        --config "$CONFIG_FILE" \
        --daemon > /tmp/simir_monitor_output.log 2>&1 &
    
    local monitor_pid=$!
    echo "$monitor_pid" > "$PID_FILE"
    
    # Verifica se iniciou corretamente
    sleep 3
    if kill -0 "$monitor_pid" 2>/dev/null; then
        log_success "Monitor iniciado (PID: $monitor_pid)"
        log_info "Logs em /tmp/simir_monitor.log"
    else
        log_error "Falha ao iniciar monitor"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# Parar monitor
stop_monitor() {
    log_info "Parando monitor de port scan..."
    
    if [ ! -f "$PID_FILE" ]; then
        log_warning "Monitor não está rodando"
        return
    fi
    
    local pid=$(cat "$PID_FILE")
    
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        log_success "Monitor parado (PID: $pid)"
    else
        log_warning "Processo não encontrado"
    fi
    
    rm -f "$PID_FILE"
}

# Status do sistema
show_status() {
    echo -e "${PURPLE}=== STATUS DO SISTEMA SIMIR ===${NC}"
    echo
    
    # Status do container Zeek
    echo -e "${BLUE}Container Zeek:${NC}"
    cd "$PROJECT_ROOT"
    if docker-compose ps | grep -q "Up"; then
        echo -e "  ${GREEN}✓ Rodando${NC}"
        
        # Informações do container
        local container_id=$(docker-compose ps -q)
        local uptime=$(docker inspect --format='{{.State.StartedAt}}' "$container_id" | cut -d'T' -f1)
        echo -e "  📅 Iniciado em: $uptime"
        
        # Verifica logs do Zeek
        if docker exec "$container_id" ls /usr/local/zeek/spool/zeek/notice.log &>/dev/null; then
            echo -e "  📋 Logs: ${GREEN}Disponíveis${NC}"
        else
            echo -e "  📋 Logs: ${YELLOW}Aguardando...${NC}"
        fi
    else
        echo -e "  ${RED}✗ Parado${NC}"
    fi
    
    echo
    
    # Status do monitor
    echo -e "${BLUE}Monitor de Port Scan:${NC}"
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        local pid=$(cat "$PID_FILE")
        echo -e "  ${GREEN}✓ Rodando${NC} (PID: $pid)"
        
        # Estatísticas do monitor
        if [ -f "/tmp/simir_monitor.log" ]; then
            local log_lines=$(wc -l < /tmp/simir_monitor.log)
            local last_activity=$(tail -1 /tmp/simir_monitor.log | cut -d' ' -f1-2)
            echo -e "  📊 Logs: $log_lines linhas"
            echo -e "  ⏰ Última atividade: $last_activity"
        fi
    else
        echo -e "  ${RED}✗ Parado${NC}"
    fi
    
    echo
    
    # Configuração de email
    echo -e "${BLUE}Configuração de Email:${NC}"
    if [ -f "$EMAIL_CONFIG_FILE" ]; then
        source "$EMAIL_CONFIG_FILE"
        if [ -n "$SIMIR_EMAIL_PASSWORD" ]; then
            echo -e "  ${GREEN}✓ Configurado${NC}"
            echo -e "  📧 Remetente: $SIMIR_SENDER_EMAIL"
            echo -e "  📬 Destinatário: $SIMIR_RECIPIENT_EMAIL"
        else
            echo -e "  ${YELLOW}⚠ Parcialmente configurado${NC} (sem senha)"
        fi
    else
        echo -e "  ${RED}✗ Não configurado${NC}"
    fi
    
    echo
    
    # Alertas recentes
    echo -e "${BLUE}Alertas Recentes:${NC}"
    if [ -f "/tmp/simir_monitor.log" ]; then
        local recent_alerts=$(grep -c "ALERTA\|Alert sent" /tmp/simir_monitor.log 2>/dev/null || echo "0")
        echo -e "  📨 Total de alertas enviados: $recent_alerts"
        
        # Últimos alertas
        if [ "$recent_alerts" -gt 0 ]; then
            echo -e "  📋 Últimos alertas:"
            grep "ALERTA\|Alert sent" /tmp/simir_monitor.log 2>/dev/null | tail -3 | while read line; do
                echo -e "    • $(echo "$line" | cut -d' ' -f1-3)..."
            done
        fi
    else
        echo -e "  ${YELLOW}⚠ Nenhum log encontrado${NC}"
    fi
}

# Simular port scan para teste
simulate_port_scan() {
    log_info "Simulando port scan para teste..."
    
    # Verifica se nmap está disponível
    if ! command -v nmap &> /dev/null; then
        log_warning "nmap não encontrado, tentando instalar..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y nmap
        elif command -v yum &> /dev/null; then
            sudo yum install -y nmap
        else
            log_error "Não foi possível instalar nmap automaticamente"
            log_info "Instale nmap manualmente: sudo apt-get install nmap"
            exit 1
        fi
    fi
    
    local target_ip="127.0.0.1"
    read -p "IP alvo para simulação [$target_ip]: " input_ip
    target_ip=${input_ip:-$target_ip}
    
    log_info "Executando scan de teste em $target_ip..."
    log_warning "Aguarde alguns segundos para detectar o scan..."
    
    # Executa scan que deve ser detectado
    nmap -sS -F "$target_ip" &>/dev/null &
    
    # Aguarda detecção
    sleep 15
    
    log_info "Scan simulado executado. Verifique os logs para confirmar detecção:"
    log_info "  tail -f /tmp/simir_monitor.log"
}

# Testar detector de força bruta
test_brute_force() {
    log_info "Testando detector de força bruta..."
    
    if [ ! -f "$SCRIPT_DIR/test-brute-force.sh" ]; then
        log_error "Script de teste de força bruta não encontrado"
        return 1
    fi
    
    echo "Escolha o tipo de teste:"
    echo "1) Teste de simulação (recomendado)"
    echo "2) Monitoramento em tempo real"
    echo "3) Verificar apenas configuração"
    echo "4) Verificar apenas sintaxe"
    
    read -p "Opção: " test_type
    
    case "$test_type" in
        1)
            log_info "Executando teste de simulação..."
            "$SCRIPT_DIR/test-brute-force.sh" --test
            ;;
        2)
            log_info "Iniciando monitoramento em tempo real..."
            "$SCRIPT_DIR/test-brute-force.sh" --live
            ;;
        3)
            log_info "Verificando configuração..."
            "$SCRIPT_DIR/test-brute-force.sh" --config
            ;;
        4)
            log_info "Verificando sintaxe..."
            "$SCRIPT_DIR/test-brute-force.sh" --syntax
            ;;
        *)
            log_error "Opção inválida"
            return 1
            ;;
    esac
    
    log_success "Teste de força bruta concluído"
    log_info "Verifique os logs com 'Ver logs > alerts'"
}

# Testar Intelligence Framework
test_intelligence_framework() {
    log_info "Testando Intelligence Framework..."
    
    if [ ! -f "$SCRIPT_DIR/test-intelligence.sh" ]; then
        log_error "Script de teste do Intelligence Framework não encontrado"
        return 1
    fi
    
    echo "O teste irá simular atividades maliciosas usando os feeds de inteligência."
    read -p "Continuar? (s/N): " confirm
    
    if [[ "$confirm" =~ ^[Ss]$ ]]; then
        log_info "Executando teste do Intelligence Framework..."
        "$SCRIPT_DIR/test-intelligence.sh"
        log_success "Teste do Intelligence Framework concluído"
        log_info "Verifique os logs com 'Ver logs > intel' ou 'Ver logs > alerts'"
    else
        log_info "Teste cancelado"
    fi
}

# Atualizar feeds de inteligência
update_intel_feeds() {
    log_info "Atualizando feeds de inteligência..."
    
    echo "Escolha o tipo de atualização:"
    echo "1) Feeds básicos (exemplos internos)"
    echo "2) Feeds públicos completos (Abuse.ch, Spamhaus, etc.)"
    echo "3) Apenas Abuse.ch (recomendado para início)"
    
    read -p "Opção: " feed_type
    
    case "$feed_type" in
        1)
            if [ ! -f "$SCRIPT_DIR/update-intel-feeds.sh" ]; then
                log_error "Script de atualização básica não encontrado"
                return 1
            fi
            log_info "Atualizando feeds básicos..."
            "$SCRIPT_DIR/update-intel-feeds.sh"
            ;;
        2)
            if [ ! -f "$SCRIPT_DIR/update-threat-feeds.sh" ]; then
                log_error "Script de feeds completos não encontrado"
                return 1
            fi
            echo "Isso baixará feeds de várias fontes públicas e pode demorar alguns minutos."
            read -p "Continuar? (s/N): " confirm
            if [[ "$confirm" =~ ^[Ss]$ ]]; then
                log_info "Baixando feeds públicos completos..."
                "$SCRIPT_DIR/update-threat-feeds.sh"
            else
                log_info "Atualização cancelada"
            fi
            ;;
        3)
            if [ ! -f "$SCRIPT_DIR/import-abusech-feeds.sh" ]; then
                log_error "Script Abuse.ch não encontrado"
                return 1
            fi
            log_info "Baixando feeds do Abuse.ch..."
            "$SCRIPT_DIR/import-abusech-feeds.sh"
            ;;
        *)
            log_error "Opção inválida"
            return 1
            ;;
    esac
    
    log_success "Atualização de feeds concluída"
}

# Visualizar logs
view_logs() {
    local log_type="$1"
    
    case "$log_type" in
        "monitor")
            if [ -f "/tmp/simir_monitor.log" ]; then
                tail -f /tmp/simir_monitor.log
            else
                log_error "Log do monitor não encontrado"
            fi
            ;;
        "zeek")
            cd "$PROJECT_ROOT"
            docker-compose logs -f
            ;;
        "alerts")
            if [ -f "/tmp/simir_monitor.log" ]; then
                grep -i "alert\|alerta" /tmp/simir_monitor.log | tail -20
            else
                log_error "Log de alertas não encontrado"
            fi
            ;;
        "intel")
            log_info "Visualizando logs de inteligência..."
            echo "Logs de inteligência disponíveis:"
            
            # Log principal de notices (inclui intel)
            if [ -f "$PROJECT_ROOT/logs/notice_PortScan_BruteForce.log" ]; then
                echo "=== Alertas de Inteligência (últimas 20 entradas) ==="
                grep -i "intel\|malicious\|intelligence" "$PROJECT_ROOT/logs/notice_PortScan_BruteForce.log" | tail -20
            fi
            
            # Log específico de inteligência (se existir)
            if [ -f "$PROJECT_ROOT/logs/current/intelligence.log" ]; then
                echo -e "\n=== Log de Inteligência Detalhado ==="
                tail -20 "$PROJECT_ROOT/logs/current/intelligence.log"
            fi
            
            # Intel log do Zeek
            if docker exec SIMIR_Z test -f /usr/local/zeek/logs/current/intel.log 2>/dev/null; then
                echo -e "\n=== Intel Log (Zeek) ==="
                docker exec SIMIR_Z tail -20 /usr/local/zeek/logs/current/intel.log 2>/dev/null || true
            fi
            
            if [ ! -f "$PROJECT_ROOT/logs/notice_PortScan_BruteForce.log" ] && \
               [ ! -f "$PROJECT_ROOT/logs/current/intelligence.log" ]; then
                log_warn "Nenhum log de inteligência encontrado. Execute o teste do Intelligence Framework."
            fi
            ;;
        *)
            echo "Tipos de log disponíveis:"
            echo "  monitor - Logs do monitor SIMIR"
            echo "  zeek    - Logs do container Zeek"
            echo "  alerts  - Apenas alertas"
            echo "  intel   - Logs de inteligência/IOCs"
            ;;
    esac
}

# Menu principal
show_menu() {
    echo -e "${BLUE}Escolha uma opção:${NC}"
    echo
    echo "  1) Configurar email para alertas"
    echo "  2) Testar envio de email"
    echo "  3) Iniciar container Zeek"
    echo "  4) Parar container Zeek"
    echo "  5) Iniciar monitor de port scan"
    echo "  6) Parar monitor de port scan"
    echo "  7) Ver status do sistema"
    echo "  8) Simular port scan (teste)"
    echo "  9) Testar detector de força bruta"
    echo "  10) Testar Intelligence Framework"
    echo "  11) Atualizar feeds de inteligência"
    echo "  12) Ver logs (monitor/zeek/alerts/intel)"
    echo "  0) Sair"
    echo
    read -p "Opção: " option
    
    case "$option" in
        1) configure_email ;;
        2) test_email ;;
        3) start_zeek ;;
        4) stop_zeek ;;
        5) start_monitor ;;
        6) stop_monitor ;;
        7) show_status ;;
        8) simulate_port_scan ;;
        9) test_brute_force ;;
        10) test_intelligence_framework ;;
        11) update_intel_feeds ;;
        12) 
            echo
            read -p "Tipo de log (monitor/zeek/alerts/intel): " log_type
            view_logs "$log_type"
            ;;
        0) 
            log_info "Saindo..."
            exit 0
            ;;
        *)
            log_error "Opção inválida"
            ;;
    esac
}

# Função principal
main() {
    show_banner
    
    # Verifica dependências
    check_dependencies
    
    # Se argumentos foram passados, executa diretamente
    if [ $# -gt 0 ]; then
        case "$1" in
            "configure") configure_email ;;
            "test-email") test_email ;;
            "start-zeek") start_zeek ;;
            "stop-zeek") stop_zeek ;;
            "start-monitor") start_monitor ;;
            "stop-monitor") stop_monitor ;;
            "status") show_status ;;
            "simulate") simulate_port_scan ;;
            "test-brute") test_brute_force ;;
            "logs") view_logs "$2" ;;
            "start") 
                start_zeek
                sleep 5
                start_monitor
                ;;
            "stop")
                stop_monitor
                stop_zeek
                ;;
            *)
                echo "Comandos disponíveis:"
                echo "  configure     - Configurar email"
                echo "  test-email    - Testar email"
                echo "  start-zeek    - Iniciar Zeek"
                echo "  stop-zeek     - Parar Zeek" 
                echo "  start-monitor - Iniciar monitor"
                echo "  stop-monitor  - Parar monitor"
                echo "  start         - Iniciar tudo"
                echo "  stop          - Parar tudo"
                echo "  status        - Ver status"
                echo "  simulate      - Simular port scan"
                echo "  test-brute    - Testar força bruta"
                echo "  logs [tipo]   - Ver logs"
                ;;
        esac
        return
    fi
    
    # Menu interativo
    while true; do
        echo
        show_menu
        echo
    done
}

# Executa função principal
main "$@"
