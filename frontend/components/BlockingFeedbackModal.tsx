"use client";

import React, { useState } from 'react';

interface BlockingFeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  dhcpMappingId: number;
  deviceIp?: string;
  deviceName?: string;
}

interface FeedbackData {
  user_feedback: string;
  feedback_by: string;
  problem_resolved: boolean | null;
}

const BlockingFeedbackModal: React.FC<BlockingFeedbackModalProps> = ({
  isOpen,
  onClose,
  dhcpMappingId,
  deviceIp,
  deviceName
}) => {
  const [feedbackData, setFeedbackData] = useState<FeedbackData>({
    user_feedback: '',
    feedback_by: '',
    problem_resolved: null
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!feedbackData.user_feedback.trim() || !feedbackData.feedback_by.trim()) {
      setSubmitMessage('Por favor, preencha todos os campos obrigatórios.');
      return;
    }

    setIsSubmitting(true);
    setSubmitMessage('');

    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
      
      const response = await fetch(`${base}/api/feedback/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          dhcp_mapping_id: dhcpMappingId,
          user_feedback: feedbackData.user_feedback,
          feedback_by: feedbackData.feedback_by,
          problem_resolved: feedbackData.problem_resolved
        })
      });

      if (response.ok) {
        setSubmitMessage('✅ Feedback enviado com sucesso!');
        setFeedbackData({
          user_feedback: '',
          feedback_by: '',
          problem_resolved: null
        });
        
        // Fechar modal após 2 segundos
        setTimeout(() => {
          onClose();
          setSubmitMessage('');
        }, 2000);
      } else {
        const errorData = await response.json();
        setSubmitMessage(`❌ Erro ao enviar feedback: ${errorData.detail || 'Erro desconhecido'}`);
      }
    } catch (error) {
      console.error('Erro ao enviar feedback:', error);
      setSubmitMessage('❌ Erro de conexão. Tente novamente.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFeedbackData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleResolutionChange = (resolved: boolean | null) => {
    setFeedbackData(prev => ({
      ...prev,
      problem_resolved: resolved
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-800">
            📝 Feedback sobre Bloqueio
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        <div className="mb-4 p-3 bg-blue-50 rounded-lg">
          <h3 className="font-medium text-blue-800">Dispositivo:</h3>
          <p className="text-blue-700">
            <strong>IP:</strong> {deviceIp || 'N/A'} | 
            <strong> Nome:</strong> {deviceName || 'N/A'}
          </p>
          <p className="text-sm text-blue-600 mt-1">
            <strong>ID Mapeamento:</strong> {dhcpMappingId}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="feedback_by" className="block text-sm font-medium text-gray-700 mb-1">
              Seu nome/identificação *
            </label>
            <input
              type="text"
              id="feedback_by"
              name="feedback_by"
              value={feedbackData.feedback_by}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: João Silva, joao@empresa.com"
              required
            />
          </div>

          <div>
            <label htmlFor="user_feedback" className="block text-sm font-medium text-gray-700 mb-1">
              Feedback detalhado *
            </label>
            <textarea
              id="user_feedback"
              name="user_feedback"
              value={feedbackData.user_feedback}
              onChange={handleInputChange}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Descreva o problema encontrado, como foi resolvido, sugestões, etc..."
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              O problema foi resolvido?
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="problem_resolved"
                  checked={feedbackData.problem_resolved === true}
                  onChange={() => handleResolutionChange(true)}
                  className="mr-2"
                />
                <span className="text-green-600">✅ Sim, foi resolvido</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="problem_resolved"
                  checked={feedbackData.problem_resolved === false}
                  onChange={() => handleResolutionChange(false)}
                  className="mr-2"
                />
                <span className="text-red-600">❌ Não, ainda há problemas</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="problem_resolved"
                  checked={feedbackData.problem_resolved === null}
                  onChange={() => handleResolutionChange(null)}
                  className="mr-2"
                />
                <span className="text-gray-600">❓ Não sei / Não se aplica</span>
              </label>
            </div>
          </div>

          {submitMessage && (
            <div className={`p-3 rounded-md ${
              submitMessage.includes('✅') 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {submitMessage}
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
              disabled={isSubmitting}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {isSubmitting ? 'Enviando...' : 'Enviar Feedback'}
            </button>
          </div>
        </form>

        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-700 mb-1">ℹ️ Informações:</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Seu feedback será revisado pela equipe de rede</li>
            <li>• Você pode acompanhar o status na aba "Histórico de Feedback"</li>
            <li>• Feedback ajuda a melhorar o sistema de bloqueio</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default BlockingFeedbackModal;
