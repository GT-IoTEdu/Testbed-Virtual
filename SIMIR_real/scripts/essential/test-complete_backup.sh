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
echo -e "${YELLOW}Escolha o tipo de teste:${NC}"
echo ""
echo "1) Teste de DoS (origem única) - HTTP"
echo "   → 105 requisições para um único servidor web em 60s"
echo ""
echo "2) Teste de DoS (origem única) - Porta customizada"
echo "   → 105 conexões TCP para uma porta específica"
echo ""
echo "3) Teste de DDoS simulado (múltiplas origens com hping3)"
echo "   → Requer hping3 e múltiplos IPs configurados"
echo ""
echo "4) Teste de Port Scan intenso"
echo "   → Escaneia 100 portas rapidamente (pode gerar DoS também)"
echo ""
echo "5) Teste de assinatura do dominio g1.com"
echo "   → Faz um curl para o domínio http://g1.com que está registrado como malicioso"
echo ""
echo "6) Teste de assinatura do IP 10.20.30.40"
echo "   → Faz um curl para o IP http://10.20.30.40 que está registrado como malicioso"
echo ""
echo "7) Teste de Força Bruta"
echo "   → Simula tentativas de autenticação SSH/HTTP para testar detector de brute force"
echo ""
read -p "Digite sua escolha (1-7): " choice

case $choice in
    1)
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
        read -p "Digite o host alvo: " target
        
        if [ -z "$target" ]; then
            echo -e "${RED}Host não pode estar vazio${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}[*] Alvo: $target${NC}"
        echo -e "${BLUE}[*] Escaneando 100 portas rapidamente...${NC}"
        echo -e "${YELLOW}[*] Isso deve gerar alertas de Port Scan E possivelmente DoS${NC}\n"
        
        # Escaneia 100 portas com intervalo mínimo
        for port in {1..100}; do
            timeout 0.5 nc -zv -w 1 "$target" "$port" 2>/dev/null || true
            echo -ne "${GREEN}Porta $port/100 escaneada${NC}\r"
            sleep 0.3
        done
        
        echo -e "\n${GREEN}✓ Teste concluído!${NC}"
        echo -e "${YELLOW}[*] Aguardando 5 segundos para processamento do Zeek...${NC}"
        sleep 5
        
        echo -e "\n${BLUE}[*] Verificando alertas no notice.log:${NC}\n"
        tail -20 $LOGS_DIR/notice.log | grep -E "Port_Scan|DoS_Attack_Detected|DDoS_Attack_Detected" || echo -e "${YELLOW}⚠ Nenhum alerta encontrado${NC}"
        ;;
        
    5)
        echo -e "\n${BLUE}[*] Realizando teste de assinatura de dominio:${NC}\n"
        echo -e "${YELLOW}[*] Executando curl http://g1.com...${NC}"
        
        # Conta alertas antes do teste
        alertas_antes=$(grep -c "Malicious_Domain_Hit" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
        
        curl -s "http://g1.com" > /dev/null 2>&1 || true
        
        echo -e "${YELLOW}[*] Aguardando processamento do Zeek (5 segundos)...${NC}"
        sleep 5
        
        # Conta alertas depois do teste
        alertas_depois=$(grep -c "Malicious_Domain_Hit" $LOGS_DIR/notice.log 2>/dev/null || echo "0")
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
