# ICMP Tunnel Detector para SIMIR - Zeek 8.x
# Detecta ICMP floods baseado em volume de bytes

@load base/frameworks/notice
@load base/protocols/conn

module ICMPTunnel;

export {
    redef enum Notice::Type += {
        ICMP_Flood_Detected,
        ICMP_Large_Payload,
        ICMP_High_Volume
    };
    
    const flood_threshold: count = 1000000 &redef;
    const large_payload_threshold: count = 100000 &redef;
    const normal_ping_size: count = 84;
}

event connection_state_remove(c: connection)
{
    if (c$conn$proto != icmp)
        return;
    
    if (!c?$id)
        return;
        
    local orig = c$id$orig_h;
    local resp = c$id$resp_h;
    
    local orig_bytes: count = 0;
    if (c$conn?$orig_ip_bytes)
        orig_bytes = c$conn$orig_ip_bytes;
    
    local packets: count = 0;
    if (c$conn?$orig_pkts)
        packets = c$conn$orig_pkts;
    
    local duration: interval = 0sec;
    if (c$conn?$duration)
        duration = c$conn$duration;
    
    local size_mb = (orig_bytes * 1.0) / 1048576.0;
    local size_str = fmt("%.2f MB", size_mb);
    
    if (orig_bytes >= flood_threshold) {
        NOTICE([$note=ICMP_Flood_Detected,
            $msg=fmt("[ICMP-TUNNEL] [HIGH] ICMP Flood: %s sent %s (%d packets) to %s in %.1fs",
                     orig, size_str, packets, resp, interval_to_double(duration)),
            $src=orig,
            $dst=resp,
            $n=orig_bytes,
            $sub="icmp_flood"]);
        return;
    }
    
    if (orig_bytes >= large_payload_threshold) {
        local size_kb = (orig_bytes * 1.0) / 1024.0;
        NOTICE([$note=ICMP_Large_Payload,
            $msg=fmt("[ICMP-TUNNEL] [MEDIUM] Large ICMP Payload: %s sent %.1f KB (%d packets) to %s",
                     orig, size_kb, packets, resp),
            $src=orig,
            $dst=resp,
            $n=orig_bytes,
            $sub="large_payload"]);
        return;
    }
    
    if (packets > 1000 && orig_bytes < large_payload_threshold) {
        NOTICE([$note=ICMP_High_Volume,
            $msg=fmt("[ICMP-TUNNEL] [LOW] High ICMP Packet Count: %s sent %d packets (%d bytes) to %s",
                     orig, packets, orig_bytes, resp),
            $src=orig,
            $dst=resp,
            $n=packets,
            $sub="high_packet_count"]);
    }
}
