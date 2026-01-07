# SQL Injection Detector para SIMIR
# Detecta tentativas de SQL Injection em tráfego HTTP
# Compatível com Zeek 7.2.2+

@load base/frameworks/notice
@load base/protocols/http
@load ./simir-notice-standards.zeek

module SQLInjection;

export {
    redef enum Notice::Type += {
        SQL_Injection_Attempt,
        SQL_Injection_Pattern,
        SQL_Injection_High_Risk,
        SQL_Error_Disclosure
    };
    
    # Configurações
    global time_window: interval = 10min &redef;
    global threshold_attempts: count = 3 &redef;
    
    # Padrões de SQL Injection
    global sqli_patterns: set[string] = {
        "UNION.*SELECT",
        "SELECT.*FROM",
        "INSERT.*INTO",
        "UPDATE.*SET",
        "DELETE.*FROM",
        "DROP.*TABLE",
        "CREATE.*TABLE",
        "ALTER.*TABLE",
        "EXEC.*xp_",
        "';.*--",
        "OR.*1=1",
        "OR.*'1'='1",
        "HAVING.*1=1",
        "GROUP.*BY",
        "ORDER.*BY",
        "WAITFOR.*DELAY",
        "BENCHMARK\\(",
        "SLEEP\\(",
        "pg_sleep",
        "INFORMATION_SCHEMA",
        "LOAD_FILE",
        "INTO.*OUTFILE",
        "sqlmap",
        "1' AND '1'='1",
        "1' OR '1'='1",
        "admin'--",
        "admin'#",
        "' OR 1=1--"
    } &redef;
    
    # Padrões de erro SQL
    global sql_error_patterns: set[string] = {
        "SQL syntax",
        "mysql_fetch",
        "mysql_query",
        "PostgreSQL.*ERROR",
        "ORA-[0-9]+",
        "Microsoft OLE DB Provider for SQL Server",
        "Unclosed quotation mark",
        "ODBC SQL Server Driver",
        "SQLServer JDBC Driver",
        "SqlException"
    } &redef;
    
    # Tracking de tentativas por IP
    type SQLiStats: record {
        attempts: count &default=0;
        high_risk_attempts: count &default=0;
        first_seen: time;
        last_seen: time;
        targets: set[addr] &optional;
        uris: set[string] &optional;
    };
    
    global sqli_stats: table[addr] of SQLiStats &create_expire=time_window;
}

