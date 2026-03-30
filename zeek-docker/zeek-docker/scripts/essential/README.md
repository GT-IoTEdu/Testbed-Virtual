# Scripts Essenciais - SIMIR

**ATENÇÃO**: Esta pasta contém scripts críticos para o funcionamento do sistema SIMIR. **NÃO DELETAR**.

## Scripts Essenciais

Todos os scripts desta pasta são referenciados no `Dockerfile` e são copiados para dentro do container durante a build. A remoção de qualquer um deles quebrará o sistema.

### Lista de Scripts e suas Funções:

#### 1. `entrypoint.sh`
- **Função**: Script de entrada principal do container Docker
- **Usado em**: `Dockerfile` (ENTRYPOINT)
- **Descrição**: Inicializa o container, configura interface de rede, gera node.cfg do Zeek dinamicamente
- **Crítico**: SIM - Container não inicia sem este script

#### 2. `check-interface.sh`
- **Função**: Verifica e valida interface de rede
- **Usado em**: `entrypoint.sh`
- **Descrição**: Garante que a interface de rede especificada existe e está configurada corretamente
- **Crítico**: SIM - Sistema não consegue capturar tráfego sem este script

#### 3. `setup-permissions.sh`
- **Função**: Configura permissões necessárias para o Zeek
- **Usado em**: `entrypoint.sh`
- **Descrição**: Define permissões corretas em diretórios e arquivos do Zeek
- **Crítico**: SIM - Zeek pode falhar sem permissões adequadas

#### 4. `simir-monitor.py`
- **Função**: Monitor Python para análise de logs do Zeek
- **Usado em**: `simir-autostart.sh`
- **Descrição**: Analisa logs em tempo real, detecta padrões de ataque, processa alertas
- **Crítico**: SIM - Detecção avançada não funciona sem este script

#### 5. `simir-autostart.sh`
- **Função**: Auto-inicialização do monitor SIMIR dentro do container
- **Usado em**: `entrypoint.sh`
- **Descrição**: Inicia automaticamente o simir-monitor.py quando o container é iniciado
- **Crítico**: SIM - Monitor não inicia automaticamente sem este script

## Fluxo de Execução

```
Docker Build (Dockerfile)
    ↓
Copia scripts para /usr/local/bin/
    ↓
Container Start
    ↓
entrypoint.sh (ENTRYPOINT)
    ↓
check-interface.sh
    ↓
setup-permissions.sh
    ↓
Zeek inicia
    ↓
simir-autostart.sh
    ↓
simir-monitor.py (background)
```

## Comandos no Dockerfile

```dockerfile
# Copia scripts importantes
COPY scripts/essential/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY scripts/essential/check-interface.sh /usr/local/bin/check-interface.sh
COPY scripts/essential/setup-permissions.sh /usr/local/bin/setup-permissions.sh
COPY scripts/essential/simir-monitor.py /usr/local/bin/simir-monitor.py
COPY scripts/essential/simir-autostart.sh /usr/local/bin/simir-autostart.sh

# Define o entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
```

## Manutenção

### Modificando Scripts
Se você precisa modificar algum script desta pasta:

1. Faça as alterações necessárias
2. Reconstrua a imagem Docker:
   ```bash
   docker-compose build --no-cache
   ```
3. Reinicie o container:
   ```bash
   docker-compose up -d
   ```

### Backup
Antes de fazer qualquer modificação, faça backup desta pasta:
```bash
cp -r scripts/essential scripts/essential.backup
```

### Restauração
Se algo der errado, você pode verificar o histórico do git:
```bash
git log -- scripts/essential/
git restore scripts/essential/nome-do-script.sh
```

## Scripts Auxiliares (fora desta pasta)

Os seguintes scripts estão na pasta `scripts/` principal e são opcionais (não afetam o funcionamento básico do container):

- `simir-control.sh` - Interface de controle e gerenciamento
- `test-*.sh` - Scripts de teste
- `update-threat-feeds.sh` - Atualização de feeds de inteligência
- `compartilhar-internet.sh` - Configuração de rede
- `verificar-internet.sh` - Teste de conectividade

Esses scripts podem ser modificados ou removidos sem quebrar o container Docker, mas são úteis para gerenciamento e testes do sistema.

---

**Data de Criação**: 22 de outubro de 2025  
**Última Atualização**: 22 de outubro de 2025  
**Versão**: 1.0
