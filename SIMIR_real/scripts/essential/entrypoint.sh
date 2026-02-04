#!/bin/bash
set -e
 
check_system_health() {
    echo "[Zeek Entrypoint] Verificando saúde do sistema..."
    
    if [ "$(id -u)" -ne 0 ]; then
        echo "[Zeek Entrypoint] AVISO: Não executando como root. Isso pode causar problemas."
    fi
    
    if ! command -v zeek >/dev/null 2>&1; then
        echo "[Zeek Entrypoint] ERRO: Comando zeek não encontrado!"
        exit 1
    fi
    
    if ! command -v zeekctl >/dev/null 2>&1; then
        echo "[Zeek Entrypoint] ERRO: Comando zeekctl não encontrado!"
        exit 1
    fi
    
    echo "[Zeek Entrypoint] Versão do Zeek: $(zeek --version 2>/dev/null || echo 'Não foi possível obter a versão')"
}

start_web_services() {
    echo "[Zeek Entrypoint] Iniciando serviços web..."
    
    # Create PHP socket directory with proper permissions
    echo "[Zeek Entrypoint] Configurando diretório do PHP socket..."
    mkdir -p /var/run/php
    chown www-data:www-data /var/run/php
    chmod 755 /var/run/php
    
    # Start PHP-FPM with specific version detection
    echo "[Zeek Entrypoint] Iniciando PHP-FPM..."
    
    # Find which PHP version is available
    PHP_VERSION=""
    for version in 8.4 8.2 8.1 8.0 7.4; do
        if command -v "php-fpm$version" >/dev/null 2>&1; then
            PHP_VERSION=$version
            echo "[Zeek Entrypoint] Encontrado PHP-FPM $version"
            break
        fi
    done
    
    if [ -z "$PHP_VERSION" ]; then
        echo "[Zeek Entrypoint] ERRO: Nenhuma versão do PHP-FPM encontrada!"
        echo "[Zeek Entrypoint] Versões disponíveis:"
        ls -la /usr/sbin/php-fpm* 2>/dev/null || echo "Nenhum php-fpm encontrado"
        exit 1
    fi
    
    # Start PHP-FPM
    if "php-fpm$PHP_VERSION" -D; then
        echo "[Zeek Entrypoint] PHP-FPM $PHP_VERSION iniciado com sucesso"
        # Wait for socket to be created
        sleep 3
    else
        echo "[Zeek Entrypoint] ERRO: Falha ao iniciar PHP-FPM $PHP_VERSION"
        exit 1
    fi
    
    # Verify PHP-FPM socket was created
    if [ -S /var/run/php/php-fpm.sock ]; then
        echo "[Zeek Entrypoint] Socket PHP-FPM criado: /var/run/php/php-fpm.sock"
        ls -la /var/run/php/php-fpm.sock
    else
        echo "[Zeek Entrypoint] AVISO: Socket PHP-FPM não foi criado"
        # List what's in the php directory
        ls -la /var/run/php/ 2>/dev/null || echo "Diretório /var/run/php/ não existe"
    fi
    
    # Start nginx in foreground with error checking
    echo "[Zeek Entrypoint] Iniciando nginx..."
    
    # Test nginx configuration first
    if nginx -t; then
        echo "[Zeek Entrypoint] Configuração nginx OK"
    else
        echo "[Zeek Entrypoint] ERRO: Configuração nginx inválida!"
        exit 1
    fi
    
    # Start nginx in background but capture PID
    nginx -g "daemon off;" &
    NGINX_PID=$!
    
    # Wait a moment for nginx to start
    sleep 3
    
    # Check if nginx is running
    if ps -p $NGINX_PID > /dev/null; then
        echo "[Zeek Entrypoint] nginx iniciado com PID: $NGINX_PID"
    else
        echo "[Zeek Entrypoint] ERRO: nginx não está rodando!"
        exit 1
    fi
    
    # Verify nginx is listening on port 8090
    echo "[Zeek Entrypoint] Verificando se nginx está ouvindo na porta 8090..."
    if netstat -tulpn | grep -q ":8090"; then
        echo "[Zeek Entrypoint] nginx está ouvindo na porta 8090"
        echo "[Zeek Entrypoint] Interface de escuta:"
        netstat -tulpn | grep ":8090"
    else
        echo "[Zeek Entrypoint] ERRO: nginx não está ouvindo na porta 8090!"
        exit 1
    fi
}

check_system_health
start_web_services



IFACE="${ZEEK_INTERFACE:-enx000ec89f6cc0}"
echo "[Zeek Entrypoint] Interface: $IFACE"

# Verifica se a interface existe e está configurada corretamente
echo "[Zeek Entrypoint] Verificando interface de rede..."
if ! /usr/local/bin/check-interface.sh "$IFACE"; then
    echo "[Zeek Entrypoint] ERRO: Problemas com a interface $IFACE"
    exit 1
fi

