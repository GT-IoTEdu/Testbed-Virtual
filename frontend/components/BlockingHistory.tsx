"use client";

import React, { useState, useEffect } from 'react';

interface BlockingHistoryProps {
  dhcpMappingId?: number;
}

interface BlockingItem {
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
  // Dados do dispositivo (enriquecidos)
  device?: {
    id: number;
    ipaddr: string;
    mac: string;
    descr: string;
    hostname: string;
    server_id: number;
  };
}

const BlockingHistory: React.FC<BlockingHistoryProps> = ({
  dhcpMappingId
}) => {
  const [blockings, setBlockings] = useState<BlockingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'admin' | 'user'>('all');

  useEffect(() => {
    fetchBlockingHistory();
  }, [filter]);

  const fetchDeviceData = async (dhcpMappingId: number) => {
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
      const url = `${base}/api/devices/dhcp/devices/${dhcpMappingId}`;
      
      console.log('🔍 Buscando dados do dispositivo:', url);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('📱 Dados do dispositivo recebidos:', data);
        return data.device;
      } else {
        console.warn(`⚠️ Dispositivo ${dhcpMappingId} não encontrado:`, response.status);
        return null;
      }
    } catch (err) {
      console.error('❌ Erro ao buscar dispositivo:', err);
      return null;
    }
  };

  const fetchBlockingHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
      
      let url = `${base}/api/feedback/recent?days=30`;
      if (dhcpMappingId) {
        url = `${base}/api/feedback/dhcp/${dhcpMappingId}?limit=50`;
      }
      
      console.log('🔍 Fazendo requisição para:', url);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      console.log('📡 Resposta recebida:', response.status, response.statusText);

      if (response.ok) {
        const data = await response.json();
        console.log('📊 Dados recebidos:', data);
        
        // Filtrar por tipo se necessário
        let filteredData = data;
        if (filter === 'admin') {
          filteredData = data.filter((item: BlockingItem) => 
            item.user_feedback.includes('Bloqueio administrativo') || 
            item.admin_reviewed_by
          );
        } else if (filter === 'user') {
          filteredData = data.filter((item: BlockingItem) => 
            !item.user_feedback.includes('Bloqueio administrativo') && 
            !item.admin_reviewed_by
          );
        }
        
        console.log('🔍 Dados filtrados:', filteredData);
        
        // Enriquecer dados com informações do dispositivo
        const enrichedData = await Promise.all(
          filteredData.map(async (item: BlockingItem) => {
            const deviceData = await fetchDeviceData(item.dhcp_mapping_id);
            return {
              ...item,
              device: deviceData
            };
          })
        );
        
        console.log('📱 Dados enriquecidos:', enrichedData);
        setBlockings(enrichedData);
      } else {
        const errorText = await response.text();
        console.error('❌ Erro na resposta:', response.status, errorText);
        setError(`Erro ao carregar histórico de bloqueios: ${response.status}`);
      }
    } catch (err) {
      console.error('❌ Erro ao buscar histórico:', err);
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

  const isAdminBlocking = (item: BlockingItem) => {
    return item.user_feedback.includes('Bloqueio administrativo') || item.admin_reviewed_by;
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
          onClick={fetchBlockingHistory}
          className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
        >
          Tentar Novamente
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-800">
          📋 Histórico de Bloqueios
        </h3>
        
        {!dhcpMappingId && (
          <div className="flex space-x-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 rounded text-sm ${
                filter === 'all' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Todos
            </button>
            <button
              onClick={() => setFilter('admin')}
              className={`px-3 py-1 rounded text-sm ${
                filter === 'admin' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Administrativos
            </button>
            <button
              onClick={() => setFilter('user')}
              className={`px-3 py-1 rounded text-sm ${
                filter === 'user' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Usuários
            </button>
          </div>
        )}
      </div>

      {blockings.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p className="text-lg">📭 Nenhum bloqueio encontrado</p>
          <p className="text-sm mt-1">
            {filter === 'all' && 'Não há histórico de bloqueios nos últimos 30 dias'}
            {filter === 'admin' && 'Não há bloqueios administrativos registrados'}
            {filter === 'user' && 'Não há feedbacks de usuários sobre bloqueios'}
          </p>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {blockings.map((blocking) => (
            <div key={blocking.id} className="border border-gray-200 rounded-lg p-4 bg-white shadow-sm">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(blocking.status)}`}>
                    {getStatusText(blocking.status)}
                  </span>
                  <span className="text-sm text-gray-600">
                    {getResolutionIcon(blocking.problem_resolved)} {getResolutionText(blocking.problem_resolved)}
                  </span>
                  {isAdminBlocking(blocking) && (
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      🔒 Administrativo
                    </span>
                  )}
                </div>
                <span className="text-xs text-gray-500">
                  #{blocking.id}
                </span>
              </div>

              <div className="mb-3">
                <p className="text-sm font-medium text-gray-700 mb-1">
                  👤 {blocking.feedback_by}
                </p>
                <p className="text-xs text-gray-500">
                  📅 {formatDateTime(blocking.feedback_date)}
                </p>
              </div>

              {/* Informações do Dispositivo */}
              {blocking.device && (
                <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <h4 className="text-sm font-medium text-blue-800 mb-2">
                    📱 Dispositivo Bloqueado
                  </h4>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="font-medium text-blue-700">IP:</span>
                      <span className="ml-1 text-blue-600 font-mono">{blocking.device.ipaddr}</span>
                    </div>
                    <div>
                      <span className="font-medium text-blue-700">MAC:</span>
                      <span className="ml-1 text-blue-600 font-mono">{blocking.device.mac}</span>
                    </div>
                    <div className="col-span-2">
                      <span className="font-medium text-blue-700">Descrição:</span>
                      <span className="ml-1 text-blue-600">{blocking.device.descr || 'N/A'}</span>
                    </div>
                    {blocking.device.hostname && (
                      <div className="col-span-2">
                        <span className="font-medium text-blue-700">Hostname:</span>
                        <span className="ml-1 text-blue-600">{blocking.device.hostname}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="mb-3">
                <h4 className="text-sm font-medium text-gray-700 mb-1">
                  {isAdminBlocking(blocking) ? 'Motivo do Bloqueio:' : 'Feedback:'}
                </h4>
                <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                  {blocking.user_feedback}
                </p>
              </div>

              {blocking.admin_notes && (
                <div className="mb-3">
                  <h4 className="text-sm font-medium text-gray-700 mb-1">
                    📝 Notas da Equipe:
                  </h4>
                  <p className="text-sm text-gray-600 bg-blue-50 p-2 rounded">
                    {blocking.admin_notes}
                  </p>
                  {blocking.admin_reviewed_by && (
                    <p className="text-xs text-gray-500 mt-1">
                      Revisado por: {blocking.admin_reviewed_by} em {formatDateTime(blocking.admin_review_date)}
                    </p>
                  )}
                </div>
              )}

              <div className="text-xs text-gray-400 border-t pt-2">
                Criado em: {formatDateTime(blocking.created_at)} | 
                Atualizado em: {formatDateTime(blocking.updated_at)}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="text-center">
        <button
          onClick={fetchBlockingHistory}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
        >
          🔄 Atualizar Histórico
        </button>
      </div>
    </div>
  );
};

export default BlockingHistory;
