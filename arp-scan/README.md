# Ataque "ARP Scan"

> Executa enumeração de hosts através de ARP request "who-has" para a rede `172.17.0.x/yy`

### Execução do ataque:
```
docker run --rm -d --name iotedu-attack-arp-scan iotedu-attack-arp-scan:latest "172.17.0.x/yy"
```