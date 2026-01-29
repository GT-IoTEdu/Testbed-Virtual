# Guia Rápido de Testes SIMIR

## Como Executar os Testes

Execute o script principal:
```bash
./scripts/test-complete.sh
```

## Opções de Teste Disponíveis

### Testes Originais (1-7)

**1. Port Scan Intenso**
- Escaneia 20 portas rapidamente
- Threshold: 15 portas
- Exemplo: `scanme.nmap.org` ou qualquer IP

**2. Ataque de DoS - HTTP**
- 105 requisições HTTP em 60s
- Threshold: 100 conexões
- Exemplo: `example.com`

**3. Ataque de DoS - Porta TCP**
- 105 conexões TCP customizadas
- Threshold: 100 conexões
- Requer porta específica

**4. Ataque de DDoS com hping3**
- SYN flood com múltiplas origens
- Requer root/sudo
- Use apenas em ambiente controlado

**5. Intelligence - Domínio Malicioso**
- Testa detecção de domínios maliciosos
- Usa domínio da lista de threat intelligence

**6. Intelligence - IP Malicioso**
- Testa detecção de IPs maliciosos
- Usa IP da lista de threat intelligence

**7. Força Bruta SSH/HTTP/FTP**
- Simula 15+ tentativas de autenticação falhadas
- Threshold: 10 falhas em 5 minutos
- Suporta SSH, HTTP e FTP

**8. Data Exfiltration**
- Simula upload de arquivos grandes (15MB)
- Threshold: 10MB em 60 segundos
- Exemplo de uso:
  ```bash
  # Opção: 8
  # Host: example.com
  ```

**9. DNS Tunneling**  TESTADO
- Queries DNS com alta entropia e subdomínios longos
- Threshold: 5 queries suspeitas em 60 segundos
- Detecta: strings aleatórias, subdomínios muito longos, dados codificados
- Exemplo de uso:
  ```bash
  # Opção: 9
  # DNS Server: 8.8.8.8 (ou deixe em branco para usar padrão)
  ```
- **Resultado do teste:**  21 alertas gerados com sucesso

**10. Lateral Movement**
- Scanning interno de RDP/SSH/SMB em múltiplos hosts
- Threshold: 5 hosts diferentes em 5 minutos
- Portas monitoradas: 22 (SSH), 445 (SMB), 3389 (RDP)
- Exemplo de uso:
  ```bash
  # Opção: 10
  # Rede: 192.168.0 ou 10.0.0
  ```

**11. SQL Injection**
- Tentativas de SQLi em parâmetros HTTP
- Threshold: 5 tentativas em 60 segundos
- Payloads testados: UNION, OR, DROP, etc
- Exemplo de uso:
  ```bash
  # Opção: 11
  # URL: http://example.com/search ou http://seu-servidor.local/login
  ```

**12. Beaconing (C2 Communication)**
- Conexões periódicas regulares simulando malware
- Threshold: 5 conexões regulares em 5 minutos
- Intervalo: 30 segundos entre beacons
- Este teste leva ~5 minutos para completar
- Exemplo de uso:
  ```bash
  # Opção: 12
  # Host: example.com ou malware-c2-server.com
  ```

**13. Protocol Anomaly**
- Detecta protocolos em portas não-padrão
- Exemplos: HTTP na porta 2222, SSH na porta 8080
- Testa 9 combinações anômalas
- Exemplo de uso:
  ```bash
  # Opção: 13
  # Host: example.com ou seu servidor de teste
  ```

**14. TESTE COMPLETO**
- Executa TODOS os testes acima sequencialmente
- Levará vários minutos para completar
- Requer permissões adequadas
- Gera relatório completo ao final
- Exemplo de uso:
  ```bash
  # Opção: 14
  # Host principal: example.com
  # Rede interna: 192.168.1
  ```

## Exemplos de Uso Rápido

### Teste DNS Tunneling (opção 9)
```bash
(echo "9"; echo "8.8.8.8") | ./scripts/test-complete.sh
```

### Teste Lateral Movement (opção 10)
```bash
(echo "10"; echo "192.168.1") | ./scripts/test-complete.sh
```

### Teste SQL Injection (opção 11)
```bash
(echo "11"; echo "http://example.com/search") | ./scripts/test-complete.sh
```

### Teste Completo Automatizado (opção 14)
```bash
(echo "14"; echo "example.com"; echo "192.168.1"; echo "s") | ./scripts/test-complete.sh
```

## Verificando Resultados

### Ver últimos alertas
```bash
tail -20 logs/notice.log
```

### Contar alertas por tipo
```bash
grep "PortScan::" logs/notice.log | wc -l
grep "DNSTunneling::" logs/notice.log | wc -l
grep "LateralMovement::" logs/notice.log | wc -l
grep "SQLInjection::" logs/notice.log | wc -l
grep "Beaconing::" logs/notice.log | wc -l
grep "ProtocolAnomaly::" logs/notice.log | wc -l
grep "DataExfiltration::" logs/notice.log | wc -l
```

### Ver alertas específicos
```bash
# DNS Tunneling
grep "DNSTunneling::" logs/notice.log | tail -5

# Lateral Movement
grep "LateralMovement::" logs/notice.log | tail -5

# SQL Injection
grep "SQLInjection::" logs/notice.log | tail -5
```

## Notas Importantes

1. **Ambiente Controlado**: Sempre execute testes em ambiente controlado
2. **Permissões**: Alguns testes podem reqerer sudo (ex: hping3)
3. **Tempo de Processamento**: Aguarde alguns segundos após cada teste para o Zeek processar
4. **Alertas Reais**: Os detectores geram alertas REAIS no notice.log
5. **Whitelist**: IPs 192.168.0.1, 192.168.1.1, 10.0.0.1 estão na whitelist do Port Scan

## Status dos Detectores

Todos os 10 detectores estão ativos e funcionais:

 Port Scan Detection
 DoS/DDoS Detection  
 Intelligence Framework
 Brute Force Detection
 Data Exfiltration Detection
 DNS Tunneling Detection
 Lateral Movement Detection
 SQL Injection Detection
 Beaconing Detection
 Protocol Anomaly Detection

## Troubleshooting

### "Container SIMIR_Z não está rodando"
```bash
docker ps | grep SIMIR_Z
# Se não estiver rodando:
docker start SIMIR_Z
```

### Nenhum alerta gerado
- Verifique se o threshold foi atingido
- Aguarde mais tempo para processamento do Zeek
- Verifique se o detector está ativo: `docker exec -it SIMIR_Z zeekctl diag`
- Verifique logs de erro: `tail logs/stderr.log`

### Erro de sintaxe no script
- Certifique-se de ter a versão mais recente do script
- Verifique permissões: `chmod +x scripts/test-complete.sh`
