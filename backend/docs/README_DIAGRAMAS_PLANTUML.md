# 📊 Diagramas PlantUML - Sistema de Bloqueio Automático

## 📋 Arquivos Criados

Foram criados 4 diagramas PlantUML diferentes:

1. **FLUXO_BLOQUEIO_AUTOMATICO.puml** - Diagrama de sequência completo e detalhado
2. **FLUXO_BLOQUEIO_AUTOMATICO_SIMPLIFICADO.puml** - Fluxo simplificado em formato activity
3. **FLUXO_BLOQUEIO_AUTOMATICO_COMPONENTES.puml** - Diagrama de componentes
4. **FLUXO_BLOQUEIO_AUTOMATICO_SEQUENCIA.puml** - Sequência detalhada com todos os participantes

## 🚀 Como Visualizar

### Opção 1: Online (Recomendado)

1. Acesse: http://www.plantuml.com/plantuml/uml/
2. Copie o conteúdo do arquivo `.puml`
3. Cole no editor online
4. O diagrama será gerado automaticamente

### Opção 2: VS Code

1. Instale a extensão "PlantUML" no VS Code
2. Abra o arquivo `.puml`
3. Pressione `Alt+D` para visualizar
4. Ou clique com botão direito → "Preview PlantUML"

### Opção 3: Plugin do IntelliJ/PyCharm

1. Instale o plugin "PlantUML integration"
2. Abra o arquivo `.puml`
3. O diagrama será renderizado automaticamente

### Opção 4: Via Terminal (Java necessário)

```bash
# Instalar PlantUML (requer Java)
# Windows: choco install plantuml
# Linux: sudo apt-get install plantuml
# Mac: brew install plantuml

# Gerar imagem PNG
plantuml backend/docs/FLUXO_BLOQUEIO_AUTOMATICO.puml

# Gerar imagem SVG
plantuml -tsvg backend/docs/FLUXO_BLOQUEIO_AUTOMATICO.puml
```

## 📊 Descrição dos Diagramas

### 1. FLUXO_BLOQUEIO_AUTOMATICO.puml
**Tipo:** Diagrama de Sequência Completo

**Conteúdo:**
- Todos os participantes do sistema
- Fluxo completo com todas as etapas
- Notas com tempos e recursos
- Interações detalhadas entre componentes

**Melhor para:** Documentação completa e detalhada

### 2. FLUXO_BLOQUEIO_AUTOMATICO_SIMPLIFICADO.puml
**Tipo:** Activity Diagram (Fluxo Simplificado)

**Conteúdo:**
- Fluxo linear simplificado
- Apenas as etapas principais
- Tempos e recursos de cada etapa
- Fácil de entender

**Melhor para:** Apresentações e visão geral rápida

### 3. FLUXO_BLOQUEIO_AUTOMATICO_COMPONENTES.puml
**Tipo:** Component Diagram

**Conteúdo:**
- Arquitetura de componentes
- Interfaces e endpoints
- Relacionamentos entre componentes
- Estrutura do sistema

**Melhor para:** Arquitetura e design do sistema

### 4. FLUXO_BLOQUEIO_AUTOMATICO_SEQUENCIA.puml
**Tipo:** Sequence Diagram Detalhado

**Conteúdo:**
- Sequência completa de operações
- Todos os participantes
- Mensagens detalhadas
- Notas com métricas

**Melhor para:** Análise técnica detalhada

## 📈 Dados Incluídos nos Diagramas

Todos os diagramas incluem:

- ⏰ **Tempos de execução** de cada operação
- 💻 **Consumo de CPU** (processo e sistema)
- 🧠 **Consumo de RAM** (processo e sistema)
- 📍 **Endpoints** envolvidos
- 🛣️ **Rotas** completas
- ✅ **Status** de cada operação

## 🎯 Recomendações de Uso

- **Para documentação técnica:** Use `FLUXO_BLOQUEIO_AUTOMATICO.puml`
- **Para apresentações:** Use `FLUXO_BLOQUEIO_AUTOMATICO_SIMPLIFICADO.puml`
- **Para arquitetura:** Use `FLUXO_BLOQUEIO_AUTOMATICO_COMPONENTES.puml`
- **Para análise detalhada:** Use `FLUXO_BLOQUEIO_AUTOMATICO_SEQUENCIA.puml`

## 🔧 Personalização

Os diagramas podem ser editados para:
- Adicionar mais detalhes
- Modificar cores e estilos
- Incluir novos componentes
- Ajustar layout

Basta editar o arquivo `.puml` e re-renderizar.

