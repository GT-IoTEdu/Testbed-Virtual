# Scripts do Projeto SIMIR

Esta pasta contém todos os scripts utilizados no projeto SIMIR.

## Estrutura de Pastas

```
scripts/
├── essential/        # Scripts críticos usados no Dockerfile (NÃO DELETAR)
│   ├── entrypoint.sh        # Script de entrada do container
│   ├── check-interface.sh   # Verificação de interface de rede
│   ├── setup-permissions.sh # Configuração de permissões
│   ├── simir-monitor.py     # Monitor Python de logs
│   ├── simir-autostart.sh   # Auto-inicialização do monitor
│   └── README.md            # Documentação dos scripts críticos
│
├── simir-control.sh         # Interface de controle e gerenciamento
├── test-*.sh                # Scripts de teste
├── update-threat-feeds.sh   # Atualização de feeds de inteligência
├── compartilhar-internet.sh # Configuração de rede
├── verificar-internet.sh    # Teste de conectividade
└── README.md               # Este arquivo
```

## Scripts Críticos (essential/)

**ATENÇÃO**: Os scripts dentro da pasta `essential/` são essenciais para o funcionamento do sistema e são referenciados no Dockerfile. Não devem ser deletados ou movidos.

Consulte `essential/README.md` para documentação detalhada.

### Resumo dos Scripts Críticos:
- **entrypoint.sh**: Script principal de entrada do container Docker
- **check-interface.sh**: Verificação da interface de rede
- **setup-permissions.sh**: Configuração de permissões do sistema
- **simir-monitor.py**: Monitor Python para análise de logs em tempo real
- **simir-autostart.sh**: Auto-inicialização do monitor dentro do container

## Scripts de Gerenciamento

### `simir-control.sh`
Interface completa de controle do sistema SIMIR:
- Iniciar/parar Zeek e monitor
- Ver status do sistema
- Visualizar logs
- Simular ataques para teste
- Gerenciar feeds de inteligência

**Uso:** `./simir-control.sh`

## Scripts de Teste

### `test-complete.sh`
Teste completo de todas as detecções do sistema:
- Port Scan
- Força Bruta
- Intelligence Framework
- DDoS

**Uso:** `./test-complete.sh`

### `test-brute-force.sh`
Teste específico de detecção de força bruta:
- SSH
- FTP
- HTTP

**Uso:** `./test-brute-force.sh`

### `test-intelligence.sh`
Teste básico do Intelligence Framework:
- Carregamento de feeds
- Detecção de IPs maliciosos
- Detecção de domínios maliciosos

**Uso:** `./test-intelligence.sh`

### `test-intelligence-complete.sh`
Teste completo e detalhado do Intelligence Framework:
- Todos os tipos de indicadores
- Validação de feeds
- Testes de performance

**Uso:** `./test-intelligence-complete.sh`

## Scripts Auxiliares

### `update-threat-feeds.sh`
Atualiza os feeds de threat intelligence:
- Baixa feeds de IPs maliciosos
- Atualiza domínios maliciosos
- Atualiza URLs maliciosas
- Tor exit nodes
- Malware hashes

**Uso:** `./update-threat-feeds.sh`

### `compartilhar-internet.sh`
Configura compartilhamento de internet entre interfaces:
- Configuração de NAT/masquerade
- IP forwarding
- Gateway entre redes

**Uso:** `./compartilhar-internet.sh [interface_wan] [interface_lan]`

### `verificar-internet.sh`
Verifica conectividade de internet:
- Testa DNS
- Testa conectividade HTTP/HTTPS
- Mostra configuração de rede

**Uso:** `./verificar-internet.sh`

## Como usar

### Iniciar o sistema:
```bash
# Método recomendado (da raiz do projeto)
./start-simir.sh

# Ou via script de controle
./scripts/simir-control.sh
```

### Testar detecções:
```bash
# Teste completo
./scripts/test-complete.sh

# Testes específicos
./scripts/test-brute-force.sh
./scripts/test-intelligence.sh
```

### Atualizar feeds:
```bash
./scripts/update-threat-feeds.sh
```

## Manutenção

### Modificando Scripts Críticos
Se você precisa modificar scripts em `essential/`:

1. Faça backup primeiro:
   ```bash
   cp -r scripts/essential scripts/essential.backup
   ```

2. Faça suas modificações

3. Reconstrua o container:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Adicionando Novos Scripts
Scripts opcionais devem ficar na pasta `scripts/` principal, não em `essential/`.

---

**Nota**: Para proteger os scripts críticos em futuras limpezas, sempre verifique a pasta `essential/` antes de deletar qualquer arquivo.


### Para verificar interface manualmente:
```bash
./scripts/check-interface.sh enx000ec89f6cc0
```

### Para acompanhar logs do container:
```bash
docker logs -f SIMIR_Z
```

## Estrutura de Logs

O entrypoint produz logs detalhados com prefixo `[Zeek Entrypoint]` para facilitar o debug.

## Troubleshooting

Se houver problemas:

1. **Container em loop de restart**: Verifique se a interface de rede existe no host
2. **Problemas de permissão**: Execute o container como privileged
3. **Interface não encontrada**: Use `ip link show` para listar interfaces disponíveis
4. **Zeek não inicia**: Verifique logs com `docker logs SIMIR_Z`
