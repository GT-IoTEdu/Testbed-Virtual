# Script Zeek para detecção de ataques de força bruta
# Detecta tentativas de força bruta em serviços de autenticação

@load base/frameworks/notice
@load base/protocols/conn
@load base/protocols/ssh
@load base/protocols/ftp
@load base/protocols/http
@load ./simir-notice-standards.zeek

module BruteForce;

export {
    # Tipos de notice para força bruta
    redef enum Notice::Type += {
        ## Indica tentativa de força bruta SSH
        SSH_Brute_Force,
        ## Indica tentativa de força bruta FTP
        FTP_Brute_Force,
        ## Indica tentativa de força bruta HTTP
        HTTP_Brute_Force,
        ## Indica tentativa de força bruta genérica
        Generic_Brute_Force,
        ## Indica sucesso após múltiplas tentativas
        Successful_After_Failures
    };

    # Configurações
    global ssh_failed_threshold = 5;      # Tentativas SSH falhadas para considerar força bruta
    global ftp_failed_threshold = 5;      # Tentativas FTP falhadas para considerar força bruta
    global http_failed_threshold = 10;    # Tentativas HTTP falhadas para considerar força bruta
    global generic_failed_threshold = 8;  # Tentativas genéricas falhadas
    global time_window = 10min;           # Janela de tempo para análise
    global success_after_failures = 3;    # Sucessos após falhas para alerta
    global monitor_outbound_ssh = F &redef;    # Permite monitorar tentativas internas para externos
    
    # Estrutura para rastrear tentativas de autenticação
    type auth_tracker: record {
        service: string &default="unknown";
        failed_attempts: count &default=0;
        successful_attempts: count &default=0;
        usernames: set[string] &default=set();
        targets: set[addr] &default=set();
        first_seen: time;
        last_seen: time;
        last_failure_time: time &optional;
        consecutive_failures: count &default=0;
    };
    
    # Tabelas exportadas para permitir acesso em testes
    global brute_force_trackers: table[addr] of auth_tracker &create_expire=time_window;
}

# Função auxiliar para verificar se uma porta é de autenticação
function is_auth_port(p: port): bool
{
    local port_num = port_to_count(p);
    return port_num in set(21, 22, 23, 25, 80, 110, 143, 443, 993, 995, 1433, 3306, 3389, 5432);
}

# Rastreamento de conexões SSH por origem
global ssh_connections: table[addr] of count &create_expire=time_window &default=0;

# Evento para detectar múltiplas conexões SSH (indica possível brute-force)
# Cada tentativa de login SSH cria uma nova conexão
event ssh_capabilities(c: connection, cookie: string, capabilities: SSH::Capabilities)
{
    local orig = c$id$orig_h;
    local dest = c$id$resp_h;
    
    # Incrementa contador de conexões SSH desta origem
    ++ssh_connections[orig];
    
    # Inicializa tracker se não existir
    if (orig !in brute_force_trackers) {
        brute_force_trackers[orig] = [$service="SSH", $first_seen=network_time(), $last_seen=network_time()];
    }
    
    local tracker = brute_force_trackers[orig];
    tracker$service = "SSH";
    tracker$failed_attempts = ssh_connections[orig];
    add tracker$targets[dest];
    tracker$last_seen = network_time();
    
    # Verifica se atingiu o threshold para SSH (múltiplas conexões = múltiplas tentativas)
    if (ssh_connections[orig] >= ssh_failed_threshold) {
        NOTICE([$note=SSH_Brute_Force,
                $msg=SIMIR::format_bruteforce_message("SSH", orig, dest, ssh_connections[orig]),
                $src=orig,
                $dst=dest,
                $p=22/tcp,
                $n=ssh_connections[orig],
                $proto=tcp,
                $sub="SSH",
                $identifier=cat(orig, "ssh_brute")]);
    }
}

