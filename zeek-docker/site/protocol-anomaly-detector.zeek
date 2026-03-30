# Protocol Anomaly Detector para SIMIR
# Detecta uso anômalo de protocolos e portas não-padrão
# Compatível com Zeek 7.2.2+

@load base/frameworks/notice
@load base/protocols/conn
@load base/protocols/ssl
@load base/protocols/http
@load ./simir-notice-standards.zeek

module ProtocolAnomaly;

export {
    redef enum Notice::Type += {
        HTTP_Non_Standard_Port,
        HTTPS_Non_Standard_Port,
        SSH_Non_Standard_Port,
        Invalid_SSL_Certificate,
        Unexpected_Protocol_Port,
        High_Port_Activity
    };
    
    # Configurações
    global time_window: interval = 15min &redef;
    
    # Portas padrão conhecidas
    global standard_http_ports: set[port] = { 80/tcp, 8080/tcp, 8000/tcp } &redef;
    global standard_https_ports: set[port] = { 443/tcp, 8443/tcp } &redef;
    global standard_ssh_ports: set[port] = { 22/tcp } &redef;
    
    # Tracking de anomalias
    type AnomalyStats: record {
        http_non_standard: count &default=0;
        https_non_standard: count &default=0;
        ssh_non_standard: count &default=0;
        high_port_connections: count &default=0;
        first_seen: time;
        last_seen: time;
    };
    
    global anomaly_stats: table[addr] of AnomalyStats &create_expire=time_window;
}

# Detecta HTTP em porta não-padrão
event http_request(c: connection, method: string, original_URI: string, unescaped_URI: string, version: string)
{
    if (!c?$id)
        return;
    
    local orig = c$id$orig_h;
    local resp = c$id$resp_h;
    local dport = c$id$resp_p;
    
    # Verifica se não é porta HTTP padrão
    if (dport !in standard_http_ports) {
        # Inicializa stats
        if (orig !in anomaly_stats) {
            anomaly_stats[orig] = [$first_seen=network_time(), $last_seen=network_time()];
        }
        
        local stats = anomaly_stats[orig];
        ++stats$http_non_standard;
        stats$last_seen = network_time();
        
        NOTICE([$note=HTTP_Non_Standard_Port,
                $msg=fmt("[PROTO-ANOMALY] [MEDIUM] HTTP on Non-Standard Port: %s -> %s:%d using HTTP", 
                        SIMIR::format_ip(orig), SIMIR::format_ip(resp), dport),
                $src=orig,
                $dst=resp,
                $p=dport,
                $proto=tcp,
                $sub=fmt("http_port_%d", dport),
                $identifier=fmt("http_nonstandard_%s_%s_%d", orig, resp, dport),
                $suppress_for=10min]);
    }
}

# Detecta HTTPS em porta não-padrão
event ssl_established(c: connection)
{
    if (!c?$id)
        return;
    
    local orig = c$id$orig_h;
    local resp = c$id$resp_h;
    local dport = c$id$resp_p;
    
    # Verifica se não é porta HTTPS padrão
    if (dport !in standard_https_ports) {
        # Inicializa stats
        if (orig !in anomaly_stats) {
            anomaly_stats[orig] = [$first_seen=network_time(), $last_seen=network_time()];
        }
        
        local stats = anomaly_stats[orig];
        ++stats$https_non_standard;
        stats$last_seen = network_time();
        
        NOTICE([$note=HTTPS_Non_Standard_Port,
                $msg=fmt("[PROTO-ANOMALY] [MEDIUM] HTTPS on Non-Standard Port: %s -> %s:%d using SSL/TLS", 
                        SIMIR::format_ip(orig), SIMIR::format_ip(resp), dport),
                $src=orig,
                $dst=resp,
                $p=dport,
                $proto=tcp,
                $sub=fmt("https_port_%d", dport),
                $identifier=fmt("https_nonstandard_%s_%s_%d", orig, resp, dport),
                $suppress_for=10min]);
    }
}

# Detecta certificados SSL inválidos
event ssl_established(c: connection)
{
    if (!c?$ssl)
        return;
    
    local orig = c$id$orig_h;
    local resp = c$id$resp_h;
    local dport = c$id$resp_p;
    
    # Nota: validation_status não está disponível em Zeek 8.x
    # Detecção de certificado inválido foi removida temporariamente
    # TODO: Implementar usando x509::certificate_seen event
}

