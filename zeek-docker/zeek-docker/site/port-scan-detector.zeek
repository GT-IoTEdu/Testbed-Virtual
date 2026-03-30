# Script Zeek para detecção de port scan
# Detecta tentativas de port scan e gera alertas

@load base/frameworks/notice
@load base/protocols/conn

module PortScan;

export {
    # Tipos de notice para port scan
    redef enum Notice::Type += {
        ## Indica que um host está fazendo port scan
        Port_Scan,
        ## Indica que um host está sendo alvo de port scan
        Port_Scan_Target,
        ## Tentativa de conexão em porta fechada
        Closed_Port_Access
    };

    # Configurações seguindo padrões da indústria (Snort/Suricata)
    global port_scan_threshold = 25;    # Número de portas diferentes (padrão Suricata)
    global time_window = 5min;          # Janela de tempo (padrão NIST)
    global closed_port_threshold = 20;  # Tentativas em portas fechadas (evita reconexões)
    global host_threshold = 8;          # Mínimo de hosts para scan vertical
}

# Estrutura para rastrear tentativas de conexão
type scan_tracker: record {
    hosts: set[addr] &default=set();
    ports: set[port] &default=set();
    connections: count &default=0;
    failed_connections: count &default=0;
    first_seen: time;
    last_seen: time;
};

# Tabelas para rastrear atividade
global scanners: table[addr] of scan_tracker &create_expire=time_window;
global targets: table[addr] of scan_tracker &create_expire=time_window;

# Whitelist de IPs legítimos (evita falsos positivos)
global whitelist_ips: set[addr] = {
    127.0.0.1,      # Localhost IPv4
    [::1],          # Localhost IPv6 
    192.168.0.1,    # Gateway típico
    192.168.1.1,    # Gateway típico
    10.0.0.1,       # Gateway típico
} &redef;

# Subnets para ignorar (redes locais comuns)
global ignore_subnets: set[subnet] = {
    224.0.0.0/4,    # Multicast
    169.254.0.0/16, # Link-local IPv4
    255.255.255.255/32, # Broadcast
    [fe80::]/10,    # IPv6 link-local (falsos positivos comuns)
    [ff00::]/8,     # IPv6 multicast
} &redef;

# Portas para ignorar (serviços legítimos que podem gerar falsos positivos)
global ignore_ports: set[port] = {
    135/icmp,       # ICMPv6 Neighbor Solicitation
    136/icmp,       # ICMPv6 Neighbor Advertisement
    0/icmp,         # ICMP genérico
} &redef;

# Função para detectar port scan baseado em conexões
event connection_state_remove(c: connection)
{
    local orig = c$id$orig_h;
    local dest = c$id$resp_h;
    local dest_port = c$id$resp_p;
    
    # Ignora tráfego local (mesmo host)
    if (orig == dest)
        return;
        
    # Ignora IPs na whitelist
    if (orig in whitelist_ips || dest in whitelist_ips)
        return;
        
    # Ignora subnets multicast e broadcast
    if (orig in ignore_subnets || dest in ignore_subnets)
        return;
    
    # Ignora portas específicas (ICMPv6, etc)
    if (dest_port in ignore_ports)
        return;
    
    # Ignora todo tráfego ICMP (não é típico de port scan)
    if (c$id$resp_p == 0/icmp || get_port_transport_proto(c$id$resp_p) == icmp)
        return;
    
    # REMOVIDO: Filtro que ignorava conexões privado→público (navegação web normal)
    # Agora detecta port scans em TODAS as direções:
    # - Interno → Interno (lateral movement)
    # - Interno → Externo (reconnaissance)
    # - Externo → Interno (ataques externos)
    # if (Site::is_private_addr(orig) && !Site::is_private_addr(dest))
    #     return;
    
    # Inicializa tracker para scanner se não existir
    if (orig !in scanners) {
        scanners[orig] = [$first_seen=network_time(), $last_seen=network_time()];
    }
    
    # Inicializa tracker para target se não existir
    if (dest !in targets) {
        targets[dest] = [$first_seen=network_time(), $last_seen=network_time()];
    }
    
    # Verifica se conexão foi rejeitada ou falhou ANTES de contar
    local connection_failed = F;
    if (c?$conn && c$conn?$conn_state) {
        if (c$conn$conn_state in set("REJ", "S0", "OTH")) {
            connection_failed = T;
        }
    }
    
    # Atualiza informações do scanner
    local scanner = scanners[orig];
    add scanner$hosts[dest];
    add scanner$ports[dest_port];
    ++scanner$connections;
    if (connection_failed) {
        ++scanner$failed_connections;
    }
    scanner$last_seen = network_time();
    
    # Atualiza informações do target
    local target = targets[dest];
    add target$hosts[orig];
    add target$ports[dest_port];
    ++target$connections;
    target$last_seen = network_time();
    
    # Detecta port scan por número de portas diferentes
    if (|scanner$ports| >= port_scan_threshold) {
        local scan_duration = duration_to_mins_secs(scanner$last_seen - scanner$first_seen);
        local msg_scan = SIMIR::format_portscan_active(orig, |scanner$hosts|, |scanner$ports|, scan_duration);
        
        # Identifica o alvo principal (o mais escaneado) - usa primeiro host como fallback
        local primary_target = dest;
        
        NOTICE([$note=Port_Scan,
                $msg=msg_scan,
                $src=orig,
                $dst=primary_target,
                $n=|scanner$ports|,
                $proto=get_port_transport_proto(dest_port),
                $sub=fmt("%d targets, %s duration", |scanner$hosts|, scan_duration),
                $identifier=cat(orig)]);
    }
    
    # Detecta tentativas em portas fechadas
    if (connection_failed && scanner$failed_connections >= closed_port_threshold) {
        local msg_closed = SIMIR::format_portscan_closed_ports(orig, dest, scanner$failed_connections);
        
        NOTICE([$note=Closed_Port_Access,
                $msg=msg_closed,
                $src=orig,
                $dst=dest,
                $p=dest_port,
                $n=scanner$failed_connections,
                $proto=get_port_transport_proto(dest_port),
                $sub=fmt("closed_ports"),
                $identifier=cat(orig, "closed_ports")]);
    }
    
    # Detecta host sendo muito escaneado
    if (|target$hosts| >= port_scan_threshold) {
        local msg_target = SIMIR::format_portscan_target(dest, |target$hosts|);
        
        NOTICE([$note=Port_Scan_Target,
                $msg=msg_target,
                $dst=dest,
                $n=|target$hosts|,
                $proto=get_port_transport_proto(dest_port),
                $sub=fmt("being_scanned"),
                $identifier=cat(dest, "target")]);
    }
}

# Event para limpar dados antigos
event zeek_init()
{
    print fmt("Port Scan Detection ativo - Threshold: %d portas, Janela: %s", 
              port_scan_threshold, time_window);
}
