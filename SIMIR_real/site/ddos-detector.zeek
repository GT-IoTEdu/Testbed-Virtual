# Detector de DDoS/DoS do SIMIR
# Monitora volume de conexões por destino e identifica padrões suspeitos

@load base/frameworks/notice
@load base/protocols/conn
@load ./simir-notice-standards.zeek

module DDoS;

export {
    redef enum Notice::Type += {
        DoS_Attack_Detected,
        DDoS_Attack_Detected
    };

    # Número de conexões de uma mesma origem para o mesmo destino/porta dentro da janela para DoS
    global dos_threshold: count = 100 &redef;

    # Número mínimo de fontes únicas para considerar DDoS
    global ddos_unique_sources_threshold: count = 12 &redef;

    # Número total de conexões para o destino para reforçar o alerta de DDoS
    global ddos_total_threshold: count = 120 &redef;

    # Janela de observação para contagem dos eventos
    global observation_window: interval = 2min &redef;

    # Servidores DNS conhecidos que devem ser ignorados (tráfego legítimo)
    global ignore_dns_servers: set[addr] = {
        8.8.8.8,        # Google DNS
        8.8.4.4,        # Google DNS
        1.1.1.1,        # Cloudflare DNS
        1.0.0.1,        # Cloudflare DNS
    } &redef;
}

type DestStats: record {
    total_attempts: count &default=0;
    unique_sources: set[addr] &default=set();
    ddos_alerted: bool &default=F;
};

type SrcStats: record {
    attempts: count &default=0;
    alerted: bool &default=F;
};

# Tabelas com chaves compostas (destino, porta) e (origem, destino, porta)
global dest_stats: table[addr, port] of DestStats &write_expire=observation_window;
global src_stats: table[addr, addr, port] of SrcStats &write_expire=observation_window;

event zeek_init()
{
    print fmt("SIMIR DDoS detector ativo - janela: %s, DoS threshold: %d, DDoS threshold: %d/%d",
              observation_window, dos_threshold, ddos_unique_sources_threshold, ddos_total_threshold);
}

event connection_state_remove(c: connection)
{
    if (!c?$id)
        return;

    local orig = c$id$orig_h;
    local dest = c$id$resp_h;
    local dport = c$id$resp_p;

    # Ignora tráfego de loopback
    if (orig == dest)
        return;

    # Ignora consultas DNS para servidores DNS conhecidos (tráfego legítimo)
    if (dport == 53/udp && dest in ignore_dns_servers)
        return;

    # Atualiza estatísticas por destino
    if ( [dest, dport] !in dest_stats )
        dest_stats[dest, dport] = [$ddos_alerted=F];

    local d_stats = dest_stats[dest, dport];
    ++d_stats$total_attempts;
    add d_stats$unique_sources[orig];
    dest_stats[dest, dport] = d_stats;

    # Atualiza estatísticas por origem/destino
    if ( [orig, dest, dport] !in src_stats )
        src_stats[orig, dest, dport] = [$alerted=F];

    local s_stats = src_stats[orig, dest, dport];
    ++s_stats$attempts;

    # Alerta de DoS (origem única)
    if (!s_stats$alerted && s_stats$attempts >= dos_threshold) {
        s_stats$alerted = T;

        local msg_dos = SIMIR::format_ddos_message(dest, dport, s_stats$attempts, 1, "DoS (single source)");
        NOTICE([$note=DoS_Attack_Detected,
                $msg=msg_dos,
                $src=orig,
                $dst=dest,
                $p=dport,
                $n=s_stats$attempts,
                $proto=get_port_transport_proto(dport),
                $sub="DoS_single_source",
                $identifier=fmt("dos_%s_%s_%s", orig, dest, dport),
                $suppress_for=30sec]);
    }

    src_stats[orig, dest, dport] = s_stats;

    # Alerta de DDoS (múltiplas origens)
    if (!d_stats$ddos_alerted && |d_stats$unique_sources| >= ddos_unique_sources_threshold &&
        d_stats$total_attempts >= ddos_total_threshold) {
        d_stats$ddos_alerted = T;

        local msg_ddos = SIMIR::format_ddos_message(dest, dport, d_stats$total_attempts, |d_stats$unique_sources|, "DDoS (multi-source)");
        NOTICE([$note=DDoS_Attack_Detected,
                $msg=msg_ddos,
                $dst=dest,
                $p=dport,
                $n=d_stats$total_attempts,
                $proto=get_port_transport_proto(dport),
                $sub=fmt("DDoS_multi_source_%d_sources", |d_stats$unique_sources|),
                $identifier=fmt("ddos_%s_%s", dest, dport),
                $suppress_for=30min]);
    }

    dest_stats[dest, dport] = d_stats;
}
