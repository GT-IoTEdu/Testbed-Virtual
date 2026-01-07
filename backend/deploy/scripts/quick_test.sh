#!/bin/bash
# Script de teste rápido para IoT-EDU
# Uso: ./quick_test.sh

set -e

# Configurações
BASE_URL="https://sp-python.cafeexpresso.rnp.br"
TIMEOUT=10

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Função para log
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Função para testar endpoint
test_endpoint() {
    local url="$1"
    local name="$2"
    local expected_status="${3:-200}"
    
    echo -n "Testando $name... "
    
    if curl -s -f -k --connect-timeout $TIMEOUT "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FALHOU${NC}"
        return 1
    fi
}

# Função para testar endpoint com status específico
test_endpoint_status() {
    local url="$1"
    local name="$2"
    local expected_status="$3"
    
    echo -n "Testando $name (status $expected_status)... "
    
    local status=$(curl -s -o /dev/null -w "%{http_code}" -k --connect-timeout $TIMEOUT "$url" 2>/dev/null)
    
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✅ OK (Status: $status)${NC}"
        return 0
    else
        echo -e "${RED}❌ FALHOU (Status: $status, esperado: $expected_status)${NC}"
        return 1
    fi
}

# Função para testar JSON response
test_json_endpoint() {
    local url="$1"
    local name="$2"
    local expected_field="$3"
    
    echo -n "Testando $name (JSON)... "
    
    local response=$(curl -s -k --connect-timeout $TIMEOUT "$url" 2>/dev/null)
    
    if echo "$response" | grep -q "$expected_field"; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FALHOU${NC}"
        return 1
    fi
}

# Função principal
main() {
    echo "🚀 Teste Rápido - IoT-EDU"
    echo "🌐 URL Base: $BASE_URL"
    echo "⏰ Timestamp: $(date)"
    echo "=================================="
    
    # Contadores
    total_tests=0
    passed_tests=0
    
    # 1. Teste básico de conectividade
    info "1. Testando conectividade básica..."
    total_tests=$((total_tests + 1))
    if test_endpoint "$BASE_URL" "Acesso básico"; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 2. Teste de health check
    info "2. Testando health check..."
    total_tests=$((total_tests + 1))
    if test_json_endpoint "$BASE_URL/health" "Health check" "status"; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 3. Teste da documentação
    info "3. Testando documentação da API..."
    total_tests=$((total_tests + 1))
    if test_endpoint "$BASE_URL/docs" "Documentação"; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 4. Teste de metadados SAML
    info "4. Testando metadados SAML..."
    total_tests=$((total_tests + 1))
    if test_endpoint "$BASE_URL/saml2/metadata/" "Metadados SAML"; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 5. Teste de status de autenticação
    info "5. Testando status de autenticação..."
    total_tests=$((total_tests + 1))
    if test_json_endpoint "$BASE_URL/auth/status" "Status de autenticação" "status"; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 6. Teste de endpoints da API
    info "6. Testando endpoints da API..."
    
    # 6.1 Listagem de dispositivos
    total_tests=$((total_tests + 1))
    if test_json_endpoint "$BASE_URL/api/devices/" "Listagem de dispositivos" "status"; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 6.2 Listagem de aliases
    total_tests=$((total_tests + 1))
    if test_json_endpoint "$BASE_URL/api/devices/aliases/" "Listagem de aliases" "status"; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 6.3 Servidores DHCP
    total_tests=$((total_tests + 1))
    if test_json_endpoint "$BASE_URL/api/devices/dhcp/servers" "Servidores DHCP" "status"; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # 7. Teste de SSL
    info "7. Testando certificado SSL..."
    total_tests=$((total_tests + 1))
    if curl -s -f --connect-timeout $TIMEOUT "$BASE_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Certificado SSL válido${NC}"
        passed_tests=$((passed_tests + 1))
    else
        echo -e "${RED}❌ Problema com certificado SSL${NC}"
    fi
    
    # 8. Teste de performance
    info "8. Testando performance..."
    total_tests=$((total_tests + 1))
    start_time=$(date +%s.%N)
    if curl -s -f -k --connect-timeout $TIMEOUT "$BASE_URL/health" > /dev/null 2>&1; then
        end_time=$(date +%s.%N)
        response_time=$(echo "$end_time - $start_time" | bc)
        if (( $(echo "$response_time < 2.0" | bc -l) )); then
            echo -e "${GREEN}✅ Performance OK (${response_time}s)${NC}"
            passed_tests=$((passed_tests + 1))
        else
            echo -e "${YELLOW}⚠️ Performance lenta (${response_time}s)${NC}"
            passed_tests=$((passed_tests + 1))
        fi
    else
        echo -e "${RED}❌ Falha no teste de performance${NC}"
    fi
    
    # 9. Teste de erro 404
    info "9. Testando tratamento de erro 404..."
    total_tests=$((total_tests + 1))
    if test_endpoint_status "$BASE_URL/api/endpoint-inexistente" "Erro 404" "404"; then
        passed_tests=$((passed_tests + 1))
    fi
    
    # Relatório final
    echo ""
    echo "=================================="
    echo "📋 RELATÓRIO FINAL"
    echo "=================================="
    echo "Total de testes: $total_tests"
    echo "Testes aprovados: $passed_tests"
    echo "Testes reprovados: $((total_tests - passed_tests))"
    echo "Taxa de sucesso: $((passed_tests * 100 / total_tests))%"
    
    if [ $passed_tests -eq $total_tests ]; then
        echo ""
        echo -e "${GREEN}🎉 TODOS OS TESTES PASSARAM!${NC}"
        echo "A aplicação está funcionando corretamente."
        exit 0
    elif [ $passed_tests -ge $((total_tests * 8 / 10)) ]; then
        echo ""
        echo -e "${YELLOW}⚠️ A maioria dos testes passou.${NC}"
        echo "Verifique os endpoints que falharam."
        exit 1
    else
        echo ""
        echo -e "${RED}❌ Muitos testes falharam.${NC}"
        echo "Verifique a configuração da aplicação."
        exit 2
    fi
}

# Verificar se curl está disponível
if ! command -v curl &> /dev/null; then
    error "curl não está instalado. Instale curl primeiro."
    exit 1
fi

# Verificar se bc está disponível (para cálculos)
if ! command -v bc &> /dev/null; then
    warning "bc não está instalado. Instalação recomendada para cálculos precisos."
fi

# Executar testes
main "$@" 