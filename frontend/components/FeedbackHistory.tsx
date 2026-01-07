"use client";

import React, { useState, useEffect, useRef } from 'react';

interface FeedbackHistoryProps {
  dhcpMappingId: number;
  deviceIp?: string;
  deviceName?: string;
  theme?: 'light' | 'dark';
}

interface FeedbackItem {
  id: number;
  dhcp_mapping_id: number;
  user_feedback: string;
  problem_resolved: boolean | null;
  feedback_date: string;
  feedback_by: string;
  admin_notes: string | null;
  admin_review_date: string | null;
  admin_reviewed_by: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

const FeedbackHistory: React.FC<FeedbackHistoryProps> = ({
  dhcpMappingId,
  deviceIp,
  deviceName,
  theme = 'light'
}) => {
  const [feedbacks, setFeedbacks] = useState<FeedbackItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFeedbackHistory();
  }, [dhcpMappingId]);

  // Aplicar largura dinâmica da barra de progresso
  useEffect(() => {
    const progressBars = document.querySelectorAll('[data-width]');
    progressBars.forEach(bar => {
      const width = bar.getAttribute('data-width');
      if (width) {
        (bar as HTMLElement).style.width = width;
      }
    });
  }, [feedbacks]);

  const fetchFeedbackHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
      
      const response = await fetch(`${base}/api/feedback/dhcp/${dhcpMappingId}?limit=20`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        }
      });

      if (response.ok) {
        const data = await response.json();
        setFeedbacks(data);
      } else {
        setError('Erro ao carregar histórico de feedback');
      }
    } catch (err) {
      console.error('Erro ao buscar feedback:', err);
      setError('Erro de conexão');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('pt-BR');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING': return 'bg-yellow-100 text-yellow-800';
      case 'REVIEWED': return 'bg-green-100 text-green-800';
      case 'ACTION_REQUIRED': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'PENDING': return 'Pendente';
      case 'REVIEWED': return 'Revisado';
      case 'ACTION_REQUIRED': return 'Ação Necessária';
      default: return status;
    }
  };

  const getResolutionIcon = (resolved: boolean | null) => {
    if (resolved === true) return '✅';
    if (resolved === false) return '❌';
    return '❓';
  };

  const getResolutionText = (resolved: boolean | null) => {
    if (resolved === true) return 'Resolvido';
    if (resolved === false) return 'Não Resolvido';
    return 'Não Informado';
  };

  // Estilos baseados no tema
  const styles = {
    container: theme === 'dark' ? 'space-y-4' : 'space-y-4',
    header: theme === 'dark' ? 'text-slate-200' : 'text-gray-800',
    subheader: theme === 'dark' ? 'text-slate-400' : 'text-gray-600',
    card: theme === 'dark' ? 'border border-slate-600 rounded-lg p-3 bg-slate-800' : 'border border-gray-200 rounded-lg p-3 bg-white shadow-sm',
    text: theme === 'dark' ? 'text-slate-200' : 'text-gray-600',
    mutedText: theme === 'dark' ? 'text-slate-400' : 'text-gray-500',
    bgInfo: theme === 'dark' ? 'bg-slate-700' : 'bg-gray-50',
    bgBlue: theme === 'dark' ? 'bg-slate-700' : 'bg-blue-50',
    textBlue: theme === 'dark' ? 'text-slate-200' : 'text-blue-700',
    button: theme === 'dark' ? 'px-4 py-2 bg-slate-700 text-white rounded-md hover:bg-slate-600 transition-colors text-sm' : 'px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm'
  };

  const isAdminBlocking = (item: BlockingItem) => {
    return item.user_feedback.includes('Bloqueio administrativo') || item.admin_reviewed_by;
  };

  const getWarningInfo = (adminNotes: string | null) => {
    if (!adminNotes) {
      console.log('getWarningInfo: adminNotes é null');
      return null;
    }
    
    console.log('getWarningInfo: adminNotes =', adminNotes);
    
    // Procurar por padrões de advertência mais flexíveis
    const patterns = [
      // "Advertência 1 de 3"
      /advert[êe]ncia\s*(\d+)\s*de\s*(\d+)/i,
      // "1ª advertência de 3"
      /(\d+)[ªº]\s*advert[êe]ncia\s*de\s*(\d+)/i,
      // "1 advertência de 3"
      /(\d+)\s*advert[êe]ncia\s*de\s*(\d+)/i,
      // "Essa é sua 1ª advertência de 3"
      /essa\s*é\s*sua\s*(\d+)[ªº]?\s*advert[êe]ncia\s*de\s*(\d+)/i,
      // "Essa é sua 1 advertência de 3"
      /essa\s*é\s*sua\s*(\d+)\s*advert[êe]ncia\s*de\s*(\d+)/i,
      // "advertência" seguido de números em qualquer lugar
      /advert[êe]ncia.*?(\d+).*?de\s*(\d+)/i,
      // Qualquer texto com "advertência" e números
      /.*?(\d+).*?advert[êe]ncia.*?de\s*(\d+)/i
    ];
    
    for (let i = 0; i < patterns.length; i++) {
      const pattern = patterns[i];
      const match = adminNotes.match(pattern);
      console.log(`Padrão ${i + 1}:`, pattern, 'Match:', match);
      
      if (match) {
        const currentWarning = parseInt(match[1]);
        const totalWarnings = parseInt(match[2]);
        const result = {
          current: currentWarning,
          total: totalWarnings,
          remaining: totalWarnings - currentWarning
        };
        console.log('getWarningInfo: encontrou match!', result);
        return result;
      }
    }
    
    console.log('getWarningInfo: nenhum padrão encontrado');
    return null;
  };

  const getWarningColor = (warningInfo: { current: number; total: number; remaining: number } | null) => {
    if (!warningInfo) return '';
    
    if (warningInfo.remaining <= 0) {
      return 'bg-red-100 text-red-800 border-red-200'; // Bloqueado
    } else if (warningInfo.remaining === 1) {
      return 'bg-yellow-100 text-yellow-800 border-yellow-200'; // Última chance
    } else {
      return 'bg-orange-100 text-orange-800 border-orange-200'; // Aviso
    }
  };

  const markProblemResolved = async (feedbackId: number, resolved: boolean) => {
    try {
      console.log(`Atualizando feedback ${feedbackId} para resolved=${resolved}`);
      
      const response = await fetch(`/api/feedback/${feedbackId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          problem_resolved: resolved
        }),
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (response.ok) {
        const updatedFeedback = await response.json();
        console.log('Feedback atualizado:', updatedFeedback);
        
        // Atualizar o feedback localmente
        setFeedbacks(prevFeedbacks => 
          prevFeedbacks.map(feedback => 
            feedback.id === feedbackId 
              ? { ...feedback, problem_resolved: resolved }
              : feedback
          )
        );
        
        console.log('Feedback atualizado localmente');
      } else {
        const errorText = await response.text();
        console.error('Erro ao atualizar feedback:', response.status, errorText);
        alert(`Erro ao atualizar feedback: ${response.status} - ${errorText}`);
      }
    } catch (error) {
      console.error('Erro ao atualizar feedback:', error);
      alert(`Erro de conexão: ${error}`);
    }
  };

  if (loading) {
    return (
      <div className="p-4 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2 text-gray-600">Carregando histórico...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">❌ {error}</p>
        <button
          onClick={fetchFeedbackHistory}
          className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
        >
          Tentar Novamente
        </button>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={`${styles.bgInfo} p-4 rounded-lg`}>
        <h3 className={`font-semibold ${styles.header} mb-2`}>📋 Histórico de Feedback</h3>
        <p className={`${styles.subheader} text-sm`}>
          <strong>Dispositivo:</strong> {deviceIp} ({deviceName || 'Sem nome'}) | 
          <strong> ID:</strong> {dhcpMappingId}
        </p>
        <p className={`${styles.subheader} text-sm mt-1`}>
          Total de feedbacks: {feedbacks.length}
        </p>
      </div>

      {feedbacks.length === 0 ? (
        <div className={`text-center py-8 ${styles.mutedText}`}>
          <p className="text-lg">📝 Nenhum feedback encontrado</p>
          <p className="text-sm mt-1">Seja o primeiro a fornecer feedback sobre este dispositivo!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {feedbacks.map((feedback) => (
            <div key={feedback.id} className={styles.card}>
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(feedback.status)}`}>
                    {getStatusText(feedback.status)}
                  </span>
                  <span className={`text-sm ${styles.text}`}>
                    {getResolutionIcon(feedback.problem_resolved)} {getResolutionText(feedback.problem_resolved)}
                  </span>
                  {isAdminBlocking(feedback) && (
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      🔒 Administrativo
                    </span>
                  )}
                </div>
                <span className={`text-xs ${styles.mutedText}`}>
                  #{feedback.id}
                </span>
              </div>

              <div className="mb-3">
                <p className={`text-sm font-medium ${styles.text} mb-1`}>
                  👤 {feedback.feedback_by}
                </p>
                <p className={`text-xs ${styles.mutedText}`}>
                  📅 {formatDateTime(feedback.feedback_date)}
                </p>
              </div>

              <div className="mb-3">
                <h4 className={`text-sm font-medium ${styles.text} mb-1`}>Feedback:</h4>
                <p className={`text-sm ${styles.text} ${styles.bgInfo} p-2 rounded`}>
                  {feedback.user_feedback}
                </p>
                
                {/* Botão para marcar resolução (apenas quando não foi respondido) */}
                {feedback.problem_resolved === null && (
                  <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className={`text-sm ${styles.text} mb-2`}>
                      🤔 Este problema foi resolvido?
                    </p>
                    <div className="flex gap-2">
                      <button
                        onClick={() => markProblemResolved(feedback.id, true)}
                        className="px-3 py-1 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
                      >
                        ✅ Sim, foi resolvido
                      </button>
                      <button
                        onClick={() => markProblemResolved(feedback.id, false)}
                        className="px-3 py-1 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm"
                      >
                        ❌ Não foi resolvido
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {feedback.admin_notes && (
                <div className="mb-3">
                  <h4 className={`text-sm font-medium ${styles.text} mb-1`}>
                    📝 Notas da Equipe:
                  </h4>
                  <div className={`text-sm ${styles.textBlue} ${styles.bgBlue} p-2 rounded`}>
                    {feedback.admin_notes}
                  </div>
                  
                  {/* Mostrar contador de advertências se existirem */}
                  {(() => {
                    console.log('Renderizando contador para feedback:', feedback.id, 'admin_notes:', feedback.admin_notes);
                    const warningInfo = getWarningInfo(feedback.admin_notes);
                    console.log('warningInfo result:', warningInfo);
                    
                    if (warningInfo) {
                      return (
                        <div className={`mt-3 p-3 rounded-lg border-2 ${getWarningColor(warningInfo)}`}>
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
                      );
                    }
                    return null;
                  })()}
                  
                  {feedback.admin_reviewed_by && (
                    <p className={`text-xs ${styles.mutedText} mt-1`}>
                      Revisado por: {feedback.admin_reviewed_by} em {formatDateTime(feedback.admin_review_date)}
                    </p>
                  )}
                </div>
              )}

              <div className={`text-xs ${styles.mutedText} border-t pt-2`}>
                Criado em: {formatDateTime(feedback.created_at)} | 
                Atualizado em: {formatDateTime(feedback.updated_at)}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="text-center">
        <button
          onClick={fetchFeedbackHistory}
          className={styles.button}
        >
          🔄 Atualizar Histórico
        </button>
      </div>
    </div>
  );
};

export default FeedbackHistory;
