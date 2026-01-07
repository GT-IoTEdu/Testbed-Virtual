# Contador de Advertências no Modal de Informações do Dispositivo

## Visão Geral

Implementei o contador de advertências diretamente no bloco "Informações do Dispositivo" do modal de detalhes, proporcionando uma visão imediata do status disciplinar do usuário.

## Funcionalidades Implementadas

### 🎯 **Integração no Modal de Detalhes**

O contador de advertências agora aparece automaticamente no modal "Detalhes do Dispositivo" quando:
- ✅ **Dispositivo está bloqueado**
- ✅ **Existe feedback com advertências** nas notas administrativas
- ✅ **Padrões de advertência** são detectados automaticamente

### 📊 **Interface Visual Integrada**

O contador aparece como uma seção separada dentro do bloco "Informações do Dispositivo":

```
┌─ Informações do Dispositivo ─────────────────┐
│ Nome: Celular Joner                         │
│ IP: 192.168.100.6                          │
│ MAC: f4:02:28:82:45:82                     │
│ Status: BLOQUEADO                           │
│ Descrição: Celular Joner                    │
│ ─────────────────────────────────────────── │
│ ┌─ ⚠️ ADVERTÊNCIA 1 DE 3 ─────────────────┐ │
│ │ ⚠️ ADVERTÊNCIA 1 DE 3                   │ │
│ │ ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ │
│ │ 🔄 Restam 2 advertência(s) antes do     │ │
│ │    bloqueio permanente                  │ │
│ │ Status: EM AVISO                        │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

## 🔧 **Implementação Técnica**

### **1. Funções de Detecção Adicionadas**

```typescript
// Função para detectar advertências nas notas administrativas
const getWarningInfo = (adminNotes: string | null) => {
  if (!adminNotes) return null;
  
  const patterns = [
    /advert[êe]ncia\s*(\d+)\s*de\s*(\d+)/i,
    /(\d+)[ªº]\s*advert[êe]ncia\s*de\s*(\d+)/i,
    /(\d+)\s*advert[êe]ncia\s*de\s*(\d+)/i,
    /essa\s*é\s*sua\s*(\d+)[ªº]?\s*advert[êe]ncia\s*de\s*(\d+)/i,
    /essa\s*é\s*sua\s*(\d+)\s*advert[êe]ncia\s*de\s*(\d+)/i,
    /advert[êe]ncia.*?(\d+).*?de\s*(\d+)/i,
    /.*?(\d+).*?advert[êe]ncia.*?de\s*(\d+)/i
  ];
  
  for (const pattern of patterns) {
    const match = adminNotes.match(pattern);
    if (match) {
      const currentWarning = parseInt(match[1]);
      const totalWarnings = parseInt(match[2]);
      return {
        current: currentWarning,
        total: totalWarnings,
        remaining: totalWarnings - currentWarning
      };
    }
  }
  
  return null;
};