# Evento alternativo: ssh_auth_attempted (se disponível no Zeek)
event ssh_auth_attempted(c: connection, authenticated: bool)
{
    local orig = c$id$orig_h;
    local dest = c$id$resp_h;
    
    # Ignora autenticações bem-sucedidas
    if (authenticated)
        return;
    
    # Inicializa tracker se não existir
    if (orig !in brute_force_trackers) {
        brute_force_trackers[orig] = [$service="SSH", $first_seen=network_time(), $last_seen=network_time()];
    }
    
    local tracker = brute_force_trackers[orig];
    tracker$service = "SSH";
    ++tracker$failed_attempts;
    ++tracker$consecutive_failures;
    add tracker$targets[dest];
    tracker$last_seen = network_time();
    tracker$last_failure_time = network_time();
    
    # Verifica se atingiu o threshold para SSH
    if (tracker$failed_attempts >= ssh_failed_threshold) {
        NOTICE([$note=SSH_Brute_Force,
                $msg=SIMIR::format_bruteforce_message("SSH", orig, dest, tracker$failed_attempts),
                $src=orig,
                $dst=dest,
                $p=22/tcp,
                $n=tracker$failed_attempts,
                $proto=tcp,
                $sub="SSH",
                $identifier=cat(orig, "ssh_brute")]);
    }
}

# Evento para autenticações SSH bem-sucedidas
event ssh_auth_successful(c: connection, auth_method_none: bool)
{
    local orig = c$id$orig_h;
    local dest = c$id$resp_h;
    
    # Verifica se houve falhas anteriores
    if (orig !in brute_force_trackers)
        return;
    
    local tracker = brute_force_trackers[orig];
    
    # Detecta sucesso após múltiplas falhas (possível brute-force bem-sucedido)
    if (tracker$failed_attempts >= success_after_failures) {
        NOTICE([$note=Successful_After_Failures,
                $msg=fmt("SSH: Autenticação bem-sucedida após %d tentativas falhadas de %s para %s", 
                         tracker$failed_attempts, orig, dest),
                $src=orig,
                $dst=dest,
                $p=22/tcp,
                $n=tracker$failed_attempts,
                $proto=tcp,
                $sub="SSH-SUCCESS",
                $identifier=cat(orig, "ssh_success_after_failures")]);
    }
    
    # Registra o sucesso
    ++tracker$successful_attempts;
    tracker$consecutive_failures = 0;
}

# Função para detectar força bruta baseada em falhas de autenticação FTP
event ftp_reply(c: connection, code: count, msg: string, cont_resp: bool)
{
    local orig = c$id$orig_h;
    local dest = c$id$resp_h;
    
    # Códigos FTP para falha de autenticação: 530 (login incorrect), 331 (password required)
    if (code !in set(530, 421, 425)) 
        return;
    
    # REMOVIDO: Filtro que ignorava tráfego interno→interno
    # Agora detecta ataques de força bruta em toda a rede
    # if (Site::is_private_addr(orig) && Site::is_private_addr(dest))
    #     return;
    
    # Inicializa tracker se não existir
    if (orig !in brute_force_trackers) {
        brute_force_trackers[orig] = [$service="FTP", $first_seen=network_time(), $last_seen=network_time()];
    }
    
    local tracker = brute_force_trackers[orig];
    tracker$service = "FTP";
    ++tracker$failed_attempts;
    ++tracker$consecutive_failures;
    add tracker$targets[dest];
    tracker$last_seen = network_time();
    tracker$last_failure_time = network_time();
    
    # Verifica se atingiu o threshold para FTP
    if (tracker$failed_attempts >= ftp_failed_threshold) {
        NOTICE([$note=FTP_Brute_Force,
                $msg=SIMIR::format_bruteforce_message("FTP", orig, dest, tracker$failed_attempts),
                $src=orig,
                $dst=dest,
                $p=21/tcp,
                $n=tracker$failed_attempts,
                $proto=tcp,
                $sub="FTP",
                $identifier=cat(orig, "ftp_brute")]);
    }
}