# Detecta SSH em porta não-padrão
event ssh_capabilities(c: connection, cookie: string, capabilities: SSH::Capabilities)
{
    if (!c?$id)
        return;
    
    local orig = c$id$orig_h;
    local resp = c$id$resp_h;
    local dport = c$id$resp_p;
    
    # Verifica se não é porta SSH padrão
    if (dport !in standard_ssh_ports) {
        # Inicializa stats
        if (orig !in anomaly_stats) {
            anomaly_stats[orig] = [$first_seen=network_time(), $last_seen=network_time()];
        }
        
        local stats = anomaly_stats[orig];
        ++stats$ssh_non_standard;
        stats$last_seen = network_time();
        
        NOTICE([$note=SSH_Non_Standard_Port,
                $msg=fmt("[PROTO-ANOMALY] [HIGH] SSH on Non-Standard Port: %s -> %s:%d using SSH", 
                        SIMIR::format_ip(orig), SIMIR::format_ip(resp), dport),
                $src=orig,
                $dst=resp,
                $p=dport,
                $proto=tcp,
                $sub=fmt("ssh_port_%d", dport),
                $identifier=fmt("ssh_nonstandard_%s_%s_%d", orig, resp, dport),
                $suppress_for=10min]);
    }
}

# Detecta atividade em portas altas (possível malware)
event new_connection(c: connection)
{
    if (!c?$id)
        return;
    
    local orig = c$id$orig_h;
    local resp = c$id$resp_h;
    local dport = c$id$resp_p;
    
    # Verifica portas altas suspeitas (acima de 40000)
    local port_num = port_to_count(dport);
    if (port_num > 40000 && port_num < 65535) {
        # Inicializa stats
        if (orig !in anomaly_stats) {
            anomaly_stats[orig] = [$first_seen=network_time(), $last_seen=network_time()];
        }
        
        local stats = anomaly_stats[orig];
        ++stats$high_port_connections;
        stats$last_seen = network_time();
        
        # Só alerta se houver múltiplas conexões
        if (stats$high_port_connections >= 5) {
            NOTICE([$note=High_Port_Activity,
                    $msg=fmt("[PROTO-ANOMALY] [MEDIUM] High Port Activity: %s made %d connections to high ports (>40000)", 
                            SIMIR::format_ip(orig), stats$high_port_connections),
                    $src=orig,
                    $n=stats$high_port_connections,
                    $proto=get_port_transport_proto(dport),
                    $sub="high_port_activity",
                    $identifier=fmt("highport_%s", orig),
                    $suppress_for=15min]);
        }
    }
}

# Detecta protocolos inesperados em portas específicas
event connection_state_remove(c: connection)
{
    if (!c?$id || !c?$conn)
        return;
    
    local orig = c$id$orig_h;
    local resp = c$id$resp_h;
    local dport = c$id$resp_p;
    local service = c$conn?$service ? c$conn$service : "unknown";
    
    # Ignora se não detectou serviço
    if (service == "unknown" || service == "-")
        return;
    
    local port_num = port_to_count(dport);
    local is_unexpected = F;
    local expected_service = "";
    
    # Verifica alguns casos específicos de anomalia
    if (port_num == 80 && service != "http") {
        is_unexpected = T;
        expected_service = "http";
    }
    else if (port_num == 443) {
        # Porta 443 aceita SSL, HTTPS, QUIC e AYIYA (protocolos legítimos)
        # QUIC é protocolo moderno do Google, AYIYA é para IPv6 tunneling
        if (service != "ssl" && service != "quic,ssl" && service != "quic" && service != "https" && 
            service != "quic,ssl,ayiya" && service != "ayiya") {
            is_unexpected = T;
            expected_service = "ssl/https/quic";
        }
    }
    else if (port_num == 22 && service != "ssh") {
        is_unexpected = T;
        expected_service = "ssh";
    }
    else if (port_num == 21 && service != "ftp") {
        is_unexpected = T;
        expected_service = "ftp";
    }
    else if (port_num == 25 && service != "smtp") {
        is_unexpected = T;
        expected_service = "smtp";
    }
    
    if (is_unexpected) {
        NOTICE([$note=Unexpected_Protocol_Port,
                $msg=fmt("[PROTO-ANOMALY] [HIGH] Unexpected Protocol: %s -> %s:%d detected '%s' instead of '%s'", 
                        SIMIR::format_ip(orig), SIMIR::format_ip(resp), port_num, service, expected_service),
                $src=orig,
                $dst=resp,
                $p=dport,
                $proto=get_port_transport_proto(dport),
                $sub=fmt("unexpected_%s_on_%d", service, port_num),
                $identifier=fmt("unexpected_%s_%s_%d", orig, resp, port_num),
                $suppress_for=15min]);
    }
}

event zeek_init()
{
    print fmt("Protocol Anomaly Detector ativo - HTTP ports: %d, HTTPS ports: %d, SSH ports: %d",
              |standard_http_ports|, |standard_https_ports|, |standard_ssh_ports|);
}
