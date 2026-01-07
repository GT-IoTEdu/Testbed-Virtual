# 🚀 **Guia Completo - Testando Sistema de Permissões no Postman**

## **📥 Passo 1: Importar Collection**

1. **Abra o Postman**
2. **Clique em "Import"** (botão no canto superior esquerdo)
3. **Selecione o arquivo** `IoT-EDU_Permission_Tests.postman_collection.json`
4. **Clique em "Import"**

## **⚙️ Passo 2: Configurar Variáveis de Ambiente**

A collection já vem com variáveis pré-configuradas, mas você pode ajustá-las:

### **Variáveis Padrão:**
- `base_url`: `http://127.0.0.1:8000`
- `api_base`: `{{base_url}}/api/devices`
- `user_id`: `1` (usuário comum)
- `manager_id`: `2` (gestor)

### **Para Alterar Variáveis:**
1. **Clique na collection** "IoT-EDU Permission Tests"
2. **Vá para a aba "Variables"**
3. **Ajuste os valores** conforme necessário
4. **Clique em "Save"**

## **🧪 Passo 3: Executar Testes**

### **🔧 Setup Inicial (OBRIGATÓRIO)**
**Sempre execute primeiro:**
1. **Clique em "🔧 Setup - Salvar Dados DHCP"**
2. **Clique em "Send"**
3. **Verifique se retorna status 200**

### **📋 Ordem Recomendada de Testes**

#### **1. Testes de Atribuição de Dispositivos**

**✅ Teste 1: Usuário Comum - Atribuir a Si Mesmo**
- **Endpoint**: `👤 Usuário Comum - Atribuir Dispositivo a Si Mesmo`
- **Resultado esperado**: `200 OK`
- **Resposta**: Dispositivo atribuído com sucesso

**❌ Teste 2: Usuário Comum - Tentar Atribuir a Outro**
- **Endpoint**: `❌ Usuário Comum - Tentar Atribuir a Outro Usuário (Deve Falhar)`
- **Resultado esperado**: `403 Forbidden`
- **Resposta**: "Você não tem permissão para atribuir este dispositivo a este usuário"

**✅ Teste 3: Gestor - Atribuir a Qualquer Usuário**
- **Endpoint**: `👨‍💼 Gestor - Atribuir Dispositivo a Outro Usuário`
- **Resultado esperado**: `200 OK`
- **Resposta**: Dispositivo atribuído com sucesso

#### **2. Testes de Visualização de Dispositivos**

**✅ Teste 4: Usuário Comum - Ver Seus Dispositivos**
- **Endpoint**: `👤 Usuário Comum - Ver Seus Próprios Dispositivos`
- **Resultado esperado**: `200 OK`
- **Resposta**: Lista de dispositivos do usuário

**❌ Teste 5: Usuário Comum - Tentar Ver Dispositivos de Outro**
- **Endpoint**: `❌ Usuário Comum - Tentar Ver Dispositivos de Outro Usuário (Deve Falhar)`
- **Resultado esperado**: `403 Forbidden`
- **Resposta**: "Você não tem permissão para visualizar os dispositivos deste usuário"

**✅ Teste 6: Gestor - Ver Dispositivos de Qualquer Usuário**
- **Endpoint**: `👨‍💼 Gestor - Ver Dispositivos de Qualquer Usuário`
- **Resultado esperado**: `200 OK`
- **Resposta**: Lista de dispositivos do usuário

#### **3. Testes de Visualização de Usuários por Dispositivo**

**✅ Teste 7: Usuário Comum - Ver Usuários de Seu Dispositivo**
- **Endpoint**: `👤 Usuário Comum - Ver Usuários de Seu Dispositivo`
- **Resultado esperado**: `200 OK`
- **Resposta**: Lista de usuários do dispositivo

**❌ Teste 8: Usuário Comum - Tentar Ver Usuários de Dispositivo que Não Possui**
- **Endpoint**: `❌ Usuário Comum - Tentar Ver Usuários de Dispositivo que Não Possui (Deve Falhar)`
- **Resultado esperado**: `403 Forbidden`
- **Resposta**: "Você não tem permissão para visualizar os usuários deste dispositivo"

**✅ Teste 9: Gestor - Ver Usuários de Qualquer Dispositivo**
- **Endpoint**: `👨‍💼 Gestor - Ver Usuários de Qualquer Dispositivo`
- **Resultado esperado**: `200 OK`
- **Resposta**: Lista de usuários do dispositivo

#### **4. Testes de Remoção de Atribuições**

**✅ Teste 10: Usuário Comum - Remover Sua Própria Atribuição**
- **Endpoint**: `👤 Usuário Comum - Remover Sua Própria Atribuição`
- **Resultado esperado**: `200 OK`
- **Resposta**: Atribuição removida com sucesso

