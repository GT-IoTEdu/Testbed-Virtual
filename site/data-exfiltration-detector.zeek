# Data Exfiltration Detector para SIMIR
# Detecta transferências massivas de dados e possível roubo de informação
# Compatível com Zeek 7.2.2+

@load base/frameworks/notice
@load base/protocols/conn
@load ./simir-notice-standards.zeek

module DataExfiltration;

export {
    redef enum Notice::Type += {
        Large_Upload_Detected,
        Large_Download_Detected,
        Massive_Data_Transfer,
        Suspicious_External_Transfer
    };
    
    # Configurações de thresholds
    global upload_threshold: count = 100 * 1024 * 1024 &redef;  # 100 MB
    global download_threshold: count = 500 * 1024 * 1024 &redef;  # 500 MB
    global massive_threshold: count = 1024 * 1024 * 1024 &redef;  # 1 GB
    global time_window: interval = 5min &redef;
    
    # Tracking de transferências
    type TransferStats: record {
        bytes_sent: count &default=0;
        bytes_recv: count &default=0;
        connections: count &default=0;
        first_seen: time;
        last_seen: time;
        external_ips: set[addr] &optional;
    };
    
    global transfer_stats: table[addr] of TransferStats &create_expire=time_window;
}

# Converte bytes para formato legível
function format_bytes(bytes: count): string
{
    if (bytes >= 1073741824)  # 1 GB
        return fmt("%.2f GB", bytes / 1073741824.0);
    else if (bytes >= 1048576)  # 1 MB
        return fmt("%.2f MB", bytes / 1048576.0);
    else if (bytes >= 1024)  # 1 KB
        return fmt("%.2f KB", bytes / 1024.0);
    else
        return fmt("%d bytes", bytes);
}

event connection_state_remove(c: connection)
{
    if (!c?$conn)
        return;
    
    local orig = c$id$orig_h;
    local resp = c$id$resp_h;
    local orig_bytes = c$conn$orig_bytes;
    local resp_bytes = c$conn$resp_bytes;
    
    # Ignora tráfego local ou sem transferência significativa
    if (orig == resp || (orig_bytes < 1024 && resp_bytes < 1024))
        return;
    
    # Ignora protocolos não relevantes para exfiltração de dados
    # ICMP: detectado por DDoS/ICMP Tunnel detectors
    # UDP sem aplicação conhecida: geralmente não é exfiltração
    if (c$conn$proto == icmp)
        return;
    
    # Inicializa tracking para origem se não existir
    if (orig !in transfer_stats) {
        transfer_stats[orig] = [$first_seen=network_time(), $last_seen=network_time()];
        transfer_stats[orig]$external_ips = set();
    }
    
    local stats = transfer_stats[orig];
    stats$bytes_sent += orig_bytes;
    stats$bytes_recv += resp_bytes;
    ++stats$connections;
    stats$last_seen = network_time();
    
    # Rastreia IPs externos
    if (!Site::is_private_addr(resp)) {
        add stats$external_ips[resp];
    }
    
    # Detecta upload massivo
    if (stats$bytes_sent >= upload_threshold && orig_bytes > 10485760) {  # Conexão atual > 10MB
        local upload_str = format_bytes(stats$bytes_sent);
        local duration = stats$last_seen - stats$first_seen;
        
        NOTICE([$note=Large_Upload_Detected,
                $msg=fmt("[DATA-EXFIL] [HIGH] Large Upload: %s uploaded %s in %s", 
                        SIMIR::format_ip(orig), upload_str, duration),
                $src=orig,
                $dst=resp,
                $p=c$id$resp_p,
                $n=stats$bytes_sent,
                $proto=get_port_transport_proto(c$id$resp_p),
                $sub=fmt("upload_%s", upload_str),
                $identifier=fmt("upload_%s", orig),
                $suppress_for=10min]);
    }
    
    # Detecta download massivo
    if (stats$bytes_recv >= download_threshold && resp_bytes > 10485760) {  # Conexão atual > 10MB
        local download_str = format_bytes(stats$bytes_recv);
        local duration_dl = stats$last_seen - stats$first_seen;
        
        NOTICE([$note=Large_Download_Detected,
                $msg=fmt("[DATA-EXFIL] [MEDIUM] Large Download: %s downloaded %s in %s", 
                        SIMIR::format_ip(orig), download_str, duration_dl),
                $src=orig,
                $dst=resp,
                $p=c$id$resp_p,
                $n=stats$bytes_recv,
                $proto=get_port_transport_proto(c$id$resp_p),
                $sub=fmt("download_%s", download_str),
                $identifier=fmt("download_%s", orig),
                $suppress_for=10min]);
    }
    
    # Detecta transferência massiva total
    local total_bytes = stats$bytes_sent + stats$bytes_recv;
    if (total_bytes >= massive_threshold) {
        local total_str = format_bytes(total_bytes);
        local total_duration = stats$last_seen - stats$first_seen;
        
        NOTICE([$note=Massive_Data_Transfer,
                $msg=fmt("[DATA-EXFIL] [CRITICAL] Massive Transfer: %s transferred %s (%s up, %s down) in %s", 
                        SIMIR::format_ip(orig), total_str, 
                        format_bytes(stats$bytes_sent), format_bytes(stats$bytes_recv), 
                        total_duration),
                $src=orig,
                $n=total_bytes,
                $sub=fmt("massive_%s", total_str),
                $identifier=fmt("massive_%s", orig),
                $suppress_for=15min]);
    }
    
    # Detecta transferências suspeitas para múltiplos IPs externos
    if (|stats$external_ips| >= 5 && stats$bytes_sent >= 52428800) {  # 50 MB para ≥5 IPs externos
        local ext_transfer = format_bytes(stats$bytes_sent);
        
        NOTICE([$note=Suspicious_External_Transfer,
                $msg=fmt("[DATA-EXFIL] [HIGH] Suspicious External Transfer: %s sent %s to %d external hosts", 
                        SIMIR::format_ip(orig), ext_transfer, |stats$external_ips|),
                $src=orig,
                $n=stats$bytes_sent,
                $sub=fmt("external_%d_hosts", |stats$external_ips|),
                $identifier=fmt("external_%s", orig),
                $suppress_for=10min]);
    }
}

event zeek_init()
{
    print fmt("Data Exfiltration Detector ativo - Upload: %s, Download: %s, Massive: %s, Window: %s",
              format_bytes(upload_threshold), format_bytes(download_threshold), 
              format_bytes(massive_threshold), time_window);
}