const getWarningColor = (warningInfo: { current: number; total: number; remaining: number } | null) => {
  if (!warningInfo) return '';
  
  if (warningInfo.remaining <= 0) {
    return 'bg-red-100 text-red-800 border-red-200';
  } else if (warningInfo.remaining === 1) {
    return 'bg-yellow-100 text-yellow-800 border-yellow-200';
  } else {
    return 'bg-orange-100 text-orange-800 border-orange-200';
  }
};
```

### **2. Carregamento do Histórico de Feedback**

```typescript
const fetchDeviceDetails = async (device: any) => {
  // ... código existente ...
  
  // Buscar histórico de feedback
  let feedbackHistory = [];
  try {
    const feedbackResponse = await fetch(`/api/feedback/dhcp/${device.id}`);
    if (feedbackResponse.ok) {
      feedbackHistory = await feedbackResponse.json();
    }
  } catch (feedbackError) {
    console.warn('Aviso: Não foi possível carregar histórico de feedback:', feedbackError);
  }
  
  // Combinar dados do dispositivo com informações de bloqueio
  const deviceDetails = {
    ...device,
    is_blocked: blockData.is_blocked,
    block_reason: blockData.reason,
    block_updated_at: blockData.updated_at,
    feedback_history: feedbackHistory // Adicionado
  };
  
  // ... resto do código ...
};
```

### **3. Interface do Contador no Modal**

```jsx
{/* Contador de Advertências */}
{(() => {
  // Buscar feedback mais recente com advertências
  const recentFeedback = deviceDetails.feedback_history?.find((feedback: any) => 
    feedback.admin_notes && getWarningInfo(feedback.admin_notes)
  );
  
  if (recentFeedback) {
    const warningInfo = getWarningInfo(recentFeedback.admin_notes);
    if (warningInfo) {
      return (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <div className={`p-3 rounded-lg border-2 ${getWarningColor(warningInfo)}`}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">⚠️</span>
              <span className="text-sm font-bold">
                ADVERTÊNCIA {warningInfo.current} DE {warningInfo.total}
              </span>
            </div>
            
            {/* Barra de progresso visual */}
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  warningInfo.remaining <= 0 
                    ? 'bg-red-600' 
                    : warningInfo.remaining === 1 
                      ? 'bg-yellow-500' 
                      : 'bg-orange-500'
                }`}
                data-width={`${(warningInfo.current / warningInfo.total) * 100}%`}
              ></div>
            </div>
            
            <div className="text-xs font-medium">
              {warningInfo.remaining > 0 
                ? `🔄 Restam ${warningInfo.remaining} advertência(s) antes do bloqueio permanente`
                : '🚫 Usuário bloqueado permanentemente'
              }
            </div>
            
            {/* Indicador de status */}
            <div className="mt-2 flex items-center gap-1">
              {warningInfo.remaining > 0 ? (
                <>
                  <span className="text-xs">Status:</span>
                  <span className={`text-xs font-bold ${
                    warningInfo.remaining === 1 ? 'text-yellow-700' : 'text-orange-700'
                  }`}>
                    {warningInfo.remaining === 1 ? 'ÚLTIMA CHANCE' : 'EM AVISO'}
                  </span>
                </>
              ) : (
                <>
                  <span className="text-xs">Status:</span>
                  <span className="text-xs font-bold text-red-700">BLOQUEADO</span>
                </>
              )}
            </div>
          </div>
        </div>
      );
    }
  }
  return null;
})()}
```

### **4. Aplicação Dinâmica de Estilos**

```typescript
// Aplicar largura dinâmica da barra de progresso
useEffect(() => {
  const progressBars = document.querySelectorAll('[data-width]');
  progressBars.forEach(bar => {
    const width = bar.getAttribute('data-width');
    if (width) {
      (bar as HTMLElement).style.width = width;
    }
  });
}, [deviceDetails]);
```

## 🎨 **Exemplos de Interface**

### **🟠 1ª Advertência (EM AVISO):**
```
┌─ Informações do Dispositivo ─────────────────┐
│ Nome: Celular Joner                         │
│ IP: 192.168.100.6                          │
│ MAC: f4:02:28:82:45:82                     │
│ Status: BLOQUEADO                           │
│ Descrição: Celular Joner                    │
│ ─────────────────────────────────────────── │
│ ┌─ ⚠️ ADVERTÊNCIA 1 DE 3 ─────────────────┐ │
│ │ ⚠️ ADVERTÊNCIA 1 DE 3                   │ │
│ │ ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ │
│ │ 🔄 Restam 2 advertência(s) antes do     │ │
│ │    bloqueio permanente                  │ │
│ │ Status: EM AVISO                        │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### **🟡 2ª Advertência (ÚLTIMA CHANCE):**
```
┌─ Informações do Dispositivo ─────────────────┐
│ Nome: Celular Joner                         │
│ IP: 192.168.100.6                          │
│ MAC: f4:02:28:82:45:82                     │
│ Status: BLOQUEADO                           │
│ Descrição: Celular Joner                    │
│ ─────────────────────────────────────────── │
│ ┌─ ⚠️ ADVERTÊNCIA 2 DE 3 ─────────────────┐ │
│ │ ⚠️ ADVERTÊNCIA 2 DE 3                   │ │
│ │ ████████████████░░░░░░░░░░░░░░░░░░░░░░░░ │ │
│ │ 🔄 Restam 1 advertência(s) antes do     │ │
│ │    bloqueio permanente                  │ │
│ │ Status: ÚLTIMA CHANCE                   │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### **🔴 3ª Advertência (BLOQUEADO):**
```
┌─ Informações do Dispositivo ─────────────────┐
│ Nome: Celular Joner                         │
│ IP: 192.168.100.6                          │
│ MAC: f4:02:28:82:45:82                     │
│ Status: BLOQUEADO                           │
│ Descrição: Celular Joner                    │
│ ─────────────────────────────────────────── │
│ ┌─ ⚠️ ADVERTÊNCIA 3 DE 3 ─────────────────┐ │
│ │ ⚠️ ADVERTÊNCIA 3 DE 3                   │ │
│ │ ████████████████████████████████████████ │ │
│ │ 🚫 Usuário bloqueado permanentemente    │ │
│ │ Status: BLOQUEADO                        │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

## 🎯 **Cenários de Uso**

### **📱 Usuário Acessa Detalhes:**
1. **Usuário clica** em "Detalhes" na lista "Meus Dispositivos"
2. **Modal abre** com informações do dispositivo
3. **Sistema carrega** histórico de feedback automaticamente
4. **Contador aparece** se houver advertências
5. **Interface mostra** status disciplinar claramente

### **🔍 Administrador Adiciona Advertência:**
1. **Administrador bloqueia** dispositivo com motivo
2. **Sistema salva** feedback com advertência
3. **Usuário acessa** detalhes do dispositivo
4. **Contador aparece** automaticamente
5. **Interface atualiza** com novo status

## 🎉 **Benefícios da Implementação**

### **Para Usuários:**
- ✅ **Visibilidade imediata** do status disciplinar
- ✅ **Interface integrada** no modal de detalhes
- ✅ **Informações claras** sobre advertências
- ✅ **Barra de progresso** visual
- ✅ **Status semântico** com cores

### **Para Administradores:**
- ✅ **Controle visual** sobre advertências
- ✅ **Interface padronizada** em todos os modais
- ✅ **Detecção automática** de padrões
- ✅ **Rastreabilidade** completa

### **Para o Sistema:**
- ✅ **Integração perfeita** com modal existente
- ✅ **Carregamento automático** de dados
- ✅ **Interface responsiva** e adaptável
- ✅ **Código reutilizável** e manutenível

## 📁 **Arquivos Modificados**

### **Frontend:**
- `frontend/app/dashboard/page.tsx` - Contador integrado ao modal de detalhes

### **Documentação:**
- `frontend/docs/DEVICE_INFO_WARNING_COUNTER.md` - **NOVO**: Documentação da implementação

## 🚀 **Como Funciona**

1. **Usuário clica** "Detalhes" em um dispositivo
2. **Sistema carrega** informações do dispositivo
3. **Sistema busca** histórico de feedback automaticamente
4. **Sistema detecta** advertências nas notas administrativas
5. **Interface exibe** contador visual no bloco de informações
6. **Usuário vê** claramente seu status disciplinar

## ✅ **Conclusão**

O contador de advertências está **100% integrado** ao modal de informações do dispositivo, proporcionando:

- **Visibilidade imediata** do status disciplinar
- **Interface integrada** e consistente
- **Carregamento automático** de dados
- **Detecção automática** de advertências
- **Experiência do usuário** melhorada

O sistema agora mostra automaticamente o contador de advertências no bloco de informações do dispositivo! 🎉
