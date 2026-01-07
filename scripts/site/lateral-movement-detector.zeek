# Lateral Movement Detector para SIMIR
# Detecta movimentação lateral suspeita dentro da rede
# Compatível com Zeek 7.2.2+

@load base/frameworks/notice
@load base/protocols/conn
@load ./simir-notice-standards.zeek

module LateralMovement;

export {
    redef enum Notice::Type += {
        Lateral_Movement_RDP,
        Lateral_Movement_SSH,
        Lateral_Movement_SMB,
        Internal_Scanning_Pattern,
        Suspicious_Admin_Protocol
    };
    
    # Configurações
    global rdp_port: port = 3389/tcp &redef;
    global smb_port: port = 445/tcp &redef;
    global ssh_port: port = 22/tcp &redef;
    global threshold_hosts: count = 5 &redef;  # Número de hosts diferentes
    global time_window: interval = 15min &redef;
    
    # Portas administrativas suspeitas
    global admin_ports: set[port] = {
        22/tcp,    # SSH
        23/tcp,    # Telnet
        135/tcp,   # RPC
        139/tcp,   # NetBIOS
        445/tcp,   # SMB
        3389/tcp,  # RDP
        5900/tcp,  # VNC
        5985/tcp,  # WinRM HTTP
        5986/tcp   # WinRM HTTPS
    } &redef;
    
    # Tracking de conexões por origem
    type LateralStats: record {
        rdp_targets: set[addr] &optional;
        ssh_targets: set[addr] &optional;
        smb_targets: set[addr] &optional;
        admin_targets: set[addr] &optional;
        total_connections: count &default=0;
        first_seen: time;
        last_seen: time;
    };
    
    global lateral_stats: table[addr] of LateralStats &create_expire=time_window;
}

# Verifica se é um servidor conhecido
function is_likely_server(ip: addr): bool
{
    # Lista de servidores conhecidos (pode ser expandida)
    # Por padrão, considera IPs com final baixo como possíveis servidores
    local ip_str = fmt("%s", ip);
    
    # Considera .1, .2, .10, .20, etc como possíveis servidores
    if (/\.(1|2|10|20|50|100|200|254)$/ in ip_str)
        return T;
    
    return F;
}

event connection_state_remove(c: connection)
{
    if (!c?$id || !c?$conn)
        return;
    
    local orig = c$id$orig_h;
    local resp = c$id$resp_h;
    local dport = c$id$resp_p;
    
    # Só detecta movimentação interna (private -> private)
    if (!Site::is_private_addr(orig) || !Site::is_private_addr(resp))
        return;
    
    # Ignora auto-conexão
    if (orig == resp)
        return;
    
    # Ignora se destino parece ser um servidor legítimo
    if (is_likely_server(resp))
        return;
    
    # Só monitora protocolos administrativos
    if (dport !in admin_ports)
        return;
    
    # Inicializa tracking
    if (orig !in lateral_stats) {
        lateral_stats[orig] = [$first_seen=network_time(), $last_seen=network_time()];
        lateral_stats[orig]$rdp_targets = set();
        lateral_stats[orig]$ssh_targets = set();
        lateral_stats[orig]$smb_targets = set();
        lateral_stats[orig]$admin_targets = set();
    }
    
    local stats = lateral_stats[orig];
    ++stats$total_connections;
    stats$last_seen = network_time();
    add stats$admin_targets[resp];
    
    # Detecta RDP lateral
    if (dport == rdp_port) {
        add stats$rdp_targets[resp];
        
        if (|stats$rdp_targets| >= threshold_hosts) {
            local duration_rdp = stats$last_seen - stats$first_seen;
            
            NOTICE([$note=Lateral_Movement_RDP,
                    $msg=fmt("[LATERAL-MOVE] [CRITICAL] RDP Lateral Movement: %s connected via RDP to %d internal hosts in %s", 
                            SIMIR::format_ip(orig), |stats$rdp_targets|, duration_rdp),
                    $src=orig,
                    $dst=resp,
                    $p=rdp_port,
                    $n=|stats$rdp_targets|,
                    $proto=tcp,
                    $sub=fmt("RDP_%d_hosts", |stats$rdp_targets|),
                    $identifier=fmt("lateral_rdp_%s", orig),
                    $suppress_for=20min]);
        }
    }
    
    # Detecta SSH lateral
    if (dport == ssh_port) {
        add stats$ssh_targets[resp];
        
        if (|stats$ssh_targets| >= threshold_hosts) {
            local duration_ssh = stats$last_seen - stats$first_seen;
            
            NOTICE([$note=Lateral_Movement_SSH,
                    $msg=fmt("[LATERAL-MOVE] [HIGH] SSH Lateral Movement: %s connected via SSH to %d internal hosts in %s", 
                            SIMIR::format_ip(orig), |stats$ssh_targets|, duration_ssh),
                    $src=orig,
                    $dst=resp,
                    $p=ssh_port,
                    $n=|stats$ssh_targets|,
                    $proto=tcp,
                    $sub=fmt("SSH_%d_hosts", |stats$ssh_targets|),
                    $identifier=fmt("lateral_ssh_%s", orig),
                    $suppress_for=20min]);
        }
    }
    
    # Detecta SMB lateral
    if (dport == smb_port) {
        add stats$smb_targets[resp];
        
        if (|stats$smb_targets| >= threshold_hosts) {
            local duration_smb = stats$last_seen - stats$first_seen;
            
            NOTICE([$note=Lateral_Movement_SMB,
                    $msg=fmt("[LATERAL-MOVE] [CRITICAL] SMB Lateral Movement: %s accessed SMB on %d internal hosts in %s", 
                            SIMIR::format_ip(orig), |stats$smb_targets|, duration_smb),
                    $src=orig,
                    $dst=resp,
                    $p=smb_port,
                    $n=|stats$smb_targets|,
                    $proto=tcp,
                    $sub=fmt("SMB_%d_hosts", |stats$smb_targets|),
                    $identifier=fmt("lateral_smb_%s", orig),
                    $suppress_for=20min]);
        }
    }
    
    # Detecta scanning interno geral de portas administrativas
    if (|stats$admin_targets| >= threshold_hosts * 2) {  # Threshold mais alto
        local duration_scan = stats$last_seen - stats$first_seen;
        
        NOTICE([$note=Internal_Scanning_Pattern,
                $msg=fmt("[LATERAL-MOVE] [HIGH] Internal Admin Scanning: %s scanned admin ports on %d internal hosts in %s", 
                        SIMIR::format_ip(orig), |stats$admin_targets|, duration_scan),
                $src=orig,
                $n=|stats$admin_targets|,
                $proto=tcp,
                $sub=fmt("admin_scan_%d_hosts", |stats$admin_targets|),
                $identifier=fmt("lateral_scan_%s", orig),
                $suppress_for=20min]);
    }
}

event zeek_init()
{
    print fmt("Lateral Movement Detector ativo - Threshold: %d hosts, Window: %s, Admin ports: %d",
              threshold_hosts, time_window, |admin_ports|);
}
