# Beaconing Detector para SIMIR
# Detecta comunicação periódica com C2 (Command & Control)
# Compatível com Zeek 7.2.2+

@load base/frameworks/notice
@load base/protocols/conn
@load ./simir-notice-standards.zeek

module Beaconing;

export {
    redef enum Notice::Type += {
        Beaconing_Detected,
        Regular_Beacon_Pattern,
        Suspicious_Periodic_Connection
    };
    
    # Configurações
    global min_connections: count = 10 &redef;  # Mínimo de conexões para considerar
    global time_window: interval = 30min &redef;
    global jitter_tolerance: double = 0.15 &redef;  # 15% de variação permitida
    global min_interval: interval = 5sec &redef;  # Intervalo mínimo entre beacons
    global max_interval: interval = 5min &redef;  # Intervalo máximo entre beacons
    
    # Tracking de conexões
    type BeaconStats: record {
        timestamps: vector of time;
        byte_counts: vector of count;
        intervals: vector of interval;
        connections: count &default=0;
        first_seen: time;
        last_seen: time;
        avg_interval: interval &default=0sec;
        interval_variance: double &default=0.0;
    };
    
    global beacon_stats: table[addr, addr, port] of BeaconStats &create_expire=time_window;
}

# Calcula variância dos intervalos
function calculate_variance(intervals: vector of interval): double
{
    local n = |intervals|;
    if (n < 2)
        return 0.0;
    
    # Calcula média
    local sum = 0.0;
    local i = 0;
    while (i < n) {
        sum += interval_to_double(intervals[i]);
        ++i;
    }
    local mean = sum / n;
    
    # Calcula variância
    local variance = 0.0;
    i = 0;
    while (i < n) {
        local diff = interval_to_double(intervals[i]) - mean;
        variance += diff * diff;
        ++i;
    }
    
    return variance / n;
}

# Calcula desvio padrão normalizado (coefficient of variation)
function calculate_regularity(intervals: vector of interval, avg: interval): double
{
    if (|intervals| < 2)
        return 1.0;
    
    local variance = calculate_variance(intervals);
    local std_dev = sqrt(variance);
    local avg_double = interval_to_double(avg);
    
    if (avg_double == 0.0)
        return 1.0;
    
    # Retorna coeficiente de variação (quanto menor, mais regular)
    return std_dev / avg_double;
}

# Verifica se bytes transferidos são similares
function has_similar_payload_sizes(byte_counts: vector of count): bool
{
    local n = |byte_counts|;
    if (n < 3)
        return F;
    
    # Calcula média de bytes
    local sum: count = 0;
    local i = 0;
    while (i < n) {
        sum += byte_counts[i];
        ++i;
    }
    local avg = sum / n;
    
    # Se média é zero ou muito pequena, ignora
    if (avg < 10)
        return F;
    
    # Verifica se maioria dos valores está próxima da média (±30%)
    local similar_count = 0;
    i = 0;
    while (i < n) {
        local diff = byte_counts[i] > avg ? byte_counts[i] - avg : avg - byte_counts[i];
        if (diff < avg * 0.3)  # 30% de tolerância
            ++similar_count;
        ++i;
    }
    
    # Se mais de 70% são similares, considera suspeito
    return similar_count >= (n * 7 / 10);
}

event new_connection(c: connection)
{
    if (!c?$id)
        return;
    
    local orig = c$id$orig_h;
    local resp = c$id$resp_h;
    local dport = c$id$resp_p;
    
    # Ignora tráfego local
    if (orig == resp)
        return;
    
    # Ignora portas comuns de navegação (reduz falsos positivos)
    if (dport == 80/tcp || dport == 443/tcp)
        return;
    
    # Inicializa ou atualiza stats (chave composta: orig, resp, dport)
    if ([orig, resp, dport] !in beacon_stats) {
        local now = network_time();
        beacon_stats[orig, resp, dport] = BeaconStats(
            $timestamps=vector(),
            $byte_counts=vector(),
            $intervals=vector(),
            $connections=0,
            $first_seen=now,
            $last_seen=now
        );
    }
    
    local stats = beacon_stats[orig, resp, dport];
    local ts = network_time();
    
    # Adiciona timestamp
    stats$timestamps += ts;
    ++stats$connections;
    stats$last_seen = ts;
    
    # Calcula intervalo desde última conexão
    if (|stats$timestamps| > 1) {
        local prev_time = stats$timestamps[|stats$timestamps| - 2];
        local time_diff = ts - prev_time;
        stats$intervals += time_diff;
        
        # Só analisa se temos conexões suficientes
        if (|stats$intervals| >= min_connections) {
            # Calcula média dos intervalos
            local sum_intervals = 0.0;
            local i = 0;
            while (i < |stats$intervals|) {
                sum_intervals += interval_to_double(stats$intervals[i]);
                ++i;
            }
            local avg_interval_double = sum_intervals / |stats$intervals|;
            stats$avg_interval = double_to_interval(avg_interval_double);
            
            # Verifica se intervalo está no range suspeito
            if (stats$avg_interval < min_interval || stats$avg_interval > max_interval)
                return;
            
            # Calcula regularidade
            local regularity = calculate_regularity(stats$intervals, stats$avg_interval);
            
            # Se regularidade é alta (baixa variação), pode ser beacon
            if (regularity <= jitter_tolerance) {
                local payload_similar = has_similar_payload_sizes(stats$byte_counts);
                local severity = "MEDIUM";
                
                if (regularity <= jitter_tolerance / 2 && payload_similar)
                    severity = "CRITICAL";
                else if (regularity <= jitter_tolerance && payload_similar)
                    severity = "HIGH";
                
                NOTICE([$note=Beaconing_Detected,
                        $msg=fmt("[BEACONING] [%s] Beaconing Detected: %s -> %s:%d shows regular periodic pattern (avg: %s, regularity: %.3f, connections: %d)", 
                                severity, SIMIR::format_ip(orig), SIMIR::format_ip(resp), dport, 
                                stats$avg_interval, regularity, stats$connections),
                        $src=orig,
                        $dst=resp,
                        $p=dport,
                        $n=stats$connections,
                        $proto=get_port_transport_proto(dport),
                        $sub=fmt("beacon_%.3f_regularity", regularity),
                        $identifier=fmt("beacon_%s_%s_%d", orig, resp, dport),
                        $suppress_for=20min]);
            }
        }
    }
}

event connection_state_remove(c: connection)
{
    if (!c?$id || !c?$conn)
        return;
    
    local orig = c$id$orig_h;
    local resp = c$id$resp_h;
    local dport = c$id$resp_p;
    
    if ([orig, resp, dport] !in beacon_stats)
        return;
    
    local stats = beacon_stats[orig, resp, dport];
    
    # Registra quantidade de bytes transferidos
    local total_bytes = c$conn$orig_bytes + c$conn$resp_bytes;
    stats$byte_counts += total_bytes;
}

event zeek_init()
{
    print fmt("Beaconing Detector ativo - Min connections: %d, Jitter tolerance: %.2f%%, Interval: %s-%s",
              min_connections, jitter_tolerance * 100, min_interval, max_interval);
}
