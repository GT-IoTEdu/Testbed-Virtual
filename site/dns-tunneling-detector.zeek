# DNS Tunneling Detector para SIMIR
# Detecta uso malicioso de DNS para exfiltração de dados e C2
# Compatível com Zeek 7.2.2+

@load base/frameworks/notice
@load base/protocols/dns
@load ./simir-notice-standards.zeek

module DNSTunneling;

export {
    redef enum Notice::Type += {
        DNS_Long_Subdomain,
        DNS_High_Entropy,
        DNS_Excessive_NXDOMAIN,
        DNS_Suspicious_TXT_Query,
        DNS_Tunneling_Pattern
    };
    
    # Configurações
    global max_subdomain_length: count = 60 &redef;
    global max_query_length: count = 100 &redef;
    global nxdomain_threshold: count = 50 &redef;
    global time_window: interval = 10min &redef;
    global min_entropy: double = 3.5 &redef;  # Entropia mínima para considerar suspeito
    
    # Tracking de queries por host
    type DNSStats: record {
        total_queries: count &default=0;
        nxdomain_count: count &default=0;
        long_queries: count &default=0;
        txt_queries: count &default=0;
        first_seen: time;
        last_seen: time;
        suspicious_domains: set[string] &optional;
    };
    
    global dns_stats: table[addr] of DNSStats &create_expire=time_window;
}

# Calcula entropia de Shannon (detecta strings aleatórias/codificadas)
function calculate_entropy(s: string): double
{
    local freq: table[string] of count;
    local len = |s|;
    
    if (len == 0)
        return 0.0;
    
    # Conta frequência de cada caractere
    local i = 0;
    while (i < len) {
        local character = sub_bytes(s, i, 1);
        if (character !in freq)
            freq[character] = 0;
        ++freq[character];
        ++i;
    }
    
    # Calcula entropia
    local entropy = 0.0;
    local total = len + 0.0;  # Converter para double
    
    # Itera sobre as chaves da tabela
    for (ch in freq) {
        local cnt = freq[ch];
        local prob = cnt / total;
        if (prob > 0.0)
            entropy += -prob * (log10(prob) / log10(2.0));
    }
    
    return entropy;
}

# Verifica se domínio tem padrão de encoding (base64, hex)
function has_encoding_pattern(domain: string): bool
{
    # Padrões comuns de base64/hex
    if (/[A-Za-z0-9+\/]{20,}/ in domain)  # Base64-like
        return T;
    if (/[0-9a-fA-F]{32,}/ in domain)  # Hex-like
        return T;
    if (/[A-Z0-9]{15,}/ in domain)  # Uppercase alphanumeric
        return T;
    
    return F;
}

