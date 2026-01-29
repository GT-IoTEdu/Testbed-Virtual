# SIMIR - Padrões de Mensagens para Notice.log
# Definições padronizadas para logs de produção

@load base/frameworks/notice

module SIMIR;

export {
    # Função para formatação padronizada de timestamps
    global format_timestamp: function(ts: time): string;
    
    # Função para padronização de IPs
    global format_ip: function(ip: addr): string;
    
    # Função para formatação de mensagens de intelligence
    global format_intel_message: function(indicator: string, itype: string, source: string, confidence: string &default="MEDIUM"): string;
    
    # Função para formatação de mensagens de port scan
    global format_portscan_message: function(action: string, src: addr, details: string): string;
    
    # Novas funções padronizadas para port scan
    global format_portscan_active: function(scanner: addr, targets_count: count, ports_count: count, duration: string): string;
    global format_portscan_closed_ports: function(scanner: addr, target: addr, attempts: count): string;
    global format_portscan_target: function(target: addr, scanners_count: count): string;
    
    # Função para formatação de mensagens de brute force
    global format_bruteforce_message: function(service: string, src: addr, target: addr, attempts: count): string;

    # Função para formatação de mensagens de DDoS/DoS
    global format_ddos_message: function(target: addr, service_port: port, attempts: count, unique_sources: count, attack_type: string): string;
    
    # Níveis de severidade padronizados
    type Severity: enum { LOW, MEDIUM, HIGH, CRITICAL };
    
    # Estrutura padronizada para metadados de notice
    type NoticeMetadata: record {
        severity: Severity;
        category: string;
        subcategory: string;
        confidence: string &default="MEDIUM";
        action_required: bool &default=F;
    };
}

# Implementação das funções de formatação
function format_timestamp(ts: time): string
{
    return strftime("%Y-%m-%d %H:%M:%S UTC", ts);
}

function format_ip(ip: addr): string
{
    # Mascarar IPs privados para logs de produção se necessário
    local ip_str = fmt("%s", ip);
    
    # Identificar tipo de IP
    if (Site::is_private_addr(ip)) {
        return fmt("[PRIVATE] %s", ip_str);
    } else {
        return fmt("[PUBLIC] %s", ip_str);
    }
}

function format_intel_message(indicator: string, itype: string, source: string, confidence: string &default="MEDIUM"): string
{
    return fmt("[THREAT-INTEL] [%s] [%s] Indicator: %s | Source: %s | Confidence: %s", 
               "HIGH", itype, indicator, source, confidence);
}

function format_portscan_message(action: string, src: addr, details: string): string
{
    local severity = "MEDIUM";
    if (action == "MULTIPLE_HOSTS")
        severity = "HIGH";
    
    return fmt("[PORT-SCAN] [%s] Source: %s | %s", 
               severity, format_ip(src), details);
}

# Nova função padronizada para port scan ativo (múltiplas portas)
function format_portscan_active(scanner: addr, targets_count: count, ports_count: count, duration: string): string
{
    local severity = "HIGH";
    if (ports_count >= 50 || targets_count >= 10)
        severity = "CRITICAL";
    
    return fmt("[PORT-SCAN] [%s] Scanner: %s | Targets: %d hosts | Ports: %d different ports | Duration: %s", 
               severity, format_ip(scanner), targets_count, ports_count, duration);
}

# Nova função para tentativas em portas fechadas
function format_portscan_closed_ports(scanner: addr, target: addr, attempts: count): string
{
    local severity = "MEDIUM";
    if (attempts >= 20)
        severity = "HIGH";
    
    return fmt("[PORT-SCAN] [%s] Scanner: %s | Target: %s | Closed Port Attempts: %d", 
               severity, format_ip(scanner), format_ip(target), attempts);
}

# Nova função para alvo sendo escaneado
function format_portscan_target(target: addr, scanners_count: count): string
{
    local severity = "HIGH";
    if (scanners_count >= 20)
        severity = "CRITICAL";
    
    return fmt("[PORT-SCAN] [%s] Target: %s | Being scanned by: %d different sources", 
               severity, format_ip(target), scanners_count);
}

function format_bruteforce_message(service: string, src: addr, target: addr, attempts: count): string
{
    local severity = "HIGH";
    if (attempts >= 20)
        severity = "CRITICAL";
    
    return fmt("[BRUTE-FORCE] [%s] Service: %s | Attacker: %s | Target: %s | Attempts: %d", 
               severity, service, format_ip(src), format_ip(target), attempts);
}

function format_ddos_message(target: addr, service_port: port, attempts: count, unique_sources: count, attack_type: string): string
{
    local severity = "HIGH";
    if (attempts >= 200 || unique_sources >= 25)
        severity = "CRITICAL";
    
    return fmt("[DDOS] [%s] Target: %s:%s | Type: %s | Requests: %d | Sources: %d",
               severity, format_ip(target), port_to_count(service_port), attack_type, attempts, unique_sources);
}