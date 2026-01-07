# Intelligence Framework - Detecção de IPs em conexões falhadas
# Este módulo complementa o conn-established.zeek padrão
# Detecta IPs maliciosos mesmo quando a conexão não é estabelecida

@load base/frameworks/intel
@load policy/frameworks/intel/seen/where-locations

# Evento acionado quando qualquer conexão termina (estabelecida ou não)
event connection_state_remove(c: connection)
{
    # Detecta IP de origem em qualquer conexão
    Intel::seen(Intel::Seen($host=c$id$orig_h, $conn=c, $where=Conn::IN_ORIG));
    
    # Detecta IP de destino em qualquer conexão
    Intel::seen(Intel::Seen($host=c$id$resp_h, $conn=c, $where=Conn::IN_RESP));
}