event dns_request(c: connection, msg: dns_msg, query: string, qtype: count, qclass: count)
{
    if (!c?$id)
        return;
    
    local orig = c$id$orig_h;
    
    # Ignora localhost
    if (orig == 127.0.0.1 || orig == [::1])
        return;
    
    # Inicializa stats se não existir
    if (orig !in dns_stats) {
        dns_stats[orig] = [$first_seen=network_time(), $last_seen=network_time()];
        dns_stats[orig]$suspicious_domains = set();
    }
    
    local stats = dns_stats[orig];
    ++stats$total_queries;
    stats$last_seen = network_time();
    
    local query_len = |query|;
    
    # Extrai subdomínios
    local parts = split_string(query, /\./);
    local has_long_subdomain = F;
    local longest_subdomain = "";
    
    for (i in parts) {
        if (|parts[i]| > |longest_subdomain|) {
            longest_subdomain = parts[i];
        }
        if (|parts[i]| > max_subdomain_length) {
            has_long_subdomain = T;
        }
    }
    
    # Detecta subdomínio excessivamente longo
    if (has_long_subdomain) {
        ++stats$long_queries;
        add stats$suspicious_domains[query];
        
        # Alerta agregado por IP, não por domínio individual
        NOTICE([$note=DNS_Long_Subdomain,
                $msg=fmt("[DNS-TUNNEL] [MEDIUM] Long Subdomain: %s queried '%s' (subdomain: %d chars)", 
                        SIMIR::format_ip(orig), query, |longest_subdomain|),
                $src=orig,
                $proto=udp,
                $n=|longest_subdomain|,
                $sub=fmt("long_subdomain_%d_chars", |longest_subdomain|),
                $identifier=fmt("dns_long_%s", orig),
                $suppress_for=10min]);
    }
    
    # Detecta alta entropia (strings aleatórias/codificadas)
    if (|longest_subdomain| > 15) {
        local entropy = calculate_entropy(longest_subdomain);
        if (entropy > min_entropy && has_encoding_pattern(longest_subdomain)) {
            add stats$suspicious_domains[query];
            
            # Alerta apenas na primeira detecção para este IP
            # Agregação por IP de origem, não por domínio individual
            NOTICE([$note=DNS_High_Entropy,
                    $msg=fmt("[DNS-TUNNEL] [HIGH] High Entropy DNS: %s queried '%s' (entropy: %.2f, pattern: encoding)", 
                            SIMIR::format_ip(orig), query, entropy),
                    $src=orig,
                    $proto=udp,
                    $sub=fmt("high_entropy_%.2f", entropy),
                    $identifier=fmt("dns_entropy_%s", orig),
                    $suppress_for=10min]);
        }
    }
    
    # Detecta queries TXT suspeitas (comuns em tunneling)
    if (qtype == 16) {  # TXT record
        ++stats$txt_queries;
        if (stats$txt_queries >= 10) {
            NOTICE([$note=DNS_Suspicious_TXT_Query,
                    $msg=fmt("[DNS-TUNNEL] [MEDIUM] Excessive TXT Queries: %s made %d TXT queries", 
                            SIMIR::format_ip(orig), stats$txt_queries),
                    $src=orig,
                    $proto=udp,
                    $n=stats$txt_queries,
                    $sub="txt_queries",
                    $identifier=fmt("dns_txt_%s", orig),
                    $suppress_for=10min]);
        }
    }
    
    # Detecta padrão geral de tunneling
    if (stats$long_queries >= 5 || |stats$suspicious_domains| >= 10) {
        NOTICE([$note=DNS_Tunneling_Pattern,
                $msg=fmt("[DNS-TUNNEL] [CRITICAL] DNS Tunneling Pattern: %s shows tunneling behavior (long: %d, suspicious: %d domains)", 
                        SIMIR::format_ip(orig), stats$long_queries, |stats$suspicious_domains|),
                $src=orig,
                $proto=udp,
                $n=|stats$suspicious_domains|,
                $sub=fmt("pattern_%d_suspicious", |stats$suspicious_domains|),
                $identifier=fmt("dns_pattern_%s", orig),
                $suppress_for=15min]);
    }
}

event dns_rejected(c: connection, msg: dns_msg, query: string, qtype: count, qclass: count)
{
    if (!c?$id)
        return;
    
    local orig = c$id$orig_h;
    
    # Inicializa stats se não existir
    if (orig !in dns_stats) {
        dns_stats[orig] = [$first_seen=network_time(), $last_seen=network_time()];
        dns_stats[orig]$suspicious_domains = set();
    }
    
    local stats = dns_stats[orig];
    ++stats$nxdomain_count;
    stats$last_seen = network_time();
    
    # Detecta excesso de NXDOMAIN (pode indicar DGA - Domain Generation Algorithm)
    if (stats$nxdomain_count >= nxdomain_threshold) {
        NOTICE([$note=DNS_Excessive_NXDOMAIN,
                $msg=fmt("[DNS-TUNNEL] [HIGH] Excessive NXDOMAIN: %s received %d NXDOMAIN responses (possible DGA)", 
                        SIMIR::format_ip(orig), stats$nxdomain_count),
                $src=orig,
                $proto=udp,
                $n=stats$nxdomain_count,
                $sub="nxdomain_excessive",
                $identifier=fmt("dns_nxdomain_%s", orig),
                $suppress_for=10min]);
    }
}

event zeek_init()
{
    print fmt("DNS Tunneling Detector ativo - Max subdomain: %d chars, NXDOMAIN threshold: %d, Window: %s",
              max_subdomain_length, nxdomain_threshold, time_window);
}