# Verifica se string contém padrões de SQLi
function has_sqli_pattern(s: string): bool
{
    if (|s| == 0)
        return F;
    
    # Converte para maiúsculas para matching case-insensitive
    local s_upper = to_upper(s);
    
    # Verifica padrões críticos inline (mais eficiente em Zeek)
    if (/UNION.*SELECT/ in s_upper) return T;
    if (/DROP.*TABLE/ in s_upper) return T;
    if (/DELETE.*FROM/ in s_upper) return T;
    if (/INSERT.*INTO/ in s_upper) return T;
    if (/UPDATE.*SET/ in s_upper) return T;
    if (/EXEC.*XP_/ in s_upper) return T;
    if (/XP_CMDSHELL/ in s_upper) return T;
    if (/' OR 1=1/ in s_upper) return T;
    if (/' AND 1=1/ in s_upper) return T;
    if (/ADMIN'--/ in s_upper) return T;
    if (/WAITFOR.*DELAY/ in s_upper) return T;
    if (/BENCHMARK\(/ in s_upper) return T;
    if (/SLEEP\(/ in s_upper) return T;
    if (/LOAD_FILE/ in s_upper) return T;
    if (/INTO.*OUTFILE/ in s_upper) return T;
    if (/INFORMATION_SCHEMA/ in s_upper) return T;
    if (/\' OR \'/ in s_upper) return T;
    if (/\' AND \'/ in s_upper) return T;
    if (/ADMIN'#/ in s_upper) return T;
    if (/SQLMAP/ in s_upper) return T;
    if (/PG_SLEEP/ in s_upper) return T;
    
    return F;
}

# Calcula severidade do padrão
function get_sqli_severity(s: string): string
{
    local s_upper = to_upper(s);
    
    # Padrões de alta severidade
    if (/DROP|DELETE|EXEC|XP_|LOAD_FILE|INTO.*OUTFILE|WAITFOR.*DELAY|BENCHMARK|SLEEP/ in s_upper)
        return "CRITICAL";
    
    # Padrões de média-alta severidade
    if (/UNION.*SELECT|INSERT.*INTO|UPDATE.*SET|sqlmap/ in s_upper)
        return "HIGH";
    
    # Outros padrões
    return "MEDIUM";
}

event http_request(c: connection, method: string, original_URI: string, unescaped_URI: string, version: string)
{
    if (!c?$id)
        return;
    
    local orig = c$id$orig_h;
    local resp = c$id$resp_h;
    
    # Verifica URI e parâmetros
    local uri_to_check = unescaped_URI;
    if (|uri_to_check| == 0)
        uri_to_check = original_URI;
    
    if (!has_sqli_pattern(uri_to_check))
        return;
    
    # Inicializa stats
    if (orig !in sqli_stats) {
        sqli_stats[orig] = [$first_seen=network_time(), $last_seen=network_time()];
        sqli_stats[orig]$targets = set();
        sqli_stats[orig]$uris = set();
    }
    
    local stats = sqli_stats[orig];
    ++stats$attempts;
    stats$last_seen = network_time();
    add stats$targets[resp];
    add stats$uris[uri_to_check];
    
    local severity = get_sqli_severity(uri_to_check);
    
    # Conta tentativas de alto risco
    if (severity == "CRITICAL" || severity == "HIGH")
        ++stats$high_risk_attempts;
    
    # Trunca URI se muito longa
    local uri_display = uri_to_check;
    if (|uri_display| > 200)
        uri_display = sub_bytes(uri_display, 0, 200) + "...";
    
    # Alerta imediato para padrões de alta severidade
    if (severity == "CRITICAL") {
        NOTICE([$note=SQL_Injection_High_Risk,
                $msg=fmt("[SQLi] [CRITICAL] High-Risk SQL Injection: %s attempted dangerous SQLi against %s: %s", 
                        SIMIR::format_ip(orig), SIMIR::format_ip(resp), uri_display),
                $src=orig,
                $dst=resp,
                $p=c$id$resp_p,
                $proto=tcp,
                $sub=fmt("high_risk_%s", method),
                $identifier=fmt("sqli_critical_%s_%s", orig, md5_hash(uri_to_check)),
                $suppress_for=5min]);
    }
    
    # Alerta para padrão de SQLi
    if (stats$attempts >= threshold_attempts) {
        NOTICE([$note=SQL_Injection_Pattern,
                $msg=fmt("[SQLi] [HIGH] SQL Injection Pattern: %s made %d SQLi attempts against %d targets", 
                        SIMIR::format_ip(orig), stats$attempts, |stats$targets|),
                $src=orig,
                $n=stats$attempts,
                $proto=tcp,
                $sub=fmt("pattern_%d_attempts", stats$attempts),
                $identifier=fmt("sqli_pattern_%s", orig),
                $suppress_for=10min]);
    }
    
    # Alerta individual
    NOTICE([$note=SQL_Injection_Attempt,
            $msg=fmt("[SQLi] [%s] SQL Injection Attempt: %s -> %s %s %s", 
                    severity, SIMIR::format_ip(orig), SIMIR::format_ip(resp), method, uri_display),
            $src=orig,
            $dst=resp,
            $p=c$id$resp_p,
            $proto=tcp,
            $sub=fmt("sqli_%s", severity),
            $identifier=fmt("sqli_%s_%s", orig, md5_hash(uri_to_check)),
            $suppress_for=3min]);
}

event http_reply(c: connection, version: string, code: count, reason: string)
{
    if (!c?$id || !c?$http)
        return;
    
    local orig = c$id$orig_h;
    local resp = c$id$resp_h;
    
    # Verifica se resposta contém erro SQL
    if (c$http?$status_msg) {
        local status_msg = c$http$status_msg;
        local has_sql_error = F;
        
        for (error_pattern in sql_error_patterns) {
            if (error_pattern in status_msg) {
                has_sql_error = T;
                break;
            }
        }
        
        if (has_sql_error) {
            NOTICE([$note=SQL_Error_Disclosure,
                    $msg=fmt("[SQLi] [HIGH] SQL Error Disclosure: %s disclosed SQL error to %s (possible SQLi vulnerability)", 
                            SIMIR::format_ip(resp), SIMIR::format_ip(orig)),
                    $src=orig,
                    $dst=resp,
                    $p=c$id$resp_p,
                    $proto=tcp,
                    $sub="sql_error",
                    $identifier=fmt("sqli_error_%s_%s", resp, orig),
                    $suppress_for=10min]);
        }
    }
}

event zeek_init()
{
    print fmt("SQL Injection Detector ativo - Threshold: %d attempts, Patterns: %d, Window: %s",
              threshold_attempts, |sqli_patterns|, time_window);
}