**❌ Teste 11: Usuário Comum - Tentar Remover Atribuição de Outro**
- **Endpoint**: `❌ Usuário Comum - Tentar Remover Atribuição de Outro Usuário (Deve Falhar)`
- **Resultado esperado**: `403 Forbidden`
- **Resposta**: "Você não tem permissão para remover esta atribuição"

**✅ Teste 12: Gestor - Remover Atribuição de Qualquer Usuário**
- **Endpoint**: `👨‍💼 Gestor - Remover Atribuição de Qualquer Usuário`
- **Resultado esperado**: `200 OK`
- **Resposta**: Atribuição removida com sucesso

#### **5. Testes de Funcionalidades Gerais**

**✅ Teste 13: Buscar Atribuições**
- **Endpoint**: `🔍 Buscar Atribuições por Termo`
- **Resultado esperado**: `200 OK`
- **Resposta**: Lista de atribuições encontradas

**✅ Teste 14: Estatísticas**
- **Endpoint**: `📊 Estatísticas de Atribuições`
- **Resultado esperado**: `200 OK`
- **Resposta**: Estatísticas do sistema

## **🔍 Passo 4: Interpretar Resultados**

### **✅ Respostas de Sucesso (200 OK)**
```json
{
  "success": true,
  "message": "Dispositivo atribuído com sucesso",
  "data": {
    "id": 1,
    "user_id": 1,
    "device_id": 1,
    "notes": "Dispositivo atribuído",
    "assigned_by": 1,
    "assigned_at": "2025-01-27T10:30:00"
  }
}
```

### **❌ Respostas de Erro (403 Forbidden)**
```json
{
  "detail": "Você não tem permissão para atribuir este dispositivo a este usuário"
}
```

### **❌ Respostas de Erro (404 Not Found)**
```json
{
  "detail": "Usuário com ID 999 não encontrado"
}
```

## **📊 Passo 5: Executar Collection Completa**

### **Opção 1: Executar Individualmente**
1. **Clique em cada endpoint**
2. **Clique em "Send"**
3. **Verifique o resultado**

### **Opção 2: Executar Collection Runner**
1. **Clique na collection** "IoT-EDU Permission Tests"
2. **Clique em "Run"** (botão no canto superior direito)
3. **Selecione os endpoints** que deseja executar
4. **Clique em "Run IoT-EDU Permission Tests"**

## **🎯 Passo 6: Validar Resultados**

### **Checklist de Validação:**

**✅ Usuário Comum (ID: 1):**
- [ ] Pode atribuir dispositivos a si mesmo
- [ ] NÃO pode atribuir dispositivos a outros usuários
- [ ] Pode ver seus próprios dispositivos
- [ ] NÃO pode ver dispositivos de outros usuários
- [ ] Pode ver usuários de seus dispositivos
- [ ] NÃO pode ver usuários de dispositivos que não possui
- [ ] Pode remover suas próprias atribuições
- [ ] NÃO pode remover atribuições de outros usuários

**✅ Gestor (ID: 2):**
- [ ] Pode atribuir dispositivos a qualquer usuário
- [ ] Pode ver dispositivos de qualquer usuário
- [ ] Pode ver usuários de qualquer dispositivo
- [ ] Pode remover atribuições de qualquer usuário

**✅ Funcionalidades Gerais:**
- [ ] Busca de atribuições funciona para todos
- [ ] Estatísticas funcionam para todos

## **🚨 Solução de Problemas**

### **Erro: "Connection refused"**
- **Verifique se o servidor está rodando**: `python main.py`
- **Verifique a URL**: deve ser `http://127.0.0.1:8000`

### **Erro: "404 Not Found"**
- **Execute primeiro** o endpoint "🔧 Setup - Salvar Dados DHCP"
- **Verifique se os dados DHCP foram salvos**

### **Erro: "500 Internal Server Error"**
- **Verifique os logs do servidor**
- **Verifique se o banco de dados está funcionando**

### **Erro: "403 Forbidden" (quando deveria funcionar)**
- **Verifique se os IDs dos usuários estão corretos**
- **Verifique se o parâmetro `current_user_id` está sendo enviado**

## **💡 Dicas Importantes**

1. **Sempre execute o setup primeiro** para salvar dados DHCP
2. **Use os IDs corretos** dos usuários de teste
3. **Verifique as respostas** para confirmar que as permissões estão funcionando
4. **Teste tanto cenários de sucesso** quanto de falha
5. **Use o Collection Runner** para executar todos os testes de uma vez
6. **Salve os resultados** para documentar o funcionamento

## **🎉 Resultado Esperado**

Após executar todos os testes, você deve ter:
- **✅ 8 testes de sucesso** (200 OK)
- **❌ 6 testes de falha** (403 Forbidden) - que é o comportamento esperado
- **✅ 2 testes de funcionalidades gerais** (200 OK)

**Total: 16 testes executados com sucesso!**

O sistema de permissões está funcionando corretamente! 🚀🔐