# Função para detectar força bruta baseada em respostas HTTP de autenticação
event http_reply(c: connection, version: string, code: count, reason: string)
{
    local orig = c$id$orig_h;
    local dest = c$id$resp_h;
    
    # Códigos HTTP para falha de autenticação: 401 (Unauthorized), 403 (Forbidden)
    if (code !in set(401, 403))
        return;
    
    # REMOVIDO: Filtro que ignorava tráfego interno→interno
    # Agora detecta ataques de força bruta em toda a rede
    # if (Site::is_private_addr(orig) && Site::is_private_addr(dest))
    #     return;
    
    # Inicializa tracker se não existir
    if (orig !in brute_force_trackers) {
        brute_force_trackers[orig] = [$service="HTTP", $first_seen=network_time(), $last_seen=network_time()];
    }
    
    local tracker = brute_force_trackers[orig];
    tracker$service = "HTTP";
    ++tracker$failed_attempts;
    ++tracker$consecutive_failures;
    add tracker$targets[dest];
    tracker$last_seen = network_time();
    tracker$last_failure_time = network_time();
    
    # Verifica se atingiu o threshold para HTTP
    if (tracker$failed_attempts >= http_failed_threshold) {
        NOTICE([$note=HTTP_Brute_Force,
                $msg=SIMIR::format_bruteforce_message("HTTP", orig, dest, tracker$failed_attempts),
                $src=orig,
                $dst=dest,
                $p=80/tcp,
                $n=tracker$failed_attempts,
                $proto=tcp,
                $sub="HTTP",
                $identifier=cat(orig, "http_brute")]);
    }
}

# Função para detectar força bruta genérica baseada em conexões rejeitadas/falhadas
event connection_state_remove(c: connection)
{
    local orig = c$id$orig_h;
    local dest = c$id$resp_h;
    local dest_port = c$id$resp_p;
    
    # SSH agora é tratado por ssh_auth_attempted/ssh_auth_successful, ignorar aqui
    if (port_to_count(dest_port) == 22)
        return;
    
    # Tratamento genérico para outras portas de autenticação
    # Ignora tráfego local
    if (orig == dest)
        return;
    
    # Ignora se não for uma porta de autenticação (exceto SSH que já foi tratado)
    if (!is_auth_port(dest_port) || port_to_count(dest_port) == 22)
        return;
    
    # Verifica se a conexão falhou de forma suspeita
    local generic_connection_failed = F;
    if (c?$conn && c$conn?$conn_state) {
        if (c$conn$conn_state in set("REJ", "S0", "RSTO", "RSTR")) {
            generic_connection_failed = T;
        }
    }
    
    if (!generic_connection_failed)
        return;
    
    # Ignora endereços privados fazendo conexões para a internet
    if (Site::is_private_addr(orig) && !Site::is_private_addr(dest))
        return;
    
    # Inicializa tracker se não existir
    if (orig !in brute_force_trackers) {
        brute_force_trackers[orig] = [$service="Generic", $first_seen=network_time(), $last_seen=network_time()];
    }
    
    local generic_tracker = brute_force_trackers[orig];
    if (generic_tracker$service == "unknown")
        generic_tracker$service = "Generic";
    
    ++generic_tracker$failed_attempts;
    ++generic_tracker$consecutive_failures;
    add generic_tracker$targets[dest];
    generic_tracker$last_seen = network_time();
    generic_tracker$last_failure_time = network_time();
    
    # Verifica se atingiu o threshold genérico (apenas se não foi detectado por outros métodos)
    if (generic_tracker$service == "Generic" && generic_tracker$failed_attempts >= generic_failed_threshold) {
        NOTICE([$note=Generic_Brute_Force,
                $msg=SIMIR::format_bruteforce_message("Generic", orig, dest, generic_tracker$failed_attempts),
                $src=orig,
                $dst=dest,
                $p=c$id$resp_p,
                $n=generic_tracker$failed_attempts,
                $proto=get_port_transport_proto(c$id$resp_p),
                $sub="Generic",
                $identifier=cat(orig, "generic_brute")]);
    }
}

# Event de inicialização
event zeek_init()
{
    print fmt("Brute Force Detection ativo - SSH: %d, FTP: %d, HTTP: %d tentativas, Janela: %s", 
              ssh_failed_threshold, ftp_failed_threshold, http_failed_threshold, time_window);
}

# Event para limpeza periódica (opcional)
event zeek_done()
{
    print "Brute Force Detection finalizado";
}
