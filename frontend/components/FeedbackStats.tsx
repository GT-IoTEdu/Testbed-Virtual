"use client";

import React, { useState, useEffect } from 'react';

interface FeedbackStats {
  total_feedbacks: number;
  status_stats: {
    pending: number;
    reviewed: number;
    action_required: number;
  };
  resolved_stats: {
    resolved: number;
    not_resolved: number;
    pending: number;
  };
  generated_at: string;
}

interface RecentFeedback {
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

const FeedbackStats: React.FC = () => {
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [recentFeedbacks, setRecentFeedbacks] = useState<RecentFeedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatsAndRecent();
  }, []);

  const fetchStatsAndRecent = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
      
      // Buscar estatísticas e feedbacks recentes em paralelo
      const [statsResponse, recentResponse] = await Promise.all([
        fetch(`${base}/api/feedback/stats`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          }
        }),
        fetch(`${base}/api/feedback/recent?days=7`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          }
        })
      ]);

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }

      if (recentResponse.ok) {
        const recentData = await recentResponse.json();
        setRecentFeedbacks(recentData);
      }

      if (!statsResponse.ok || !recentResponse.ok) {
        setError('Erro ao carregar dados de feedback');
      }
    } catch (err) {
      console.error('Erro ao buscar estatísticas:', err);
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

  if (loading) {
    return (
      <div className="p-4 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2 text-gray-600">Carregando estatísticas...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">❌ {error}</p>
        <button
          onClick={fetchStatsAndRecent}
          className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
        >
          Tentar Novamente
        </button>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-4 text-center text-gray-500">
        <p>Nenhuma estatística disponível</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Estatísticas Gerais */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">📊 Estatísticas de Feedback</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <span className="text-2xl">📝</span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-blue-600">Total de Feedbacks</p>
                <p className="text-2xl font-bold text-blue-800">{stats.total_feedbacks}</p>
              </div>
            </div>
          </div>

          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <span className="text-2xl">✅</span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-green-600">Problemas Resolvidos</p>
                <p className="text-2xl font-bold text-green-800">{stats.resolved_stats.resolved}</p>
              </div>
            </div>
          </div>

          <div className="bg-red-50 p-4 rounded-lg">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <span className="text-2xl">❌</span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-red-600">Problemas Não Resolvidos</p>
                <p className="text-2xl font-bold text-red-800">{stats.resolved_stats.not_resolved}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Status Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <p className="text-sm font-medium text-yellow-600">Pendentes</p>
            <p className="text-xl font-bold text-yellow-800">{stats.status_stats.pending}</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-sm font-medium text-green-600">Revisados</p>
            <p className="text-xl font-bold text-green-800">{stats.status_stats.reviewed}</p>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <p className="text-sm font-medium text-red-600">Ação Necessária</p>
            <p className="text-xl font-bold text-red-800">{stats.status_stats.action_required}</p>
          </div>
        </div>

        <div className="mt-4 text-xs text-gray-500 text-center">
          Atualizado em: {formatDateTime(stats.generated_at)}
        </div>
      </div>

      {/* Feedbacks Recentes */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-800">🕒 Feedbacks Recentes (7 dias)</h3>
          <button
            onClick={fetchStatsAndRecent}
            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
          >
            🔄 Atualizar
          </button>
        </div>

        {recentFeedbacks.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p className="text-lg">📭 Nenhum feedback recente</p>
            <p className="text-sm mt-1">Os feedbacks dos últimos 7 dias aparecerão aqui</p>
          </div>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {recentFeedbacks.map((feedback) => (
              <div key={feedback.id} className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(feedback.status)}`}>
                      {getStatusText(feedback.status)}
                    </span>
                    <span className="text-sm text-gray-600">
                      {getResolutionIcon(feedback.problem_resolved)}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">
                    #{feedback.id}
                  </span>
                </div>

                <div className="mb-2">
                  <p className="text-sm font-medium text-gray-700">
                    👤 {feedback.feedback_by}
                  </p>
                  <p className="text-xs text-gray-500">
                    📅 {formatDateTime(feedback.feedback_date)}
                  </p>
                </div>

                <p className="text-sm text-gray-600 line-clamp-2">
                  {feedback.user_feedback}
                </p>

                {feedback.admin_notes && (
                  <div className="mt-2 p-2 bg-blue-50 rounded text-xs">
                    <p className="font-medium text-blue-800">Nota da equipe:</p>
                    <p className="text-blue-700">{feedback.admin_notes}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default FeedbackStats;