mkdir -p /usr/local/zeek/etc
mkdir -p /usr/local/zeek/spool/zeek
chmod 777 /usr/local/zeek/etc
chmod 777 /usr/local/zeek/spool

echo "[Zeek Entrypoint] Configurando permissões do sistema..."
/usr/local/bin/setup-permissions.sh

if [ ! -f /usr/local/zeek/etc/zeekctl.cfg ]; then
    echo "[Zeek Entrypoint] Rodando zeekctl setup para criar zeekctl.cfg..."
    zeekctl setup --debug 2>&1 || {
        echo "[Zeek Entrypoint] ERRO ao rodar zeekctl setup!";
        echo "[Zeek Entrypoint] Conteúdo do diretório /usr/local/zeek/etc:";
        ls -la /usr/local/zeek/etc;
        echo "[Zeek Entrypoint] Verificando permissões:";
        ls -la /usr/local/zeek/;
        exit 1;
    }
fi

if [ ! -f /usr/local/zeek/etc/zeekctl.cfg ]; then
    echo "[Zeek Entrypoint] ERRO: zeekctl.cfg não foi criado após setup!"
    exit 1
fi

echo "[Zeek Entrypoint] Criando node.cfg com interface $IFACE..."
cat <<EOF > /usr/local/zeek/etc/node.cfg
[zeek]
type=standalone
host=172.20.0.1
interface=br-vm-access
EOF
 
echo "[Zeek Entrypoint] Testando API internamente..."
if curl -s -H "Authorization: Bearer y1X6Qn8PpV9jR4kM0wBz7Tf2GhUs3Lc8NrDq5Ke1HxYi0AzF7Gv9MbX2VwJoQp" \
   "http://localhost:8090/zeek-api/alert_data.php?logfile=notice.log&maxlines=1" > /dev/null; then
    echo "[Zeek Entrypoint] API test: SUCCESS"
else
    echo "[Zeek Entrypoint] API test: FAILED"
fi 

if [ ! -f /usr/local/zeek/etc/node.cfg ]; then
    echo "[Zeek Entrypoint] ERRO: Falha ao criar node.cfg!"
    exit 1
fi

echo "[Zeek Entrypoint] Conteúdo do node.cfg:"
cat /usr/local/zeek/etc/node.cfg

echo "[Zeek Entrypoint] Parando instâncias anteriores do Zeek..."
zeekctl stop 2>/dev/null || true
zeekctl cleanup 2>/dev/null || true

sleep 2

echo "[Zeek Entrypoint] Iniciando deploy do Zeek..."
if ! zeekctl deploy 2>&1; then
    echo "[Zeek Entrypoint] ERRO ao rodar zeekctl deploy!";
    echo "[Zeek Entrypoint] Verificando logs de erro...";
    if [ -f /usr/local/zeek/spool/zeek/zeekctl.err ]; then
        echo "[Zeek Entrypoint] Conteúdo do zeekctl.err:";
        cat /usr/local/zeek/spool/zeek/zeekctl.err;
    fi
    echo "[Zeek Entrypoint] Status dos nós:";
    zeekctl status 2>&1 || true
    echo "[Zeek Entrypoint] Listando arquivos no spool:";
    ls -la /usr/local/zeek/spool/zeek/ 2>/dev/null || true
    exit 1
fi

echo "[Zeek Entrypoint] Deploy realizado com sucesso!"
echo "[Zeek Entrypoint] Status dos nós:"
zeekctl status

echo "[Zeek Entrypoint] Procurando arquivos de log do Zeek..."

 TRIES=0
LOGFILE=""

while [ -z "$LOGFILE" ] && [ $TRIES -lt 30 ]; do
    echo "[Zeek Entrypoint] Tentativa $TRIES/30 - Procurando arquivos de log..."
    
    FOUND_CONN=$(find /usr/local/zeek/spool/zeek/ -name "conn.log" -type f 2>/dev/null | head -1)
    if [ -n "$FOUND_CONN" ] && [ -s "$FOUND_CONN" ]; then
        LOGFILE="$FOUND_CONN"
        echo "[Zeek Entrypoint] [OK] Encontrado conn.log em: $LOGFILE"
        break
    fi
    
    for log_name in "loaded_scripts.log" "packet_filter.log" "dns.log" "http.log" "ssl.log"; do
        FOUND_LOG=$(find /usr/local/zeek/spool/zeek/ -name "$log_name" -type f 2>/dev/null | head -1)
        if [ -n "$FOUND_LOG" ] && [ -s "$FOUND_LOG" ]; then
            LOGFILE="$FOUND_LOG"
            echo "[Zeek Entrypoint] [OK] Encontrado $log_name em: $LOGFILE"
            break 2
        fi
    done
    
    if [ -z "$LOGFILE" ]; then
        FOUND_ANY=$(find /usr/local/zeek/spool/zeek/ -name "*.log" -type f -size +0c 2>/dev/null | head -1)
        if [ -n "$FOUND_ANY" ]; then
            LOGFILE="$FOUND_ANY"
            echo "[Zeek Entrypoint] [OK] Encontrado arquivo de log: $LOGFILE"
            break
        fi
    fi
    
    sleep 3
    TRIES=$((TRIES+1))
    
    if [ $TRIES -eq 5 ] || [ $TRIES -eq 15 ] || [ $TRIES -eq 25 ]; then
        echo "[Zeek Entrypoint] === Status após $TRIES tentativas ==="
        zeekctl status 2>&1 || true
        echo "[Zeek Entrypoint] Arquivos no spool:"
        ls -la /usr/local/zeek/spool/zeek/ 2>/dev/null | grep -E "\.(log|txt)$" || echo "Nenhum arquivo de log encontrado ainda"
        echo "[Zeek Entrypoint] ================================="
    fi
