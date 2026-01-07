#!/bin/bash

# SIMIR Auto-Start Script
# Integra o monitor de port scan com o container Zeek

# Configurações
MONITOR_SCRIPT="/opt/simir/scripts/simir-monitor.py"
CONFIG_FILE="/opt/simir/config/simir_config.json"
LOG_FILE="/var/log/simir/monitor.log"
PID_FILE="/var/run/simir_monitor.pid"

# Função para log
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SIMIR-AUTOSTART: $1" | tee -a "$LOG_FILE"
}

# Criar diretórios necessários
setup_directories() {
    mkdir -p /var/log/simir
    mkdir -p /opt/simir/config
    mkdir -p /var/run
}

# Configuração padrão se não existir
create_default_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log_message "Criando configuração padrão..."
        
        cat > "$CONFIG_FILE" <<EOF
{
    "email": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "${SIMIR_SENDER_EMAIL:-simir.alerts@gmail.com}",
        "sender_password": "${SIMIR_EMAIL_PASSWORD:-}",
        "recipient_email": "${SIMIR_RECIPIENT_EMAIL:-rafaelbartorres@gmail.com}"
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
        log_message "Configuração padrão criada em $CONFIG_FILE"
    fi
}

# Aguardar Zeek estar pronto
wait_for_zeek() {
    log_message "Aguardando Zeek inicializar..."
    
    local max_wait=120  # 2 minutos
    local count=0
    
    while [ $count -lt $max_wait ]; do
        if pgrep -f "zeek.*local.zeek" > /dev/null; then
            log_message "Zeek detectado rodando"
            return 0
        fi
        
        sleep 1
        ((count++))
    done
    
    log_message "TIMEOUT: Zeek não iniciou dentro do tempo limite"
    return 1
}

# Aguardar logs do Zeek
wait_for_zeek_logs() {
    log_message "Aguardando logs do Zeek..."
    
    local max_wait=60  # 1 minuto
    local count=0
    local notice_log="/usr/local/zeek/spool/zeek/notice.log"
    
    while [ $count -lt $max_wait ]; do
        if [ -f "$notice_log" ] || [ -f "/usr/local/zeek/spool/zeek/conn.log" ]; then
            log_message "Logs do Zeek detectados"
            return 0
        fi
        
        sleep 1
        ((count++))
    done
    
    log_message "AVISO: Logs do Zeek ainda não disponíveis, continuando..."
    return 0
}

# Iniciar monitor
start_monitor() {
    log_message "Iniciando monitor SIMIR..."
    
    # Verifica se já está rodando
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        log_message "Monitor já está rodando (PID: $(cat "$PID_FILE"))"
        return 0
    fi
    
    # Inicia monitor
    python3 "$MONITOR_SCRIPT" --config "$CONFIG_FILE" --daemon &
    local monitor_pid=$!
    
    # Salva PID
    echo "$monitor_pid" > "$PID_FILE"
    
    # Verifica se iniciou
    sleep 3
    if kill -0 "$monitor_pid" 2>/dev/null; then
        log_message "Monitor iniciado com sucesso (PID: $monitor_pid)"
        return 0
    else
        log_message "ERRO: Falha ao iniciar monitor"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Parar monitor
stop_monitor() {
    log_message "Parando monitor SIMIR..."
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            log_message "Monitor parado (PID: $pid)"
        fi
        rm -f "$PID_FILE"
    fi
}

# Verificar status
check_status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Função principal de inicialização
auto_start() {
    log_message "=== SIMIR AUTO-START INICIADO ==="
    
    # Setup
    setup_directories
    create_default_config
    
    # Aguarda Zeek
    if ! wait_for_zeek; then
        log_message "ERRO: Zeek não iniciou, abortando auto-start"
        exit 1
    fi
    
    # Aguarda logs
    wait_for_zeek_logs
    
    # Inicia monitor
    if start_monitor; then
        log_message "=== SIMIR AUTO-START CONCLUÍDO ==="
    else
        log_message "=== SIMIR AUTO-START FALHOU ==="
        exit 1
    fi
}

# Monitoramento contínuo
monitor_health() {
    log_message "Iniciando monitoramento de saúde..."
    
    while true; do
        sleep 30  # Verifica a cada 30 segundos
        
        if ! check_status; then
            log_message "Monitor não está rodando, tentando reiniciar..."
            
            # Aguarda um pouco antes de tentar reiniciar
            sleep 10
            
            if start_monitor; then
                log_message "Monitor reiniciado com sucesso"
            else
                log_message "ERRO: Falha ao reiniciar monitor"
            fi
        fi
    done
}

# Handler para sinais
cleanup() {
    log_message "Recebido sinal de término, parando monitor..."
    stop_monitor
    exit 0
}

# Registra handlers
trap cleanup SIGINT SIGTERM

# Verifica comando
case "${1:-auto-start}" in
    "auto-start")
        auto_start
        # Inicia monitoramento de saúde em background
        monitor_health &
        # Aguarda sinais
        wait
        ;;
    "start")
        setup_directories
        create_default_config
        start_monitor
        ;;
    "stop")
        stop_monitor
        ;;
    "status")
        if check_status; then
            echo "SIMIR Monitor está rodando (PID: $(cat "$PID_FILE"))"
            exit 0
        else
            echo "SIMIR Monitor não está rodando"
            exit 1
        fi
        ;;
    "restart")
        stop_monitor
        sleep 2
        setup_directories
        create_default_config
        start_monitor
        ;;
    *)
        echo "Uso: $0 {auto-start|start|stop|status|restart}"
        echo
        echo "  auto-start - Inicia automaticamente com Zeek (padrão)"
        echo "  start      - Inicia monitor manualmente"
        echo "  stop       - Para monitor"
        echo "  status     - Verifica status"
        echo "  restart    - Reinicia monitor"
        exit 1
        ;;
esac
