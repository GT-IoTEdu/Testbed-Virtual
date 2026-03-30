#!/bin/bash

# ========================================================================
# Script de atualização de Threat Intelligence Feeds para o SIMIR + Zeek
# ========================================================================

# Detecta o diretório base do SIMIR automaticamente
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIMIR_DIR="$(dirname "$SCRIPT_DIR")"
INTEL_DIR="$SIMIR_DIR/site/intel"
TEMP_DIR="/tmp/simir_threat_feeds"
BACKUP_DIR="$INTEL_DIR/backup"

# Contadores
total_ips=0
total_domains=0
feeds_success=0
feeds_failed=0

echo "🔄 Atualizando feeds de threat intelligence..."
echo "📅 $(date)"

# Criar diretórios
mkdir -p "$TEMP_DIR" "$BACKUP_DIR"

# ========================================================================
# Funções
# ========================================================================

backup_existing_feeds() {
    echo "📦 Fazendo backup dos feeds existentes..."
    timestamp=$(date +"%Y%m%d_%H%M%S")
    for file in "$INTEL_DIR"/*.txt; do
        if [ -f "$file" ]; then
            cp "$file" "$BACKUP_DIR/$(basename "$file" .txt)_$timestamp.txt"
        fi
    done
}

convert_abusech_ips() {
    local input="$1"
    local output="$2"
    local source="$3"

    echo "#fields	indicator	indicator_type	meta.source	meta.desc" > "$output"
    grep -v "^#\|^$\|^DstIP" "$input" | while read -r ip; do
        ip=$(echo "$ip" | tr -d '[:space:]')
        if [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo -e "$ip\tIntel::ADDR\t$source\tIP malicioso" >> "$output"
        fi
    done
}

convert_urlhaus_domains() {
    local input="$1"
    local output="$2"

    echo "#fields	indicator	indicator_type	meta.source	meta.desc" > "$output"
    grep -E "^(0\.0\.0\.0|127\.0\.0\.1)" "$input" | awk '{print $2}' | grep -v "localhost" | while read -r domain; do
        domain=$(echo "$domain" | tr -d '[:space:]')
        if [ -n "$domain" ] && [[ "$domain" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            echo -e "$domain\tIntel::DOMAIN\tURLhaus\tDomínio malicioso" >> "$output"
        fi
    done
}

process_spamhaus_drop() {
    local input="$1"
    local output="$2"

    echo "#fields	indicator	indicator_type	meta.source	meta.desc" > "$output"
    grep -v "^;" "$input" | while read -r line; do
        ip=$(echo "$line" | cut -d';' -f1 | cut -d'/' -f1)
        if [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo -e "$ip\tIntel::ADDR\tSpamhaus\tIP malicioso - Spamhaus DROP" >> "$output"
        fi
    done
}

# Função para extrair IOCs das regras do Suricata
extract_suricata_iocs() {
    local input="$1"
    local output="$2"
    local rule_type="$3"

    echo "#fields	indicator	indicator_type	meta.source	meta.desc" > "$output"
    
    # Extrair IPs das regras
    grep -oP '(?<=[\s\[])[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(?=[\s\]/])' "$input" | sort -u | while read -r ip; do
        # Filtrar IPs privados e inválidos
        if [[ ! "$ip" =~ ^(127\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.|0\.|255\.) ]]; then
            echo -e "$ip\tIntel::ADDR\tSuricata-$rule_type\tIP extraído de regras Suricata $rule_type" >> "$output"
        fi
    done
    
    # Extrair domínios das regras
    grep -oP '(?<=[\s";\[])[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.([a-zA-Z]{2,}|[a-zA-Z]{2,}\.[a-zA-Z]{2,})(?=[\s";/\]])' "$input" | \
    grep -E '\.(com|org|net|edu|gov|mil|int|co\.|ru|cn|de|uk|fr|it|es|pl|nl|br|au|ca|jp|kr|in|mx|tw|tr|se|ch|be|dk|no|fi|at|cz|pt|gr|il|za|my|th|sg|ph|vn|id|eg|ar|cl|pe|ve|ec|uy|py|bo|gq|tk|ml|ga|cf|ly|sy|iq|af|pk|bd|lk|mm|kh|la|mn|bt|np|mv|fj|to|ws|tv|nu|ck|pw|vu|sb|ki|nr|mh|fm|as|gu|vi|pr|um)$' | \
    sort -u | while read -r domain; do
        if [[ "$domain" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            echo -e "$domain\tIntel::DOMAIN\tSuricata-$rule_type\tDomínio extraído de regras Suricata $rule_type" >> "$output"
        fi
    done
}

# Função para processar regras de botnet e malware do Suricata
process_suricata_rules() {
    local input="$1"
    local output="$2"
    local rule_name="$3"
    
    echo "#fields	indicator	indicator_type	meta.source	meta.desc" > "$output"
    local total_indicators=0
    
    # Extrair referências a IPs maliciosos das mensagens das regras
    grep -oP 'msg:"[^"]*"' "$input" | grep -iE '(botnet|malware|trojan|c2|c&c|command)' | \
    grep -oP '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | sort -u | while read -r ip; do
        if [[ ! "$ip" =~ ^(127\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.|0\.|255\.) ]]; then
            echo -e "$ip\tIntel::ADDR\tSuricata-$rule_name\tIP de $rule_name detectado via regras Suricata" >> "$output"
            ((total_indicators++))
        fi
    done
    
    # Extrair domínios de C&C das regras
    grep -oP 'content:"[^"]*"' "$input" | grep -oE '[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}' | \
    sort -u | while read -r domain; do
        if [[ "$domain" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]] && [[ ! "$domain" =~ \.(example|test|localhost|local)$ ]]; then
            echo -e "$domain\tIntel::DOMAIN\tSuricata-$rule_name\tDomínio de $rule_name detectado via regras Suricata" >> "$output"
            ((total_indicators++))
        fi
    done
}

check_docker_permissions() {
    if docker ps >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# ========================================================================
# Execução
# ========================================================================

backup_existing_feeds
echo ""
echo "🌐 Baixando feeds de fontes públicas..."

# 1. Abuse.ch Feodo Tracker
echo "  📡 Feodo Tracker (Botnet IPs)..."
if curl -s --connect-timeout 30 --max-time 60 \
    "https://feodotracker.abuse.ch/downloads/ipblocklist.txt" \
    -o "$TEMP_DIR/feodo_ips.txt"; then
    if [ -s "$TEMP_DIR/feodo_ips.txt" ]; then
        convert_abusech_ips "$TEMP_DIR/feodo_ips.txt" "$INTEL_DIR/feodo-ips.txt" "Feodo"
        count=$(grep -v "^#" "$INTEL_DIR/feodo-ips.txt" | wc -l)
        total_ips=$((total_ips + count))
        feeds_success=$((feeds_success + 1))
        echo "    ✅ $count IPs de botnet baixados"
    else
        feeds_failed=$((feeds_failed + 1))
        echo "    ❌ Arquivo vazio recebido"
    fi
else
    feeds_failed=$((feeds_failed + 1))
    echo "    ❌ Falha no download"
fi

# 2. Abuse.ch URLhaus
echo "  🌐 URLhaus (Domínios maliciosos)..."
if curl -s --connect-timeout 30 --max-time 60 \
    "https://urlhaus.abuse.ch/downloads/hostfile/" \
    -o "$TEMP_DIR/urlhaus_domains.txt"; then
    if [ -s "$TEMP_DIR/urlhaus_domains.txt" ]; then
        convert_urlhaus_domains "$TEMP_DIR/urlhaus_domains.txt" "$INTEL_DIR/urlhaus-domains.txt"
        count=$(grep -v "^#" "$INTEL_DIR/urlhaus-domains.txt" | wc -l)
        total_domains=$((total_domains + count))
        feeds_success=$((feeds_success + 1))
        echo "    ✅ $count domínios maliciosos baixados"
    else
        feeds_failed=$((feeds_failed + 1))
        echo "    ❌ Arquivo vazio recebido"
    fi
else
    feeds_failed=$((feeds_failed + 1))
    echo "    ❌ Falha no download"
fi

# 3. Spamhaus DROP
echo "  🚫 Spamhaus DROP (IPs maliciosos)..."
if curl -s --connect-timeout 30 --max-time 60 \
    "https://www.spamhaus.org/drop/drop.txt" \
    -o "$TEMP_DIR/spamhaus_drop.txt"; then
    if [ -s "$TEMP_DIR/spamhaus_drop.txt" ]; then
        process_spamhaus_drop "$TEMP_DIR/spamhaus_drop.txt" "$INTEL_DIR/spamhaus-drop.txt"
        count=$(grep -v "^#" "$INTEL_DIR/spamhaus-drop.txt" | wc -l)
        total_ips=$((total_ips + count))
        feeds_success=$((feeds_success + 1))
        echo "    ✅ $count IPs Spamhaus baixados"
    else
        feeds_failed=$((feeds_failed + 1))
        echo "    ❌ Arquivo vazio recebido"
    fi
else
    feeds_failed=$((feeds_failed + 1))
    echo "    ❌ Falha no download"
fi

# 4. Tor Exit Nodes
echo "  🔒 Tor Exit Nodes..."
if curl -s --connect-timeout 30 --max-time 60 \
    "https://check.torproject.org/torbulkexitlist" \
    -o "$TEMP_DIR/tor_exits.txt"; then
    if [ -s "$TEMP_DIR/tor_exits.txt" ]; then
        echo "#fields	indicator	indicator_type	meta.source	meta.desc" > "$INTEL_DIR/tor-exits.txt"
        grep -E "^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$" "$TEMP_DIR/tor_exits.txt" | while read -r ip; do
            echo -e "$ip\tIntel::ADDR\tTorProject\tTor exit node" >> "$INTEL_DIR/tor-exits.txt"
        done
        count=$(grep -v "^#" "$INTEL_DIR/tor-exits.txt" | wc -l)
        total_ips=$((total_ips + count))
        feeds_success=$((feeds_success + 1))
        echo "    ✅ $count Tor exits baixados"
    else
        feeds_failed=$((feeds_failed + 1))
        echo "    ❌ Arquivo vazio recebido"
    fi
else
    feeds_failed=$((feeds_failed + 1))
    echo "    ❌ Falha no download"
fi

# 5. Hostfile.org
echo "  🦠 Hostfile.org (Domínios maliciosos)..."
if curl -L -s --connect-timeout 30 --max-time 60 \
    "https://someonewhocares.org/hosts/zero/hosts" \
    -o "$TEMP_DIR/hostfile_domains.txt"; then
    if [ -s "$TEMP_DIR/hostfile_domains.txt" ]; then
        echo "#fields	indicator	indicator_type	meta.source	meta.desc" > "$INTEL_DIR/hostfile-domains.txt"
        grep "^0\.0\.0\.0" "$TEMP_DIR/hostfile_domains.txt" | awk '{print $2}' | grep -v "localhost\|0.0.0.0" | while read -r domain; do
            domain=$(echo "$domain" | tr -d '[:space:]')
            if [ -n "$domain" ] && [[ "$domain" =~ ^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
                echo -e "$domain\tIntel::DOMAIN\tHostfile\tDomínio malicioso" >> "$INTEL_DIR/hostfile-domains.txt"
            fi
        done
        count=$(grep -v "^#" "$INTEL_DIR/hostfile-domains.txt" | wc -l)
        total_domains=$((total_domains + count))
        feeds_success=$((feeds_success + 1))
        echo "    ✅ $count domínios Hostfile baixados"
    else
        feeds_failed=$((feeds_failed + 1))
        echo "    ❌ Arquivo vazio recebido"
    fi
else
    feeds_failed=$((feeds_failed + 1))
    echo "    ❌ Falha no download do Hostfile.org"
fi

# ========================================================================
# Feeds do Suricata - Emerging Threats
# ========================================================================

echo ""
echo "🛡️ Baixando regras do Suricata para extração de IOCs..."

# 6. Suricata - Botnet C&C Rules
echo "  🤖 Emerging Threats - Botnet C&C..."
if curl -s --connect-timeout 30 --max-time 60 \
    "https://rules.emergingthreats.net/open/suricata/rules/emerging-botcc.rules" \
    -o "$TEMP_DIR/et_botcc.rules"; then
    if [ -s "$TEMP_DIR/et_botcc.rules" ]; then
        process_suricata_rules "$TEMP_DIR/et_botcc.rules" "$INTEL_DIR/suricata-botcc.txt" "Botnet-CC"
        count=$(grep -v "^#" "$INTEL_DIR/suricata-botcc.txt" | wc -l)
        if [ "$count" -gt 0 ]; then
            total_ips=$((total_ips + $(grep "Intel::ADDR" "$INTEL_DIR/suricata-botcc.txt" | wc -l)))
            total_domains=$((total_domains + $(grep "Intel::DOMAIN" "$INTEL_DIR/suricata-botcc.txt" | wc -l)))
            feeds_success=$((feeds_success + 1))
            echo "    ✅ $count IOCs extraídos das regras de Botnet C&C"
        else
            echo "    ⚠️  Nenhum IOC extraído das regras de Botnet C&C"
        fi
    else
        feeds_failed=$((feeds_failed + 1))
        echo "    ❌ Arquivo de regras vazio"
    fi
else
    feeds_failed=$((feeds_failed + 1))
    echo "    ❌ Falha no download das regras de Botnet C&C"
fi

# 7. Suricata - Compromised IPs
echo "  💀 Emerging Threats - Compromised IPs..."
if curl -s --connect-timeout 30 --max-time 60 \
    "https://rules.emergingthreats.net/open/suricata/rules/emerging-compromised.rules" \
    -o "$TEMP_DIR/et_compromised.rules"; then
    if [ -s "$TEMP_DIR/et_compromised.rules" ]; then
        extract_suricata_iocs "$TEMP_DIR/et_compromised.rules" "$INTEL_DIR/suricata-compromised.txt" "Compromised"
        count=$(grep -v "^#" "$INTEL_DIR/suricata-compromised.txt" | wc -l)
        if [ "$count" -gt 0 ]; then
            total_ips=$((total_ips + $(grep "Intel::ADDR" "$INTEL_DIR/suricata-compromised.txt" | wc -l)))
            total_domains=$((total_domains + $(grep "Intel::DOMAIN" "$INTEL_DIR/suricata-compromised.txt" | wc -l)))
            feeds_success=$((feeds_success + 1))
            echo "    ✅ $count IOCs extraídos das regras de IPs comprometidos"
        else
            echo "    ⚠️  Nenhum IOC extraído das regras de IPs comprometidos"
        fi
    else
        feeds_failed=$((feeds_failed + 1))
        echo "    ❌ Arquivo de regras vazio"
    fi
else
    feeds_failed=$((feeds_failed + 1))
    echo "    ❌ Falha no download das regras de IPs comprometidos"
fi

# 8. Suricata - Malware Rules
echo "  🦠 Emerging Threats - Malware..."
if curl -s --connect-timeout 30 --max-time 60 \
    "https://rules.emergingthreats.net/open/suricata/rules/emerging-malware.rules" \
    -o "$TEMP_DIR/et_malware.rules"; then
    if [ -s "$TEMP_DIR/et_malware.rules" ]; then
        process_suricata_rules "$TEMP_DIR/et_malware.rules" "$INTEL_DIR/suricata-malware.txt" "Malware"
        count=$(grep -v "^#" "$INTEL_DIR/suricata-malware.txt" | wc -l)
        if [ "$count" -gt 0 ]; then
            total_ips=$((total_ips + $(grep "Intel::ADDR" "$INTEL_DIR/suricata-malware.txt" | wc -l)))
            total_domains=$((total_domains + $(grep "Intel::DOMAIN" "$INTEL_DIR/suricata-malware.txt" | wc -l)))
            feeds_success=$((feeds_success + 1))
            echo "    ✅ $count IOCs extraídos das regras de Malware"
        else
            echo "    ⚠️  Nenhum IOC extraído das regras de Malware"
        fi
    else
        feeds_failed=$((feeds_failed + 1))
        echo "    ❌ Arquivo de regras vazio"
    fi
else
    feeds_failed=$((feeds_failed + 1))
    echo "    ❌ Falha no download das regras de Malware"
fi

# ========================================================================
# Atualizar configuração do Zeek
# ========================================================================
echo ""
echo "🔧 Atualizando configuração do Zeek..."
feeds=(
    "feodo-ips.txt"
    "urlhaus-domains.txt" 
    "spamhaus-drop.txt"
    "tor-exits.txt"
    "hostfile-domains.txt"
    "suricata-botcc.txt"
    "suricata-compromised.txt"
    "suricata-malware.txt"
)

config_file="$SIMIR_DIR/site/intelligence-framework.zeek"
for feed in "${feeds[@]}"; do
    if [ -f "$INTEL_DIR/$feed" ] && ! grep -q "$feed" "$config_file"; then
        if grep -q "Intel::read_files" "$config_file"; then
            sed -i "/malicious-.*\.txt\"/a\\    \"/usr/local/zeek/share/zeek/site/intel/$feed\"," "$config_file"
            echo "    ➕ Adicionado $feed à configuração"
        fi
    fi
done

# Limpeza
rm -rf "$TEMP_DIR"

# ========================================================================
# Resumo
# ========================================================================
echo ""
echo "📊 Resumo dos feeds atualizados:"
for file in "$INTEL_DIR"/*.txt; do
    if [ -f "$file" ]; then
        name=$(basename "$file")
        count=$(grep -v "^#" "$file" | wc -l 2>/dev/null || echo "0")
        echo "  📄 $name: $count entradas"
    fi
done

echo ""
echo "📈 Total de indicadores de ameaças baixados: $((total_ips + total_domains))"
echo "   ├─ IPs maliciosos: $total_ips"
echo "   └─ Domínios maliciosos: $total_domains"

# ========================================================================
# Reiniciar Zeek
# ========================================================================
echo ""
echo "🔄 Reiniciando Zeek para carregar novos feeds..."
if command -v docker-compose &> /dev/null; then
    if check_docker_permissions; then
        if docker-compose ps | grep -q "SIMIR_Z"; then
            docker-compose restart SIMIR_Z
            echo "    ✅ Container Zeek reiniciado"
        else
            echo "    ⚠️  Container não está rodando. Inicie com: docker-compose up -d"
        fi
    else
        echo "    ℹ️  Usando sudo para acessar Docker"
        if sudo docker-compose ps | grep -q "SIMIR_Z"; then
            sudo docker-compose restart SIMIR_Z
            echo "    ✅ Container Zeek reiniciado com sudo"
        else
            echo "    ⚠️  Container não está rodando. Inicie com: sudo docker-compose up -d"
        fi
    fi
else
    echo "    ⚠️  docker-compose não encontrado"
fi

# ========================================================================
# Finalização
# ========================================================================
echo ""
echo "✅ Atualização de feeds concluída!"
echo "📅 $(date)"
echo ""
echo "📊 Estatísticas da execução:"
echo "   🎯 Total de indicadores baixados: $((total_ips + total_domains))"
echo "   ├─ 🔴 IPs maliciosos: $total_ips"
echo "   └─ 🌐 Domínios maliciosos: $total_domains"
echo ""
echo "   📈 Status dos feeds:"
echo "   ├─ ✅ Feeds com sucesso: $feeds_success"
echo "   └─ ❌ Feeds com falha: $feeds_failed"
echo ""
if [ $feeds_success -gt 0 ]; then
    echo "🛡️  O SIMIR agora monitora automaticamente todos estes indicadores!"
else
    echo "⚠️  Nenhum feed foi baixado com sucesso. Verifique conectividade de rede."
fi