done

if [ -z "$LOGFILE" ]; then
    echo "[Zeek Entrypoint] [AVISO] Nenhum arquivo de log foi encontrado após 30 tentativas."
    echo "[Zeek Entrypoint] Isso pode ser normal se não houver tráfego de rede."
    echo
    echo "[Zeek Entrypoint] Status final dos nós:"
    zeekctl status 2>&1 || true
    echo
    echo "[Zeek Entrypoint] Todos os arquivos no spool:"
    ls -la /usr/local/zeek/spool/zeek/ 2>/dev/null || true
    echo
    echo "[Zeek Entrypoint] O Zeek continuará rodando. Para gerar logs:"
    echo "1. Conecte um dispositivo na rede monitorada"
    echo "2. Gere tráfego de rede (navegação, ping, etc.)"
    echo "3. Use 'docker exec -it SIMIR_Z ls -la /usr/local/zeek/spool/zeek/' para verificar logs"
    echo
    echo "[Zeek Entrypoint] Mantendo container ativo e monitorando diretório de logs..."
    
    # Monitora o diretório de logs em vez de um arquivo específico
    while true; do
        sleep 30
        NEW_LOGS=$(find /usr/local/zeek/spool/zeek/ -name "*.log" -type f -size +0c 2>/dev/null)
        if [ -n "$NEW_LOGS" ]; then
            echo "[Zeek Entrypoint] Novos logs detectados!"
            echo "$NEW_LOGS"
            LOGFILE=$(echo "$NEW_LOGS" | head -1)
            break
        fi
        echo "[Zeek Entrypoint] $(date): Aguardando tráfego de rede para gerar logs..."
    done
fi

# Iniciar sistema SIMIR se disponível
if [ -f "/usr/local/bin/simir-autostart.sh" ]; then
    echo "[Zeek Entrypoint] Iniciando sistema SIMIR de monitoramento..."
    
    # Copia scripts SIMIR para locais padrão
    mkdir -p /opt/simir/scripts
    mkdir -p /opt/simir/config
    
    if [ -f "/usr/local/bin/simir-monitor.py" ]; then
        cp /usr/local/bin/simir-monitor.py /opt/simir/scripts/
        chmod +x /opt/simir/scripts/simir-monitor.py
    fi
    
    /usr/local/bin/simir-autostart.sh auto-start &
    SIMIR_PID=$!
    
    echo "[Zeek Entrypoint] [OK] Sistema SIMIR iniciado (PID: $SIMIR_PID)"
else
    echo "[Zeek Entrypoint] [AVISO] Sistema SIMIR não encontrado, prosseguindo apenas com Zeek"
fi

echo "[Zeek Entrypoint] Monitorando arquivo de log: $LOGFILE"
echo "[Zeek Entrypoint] Sistema SIMIR ativo para detecção de port scan"
echo "[Zeek Entrypoint] Use Ctrl+C para parar o monitoramento"
while true; do
    # Check for new logs every second (optional - can be intensive)
    NEW_LOGS=$(find /usr/local/zeek/spool/zeek/ -name "*.log" -type f -size +0c 2>/dev/null | head -1)
    if [ -n "$NEW_LOGS" ] && [ "$NEW_LOGS" != "$LAST_LOG" ]; then
        echo "[Zeek Entrypoint] [LOG DETECTADO] $(date '+%H:%M:%S'): $NEW_LOGS"
        LAST_LOG="$NEW_LOGS"
    fi
    
    # Show status every 60 seconds to avoid spam
    COUNTER=$((COUNTER + 1))
    if [ $((COUNTER % 60)) -eq 0 ]; then
        echo "[Zeek Entrypoint] [STATUS] $(date): Zeek monitorando ativamente a rede..."
        # Quick status check without full output
        if zeekctl status 2>&1 | grep -q "running"; then
            echo "[Zeek Entrypoint] [STATUS] Zeek processos: OK"
        else
            echo "[Zeek Entrypoint] [STATUS] Zeek processos: PROBLEMA"
        fi
    fi
    
    sleep 1
done
 
