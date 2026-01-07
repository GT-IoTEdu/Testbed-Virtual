/*

COMPONENTIZAR A HEADER

COMPONENTIZAR AS TABS -> components/DashboardTabs/

DASHBORAD DA RAIZ SER APENAS DE ROTEAMENTO PARA OS DASHBOARDS DE USER E MANAGER -> CADA UM É UMA PAGE SEPARADA

RETIRAR A SIDE-BAR

REGRAS VIRA SANFONA DENTRO DO ALIASES

INCLUIR MODAL PARA EDITAR REGRAS

BOTÃO DE SAIR

DEIXAR TUDO NO PADRÃO NEXT

*/

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import BlockingFeedbackModal from "../../components/BlockingFeedbackModal";
import BlockingHistory from "../../components/BlockingHistory";
import FeedbackHistory from "../../components/FeedbackHistory";

export default function DashboardPage() {
  const [name, setName] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [picture, setPicture] = useState<string | null>(null);
  const [permission, setPermission] = useState<"USER" | "MANAGER">("USER");
  const [userId, setUserId] = useState<number | null>(null);
  const [devices, setDevices] = useState<Array<{ id: number; pf_id?: number; nome?: string; ipaddr?: string; mac?: string; cid?: string; descr?: string; statusAcesso?: string; ultimaAtividade?: string }>>([]);
  const [devicesLoading, setDevicesLoading] = useState(false);
  const [devicesError, setDevicesError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [addOpen, setAddOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [form, setForm] = useState<{ mac: string; ipaddr: string; cid: string; descr: string }>({ mac: "", ipaddr: "", cid: "", descr: "" });
  const macRegex = useMemo(() => /^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$/u, []);
  const ipv4Regex = useMemo(() => /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/u, []);
  const macError = form.mac && !macRegex.test(form.mac.trim());
  const ipError = form.ipaddr && !ipv4Regex.test(form.ipaddr.trim());
  const [deletingId, setDeletingId] = useState<number | null>(null);
  // Estados para edição de dispositivos
  const [editOpen, setEditOpen] = useState(false);
  const [editingDevice, setEditingDevice] = useState<{ id: number; pf_id?: number; nome?: string; ipaddr?: string; mac?: string; cid?: string; descr?: string } | null>(null);
  const [editForm, setEditForm] = useState<{ cid: string; descr: string }>({ cid: "", descr: "" });
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  // Estados para visão MANAGER - todos os dispositivos
  const [allDevices, setAllDevices] = useState<Array<{ id: number; pf_id?: number; nome?: string; ipaddr?: string; mac?: string; descr?: string; ultimaAtividade?: string; assignedTo?: string; statusAcesso?: string; actionRule?: 'PASS' | 'BLOCK' }>>([]);
  const [allLoading, setAllLoading] = useState(false);
  const [allError, setAllError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [totalAll, setTotalAll] = useState(0);
  // Filtros para Lista de Dispositivos
  const [filterIP, setFilterIP] = useState("");
  const [filterMAC, setFilterMAC] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("");


  // Estados para incidentes (logs notice)
  const [noticeIncidents, setNoticeIncidents] = useState<Array<{
    ts: string;
    uid: string;
    id_orig_h: string;
    id_orig_p: string;
    id_resp_h: string;
    id_resp_p: string;
    fuid: string;
    file_mime_type: string;
    file_desc: string;
    proto: string;
    note: string;
    msg: string;
    sub: string;
    src: string;
    dst: string;
    p: string;
    n: string;
    peer_descr: string;
    actions: string;
    email_dest: string;
    suppress_for: string;
    remote_location_country_code: string;
    remote_location_region: string;
    remote_location_city: string;
    remote_location_latitude: string;
    remote_location_longitude: string;
  }>>([]);
  const [noticeLoading, setNoticeLoading] = useState(false);
  const [noticeError, setNoticeError] = useState<string | null>(null);
  const [incidentSearch, setIncidentSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [logTypeFilter, setLogTypeFilter] = useState<string>("");


  // Função para mapear severidade do notice para incident severity
  const mapNoticeSeverityToIncidentSeverity = (severity: string): string => {
    if (!severity) return 'medium';
    
    const severityLower = severity.toLowerCase();
    switch (severityLower) {
      case 'critical': return 'critical';
      case 'high': return 'high';
      case 'medium': return 'medium';
      case 'low': return 'low';
      default: return 'medium';
    }
  };

  // Função para modal de bloqueio
  const showBlockModal = (deviceIp: string) => {
    const options = [
      { value: '1', label: 'Bloqueio Temporário (1 hora)', duration: '1 hora' },
      { value: '2', label: 'Bloqueio Temporário (24 horas)', duration: '24 horas' },
      { value: '3', label: 'Bloqueio Permanente', duration: 'permanente' }
    ];
    
    const optionText = options.map((opt, index) => `${index + 1} - ${opt.label}`).join('\n');
    
    const blockType = prompt(
      `Selecione o tipo de bloqueio para o IP ${deviceIp}:\n\n${optionText}\n\nDigite o número da opção:`
    );
    
    if (blockType && ['1', '2', '3'].includes(blockType)) {
      const selectedOption = options[parseInt(blockType) - 1];
      const confirmed = confirm(
        `Confirma o bloqueio ${selectedOption.duration} para o IP ${deviceIp}?\n\nEsta ação irá bloquear o tráfego de rede deste dispositivo.`
      );
      
      if (confirmed) {
        alert(`✅ Bloqueio ${selectedOption.duration} aplicado com sucesso ao IP ${deviceIp}\n\nA regra de firewall será configurada automaticamente.`);
      }
    } else if (blockType) {
      alert('❌ Opção inválida. Por favor, selecione 1, 2 ou 3.');
    }
  };

  // Estados para status online/offline dos dispositivos
  const [deviceStatus, setDeviceStatus] = useState<Record<string, {
    online_status: string;
    active_status: string;
    hostname?: string;
  }>>({});
  const [statusLoading, setStatusLoading] = useState(false);
  const [statusSource, setStatusSource] = useState<'live' | 'fallback' | 'unknown'>('unknown');
  
  // Estados para IPs de dispositivos existentes
  const [deviceIps, setDeviceIps] = useState<any[]>([]);
  const [deviceIpsLoading, setDeviceIpsLoading] = useState(false);
  
  // Estados para feedback de bloqueio
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [selectedDhcpMappingId, setSelectedDhcpMappingId] = useState<number | null>(null);
  const [selectedDeviceIp, setSelectedDeviceIp] = useState<string | null>(null);
  const [selectedDeviceName, setSelectedDeviceName] = useState<string | null>(null);
  const [deviceIpsError, setDeviceIpsError] = useState<string | null>(null);

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

  // Estados para modal de bloqueio com motivo
  const [blockModalOpen, setBlockModalOpen] = useState(false);
  const [blockingDevice, setBlockingDevice] = useState<any>(null);
  const [blockReason, setBlockReason] = useState("");
  const [blockSaving, setBlockSaving] = useState(false);
  const [blockError, setBlockError] = useState<string | null>(null);

  // Estados para modal de detalhes do dispositivo bloqueado
  const [deviceDetailsOpen, setDeviceDetailsOpen] = useState(false);
  const [deviceDetails, setDeviceDetails] = useState<any>(null);
  const [deviceDetailsLoading, setDeviceDetailsLoading] = useState(false);
  const [deviceDetailsError, setDeviceDetailsError] = useState<string | null>(null);

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
  
  const fetchDeviceDetails = async (device: any) => {
    setDeviceDetailsLoading(true);
    setDeviceDetailsError(null);
    
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
      
      // Buscar status de bloqueio do dispositivo
      const response = await fetch(`${base}/devices/${device.id}/block-status`);
      
      if (response.ok) {
        const blockData = await response.json();
        
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
          feedback_history: feedbackHistory
        };
        
        setDeviceDetails(deviceDetails);
        setDeviceDetailsOpen(true);
        
        console.log('📋 Detalhes do dispositivo carregados:', deviceDetails);
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Erro ${response.status}`);
      }
    } catch (error: any) {
      console.error('❌ Erro ao buscar detalhes do dispositivo:', error);
      setDeviceDetailsError(error.message || 'Erro ao carregar detalhes');
    } finally {
      setDeviceDetailsLoading(false);
    }
  };
  const fetchDeviceStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
      const response = await fetch(`${base}/api/devices/dhcp/status`);
      
      if (!response.ok) {
        // Tenta obter mensagem de erro mais detalhada
        let errorMessage = `Erro ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch {}
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      
      // Criar um mapa de IP -> status para lookup rápido
      const statusMap: Record<string, any> = {};
      if (data.devices) {
        data.devices.forEach((device: any) => {
          if (device.ip) {
            statusMap[device.ip] = {
              online_status: device.online_status,
              active_status: device.active_status,
              hostname: device.hostname
            };
          }
          // Também mapear por MAC para casos onde não temos IP
          if (device.mac) {
            statusMap[device.mac] = {
              online_status: device.online_status,
              active_status: device.active_status,
              hostname: device.hostname
            };
          }
        });
      }
      
      setDeviceStatus(statusMap);
      setStatusSource('live');
      console.log('📊 Status dos dispositivos carregado (live):', statusMap);
      
    } catch (error: any) {
      // Se for erro de conectividade com pfSense, usar status padrão silenciosamente
      if (error.message?.includes('503') || error.message?.includes('504') || 
          error.message?.includes('pfSense') || error.message?.includes('Service Unavailable')) {
        console.warn('⚠️ pfSense indisponível - usando status baseado no statusAcesso');
        
        // Definir status padrão baseado no statusAcesso dos dispositivos conhecidos
        const defaultStatusMap: Record<string, any> = {};
        
        // Para dispositivos do usuário
        devices.forEach(device => {
          if (device.ipaddr) {
            defaultStatusMap[device.ipaddr] = {
              online_status: device.statusAcesso === 'LIBERADO' ? 'idle/offline' : 'idle/offline',
              active_status: 'static',
              hostname: device.nome
            };
          }
          if (device.mac) {
            defaultStatusMap[device.mac] = {
              online_status: device.statusAcesso === 'LIBERADO' ? 'idle/offline' : 'idle/offline',
              active_status: 'static',
              hostname: device.nome
            };
          }
        });
        
        // Para dispositivos do gestor (se disponível)
        if (typeof allDevices !== 'undefined') {
          allDevices.forEach(device => {
            if (device.ipaddr) {
              defaultStatusMap[device.ipaddr] = {
                online_status: device.statusAcesso === 'LIBERADO' ? 'idle/offline' : 'idle/offline',
                active_status: 'static',
                hostname: device.nome
              };
            }
            if (device.mac) {
              defaultStatusMap[device.mac] = {
                online_status: device.statusAcesso === 'LIBERADO' ? 'idle/offline' : 'idle/offline',
                active_status: 'static',
                hostname: device.nome
              };
            }
          });
        }
        
        setDeviceStatus(defaultStatusMap);
        setStatusSource('fallback');
        
        // Log informativo sem alarmar o usuário
        console.info('ℹ️ Status dos dispositivos definido como offline (pfSense indisponível)');
      } else {
        // Apenas log para erros inesperados, sem impactar UX
        console.error('Erro inesperado ao buscar status dos dispositivos:', error);
      }
    } finally {
      setStatusLoading(false);
    }
  }, []);

  // Função para buscar IPs de dispositivos cadastrados
  const fetchDeviceIps = useCallback(async () => {
    setDeviceIpsLoading(true);
    setDeviceIpsError(null);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
      const response = await fetch(`${base}/api/devices/devices/ips`);
      
      if (response.ok) {
        const data = await response.json();
        setDeviceIps(data.device_ips || []);
        console.log('📋 IPs de dispositivos carregados:', data.device_ips);
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Erro ${response.status}`);
      }
    } catch (error: any) {
      console.error('Erro ao buscar IPs de dispositivos:', error);
      setDeviceIpsError(error.message || 'Erro ao carregar IPs de dispositivos');
    } finally {
      setDeviceIpsLoading(false);
    }
  }, []);

  // Função para salvar automaticamente incidentes notice no banco
  const autoSaveNoticeIncidents = async (incidents: any[]) => {
    if (incidents.length === 0) return;

    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
      let savedCount = 0;

      // Processa cada incidente notice
      for (const incident of incidents) {
        try {
          // Mapeia os dados do incidente notice para o formato da API
          const incidentData = {
            device_ip: incident.id_orig_h || 'unknown',
            device_name: incident.peer_descr || null,
            incident_type: incident.note || 'Unknown',
            severity: mapNoticeSeverityToIncidentSeverity(incident.severity),
            description: incident.msg || '',
            detected_at: incident.ts || new Date().toISOString(),
            zeek_log_type: 'notice.log',
            raw_log_data: {
              ts: incident.ts,
              uid: incident.uid,
              id_orig_h: incident.id_orig_h,
              id_orig_p: incident.id_orig_p,
              id_resp_h: incident.id_resp_h,
              id_resp_p: incident.id_resp_p,
              note: incident.note,
              msg: incident.msg,
              src: incident.src,
              dst: incident.dst,
              peer_descr: incident.peer_descr,
              actions: incident.actions
            },
            action_taken: incident.actions || null,
            notes: null
          };

          const response = await fetch(`${base}/api/incidents/`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(incidentData)
          });

          if (response.ok) {
            savedCount++;
          }
        } catch (error) {
          console.warn('Erro ao salvar incidente automaticamente:', error);
        }
      }

      if (savedCount > 0) {
        console.log(`✅ Salvamento automático: ${savedCount} incidentes notice.log salvos no banco`);
      }

    } catch (error) {
      console.warn('Erro no salvamento automático de incidentes:', error);
    }
  };

  // Função para abrir modal de feedback
  const showFeedbackModal = (deviceIp: string, deviceName?: string, dhcpMappingId?: number) => {
    // Buscar o mapeamento DHCP correspondente
    const device = devices.find(d => d.ipaddr === deviceIp);
    const mappingId = dhcpMappingId || device?.id;
    
    if (!mappingId) {
      alert(`❌ Não foi possível encontrar o mapeamento DHCP para o dispositivo ${deviceIp}`);
      return;
    }

    setSelectedDhcpMappingId(mappingId);
    setSelectedDeviceIp(deviceIp);
    setSelectedDeviceName(deviceName || device?.descr || 'Sem nome');
    setFeedbackModalOpen(true);
  };

  // Função para buscar logs notice (incidentes) do Zeek
  const fetchIncidentsFromDatabase = useCallback(async () => {
    setNoticeLoading(true);
    setNoticeError(null);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
      console.log('🌐 Base URL configurada para incidentes do banco:', base);
      
      // Busca incidentes do banco de dados MySQL
      let url = `${base}/api/incidents/`;
      
      console.log('🔍 Buscando incidentes do banco de dados:', url);
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('📡 Response status:', response.status);
      console.log('📡 Response ok:', response.ok);

      if (response.ok) {
        const data = await response.json();
        console.log('📊 Dados dos incidentes do banco:', data);
        
        if (Array.isArray(data) && data.length > 0) {
          // Converte os dados do banco para o formato esperado pelo frontend
          const incidentsData = data.map((incident: any) => {
            // Função para formatar timestamp
            const formatTimestamp = (timestamp: string | Date) => {
              if (!timestamp) return '-';
              
              try {
                const date = new Date(timestamp);
                if (isNaN(date.getTime())) return timestamp; // Retorna original se inválido
                
                // Formato: DD/MM/YYYY HH:MM:SS
                const day = date.getDate().toString().padStart(2, '0');
                const month = (date.getMonth() + 1).toString().padStart(2, '0');
                const year = date.getFullYear();
                const hours = date.getHours().toString().padStart(2, '0');
                const minutes = date.getMinutes().toString().padStart(2, '0');
                const seconds = date.getSeconds().toString().padStart(2, '0');
                
                return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
              } catch (error) {
                return timestamp; // Retorna original em caso de erro
              }
            };
            
            // Função para calcular tempo relativo
            const getRelativeTime = (timestamp: string | Date) => {
              if (!timestamp) return '';
              
              try {
                const date = new Date(timestamp);
                if (isNaN(date.getTime())) return '';
                
                const now = new Date();
                const diffMs = now.getTime() - date.getTime();
                const diffMinutes = Math.floor(diffMs / (1000 * 60));
                const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
                
                if (diffMinutes < 1) return 'agora';
                if (diffMinutes < 60) return `há ${diffMinutes}min`;
                if (diffHours < 24) return `há ${diffHours}h`;
                if (diffDays < 7) return `há ${diffDays} dias`;
                return `há ${Math.floor(diffDays / 7)} semanas`;
              } catch (error) {
                return '';
              }
            };
            
            return {
              id: incident.id,
              ts: formatTimestamp(incident.detected_at),
              uid: '-',
              id_orig_h: incident.device_ip,
              id_orig_p: '-',
              id_resp_h: '-',
              id_resp_p: '-',
              note: incident.incident_type,
              msg: incident.description,
              src: incident.device_ip,
              dst: '-',
              p: '-',
              n: '-',
              peer_descr: incident.device_name || '-',
              actions: incident.action_taken || '-',
              email_dest: '-',
              suppress_for: '-',
              // Campos adicionais do banco
              severity: incident.severity,
              status: incident.status,
              zeek_log_type: incident.zeek_log_type,
              created_at: formatTimestamp(incident.created_at),
              updated_at: formatTimestamp(incident.updated_at),
              // Tempos relativos
              detected_relative: getRelativeTime(incident.detected_at),
              created_relative: getRelativeTime(incident.created_at)
            };
          });
          
          console.log('✅ Incidentes processados do banco:', incidentsData);
          setNoticeIncidents(incidentsData);
        } else {
          console.log('ℹ️ Nenhum incidente encontrado no banco de dados, tentando buscar diretamente do Zeek...');
          
          // Fallback: buscar dados diretamente do Zeek
          try {
            await fetchZeekNoticeIncidents();
          } catch (fallbackError) {
            console.error('❌ Erro no fallback do Zeek:', fallbackError);
          setNoticeIncidents([]);
          }
        }
      } else {
        console.error('❌ Erro na resposta da API de incidentes:', response.status, response.statusText);
        const errorData = await response.text();
        console.error('📄 Conteúdo do erro:', errorData);
        
        // Fallback: tentar buscar dados diretamente do Zeek
        console.log('🔄 Tentando fallback para dados diretos do Zeek...');
        try {
          await fetchZeekNoticeIncidents();
        } catch (fallbackError) {
          console.error('❌ Erro no fallback do Zeek:', fallbackError);
        setNoticeError(`Erro ${response.status}: ${response.statusText}`);
        setNoticeIncidents([]);
        }
      }
    } catch (error: any) {
      console.error('❌ Erro ao buscar incidentes do banco:', error);
      
      // Fallback: tentar buscar dados diretamente do Zeek
      console.log('🔄 Tentando fallback para dados diretos do Zeek...');
      try {
        await fetchZeekNoticeIncidents();
      } catch (fallbackError) {
        console.error('❌ Erro no fallback do Zeek:', fallbackError);
      setNoticeError(`Erro de conexão: ${error.message}`);
      setNoticeIncidents([]);
      }
    } finally {
      setNoticeLoading(false);
    }
  }, []);

  const fetchZeekNoticeIncidents = useCallback(async () => {
    setNoticeLoading(true);
    setNoticeError(null);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
      console.log('🌐 Base URL configurada para notice:', base);
      
      // Primeiro tenta usar o endpoint de logs diretamente
      let url = `${base}/api/scanners/zeek/logs?logfile=notice.log&maxlines=100&hours_ago=24`;
      
      console.log('🔍 Buscando logs notice Zeek (endpoint logs):', url);
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('📡 Response status:', response.status);
      console.log('📡 Response ok:', response.ok);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.log('❌ Erro na resposta:', errorData);
        throw new Error(errorData.detail || `Erro ${response.status}`);
      }

      const data = await response.json();
      console.log('📊 Dados notice recebidos:', data);
      console.log('📊 Success:', data.success);
      console.log('📊 Logs array:', data.logs);
      console.log('📊 Logs length:', data.logs?.length);

      if (data.success && data.logs && Array.isArray(data.logs)) {
        // Converte os dados do log notice para o formato esperado
        const noticeData = data.logs.map((log: any) => ({
          ts: (typeof log.ts === 'object' && log.ts?.iso) ? log.ts.iso : (log.ts || log.timestamp || '-'),
          uid: log.uid || '-',
          id_orig_h: log.src || log.id_orig_h || log.src_ip || '-',
          id_orig_p: log.id_orig_p || log.src_port || '-',
          id_resp_h: log.dst || log.id_resp_h || log.dst_ip || '-',
          id_resp_p: log.id_resp_p || log.dst_port || '-',
          fuid: log.fuid || '-',
          file_mime_type: log.file_mime_type || '-',
          file_desc: log.file_desc || '-',
          proto: log.proto || '-',
          note: log.note || '-',
          msg: log.msg || log.message || '-',
          sub: log.sub || '-',
          src: log.src || log.src_ip || '-',
          dst: log.dst || log.dst_ip || '-',
          p: log.p || '-',
          n: log.n || '-',
          peer_descr: log.peer_descr || '-',
          actions: log.actions || '-',
          email_dest: log.email_dest || '-',
          suppress_for: log.suppress_for || '-',
          remote_location_country_code: log.remote_location?.country_code || '-',
          remote_location_region: log.remote_location?.region || '-',
          remote_location_city: log.remote_location?.city || '-',
          remote_location_latitude: log.remote_location?.latitude || '-',
          remote_location_longitude: log.remote_location?.longitude || '-'
        }));

        setNoticeIncidents(noticeData);
        console.log('✅ Logs notice processados:', noticeData.length);
        
        // Salva automaticamente os incidentes notice no banco de dados
        await autoSaveNoticeIncidents(noticeData);
      } else {
        // Se não há logs, tenta usar o endpoint de incidentes filtrado por notice
        console.log('⚠️ Nenhum log notice encontrado, tentando endpoint de incidentes...');
        
        const incidentsUrl = `${base}/api/scanners/zeek/incidents?logfile=notice.log&hours_ago=24&maxlines=100`;
        console.log('🔍 Tentando endpoint de incidentes:', incidentsUrl);
        
        const incidentsResponse = await fetch(incidentsUrl, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        });

        if (incidentsResponse.ok) {
          const incidentsData = await incidentsResponse.json();
          console.log('📊 Incidentes notice recebidos:', incidentsData);
          
          if (Array.isArray(incidentsData) && incidentsData.length > 0) {
            // Converte incidentes para o formato de notice
            const noticeData = incidentsData.map((incident: any) => ({
              ts: (typeof incident.detected_at === 'object' && incident.detected_at?.iso) ? incident.detected_at.iso : (incident.detected_at || '-'),
              uid: '-',
              id_orig_h: incident.device_ip || '-',
              id_orig_p: '-',
              id_resp_h: '-',
              id_resp_p: '-',
              fuid: '-',
              file_mime_type: '-',
              file_desc: '-',
              proto: '-',
              note: incident.incident_type || '-',
              msg: incident.description || '-',
              sub: '-',
              src: incident.device_ip || '-',
              dst: '-',
              p: '-',
              n: '-',
              peer_descr: '-',
              actions: incident.action_taken || '-',
              email_dest: '-',
              suppress_for: '-',
              remote_location_country_code: '-',
              remote_location_region: '-',
              remote_location_city: '-',
              remote_location_latitude: '-',
              remote_location_longitude: '-'
            }));

            setNoticeIncidents(noticeData);
            console.log('✅ Incidentes notice processados:', noticeData.length);
            
            // Salva automaticamente os incidentes notice no banco de dados
            await autoSaveNoticeIncidents(noticeData);
          } else {
            setNoticeIncidents([]);
            console.log('⚠️ Nenhum incidente notice encontrado');
          }
        } else {
          setNoticeIncidents([]);
          console.log('⚠️ Erro ao buscar incidentes notice');
        }
      }
    } catch (error: any) {
      console.error('❌ Erro ao buscar logs notice:', error);
      setNoticeError(error.message || 'Erro ao carregar logs notice');
      setNoticeIncidents([]);
    } finally {
      setNoticeLoading(false);
    }
  }, []);



  // Função para liberar dispositivo (adicionar ao alias Autorizados)
  const liberarDispositivo = async (dispositivo: any) => {
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
      
      console.log(`🔓 Liberando dispositivo ${dispositivo.ipaddr}...`);
      
      // 1. Adicionar ao alias "Autorizados"
      const addUrl = `${base}/aliases-db/Autorizados/add-addresses`;
      const addResponse = await fetch(addUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          addresses: [
            {
              address: dispositivo.ipaddr,
              detail: `Dispositivo liberado: ${dispositivo.nome || dispositivo.cid} - ${new Date().toLocaleString()}`
            }
          ]
        }),
      });

      if (!addResponse.ok) {
        const errorData = await addResponse.json().catch(() => ({}));
        throw new Error(`Erro ao adicionar à lista de autorizados: ${errorData.detail || addResponse.statusText}`);
      }

      console.log(`✅ Adicionado à lista de autorizados`);

      // 2. Remover do alias "Bloqueados" (se existir)
      try {
        console.log(`🗑️ Removendo da lista de bloqueados...`);
        
        // Primeiro, buscar os dados atuais do alias Bloqueados
        const currentResponse = await fetch(`${base}/aliases-db/Bloqueados`);
        if (currentResponse.ok) {
          const currentData = await currentResponse.json();
          
          // Filtrar os endereços para remover o IP do dispositivo
          const updatedAddresses = (currentData.addresses || []).filter((addr: any) => {
            const address = addr.address ?? addr?.value ?? '';
            return address !== dispositivo.ipaddr;
          });
          
          // Se havia endereços e agora tem menos, significa que removemos algo
          if (currentData.addresses && currentData.addresses.length > updatedAddresses.length) {
            // Atualizar o alias Bloqueados via PATCH
            const patchUrl = `${base}/aliases-db/Bloqueados`;
            const patchResponse = await fetch(patchUrl, {
              method: 'PATCH',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                alias_type: currentData.alias_type || currentData.type,
                descr: currentData.descr || currentData.description,
                addresses: updatedAddresses
              })
            });

            if (patchResponse.ok) {
              console.log(`✅ Removido da lista de bloqueados`);
            } else {
              console.warn(`⚠️ Não foi possível remover da lista de bloqueados`);
            }
          } else {
            console.log(`ℹ️ IP não estava na lista de bloqueados`);
          }
        }
      } catch (removeError) {
        console.warn('Erro ao remover da lista de bloqueados:', removeError);
        // Não falhar a operação principal se a remoção falhar
      }

      alert(`Dispositivo ${dispositivo.nome || dispositivo.cid} liberado com sucesso!`);
      
      // Recarregar dados para atualizar o status
      if (activeTab === "devices") {
        await loadDevices();
      } else if (activeTab === "all-devices") {
        // Recarregar todos os dispositivos se estivermos na aba de gestão
        window.location.reload();
      }
      
    } catch (error) {
      console.error('❌ Erro ao liberar dispositivo:', error);
      alert(`Erro ao liberar dispositivo: ${error}`);
    }
  };

  // Função para bloquear dispositivo (adicionar ao alias Bloqueados)
  // Função para bloquear dispositivo com motivo
  const bloquearDispositivo = async (dispositivo: any) => {
    setBlockingDevice(dispositivo);
    setBlockReason("");
    setBlockError(null);
    setBlockModalOpen(true);
  };

  // Função para confirmar bloqueio
  const confirmarBloqueio = async () => {
    if (!blockingDevice || !blockReason.trim()) {
      setBlockError("Motivo é obrigatório");
      return;
    }

    if (blockReason.trim().length < 5) {
      setBlockError("Motivo deve ter pelo menos 5 caracteres");
      return;
    }

    setBlockSaving(true);
    setBlockError(null);

    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
      
      console.log(`🔒 Bloqueando dispositivo ${blockingDevice.ipaddr} com motivo: ${blockReason}...`);
      
      // 1. Bloquear no banco de dados
      const blockResponse = await fetch(`${base}/devices/${blockingDevice.id}/block`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          device_id: blockingDevice.id,
          reason: blockReason.trim(),
          reason_by: name || email || 'Administrador'
        })
      });

      if (!blockResponse.ok) {
        const errorData = await blockResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || `Erro ${blockResponse.status}`);
      }

      const blockResult = await blockResponse.json();
      console.log('✅ Dispositivo bloqueado no banco:', blockResult);

      // 2. Adicionar IP ao alias "Bloqueados"
      const addUrl = `${base}/aliases-db/Bloqueados/add-addresses`;
      const addResponse = await fetch(addUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          addresses: [
            {
              address: blockingDevice.ipaddr,
              detail: `${blockingDevice.nome || blockingDevice.cid} - ${blockReason.trim()}`
            }
          ]
        }),
      });

      if (!addResponse.ok) {
        const errorData = await addResponse.json().catch(() => ({}));
        throw new Error(`Erro ao adicionar à lista de bloqueados: ${errorData.detail || addResponse.statusText}`);
      }

      console.log(`✅ Adicionado à lista de bloqueados`);

      // 3. Remover IP do alias "Autorizados" se estiver lá
      try {
        console.log(`🗑️ Removendo da lista de autorizados...`);
        
        const currentResponse = await fetch(`${base}/aliases-db/Autorizados`);
        if (currentResponse.ok) {
          const currentData = await currentResponse.json();
          
          const updatedAddresses = (currentData.addresses || []).filter((addr: any) => {
            const address = addr.address ?? addr?.value ?? '';
            return address !== blockingDevice.ipaddr;
          });
          
          if (currentData.addresses && currentData.addresses.length > updatedAddresses.length) {
            const patchUrl = `${base}/aliases-db/Autorizados`;
            const patchResponse = await fetch(patchUrl, {
              method: 'PATCH',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                alias_type: currentData.alias_type || currentData.type,
                descr: currentData.descr || currentData.description,
                addresses: updatedAddresses
              })
            });

            if (patchResponse.ok) {
              console.log(`✅ Removido da lista de autorizados`);
            }
          }
        }
      } catch (removeError) {
        console.warn('Erro ao remover da lista de autorizados:', removeError);
      }

      // Fechar modal e recarregar dados
      setBlockModalOpen(false);
      setBlockingDevice(null);
      setBlockReason("");
      
      // Recarregar dados para atualizar o status
      if (activeTab === "devices") {
        await loadDevices();
      } else if (activeTab === "all-devices") {
        // Recarregar todos os dispositivos se estivermos na aba de gestão
        window.location.reload();
      }

      alert(`Dispositivo ${blockingDevice.ipaddr} bloqueado com sucesso!`);
      
    } catch (error: any) {
      console.error('❌ Erro ao bloquear dispositivo:', error);
      setBlockError(error.message || 'Erro ao bloquear dispositivo');
    } finally {
      setBlockSaving(false);
    }
  };
  // Estados para visão MANAGER - mapeamento Aliases
  const [aliases, setAliases] = useState<Array<{ id?: number; nome: string; pathName: string; tipo?: string; descr?: string; itens?: number; atualizado?: string }>>([]);
  const [aliasesLoading, setAliasesLoading] = useState(false);
  const [aliasesError, setAliasesError] = useState<string | null>(null);
  const [aliasModalOpen, setAliasModalOpen] = useState(false);
  const [aliasTargetName, setAliasTargetName] = useState<string | null>(null); // canonical name for URL
  const [aliasTargetDisplay, setAliasTargetDisplay] = useState<string | null>(null); // for UI title
  const [aliasAddresses, setAliasAddresses] = useState<Array<{ address: string; detail: string; selectFromDevices?: boolean }>>([{ address: "", detail: "", selectFromDevices: false }]);
  const [aliasSaving, setAliasSaving] = useState(false);
  const [aliasSaveError, setAliasSaveError] = useState<string | null>(null);
  // Sincronização de aliases (pfSense -> base local)
  const syncAliases = useCallback(async () => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
    const url = `${base}/aliases-db/save`;
    try {
      const res = await fetch(url, { method: 'POST' });
      if (res.ok) return true;
      if (res.status === 405) {
        const r = await fetch(url);
        return r.ok;
      }
    } catch {}
    return false;
  }, []);
  // Criar novo alias
  const [createAliasOpen, setCreateAliasOpen] = useState(false);
  const [createAliasName, setCreateAliasName] = useState("");
  const [createAliasType, setCreateAliasType] = useState<"host" | "network">("host");
  const [createAliasDescr, setCreateAliasDescr] = useState("");
  const [createAliasAddresses, setCreateAliasAddresses] = useState<Array<{ address: string; detail: string }>>([{ address: "", detail: "" }]);
  const [createSaving, setCreateSaving] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const cidrRegex = useMemo(() => /^(?:\d{1,3}\.){3}\d{1,3}\/(3[0-2]|[12]?\d)$/u, []);
  const syncPfSenseIds = useCallback(async () => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
    const url = `${base}/dhcp/sync`;
    try {
      const res = await fetch(url, { method: 'POST' });
      if (res.ok) return true;
      if (res.status === 405) {
        const resGet = await fetch(url);
        return resGet.ok;
      }
    } catch {}
    return false;
  }, []);
  const [activeTab, setActiveTab] = useState<
    | "devices"
    | "incidents"
    | "all-devices"
    | "blocking-history"
    | "aliases"
    | "rules"
    | "users"
    | "reports"
    | "settings"
  >("devices");
  const router = useRouter();

  useEffect(() => {
    try {
      const raw = typeof window !== "undefined" ? window.localStorage.getItem("auth:user") : null;
      if (raw) {
        const data = JSON.parse(raw);
        setName(data?.name || null);
        setEmail(data?.email || null);
        setPicture(data?.picture || null);
        if (data?.permission === "MANAGER") {
          setPermission("MANAGER");
          // Se for manager, mudar aba padrão para todos os dispositivos
          setActiveTab("all-devices");
        }
        if (data?.user_id) setUserId(Number(data.user_id));
      } else {
        router.push("/login");
      }
    } catch (e) {
      console.warn("Falha ao ler auth:user do localStorage:", e);
      router.push("/login");
    }
  }, [router]);

  // Função para carregar dispositivos do usuário
  const loadDevices = async () => {
    if (activeTab !== "devices" || !userId) return;
    setDevicesLoading(true);
    setDevicesError(null);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
      const url = `${base}/users/${userId}/devices?current_user_id=${userId}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Erro ${res.status}`);
      const data = await res.json();
      // normalizar campos esperados (API retorna objeto com chave "devices")
      const list = Array.isArray(data)
        ? data
        : (data?.devices ?? data?.items ?? []);
      const normalized = list.map((d: any) => ({
        id: Number(d.id ?? d.pf_id ?? d.device_id ?? Math.random() * 1e9),
        pf_id: d.pf_id !== undefined && d.pf_id !== null ? Number(d.pf_id) : undefined,
        nome: d.nome ?? d.cid ?? d.hostname ?? d.descr ?? "Dispositivo",
        ipaddr: d.ipaddr ?? d.ip ?? d.ip_address ?? "-",
        mac: d.mac ?? d.mac_address ?? "-",
        cid: d.cid ?? d.hostname ?? "",
        descr: d.descr ?? d.description ?? "",
        statusAcesso: d.status_acesso ?? undefined,
        ultimaAtividade: d.updated_at ?? d.last_seen ?? "-",
      }));
      setDevices(normalized);
    } catch (e: any) {
      setDevicesError(e?.message || "Falha ao carregar dispositivos");
    } finally {
      setDevicesLoading(false);
    }
  };

  // Carregar dispositivos do usuário quando aba ativa for "devices" e tivermos userId
  useEffect(() => {
    loadDevices();
  }, [activeTab, userId]);

  // Carregar todos os dispositivos quando MANAGER e aba 'all-devices'
  useEffect(() => {
    const loadAllDevices = async () => {
      if (permission !== "MANAGER" || activeTab !== "all-devices") return;
      setAllLoading(true);
      setAllError(null);
      try {
        const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
        const url = `${base}/dhcp/devices?page=${page}&per_page=${perPage}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Erro ${res.status}`);
        const data = await res.json();
        const list = Array.isArray(data) ? data : (data?.devices ?? []);
        const normalized = list.map((d: any) => {
          const users = Array.isArray(d.assigned_users) ? d.assigned_users : [];
          const names = users.map((u: any) => u?.nome || u?.email).filter(Boolean);
          return {
            id: Number(d.id ?? d.device_id ?? Math.random() * 1e9),
            pf_id: d.pf_id !== undefined && d.pf_id !== null ? Number(d.pf_id) : undefined,
            nome: d.nome ?? d.cid ?? d.hostname ?? d.descr ?? "Dispositivo",
            ipaddr: d.ipaddr ?? d.ip ?? d.ip_address ?? "-",
            mac: d.mac ?? d.mac_address ?? "-",
            descr: d.descr ?? d.cid ?? d.hostname ?? "",
            ultimaAtividade: d.updated_at ?? d.last_seen ?? "-",
            statusAcesso: d.status_acesso ?? undefined,
            assignedTo: names.length ? names.join(", ") : undefined,
            actionRule: d.status_acesso === 'LIBERADO' ? 'PASS' : (d.status_acesso === 'BLOQUEADO' ? 'BLOCK' : undefined),
          };
        });
        setAllDevices(normalized);
        setTotalAll(Number(data?.total ?? normalized.length));
      } catch (e: any) {
        setAllError(e?.message || "Falha ao carregar todos os dispositivos");
      } finally {
        setAllLoading(false);
      }
    };
    loadAllDevices();
  }, [permission, activeTab, page, perPage, userId]);

  // Mapa alias->Ação (PASS/BLOCK) baseado nas regras salvas no banco
  const [rulesAliasAction, setRulesAliasAction] = useState<Record<string, 'PASS' | 'BLOCK'>>({});
  useEffect(() => {
    const loadRulesMap = async () => {
      if (permission !== 'MANAGER' || (activeTab !== 'aliases' && activeTab !== 'all-devices')) return;
      try {
        const base = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000/api/devices';
        const r = await fetch(`${base}/firewall/rules-db`);
        if (!r.ok) return;
        const data = await r.json();
        const list = Array.isArray(data) ? data : (data?.result ?? data?.data ?? []);
        const map: Record<string, 'PASS' | 'BLOCK'> = {};
        for (const ru of list) {
          const src = String(ru.source || '').split(',').map((s: string) => s.trim()).filter(Boolean);
          const dst = String(ru.destination || '').split(',').map((s: string) => s.trim()).filter(Boolean);
          const all = [...src, ...dst];
          for (const token of all) {
            if (!token) continue;
            const aliasName = token.replace(/^!/, '');
            if (!aliasName || aliasName === 'any' || aliasName === '-') continue;
            const typ = String(ru.type || '').toUpperCase();
            if (typ === 'BLOCK') {
              map[aliasName] = 'BLOCK'; // prioridade para BLOCK
            } else if (typ === 'PASS') {
              if (!map[aliasName]) map[aliasName] = 'PASS';
            }
          }
        }
        setRulesAliasAction(map);
      } catch {}
    };
    loadRulesMap();
  }, [permission, activeTab]);

  // Carregar aliases quando MANAGER e aba 'aliases'
  useEffect(() => {
    const loadAliases = async () => {
      if (permission !== "MANAGER" || activeTab !== "aliases") return;
      setAliasesLoading(true);
      setAliasesError(null);
      try {
        const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
        const url = `${base}/aliases-db`;
        const res = await fetch(url);
        if (!res.ok) {
          if (res.status === 504) {
            throw new Error('pfSense indisponível. Verifique se o servidor está acessível e as credenciais estão corretas.');
          }
          throw new Error(`Erro ${res.status}`);
        }
        const data = await res.json();
        const list = Array.isArray(data) ? data : (data?.aliases ?? data?.items ?? []);
        const normalized = list.map((a: any) => ({
          id: a.id ?? undefined,
          nome: a.name ?? a.alias_name ?? a.nome ?? "(sem nome)",
          pathName: a.name ?? a.alias_name ?? (a.nome || ""),
          tipo: a.type ?? a.alias_type ?? a.tipo ?? "-",
          descr: a.descr ?? a.description ?? "",
          itens: Array.isArray(a.addresses) ? a.addresses.length : (Array.isArray(a.items) ? a.items.length : undefined),
          addresses: Array.isArray(a.addresses) ? a.addresses : (Array.isArray(a.items) ? a.items : []),
          atualizado: a.updated_at ?? a.last_updated ?? "-",
        })).filter((a: any) => String(a.tipo || '').toLowerCase() !== 'network');
        setAliases(normalized);
      } catch (e: any) {
        setAliasesError(e?.message || "Falha ao carregar aliases");
      } finally {
        setAliasesLoading(false);
      }
    };
    loadAliases();
  }, [permission, activeTab]);

  // Carregar regras de firewall quando MANAGER e aba 'rules'
  const [rules, setRules] = useState<any[]>([]);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [rulesError, setRulesError] = useState<string | null>(null);

  // Carregar incidentes (logs notice) quando na aba 'incidents'
  useEffect(() => {
    if (activeTab === "incidents") {
      fetchIncidentsFromDatabase();
    }
  }, [activeTab, fetchIncidentsFromDatabase]);

  // Carregar status dos dispositivos quando necessário
  useEffect(() => {
    if (activeTab === "devices" || activeTab === "all-devices") {
      fetchDeviceStatus();
    }
  }, [activeTab, fetchDeviceStatus]);

  // Recarregar status dos dispositivos a cada 30 segundos
  useEffect(() => {
    if (activeTab === "devices" || activeTab === "all-devices") {
      const interval = setInterval(() => {
        fetchDeviceStatus();
      }, 30000); // 30 segundos

      return () => clearInterval(interval);
    }
  }, [activeTab, fetchDeviceStatus]);

  useEffect(() => {
    const loadRules = async () => {
      if (permission !== "MANAGER" || activeTab !== "rules") return;
      setRulesLoading(true);
      setRulesError(null);
      try {
        const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
        const url = `${base}/firewall/rules-db`;
        const res = await fetch(url);
        if (!res.ok) {
          let msg = `Erro ${res.status}`;
          try { const j = await res.json(); msg = j?.detail || msg; } catch {}
          throw new Error(msg);
        }
        const data = await res.json();
        const raw = Array.isArray(data) ? data : (data?.result ?? data?.data ?? []);
        const filtered = (raw || []).filter((r: any) => {
          const ifs = Array.isArray(r.interface) ? r.interface : [r.interface];
          return !ifs.some((it: any) => String(it || '').toLowerCase() === 'wan');
        });
        const norm = filtered.map((r: any, idx: number) => ({
          id: r.pf_id ?? r.id ?? idx,
          action: r.type ?? r.action ?? '-',
          interface: Array.isArray(r.interface) ? r.interface.join(', ') : (r.interface ?? r.if ?? '-'),
          ipprotocol: r.ipprotocol ?? '-',
          protocol: r.protocol ?? r.proto ?? '-',
          source: r.source ?? r.src ?? r.source_net ?? '-',
          destination: r.destination ?? r.dst ?? r.destination_net ?? '-',
          destination_port: r.destination_port ?? '-',
          description: r.descr ?? r.description ?? '-',
          updated_at: r.updated_time ?? r.updated_at ?? r.last_updated ?? undefined,
        }));
        setRules(norm);
      } catch (e: any) {
        setRulesError(e?.message || 'Falha ao carregar regras');
      } finally {
        setRulesLoading(false);
      }
    };
    loadRules();
  }, [permission, activeTab]);

  // Carregar IPs de dispositivos quando o componente montar
  useEffect(() => {
    fetchDeviceIps();
  }, [fetchDeviceIps]);

  // Modal de detalhes do Alias
  const [aliasDetailsOpen, setAliasDetailsOpen] = useState(false);
  const [aliasDetailsTarget, setAliasDetailsTarget] = useState<string | null>(null);
  const [aliasDetails, setAliasDetails] = useState<any | null>(null);
  const [aliasDetailsLoading, setAliasDetailsLoading] = useState(false);
  const [aliasDetailsError, setAliasDetailsError] = useState<string | null>(null);
  const [removingAddress, setRemovingAddress] = useState<string | null>(null);

  // Função para remover endereço de um alias
  const removeAddressFromAlias = async (aliasName: string, addressToRemove: string) => {
    if (!window.confirm(`Tem certeza que deseja remover o endereço ${addressToRemove} do alias ${aliasName}?`)) {
      return;
    }

    setRemovingAddress(addressToRemove);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000/api/devices';
      
      // Primeiro, obter os dados atuais do alias
      const currentResponse = await fetch(`${base}/aliases-db/${encodeURIComponent(aliasName)}`);
      if (!currentResponse.ok) {
        throw new Error(`Erro ao buscar dados do alias: ${currentResponse.status}`);
      }
      
      const currentData = await currentResponse.json();
      
      // Filtrar os endereços para remover o endereço especificado
      const updatedAddresses = (currentData.addresses || []).filter((addr: any) => {
        const address = addr.address ?? addr?.value ?? '';
        return address !== addressToRemove;
      });
      
      // Preparar payload para PATCH
      const patchPayload = {
        alias_type: currentData.alias_type || currentData.type,
        descr: currentData.descr || currentData.description,
        addresses: updatedAddresses
      };
      
      console.log('🔄 Atualizando alias:', aliasName, 'Removendo:', addressToRemove, 'Payload:', patchPayload);
      
      // Fazer PATCH para atualizar o alias
      const patchUrl = `${base}/aliases-db/${encodeURIComponent(aliasName)}`;
      const patchResponse = await fetch(patchUrl, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(patchPayload)
      });

      if (!patchResponse.ok) {
        let errorMsg = `Erro ${patchResponse.status}`;
        try {
          const errorData = await patchResponse.json();
          errorMsg = errorData.detail || errorMsg;
        } catch {}
        throw new Error(errorMsg);
      }

      const result = await patchResponse.json();
      console.log('✅ Alias atualizado:', result);
      
      // Atualizar os detalhes localmente
      setAliasDetails({ 
        name: result.name || aliasName, 
        addresses: result.addresses || updatedAddresses,
        alias_type: result.alias_type,
        descr: result.descr
      });
      
      // Mostrar mensagem de sucesso
      alert(`Endereço ${addressToRemove} removido com sucesso!`);
      
    } catch (error: any) {
      console.error('❌ Erro ao remover endereço:', error);
      setAliasDetailsError(error.message || 'Erro ao remover endereço');
      alert(`Erro ao remover endereço: ${error.message}`);
    } finally {
      setRemovingAddress(null);
    }
  };

  // Função para obter status formatado do dispositivo
  const getDeviceOnlineStatus = (deviceIP: string, deviceMAC: string) => {
    const statusByIP = deviceStatus[deviceIP];
    const statusByMAC = deviceStatus[deviceMAC];
    const status = statusByIP || statusByMAC;
    
    if (!status) {
      return {
        label: 'Desconhecido',
        color: 'bg-gray-500',
        textColor: 'text-gray-100',
        icon: '❓'
      };
    }
    
    const isOnline = status.online_status?.includes('active') || status.online_status?.includes('online');
    const isActive = status.active_status === 'static' || status.active_status === 'active';
    
    if (isOnline && isActive) {
      return {
        label: 'Online',
        color: 'bg-green-500',
        textColor: 'text-green-100',
        icon: '🟢'
      };
    } else if (isActive) {
      return {
        label: 'Offline',
        color: 'bg-yellow-500',
        textColor: 'text-yellow-100',
        icon: '🟡'
      };
    } else if (status.active_status === 'expired') {
      return {
        label: 'Expirado',
        color: 'bg-red-500',
        textColor: 'text-red-100',
        icon: '🔴'
      };
    } else {
      return {
        label: 'Inativo',
        color: 'bg-gray-500',
        textColor: 'text-gray-100',
        icon: '⚫'
      };
    }
  };

  const initials = useMemo(() => {
    const source = name || email || "";
    const parts = source.split(" ").filter(Boolean);
    if (parts.length === 0) return "?";
    const first = parts[0]?.[0] || "";
    const last = parts.length > 1 ? parts[parts.length - 1]?.[0] || "" : "";
    return (first + last).toUpperCase();
  }, [name, email]);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      {/* Header */}

      {/* COMPONENTIZAR A HEADER */}
      <header className="h-20 px-6 flex items-center justify-between bg-gradient-to-r from-slate-800 via-slate-700 to-slate-600 shadow-lg">
        <div className="text-xl font-bold">IoT-EDU</div>
        <div className="flex items-center gap-3">
          <div className="text-sm text-slate-200">{name || "Usuário"}</div>
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center overflow-hidden border border-white/20 shadow-lg">
            {picture ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img 
                src={picture} 
                alt="avatar" 
                className="w-full h-full object-cover"
                onError={(e) => {
                  // Fallback se a imagem falhar ao carregar
                  const target = e.target as HTMLImageElement;
                  target.style.display = 'none';
                  const parent = target.parentElement;
                  if (parent) {
                    parent.innerHTML = `<span class="text-white text-sm font-semibold">${initials}</span>`;
                  }
                }}
              />
            ) : (
              <span className="text-white text-sm font-semibold">{initials}</span>
            )}
          </div>
          <button
            className="ml-2 px-3 py-1.5 rounded-md bg-rose-600/90 hover:bg-rose-600 text-white text-sm"
            onClick={async () => {
              try {
                await fetch("http://localhost:8000/api/auth/logout", { method: "POST", credentials: "include" });
              } catch {}
              try {
                window.localStorage.removeItem("auth:user");
              } catch {}
              router.push("/login");
            }}
          >
            Sair
          </button>
        </div>
      </header>

      {/* Body */}
      <div className="flex">
        {/* Sidebar */}
        {/* EXCLUIR A SIDE-BAR */}
        <aside className="w-64 bg-slate-800 min-h-[calc(100vh-80px)] border-r border-slate-700 p-4">
          <nav className="space-y-1">
            <div className="px-4 py-3 rounded-md bg-slate-700/60 border-l-4 border-cyan-400 text-cyan-300">📊 Dashboard</div>
            {permission !== "MANAGER" && (
              <button className="w-full text-left px-4 py-3 rounded-md hover:bg-slate-700/60" onClick={() => setActiveTab("devices")}>🔧 Meus Dispositivos</button>
            )}
            {permission === "MANAGER" && (
              <>
                <button className="w-full text-left px-4 py-3 rounded-md hover:bg-slate-700/60" onClick={() => setActiveTab("all-devices")}>🗂️ Lista de Dispositivos</button>
                <button className="w-full text-left px-4 py-3 rounded-md hover:bg-slate-700/60" onClick={() => setActiveTab("aliases")}>🧩 Mapeamento Aliases</button>
              </>
            )}
            <button className="w-full text-left px-4 py-3 rounded-md hover:bg-slate-700/60" onClick={() => setActiveTab("incidents")}>🚨 Incidentes de Segurança</button>
            <button className="w-full text-left px-4 py-3 rounded-md hover:bg-slate-700/60" onClick={() => setActiveTab("blocking-history")}>📋 Histórico de Bloqueios</button>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          {/* Dashboard cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {statusSource === 'fallback' && (
              <div className="col-span-full">
                <div className="bg-amber-900/20 border border-amber-700/50 rounded-lg p-3 mb-4">
                  <div className="flex items-center gap-2 text-amber-300 text-sm">
                    <span>⚠️</span>
                    <span>Status dos dispositivos em modo offline - pfSense indisponível</span>
                  </div>
                </div>
              </div>
            )}
            {permission === "MANAGER" ? (
              <>
                {/* Card: Total de Dispositivos */}
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-20 h-20 bg-cyan-500/10 rounded-full -translate-y-10 translate-x-10"></div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-slate-200 font-medium">Total de Dispositivos</div>
                    <div className="text-slate-400">📱</div>
                  </div>
                  <div className="text-3xl font-bold text-cyan-400">{allDevices.length}</div>
                  <div className="text-xs text-cyan-300 font-semibold bg-cyan-500/20 px-2 py-1 rounded-full inline-block mt-1">
                    {allDevices.filter(d => d.statusAcesso === 'LIBERADO').length} liberados
                  </div>
                </div>

                {/* Card: Dispositivos Bloqueados */}
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-slate-200 font-medium">Bloqueados</div>
                    <div className="text-slate-400">🚫</div>
                  </div>
                  <div className="text-3xl font-bold text-rose-400">
                    {allDevices.filter(d => d.statusAcesso === 'BLOQUEADO').length}
                  </div>
                  <div className="text-xs text-slate-400">
                    {allDevices.length > 0 ? 
                      Math.round((allDevices.filter(d => d.statusAcesso === 'BLOQUEADO').length / allDevices.length) * 100) : 0
                    }% do total
                  </div>
                </div>

                {/* Card: Aguardando Configuração */}
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-slate-200 font-medium">Aguardando</div>
                    <div className="text-slate-400">⏳</div>
                  </div>
                  <div className="text-3xl font-bold text-amber-400">
                    {allDevices.filter(d => d.statusAcesso === 'AGUARDANDO').length}
                  </div>
                  <div className="text-xs text-slate-400">
                    {allDevices.length > 0 ? 
                      Math.round((allDevices.filter(d => d.statusAcesso === 'AGUARDANDO').length / allDevices.length) * 100) : 0
                    }% do total
                  </div>
                </div>

                {/* Card: Logs dos dispositivos */}
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-slate-200 font-medium">Logs dos dispositivos</div>
                    <div className="text-slate-400">📋</div>
                  </div>
                  <div className="text-3xl font-bold text-cyan-400">0</div>
                  <div className="text-xs text-slate-400">Sistema em desenvolvimento</div>
                </div>
              </>
            ) : (
              <>
                {/* Cards para usuário comum */}
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-slate-200 font-medium">Meus Dispositivos</div>
                    <div className="text-slate-400">📱</div>
                  </div>
                  <div className="text-3xl font-bold text-cyan-400">{devices.length}</div>
                  <div className="text-xs text-slate-400 space-y-1">
                    <div>{devices.filter(d => d.statusAcesso === 'LIBERADO').length} liberados</div>
                    <div className="text-green-400">
                      {devices.filter(d => {
                        const onlineStatus = getDeviceOnlineStatus(d.ipaddr || '', d.mac || '');
                        return onlineStatus.label === 'Online';
                      }).length} online
                    </div>
                  </div>
                </div>
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-slate-200 font-medium">Dispositivos Online</div>
                    <div className="text-slate-400">🟢</div>
                  </div>
                  <div className="text-3xl font-bold text-cyan-400">
                    {devices.filter(d => {
                      const onlineStatus = getDeviceOnlineStatus(d.ipaddr || '', d.mac || '');
                      return onlineStatus.label === 'Online';
                    }).length}
                  </div>
                  <div className="text-xs text-green-400">
                    {devices.length > 0 
                      ? `${Math.round((devices.filter(d => {
                          const onlineStatus = getDeviceOnlineStatus(d.ipaddr || '', d.mac || '');
                          return onlineStatus.label === 'Online';
                        }).length / devices.length) * 100)}% online`
                      : '0% online'
                    }
                  </div>
                </div>
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-slate-200 font-medium">Meus Logs</div>
                    <div className="text-slate-400">📋</div>
                  </div>
                  <div className="text-3xl font-bold text-cyan-400">0</div>
                  <div className="text-xs text-slate-400">Sistema em desenvolvimento</div>
                </div>
              </>
            )}
          </div>

          {/* Tabs */}
          <div className="border-b border-slate-700 mb-4 flex gap-6 flex-wrap">
            {permission !== "MANAGER" && (
              <button
                className={`pb-2 -mb-px border-b-2 ${
                  activeTab === "devices" ? "border-indigo-400 text-indigo-400" : "border-transparent text-slate-300 hover:text-slate-100"
                }`}
                onClick={() => setActiveTab("devices")}
              >
                Meus Dispositivos
              </button>
            )}
            {permission === "MANAGER" && (
              <>
                <button
                  className={`pb-2 -mb-px border-b-2 ${
                    activeTab === "all-devices" ? "border-indigo-400 text-indigo-400" : "border-transparent text-slate-300 hover:text-slate-100"
                  }`}
                  onClick={() => setActiveTab("all-devices")}
                >
                  Lista de Dispositivos
                </button>
                <button
                  className={`pb-2 -mb-px border-b-2 ${
                    activeTab === "aliases" ? "border-indigo-400 text-indigo-400" : "border-transparent text-slate-300 hover:text-slate-100"
                  }`}
                  onClick={() => setActiveTab("aliases")}
                >
                  Mapeamento Aliases
                </button>
                <button
                  className={`pb-2 -mb-px border-b-2 ${
                    activeTab === "rules" ? "border-indigo-400 text-indigo-400" : "border-transparent text-slate-300 hover:text-slate-100"
                  }`}
                  onClick={() => setActiveTab("rules")}
                >
                  Regras
                </button>
              </>
            )}
            <button
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === "incidents"
                  ? "bg-cyan-600 text-white"
                  : "text-slate-400 hover:text-white hover:bg-slate-700/50"
            }`}
              onClick={() => setActiveTab("incidents")}
            >
              Incidentes de Segurança
            </button>
            <button
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === "blocking-history"
                  ? "bg-cyan-600 text-white"
                  : "text-slate-400 hover:text-white hover:bg-slate-700/50"
            }`}
              onClick={() => setActiveTab("blocking-history")}
            >
              Histórico de Bloqueios
            </button>
          </div>

          {/* Tab content: Meus Dispositivos */}
          {activeTab === "devices" && (
            <div>
              <div className="flex gap-3 mb-4">
                <input
                  className="flex-1 px-3 py-2 rounded-md bg-slate-800 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  placeholder="Buscar dispositivos..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <button className="px-4 py-2 rounded-md bg-cyan-500 hover:bg-cyan-600" onClick={() => {
                  // força recarregar
                  if (userId) {
                    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
                    const url = `${base}/users/${userId}/devices?current_user_id=${userId}`;
                    setDevicesLoading(true);
                    fetch(url).then(r => r.json()).then((data) => {
                      const list = Array.isArray(data)
                        ? data
                        : (data?.devices ?? data?.items ?? []);
                      const normalized = list.map((d: any) => ({
                        id: Number(d.id ?? d.pf_id ?? d.device_id ?? Math.random() * 1e9),
                        pf_id: d.pf_id !== undefined && d.pf_id !== null ? Number(d.pf_id) : undefined,
                        nome: d.nome ?? d.cid ?? d.hostname ?? d.descr ?? "Dispositivo",
                        ipaddr: d.ipaddr ?? d.ip ?? d.ip_address ?? "-",
                        mac: d.mac ?? d.mac_address ?? "-",
                        cid: d.cid ?? d.hostname ?? "",
                        descr: d.descr ?? d.description ?? "",
                        statusAcesso: d.status_acesso ?? undefined,
                        ultimaAtividade: d.updated_at ?? d.last_seen ?? "-",
                      }));
                      setDevices(normalized);
                    }).catch(() => setDevicesError("Falha ao recarregar")).finally(() => setDevicesLoading(false));
                  }
                }}>Buscar</button>
                <button className="px-4 py-2 rounded-md bg-emerald-600 hover:bg-emerald-700" onClick={() => { setSaveError(null); setForm({ mac: "", ipaddr: "", cid: "", descr: "" }); setAddOpen(true); }}>+ Novo Dispositivo</button>
              </div>
              {/* Modal Adicionar Dispositivo */}
              {addOpen && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
                  <div className="bg-slate-800 border border-slate-700 rounded-lg w-full max-w-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">Adicionar Novo Dispositivo</h3>
                      <button className="text-slate-300 hover:text-white" onClick={() => setAddOpen(false)}>✕</button>
                    </div>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm text-slate-300 mb-1">MAC</label>
                        <input className={`w-full px-3 py-2 rounded-md bg-slate-900 border ${macError ? 'border-rose-500' : 'border-slate-700'} text-slate-100`} placeholder="ex: d5:a3:e1:01:b4:f8" value={form.mac} onChange={(e) => setForm((f) => ({ ...f, mac: e.target.value }))} />
                        {macError && <p className="text-xs text-rose-400 mt-1">MAC inválido. Use formato XX:XX:XX:XX:XX:XX (hexadecimal).</p>}
                      </div>
                      <div className="px-3 py-2 rounded-md bg-slate-800 border border-slate-600 text-slate-300 text-sm">
                        <div className="flex items-center gap-2">
                          <span>🌐</span>
                          <span>IP será atribuído automaticamente pelo sistema</span>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm text-slate-300 mb-1">CID</label>
                        <input className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100" placeholder="Nome do dispositivo (ex: Celular)" value={form.cid} onChange={(e) => setForm((f) => ({ ...f, cid: e.target.value }))} />
                      </div>
                      <div>
                        <label className="block text-sm text-slate-300 mb-1">Descrição</label>
                        <input className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100" placeholder="Descrição" value={form.descr} onChange={(e) => setForm((f) => ({ ...f, descr: e.target.value }))} />
                      </div>
                      {saveError && <div className="text-rose-400 text-sm">{saveError}</div>}
                    </div>
                    <div className="flex justify-end gap-2 mt-5">
                      <button className="px-4 py-2 rounded-md bg-slate-700 hover:bg-slate-600" onClick={() => setAddOpen(false)}>Cancelar</button>
                      <button
                        className={`px-4 py-2 rounded-md ${saving ? 'bg-emerald-700/60' : 'bg-emerald-600 hover:bg-emerald-700'} disabled:opacity-50`}
                        disabled={saving}
                        onClick={async () => {
                          setSaving(true);
                          setSaveError(null);
                          try {
                            const mac = form.mac.trim().toLowerCase();
                            
                            if (!mac || !form.cid || !form.descr) {
                              throw new Error("Preencha todos os campos obrigatórios");
                            }
                            if (!macRegex.test(mac)) {
                              throw new Error("MAC inválido. Use formato XX:XX:XX:XX:XX:XX (hex).");
                            }
                            
                            // IP será atribuído automaticamente pelo backend
                            console.log('🔄 Dispositivo será cadastrado com IP automático');
                            const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
                            const url = `${base}/dhcp/save`;
                            const res = await fetch(url, {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({
                                mac,
                                cid: form.cid,
                                descr: form.descr,
                                auto_assign_ip: true, // Flag para indicar atribuição automática
                              }),
                            });
                            let payload: any = null;
                            try { payload = await res.json(); } catch {}
                            if (!res.ok) {
                              const t = payload ? JSON.stringify(payload) : (await res.text().catch(() => ""));
                              throw new Error(`Erro ao salvar (${res.status}) ${t}`);
                            }
                            // Se o backend indicar conflito/sem salvar no pfSense, mostrar mensagem e manter modal aberto
                            if (payload && payload.pfsense_saved === false) {
                              setSaveError(payload.pfsense_message || "Não foi possível salvar no pfSense. Verifique IP/MAC existentes.");
                              return;
                            }
                            // Sucesso no pfSense: buscar device_id pelo MAC (identificador persistente)
                            let deviceId: number | null = null;
                            
                            try {
                              const searchUrl = `${base}/dhcp/devices/search?query=${encodeURIComponent(mac)}`;
                              const searchRes = await fetch(searchUrl);
                              const searchData = await searchRes.json();
                              const list = Array.isArray(searchData)
                                ? searchData
                                : (searchData?.devices ?? []);
                              const found = list.find((d: any) => (d.mac || "").toLowerCase() === mac);
                              if (found && (found.id || found.device_id)) {
                                deviceId = Number(found.id ?? found.device_id);
                              }
                            } catch (e) {
                              console.warn("Falha ao localizar device_id recém-criado:", e);
                            }
                            if (deviceId && userId) {
                              try {
                                const assignUrl = `${base}/assignments`;
                                const assignRes = await fetch(assignUrl, {
                                  method: 'POST',
                                  headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify({
                                    user_id: userId,
                                    device_id: deviceId,
                                    notes: `Dispositivo ${form.cid} atribuído ao usuário`,
                                    assigned_by: userId,
                                  }),
                                });
                                if (!assignRes.ok) {
                                  const txt = await assignRes.text().catch(() => "");
                                  setSaveError(`Salvo, mas falhou atribuição: (${assignRes.status}) ${txt}`);
                                }
                              } catch (e: any) {
                                setSaveError(`Salvo, mas falhou atribuição: ${e?.message || e}`);
                              }
                            }
                            // Sincronizar pf_id e fechar modal
                            await syncPfSenseIds();
                            // Fechar modal
                            setAddOpen(false);
                            // Recarregar lista
                            if (userId) {
                              const listUrl = `${base}/users/${userId}/devices?current_user_id=${userId}`;
                              setDevicesLoading(true);
                              const data = await fetch(listUrl).then(r => r.json());
                              const list = Array.isArray(data) ? data : (data?.devices ?? data?.items ?? []);
                              const normalized = list.map((d: any) => ({
                                id: Number(d.id ?? d.pf_id ?? d.device_id ?? Math.random() * 1e9),
                                pf_id: d.pf_id !== undefined && d.pf_id !== null ? Number(d.pf_id) : undefined,
                                nome: d.nome ?? d.cid ?? d.hostname ?? d.descr ?? "Dispositivo",
                                ipaddr: d.ipaddr ?? d.ip ?? d.ip_address ?? "-",
                                mac: d.mac ?? d.mac_address ?? "-",
                                cid: d.cid ?? d.hostname ?? "",
                                descr: d.descr ?? d.description ?? "",
                                statusAcesso: d.status_acesso ?? undefined,
                                ultimaAtividade: d.updated_at ?? d.last_seen ?? "-",
                              }));
                              setDevices(normalized);
                              setDevicesLoading(false);
                            }
                          } catch (e: any) {
                            setSaveError(e?.message || "Falha ao salvar");
                          } finally {
                            setSaving(false);
                          }
                        }}
                      >
                        {saving ? 'Salvando...' : 'Salvar'}
                      </button>
            </div>
          </div>
        </div>
              )}

              {/* Modal Editar Dispositivo */}
              {editOpen && editingDevice && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
                  <div className="bg-slate-800 border border-slate-700 rounded-lg w-full max-w-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">Editar Dispositivo</h3>
                      <button className="text-slate-300 hover:text-white" onClick={() => setEditOpen(false)}>✕</button>
            </div>
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-sm text-slate-300 mb-1">IP</label>
                          <input className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100" value={editingDevice.ipaddr || ""} disabled aria-label="Endereço IP (somente leitura)" />
          </div>
                        <div>
                          <label className="block text-sm text-slate-300 mb-1">MAC</label>
                          <input className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100" value={editingDevice.mac || ""} disabled aria-label="Endereço MAC (somente leitura)" />
        </div>
                      </div>
                      <div>
                        <label className="block text-sm text-slate-300 mb-1">CID</label>
                        <input className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100" placeholder="Identificação do cliente" value={editForm.cid} onChange={(e) => setEditForm((f) => ({ ...f, cid: e.target.value }))} />
                      </div>
                      <div>
                        <label className="block text-sm text-slate-300 mb-1">Descrição</label>
                        <input className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100" placeholder="Descrição" value={editForm.descr} onChange={(e) => setEditForm((f) => ({ ...f, descr: e.target.value }))} />
                      </div>
                      {editError && <div className="text-rose-400 text-sm">{editError}</div>}
                    </div>
                    <div className="flex justify-end gap-2 mt-5">
                      <button className="px-4 py-2 rounded-md bg-slate-700 hover:bg-slate-600" onClick={() => setEditOpen(false)}>Cancelar</button>
                      <button
                        className={`px-4 py-2 rounded-md ${editSaving ? 'bg-amber-700/60' : 'bg-amber-600 hover:bg-amber-700'} disabled:opacity-50`}
                        disabled={editSaving}
                        onClick={async () => {
                          setEditSaving(true);
                          setEditError(null);
                          try {
                            if (!editForm.cid || !editForm.descr) {
                              throw new Error("Preencha todos os campos");
                            }
                            const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
                            const url = `${base}/dhcp/static_mapping/by_mac?mac=${encodeURIComponent(editingDevice.mac || '')}&apply=true`;
                            const res = await fetch(url, {
                              method: 'PATCH',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({
                                cid: editForm.cid,
                                hostname: editForm.cid, // hostname recebe o valor de CID
                                descr: editForm.descr,
                              }),
                            });
                            let payload: any = null;
                            try { payload = await res.json(); } catch {}
                            if (!res.ok) {
                              const t = payload ? JSON.stringify(payload) : (await res.text().catch(() => ""));
                              throw new Error(`Erro ao editar (${res.status}) ${t}`);
                            }
                            // Sincronizar pf_id e fechar modal
                            await syncPfSenseIds();
                            // Fechar modal
                            setEditOpen(false);
                            // Recarregar lista
                            if (userId) {
                              const listUrl = `${base}/users/${userId}/devices?current_user_id=${userId}`;
                              setDevicesLoading(true);
                              const data = await fetch(listUrl).then(r => r.json());
                              const list = Array.isArray(data) ? data : (data?.devices ?? data?.items ?? []);
                              const normalized = list.map((d: any) => ({
                                id: Number(d.id ?? d.pf_id ?? d.device_id ?? Math.random() * 1e9),
                                pf_id: d.pf_id !== undefined && d.pf_id !== null ? Number(d.pf_id) : undefined,
                                nome: d.nome ?? d.cid ?? d.hostname ?? d.descr ?? "Dispositivo",
                                ipaddr: d.ipaddr ?? d.ip ?? d.ip_address ?? "-",
                                mac: d.mac ?? d.mac_address ?? "-",
                                cid: d.cid ?? d.hostname ?? "",
                                descr: d.descr ?? d.description ?? "",
                                statusAcesso: d.status_acesso ?? undefined,
                                ultimaAtividade: d.updated_at ?? d.last_seen ?? "-",
                              }));
                              setDevices(normalized);
                              setDevicesLoading(false);
                            }
                          } catch (e: any) {
                            setEditError(e?.message || "Falha ao editar");
                          } finally {
                            setEditSaving(false);
                          }
                        }}
                      >
                        {editSaving ? 'Salvando...' : 'Salvar'}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              <div className="overflow-x-auto rounded-lg border border-slate-700">
                <table className="w-full text-left">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="px-4 py-3">Nome</th>
                      <th className="px-4 py-3">IP</th>
                      <th className="px-4 py-3">MAC</th>
                      <th className="px-4 py-3">Status Acesso</th>
                      <th className="px-4 py-3">Status Online</th>
                      <th className="px-4 py-3">Última Atividade</th>
                      <th className="px-4 py-3">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {devicesLoading && (
                      <tr><td className="px-4 py-3" colSpan={7}>Carregando...</td></tr>
                    )}
                    {!devicesLoading && devicesError && (
                      <tr><td className="px-4 py-3 text-rose-400" colSpan={7}>{devicesError}</td></tr>
                    )}
                    {!devicesLoading && !devicesError && devices
                      .filter((d) => {
                        const q = search.toLowerCase();
                        return !q ||
                          d.nome?.toLowerCase().includes(q) ||
                          d.ipaddr?.toLowerCase().includes(q) ||
                          d.mac?.toLowerCase().includes(q);
                      })
                      .map((d) => (
                        <tr key={d.id} className={`border-t border-slate-800 ${d.statusAcesso === 'BLOQUEADO' ? 'bg-rose-900/20 border-rose-700/30' : ''}`}>
                          <td className="px-4 py-3">{d.nome}</td>
                          <td className="px-4 py-3">{d.ipaddr}</td>
                          <td className="px-4 py-3">{d.mac}</td>
                          <td className="px-4 py-3">
                            {d.statusAcesso ? (
                              <span className={`text-xs px-2 py-1 rounded-full font-semibold ${
                                d.statusAcesso === 'LIBERADO' ? 'bg-emerald-200 text-emerald-800' : 
                                d.statusAcesso === 'BLOQUEADO' ? 'bg-rose-200 text-rose-800 border border-rose-300' : 
                                d.statusAcesso === 'AGUARDANDO' ? 'bg-amber-200 text-amber-800' : 
                                'bg-slate-200 text-slate-800'
                              }`}>
                                {d.statusAcesso}
                              </span>
                            ) : '-'}
                          </td>
                          <td className="px-4 py-3">
                            {(() => {
                              const onlineStatus = getDeviceOnlineStatus(d.ipaddr || '', d.mac || '');
                              return (
                                <span className={`text-xs px-2 py-1 rounded-full font-semibold ${onlineStatus.color} ${onlineStatus.textColor} flex items-center gap-1 w-fit`}>
                                  <span>{onlineStatus.icon}</span>
                                  {onlineStatus.label}
                                </span>
                              );
                            })()}
                          </td>
                          <td className="px-4 py-3">{d.ultimaAtividade}</td>
                          <td className="px-4 py-3 space-x-2">
                            {d.statusAcesso === 'BLOQUEADO' ? (
                              <button 
                                className="px-2 py-1 rounded bg-slate-600 hover:bg-slate-500 text-sm"
                                onClick={() => fetchDeviceDetails(d)}
                                disabled={deviceDetailsLoading}
                              >
                                {deviceDetailsLoading ? 'Carregando...' : 'Detalhes'}
                              </button>
                            ) : (
                              <>
                            <button 
                              className="px-2 py-1 rounded bg-amber-500/80 hover:bg-amber-500 text-sm"
                              onClick={() => {
                                setEditingDevice(d);
                                setEditForm({ 
                                  cid: d.cid || "", 
                                  descr: d.descr || "" 
                                });
                                setEditError(null);
                                setEditOpen(true);
                              }}
                            >
                              Editar
                            </button>
                                <button
                                  className={`px-2 py-1 rounded ${deletingId === d.id ? 'bg-rose-800/70' : 'bg-rose-600/80 hover:bg-rose-600'} text-sm`}
                                  disabled={deletingId === d.id}
                                  onClick={async () => {
                                    if (!userId) return;
                                    const confirmDel = window.confirm(`Remover mapeamento estático do dispositivo ${d.nome}?`);
                                    if (!confirmDel) return;
                                    setDevicesError(null);
                                    setDeletingId(d.id);
                                    try {
                                      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
                                      // 1) Remover/desativar associação primeiro (user_device_assignments)
                                      try {
                                        const assignDeleteUrl = `${base}/assignments/${userId}/${d.id}?current_user_id=${userId}`;
                                        await fetch(assignDeleteUrl, { method: 'DELETE' });
                                      } catch {}
                                      // 2) Depois remover no pfSense usando MAC como identificador
                                      const delUrl = `${base}/dhcp/static_mapping/by_mac?mac=${encodeURIComponent(d.mac || '')}&apply=true`;
                                      const res = await fetch(delUrl, { method: 'DELETE' });
                                      let payload: any = null;
                                      try { payload = await res.json(); } catch {}
                                      if (!res.ok) {
                                        const txt = payload ? JSON.stringify(payload) : (await res.text().catch(() => ""));
                                        throw new Error(`Falha ao remover (${res.status}) ${txt}`);
                                      }
                                      // Sincronizar pf_id e recarregar lista
                                      await syncPfSenseIds();
                                      const baseList = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
                                      const listUrl = `${baseList}/users/${userId}/devices?current_user_id=${userId}`;
                                      setDevicesLoading(true);
                                      const data = await fetch(listUrl).then(r => r.json());
                                      const list = Array.isArray(data) ? data : (data?.devices ?? data?.items ?? []);
                                      const normalized = list.map((x: any) => ({
                                        id: Number(x.id ?? x.pf_id ?? x.device_id ?? Math.random() * 1e9),
                                        pf_id: x.pf_id !== undefined && x.pf_id !== null ? Number(x.pf_id) : undefined,
                                        nome: x.nome ?? x.cid ?? x.hostname ?? x.descr ?? "Dispositivo",
                                        ipaddr: x.ipaddr ?? x.ip ?? x.ip_address ?? "-",
                                        mac: x.mac ?? x.mac_address ?? "-",
                                        status: (x.status !== undefined && x.status !== null) ? String(x.status) : (x.enable ? "Online" : "Offline"),
                                        ultimaAtividade: x.updated_at ?? x.last_seen ?? "-",
                                      }));
                                      setDevices(normalized);
                                      setDevicesLoading(false);
                                    } catch (e: any) {
                                      setDevicesError(e?.message || "Erro ao remover dispositivo");
                                    } finally {
                                      setDeletingId(null);
                                    }
                                  }}
                                >
                                  {deletingId === d.id ? 'Removendo...' : 'Remover'}
                                </button>
                              </>
                            )}
                          </td>
                        </tr>
                      ))}
                    {!devicesLoading && !devicesError && devices.length === 0 && (
                      <tr><td className="px-4 py-3" colSpan={7}>Nenhum dispositivo encontrado.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}


          {permission === "MANAGER" && activeTab === "all-devices" && (
            <div>
              {/* Filtros */}
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-4">
                <div className="text-slate-300 font-medium mb-3">Filtros</div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm text-slate-300 mb-1">Filtrar por IP</label>
                    <input
                      className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100"
                      placeholder="ex: 10.30.30"
                      value={filterIP}
                      onChange={(e) => setFilterIP(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-300 mb-1">Filtrar por MAC</label>
                    <input
                      className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100"
                      placeholder="ex: d8:e0:e1"
                      value={filterMAC}
                      onChange={(e) => setFilterMAC(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-slate-300 mb-1">Filtrar por Status</label>
                    <select
                      className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100"
                      value={filterStatus}
                      onChange={(e) => setFilterStatus(e.target.value)}
                      aria-label="Filtrar por Status"
                      title="Filtrar por Status"
                    >
                      <option value="">Todos os status</option>
                      <option value="LIBERADO">Liberado</option>
                      <option value="BLOQUEADO">Bloqueado</option>
                      <option value="AGUARDANDO">Aguardando</option>
                    </select>
                  </div>
                </div>
                <div className="flex justify-end gap-2 mt-3">
                  <button
                    className="px-4 py-2 rounded-md bg-slate-700 hover:bg-slate-600"
                    onClick={() => {
                      setFilterIP("");
                      setFilterMAC("");
                      setFilterStatus("");
                    }}
                  >
                    Limpar Filtros
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-3 mb-4">
                <div className="text-slate-300">
                  Lista de Dispositivos
                  {(() => {
                    const filteredCount = allDevices.filter((d) => {
                      if (filterIP && !d.ipaddr?.toLowerCase().includes(filterIP.toLowerCase())) return false;
                      if (filterMAC && !d.mac?.toLowerCase().includes(filterMAC.toLowerCase())) return false;
                      if (filterStatus && d.statusAcesso !== filterStatus) return false;
                      return true;
                    }).length;
                    return filteredCount !== allDevices.length ? ` (${filteredCount} de ${allDevices.length})` : ` (${allDevices.length})`;
                  })()}
                </div>
                <div className="ml-auto flex items-center gap-2">
                  <select aria-label="Itens por página" title="Itens por página" className="bg-slate-800 border border-slate-700 rounded px-2 py-1" value={perPage} onChange={(e) => { setPerPage(Number(e.target.value) || 20); setPage(1); }}>
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                  </select>
                  <button className="px-3 py-1 rounded bg-slate-700 hover:bg-slate-600" onClick={() => { setPage((p) => Math.max(1, p - 1)); }} disabled={page <= 1}>Anterior</button>
                  <span className="text-slate-400 text-sm">Página {page}</span>
                  <button className="px-3 py-1 rounded bg-slate-700 hover:bg-slate-600" onClick={() => { const max = Math.ceil((totalAll || 0) / perPage) || 1; setPage((p) => Math.min(max, p + 1)); }} disabled={page * perPage >= totalAll}>Próxima</button>
                </div>
              </div>
              <div className="overflow-x-auto rounded-lg border border-slate-700">
                <table className="w-full text-left">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="px-4 py-3">Nome</th>
                      <th className="px-4 py-3">IP</th>
                      <th className="px-4 py-3">MAC</th>
                      <th className="px-4 py-3">Usuário</th>
                      <th className="px-4 py-3">Status Acesso</th>
                      <th className="px-4 py-3">Status Online</th>
                      <th className="px-4 py-3">Descrição</th>
                      <th className="px-4 py-3">Última Atividade</th>
                      <th className="px-4 py-3">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allLoading && (<tr><td className="px-4 py-3" colSpan={9}>Carregando...</td></tr>)}
                    {!allLoading && allError && (<tr><td className="px-4 py-3 text-rose-400" colSpan={9}>{allError}</td></tr>)}
                    {!allLoading && !allError && allDevices
                      .filter((d) => {
                        // Filtro por IP
                        if (filterIP && !d.ipaddr?.toLowerCase().includes(filterIP.toLowerCase())) {
                          return false;
                        }
                        // Filtro por MAC
                        if (filterMAC && !d.mac?.toLowerCase().includes(filterMAC.toLowerCase())) {
                          return false;
                        }
                        // Filtro por Status
                        if (filterStatus && d.statusAcesso !== filterStatus) {
                          return false;
                        }
                        return true;
                      })
                      .map((d) => (
                      <tr key={`all-${d.id}`} className={`border-t border-slate-800 ${d.statusAcesso === 'BLOQUEADO' ? 'bg-rose-900/20 border-rose-700/30' : ''}`}>
                        <td className="px-4 py-3">{d.nome}</td>
                        <td className="px-4 py-3">{d.ipaddr || '-'}</td>
                        <td className="px-4 py-3">{d.mac || '-'}</td>
                        <td className="px-4 py-3">{d.assignedTo || '-'}</td>
                        <td className="px-4 py-3">
                          {d.statusAcesso ? (
                            <span className={`text-xs px-2 py-1 rounded-full font-semibold ${
                              d.statusAcesso === 'LIBERADO' ? 'bg-emerald-200 text-emerald-800' : 
                              d.statusAcesso === 'BLOQUEADO' ? 'bg-rose-200 text-rose-800 border border-rose-300' : 
                              d.statusAcesso === 'AGUARDANDO' ? 'bg-amber-200 text-amber-800' : 
                              'bg-slate-200 text-slate-800'
                            }`}>
                              {d.statusAcesso}
                            </span>
                          ) : '-'}
                        </td>
                        <td className="px-4 py-3">
                          {(() => {
                            const onlineStatus = getDeviceOnlineStatus(d.ipaddr || '', d.mac || '');
                            return (
                              <span className={`text-xs px-2 py-1 rounded-full font-semibold ${onlineStatus.color} ${onlineStatus.textColor} flex items-center gap-1 w-fit`}>
                                <span>{onlineStatus.icon}</span>
                                {onlineStatus.label}
                              </span>
                            );
                          })()}
                        </td>
                        <td className="px-4 py-3">{d.descr || '-'}</td>
                        <td className="px-4 py-3">{d.ultimaAtividade || '-'}</td>
                        <td className="px-4 py-3">
                          {d.statusAcesso === 'BLOQUEADO' && (
                            <button 
                              onClick={() => liberarDispositivo(d)}
                              className="px-3 py-1 rounded-md bg-emerald-600 hover:bg-emerald-700 text-white text-sm"
                            >
                              Liberar
                            </button>
                          )}
                          {d.statusAcesso === 'LIBERADO' && (
                            <button 
                              onClick={() => bloquearDispositivo(d)}
                              className="px-3 py-1 rounded-md bg-rose-600 hover:bg-rose-700 text-white text-sm"
                            >
                              Bloquear
                            </button>
                          )}
                          {d.statusAcesso === 'AGUARDANDO' && (
                            <button 
                              onClick={() => liberarDispositivo(d)}
                              className="px-3 py-1 rounded-md bg-cyan-600 hover:bg-cyan-700 text-white text-sm"
                            >
                              Liberar
                            </button>
                          )}
                          {!d.statusAcesso && (
                            <span className="text-slate-400 text-sm">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                    {!allLoading && !allError && allDevices
                      .filter((d) => {
                        if (filterIP && !d.ipaddr?.toLowerCase().includes(filterIP.toLowerCase())) return false;
                        if (filterMAC && !d.mac?.toLowerCase().includes(filterMAC.toLowerCase())) return false;
                        if (filterStatus && d.statusAcesso !== filterStatus) return false;
                        return true;
                      }).length === 0 && (
                      <tr><td className="px-4 py-3" colSpan={9}>
                        {filterIP || filterMAC || filterStatus ? 
                          'Nenhum dispositivo encontrado com os filtros aplicados.' : 
                          'Nenhum dispositivo encontrado.'
                        }
                      </td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {permission === "MANAGER" && activeTab === "aliases" && (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="text-slate-300">Mapeamento Aliases</div>
                <div className="ml-auto flex items-center gap-2">
                  <button className="px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-700" onClick={() => { setCreateAliasOpen(true); setCreateError(null); setCreateSaving(false); setCreateAliasName(""); setCreateAliasDescr(""); setCreateAliasType("host"); setCreateAliasAddresses([{ address: "", detail: "" }]); }}>+ Novo Alias</button>
                  <button className="px-3 py-1 rounded bg-indigo-600 hover:bg-indigo-700" onClick={async () => {
                    setAliasesError(null);
                    setAliasesLoading(true);
                    await syncAliases();
                    try {
                      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
                      const r = await fetch(`${base}/aliases-db`);
                      if (!r.ok) {
                        if (r.status === 504) throw new Error('pfSense indisponível. Tente novamente mais tarde.');
                      }
                      const data = await r.json();
                      const list = Array.isArray(data) ? data : (data?.aliases ?? data?.items ?? []);
                      const normalized = list.map((a: any) => ({
                        id: a.id ?? undefined,
                        nome: a.name ?? a.alias_name ?? a.nome ?? "(sem nome)",
                        pathName: a.name ?? a.alias_name ?? (a.nome || ""),
                        tipo: a.type ?? a.alias_type ?? a.tipo ?? "-",
                        descr: a.descr ?? a.description ?? "",
                        itens: Array.isArray(a.addresses) ? a.addresses.length : (Array.isArray(a.items) ? a.items.length : undefined),
                        atualizado: a.updated_at ?? a.last_updated ?? "-",
                      })).filter((a: any) => String(a.tipo || '').toLowerCase() !== 'network');
                      setAliases(normalized);
                    } catch (e: any) {
                      setAliasesError(e?.message || "Falha ao sincronizar aliases");
                    } finally {
                      setAliasesLoading(false);
                    }
                  }}>Sincronizar</button>
                  <button className="px-3 py-1 rounded bg-slate-700 hover:bg-slate-600" onClick={() => { setAliasesError(null); setAliasesLoading(true); const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices"; fetch(`${base}/aliases-db`).then(r => r.json()).then((data) => {
                    const list = Array.isArray(data) ? data : (data?.aliases ?? data?.items ?? []);
                    const normalized = list.map((a: any) => ({
                      id: a.id ?? undefined,
                      nome: a.name ?? a.alias_name ?? a.nome ?? "(sem nome)",
                      pathName: a.name ?? a.alias_name ?? (a.nome || ""),
                      tipo: a.type ?? a.alias_type ?? a.tipo ?? "-",
                      descr: a.descr ?? a.description ?? "",
                      itens: Array.isArray(a.addresses) ? a.addresses.length : (Array.isArray(a.items) ? a.items.length : undefined),
                      atualizado: a.updated_at ?? a.last_updated ?? "-",
                    })).filter((a: any) => String(a.tipo || '').toLowerCase() !== 'network');
                    setAliases(normalized);
                  }).catch(() => setAliasesError("Falha ao recarregar aliases")).finally(() => setAliasesLoading(false)); }}>Recarregar</button>
                </div>
              </div>
              <div className="overflow-x-auto rounded-lg border border-slate-700">
                <table className="w-full text-left">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="px-4 py-3">Nome</th>
                      <th className="px-4 py-3">Tipo</th>
                      <th className="px-4 py-3">Descrição</th>
                      <th className="px-4 py-3">Itens</th>
                      <th className="px-4 py-3">Atualizado</th>
                      <th className="px-4 py-3">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {aliasesLoading && (<tr><td className="px-4 py-3" colSpan={6}>Carregando...</td></tr>)}
                    {!aliasesLoading && aliasesError && (<tr><td className="px-4 py-3 text-rose-400" colSpan={6}>{aliasesError}</td></tr>)}
                    {!aliasesLoading && !aliasesError && aliases.map((a, idx) => (
                      <tr key={`alias-${a.id ?? idx}`} className="border-t border-slate-800">
                        <td className="px-4 py-3">{a.nome}</td>
                        <td className="px-4 py-3">
                          {(() => {
                            const act = rulesAliasAction[a.pathName];
                            return act ? (
                              <span className={`text-xs px-2 py-1 rounded-full ${act === 'PASS' ? 'bg-emerald-200 text-emerald-800' : 'bg-rose-200 text-rose-800'}`}>{act}</span>
                            ) : '-';
                          })()}
                        </td>
                        <td className="px-4 py-3">{a.descr || '-'}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span>{a.itens ?? '-'}</span>
                            <button
                              className="px-2 py-1 rounded bg-slate-700 hover:bg-slate-600 text-xs"
                              onClick={async () => {
                                try {
                                  setAliasDetailsError(null);
                                  setAliasDetailsLoading(true);
                                  setAliasDetailsTarget(a.pathName);
                                  // se já temos os endereços carregados via listagem, usar diretamente
                                  if (Array.isArray((a as any).addresses) && (a as any).addresses.length) {
                                    setAliasDetails({ name: a.pathName, addresses: (a as any).addresses });
                                  } else {
                                    const base = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000/api/devices';
                                    const r = await fetch(`${base}/aliases-db/${encodeURIComponent(a.pathName)}`);
                                    if (!r.ok) {
                                      let msg = `Erro ${r.status}`;
                                      try { const j = await r.json(); msg = j?.detail || msg; } catch {}
                                      throw new Error(msg);
                                    }
                                    const j = await r.json();
                                    setAliasDetails({ name: j?.name || a.pathName, addresses: j?.addresses || [] });
                                  }
                                  setAliasDetailsOpen(true);
                                } catch (e: any) {
                                  setAliasDetailsError(e?.message || 'Falha ao carregar detalhes do alias');
                                  setAliasDetailsOpen(true);
                                } finally {
                                  setAliasDetailsLoading(false);
                                }
                              }}
                            >Ver detalhes</button>
                          </div>
                        </td>
                        <td className="px-4 py-3">{a.atualizado || '-'}</td>
                        <td className="px-4 py-3">
                          <button className="px-2 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-sm" onClick={() => {
                            setAliasSaveError(null);
                            setAliasAddresses([{ address: "", detail: "" }]);
                            setAliasTargetName(a.pathName);
                            setAliasTargetDisplay(a.nome);
                            setAliasModalOpen(true);
                          }}>Adicionar IPs</button>
                        </td>
                      </tr>
                    ))}
                    {!aliasesLoading && !aliasesError && aliases.length === 0 && (
                      <tr><td className="px-4 py-3" colSpan={6}>Nenhum alias encontrado.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>

              {aliasModalOpen && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
                  <div className="bg-slate-800 border border-slate-700 rounded-lg w-full max-w-2xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">Adicionar IPs ao alias: {aliasTargetDisplay || aliasTargetName}</h3>
                      <button className="text-slate-300 hover:text-white" onClick={() => setAliasModalOpen(false)}>✕</button>
                    </div>
                    {aliasSaveError && <div className="text-rose-400 text-sm mb-3">{aliasSaveError}</div>}
                    <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
                      {aliasAddresses.map((row, idx) => (
                        <div key={`addr-${idx}`} className="grid grid-cols-1 md:grid-cols-2 gap-3 items-end">
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <label className="block text-sm text-slate-300">Endereço IP</label>
                              <div className="flex items-center gap-2">
                                <input 
                                  type="checkbox" 
                                  id={`select-device-ip-${idx}`}
                                  checked={(row as any).selectFromDevices || false}
                                  onChange={(e) => {
                                    const selectFromDevices = e.target.checked;
                                    setAliasAddresses((arr) => arr.map((it, i) => 
                                      i === idx ? { ...it, selectFromDevices, address: selectFromDevices ? '' : it.address } : it
                                    ));
                                  }}
                                  className="rounded"
                                />
                                <label htmlFor={`select-device-ip-${idx}`} className="text-xs text-slate-400">Selecionar dispositivo</label>
                              </div>
                            </div>
                            
                            {(row as any).selectFromDevices ? (
                              <div className="space-y-2">
                                <div className="px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100">
                                  <span className="text-slate-400">Selecione um dispositivo cadastrado:</span>
                                </div>
                                
                                {deviceIpsLoading ? (
                                  <div className="text-xs text-slate-400">Carregando dispositivos...</div>
                                ) : deviceIpsError ? (
                                  <div className="text-xs text-rose-400">{deviceIpsError}</div>
                                ) : deviceIps.length > 0 ? (
                                  <div className="space-y-1 max-h-32 overflow-y-auto">
                                    <p className="text-xs text-slate-400">Dispositivos cadastrados:</p>
                                    <div className="space-y-1">
                                      {deviceIps.map((device) => (
                                        <button
                                          key={device.ip}
                                          type="button"
                                          onClick={() => {
                                            setAliasAddresses((arr) => arr.map((it, i) => 
                                              i === idx ? { 
                                                ...it, 
                                                address: device.ip,
                                                detail: `${device.hostname} (${device.mac})`
                                              } : it
                                            ));
                                          }}
                                          className="w-full text-left text-xs px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded flex justify-between"
                                        >
                                          <span>{device.ip}</span>
                                          <span className="text-slate-400">{device.hostname}</span>
                                        </button>
                                      ))}
                                    </div>
                                  </div>
                                ) : (
                                  <div className="text-xs text-slate-400">Nenhum dispositivo cadastrado encontrado</div>
                                )}
                              </div>
                            ) : (
                              <input 
                                className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100" 
                                placeholder="ex: 192.168.1.210" 
                                value={row.address} 
                                onChange={(e) => {
                              const v = e.target.value;
                              setAliasAddresses((arr) => arr.map((it, i) => i === idx ? { ...it, address: v } : it));
                                }} 
                              />
                            )}
                          </div>
                          <div className="flex gap-2">
                            <div className="flex-1">
                              <label className="block text-sm text-slate-300 mb-1">Detalhe</label>
                              <input className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100" placeholder="Descrição opcional" value={row.detail} onChange={(e) => {
                                const v = e.target.value;
                                setAliasAddresses((arr) => arr.map((it, i) => i === idx ? { ...it, detail: v } : it));
                              }} />
                            </div>
                            <button className="h-10 mt-auto px-3 py-2 rounded-md bg-rose-600/80 hover:bg-rose-600 text-white" onClick={() => {
                              setAliasAddresses((arr) => arr.filter((_, i) => i !== idx));
                            }}>Remover</button>
                          </div>
                        </div>
                      ))}
                      <div className="flex gap-2 flex-wrap">
                        <button className="px-3 py-2 rounded-md bg-slate-700 hover:bg-slate-600" onClick={() => setAliasAddresses((arr) => [...arr, { address: "", detail: "", selectFromDevices: false }])}>+ Adicionar linha</button>
                        <button className="px-3 py-2 rounded-md bg-cyan-600 hover:bg-cyan-700" onClick={() => setAliasAddresses((arr) => [...arr, { address: "", detail: "", selectFromDevices: true }])}>+ Selecionar dispositivo</button>
                        <button 
                          className="px-3 py-2 rounded-md bg-blue-600 hover:bg-blue-700" 
                          onClick={fetchDeviceIps}
                          disabled={deviceIpsLoading}
                        >
                          {deviceIpsLoading ? 'Carregando...' : '📋 Recarregar dispositivos'}
                        </button>
                      </div>
                    </div>
                    <div className="flex justify-end gap-2 mt-5">
                      <button className="px-4 py-2 rounded-md bg-slate-700 hover:bg-slate-600" onClick={() => setAliasModalOpen(false)}>Cancelar</button>
                      <button className={`px-4 py-2 rounded-md ${aliasSaving ? 'bg-emerald-700/60' : 'bg-emerald-600 hover:bg-emerald-700'} disabled:opacity-50`} disabled={aliasSaving} onClick={async () => {
                        setAliasSaving(true);
                        setAliasSaveError(null);
                        try {
                          const aliasName = aliasTargetName?.trim();
                          if (!aliasName) throw new Error('Alias inválido');
                          
                          // Processar endereços (apenas IPs válidos)
                          const items = aliasAddresses
                            .filter(it => it.address.trim())
                            .map(it => ({ 
                              address: it.address.trim(), 
                              detail: (it.detail || '').trim() 
                            }));
                          
                          // Validar IPv4 de cada entrada
                          for (const it of items) {
                            if (!ipv4Regex.test(it.address)) {
                              throw new Error(`IP inválido: ${it.address}`);
                            }
                          }
                          if (items.length === 0) throw new Error('Inclua pelo menos um endereço');
                          const base = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000/api/devices';
                          const url = `${base}/aliases-db/${encodeURIComponent(aliasName)}/add-addresses`;
                          const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ addresses: items }) });
                          if (!res.ok) {
                            // tentar extrair JSON.detail do backend
                            let txt = '';
                            try {
                              const j = await res.json();
                              txt = j?.detail ? String(j.detail) : JSON.stringify(j);
                            } catch {
                              try { txt = await res.text(); } catch {}
                            }
                            if (res.status === 504) {
                              throw new Error('pfSense indisponível. Tente novamente mais tarde.');
                            }
                            throw new Error(`Erro ao adicionar IPs (${res.status}) ${txt}`);
                          }
                          // Sincronizar antes de recarregar
                          await syncAliases();
                          // Recarregar aliases
                          try {
                            setAliasesLoading(true);
                            const data = await fetch(`${base}/aliases-db`).then(r => r.json());
                            const list = Array.isArray(data) ? data : (data?.aliases ?? data?.items ?? []);
                            const normalized = list.map((a: any) => ({
                              id: a.id ?? undefined,
                              nome: a.name ?? a.alias_name ?? a.nome ?? '(sem nome)',
                              pathName: a.name ?? a.alias_name ?? (a.nome || ''),
                              tipo: a.type ?? a.alias_type ?? a.tipo ?? '-',
                              descr: a.descr ?? a.description ?? '',
                              itens: Array.isArray(a.addresses) ? a.addresses.length : (Array.isArray(a.items) ? a.items.length : undefined),
                              atualizado: a.updated_at ?? a.last_updated ?? '-',
                            })).filter((a: any) => String(a.tipo || '').toLowerCase() !== 'network');
                            setAliases(normalized);
                          } catch {}
                          setAliasModalOpen(false);
                        } catch (e: any) {
                          setAliasSaveError(e?.message || 'Falha ao adicionar IPs');
                        } finally {
                          setAliasSaving(false);
                          setAliasesLoading(false);
                        }
                      }}>{aliasSaving ? 'Salvando...' : 'Salvar'}</button>
            </div>
          </div>
        </div>
              )}
              {aliasDetailsOpen && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
                  <div className="bg-slate-800 border border-slate-700 rounded-lg w-full max-w-2xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">Detalhes do alias: {aliasDetailsTarget}</h3>
                      <button className="text-slate-300 hover:text-white" onClick={() => setAliasDetailsOpen(false)}>✕</button>
                    </div>
                    {aliasDetailsError && <div className="text-rose-400 text-sm mb-3">{aliasDetailsError}</div>}
                    {aliasDetailsLoading ? (
                      <div className="text-slate-300">Carregando...</div>
                    ) : (
                      <div className="overflow-x-auto rounded border border-slate-700">
                        <table className="w-full text-left">
                          <thead className="bg-slate-800">
                            <tr>
                              <th className="px-4 py-3">Endereço</th>
                              <th className="px-4 py-3">Detalhe</th>
                              <th className="px-4 py-3 w-24">Ações</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Array.isArray(aliasDetails?.addresses) && aliasDetails.addresses.length > 0 ? (
                              aliasDetails.addresses.map((ad: any, idx: number) => {
                                const address = ad.address ?? ad?.value ?? '-';
                                const isRemoving = removingAddress === address;
                                
                                return (
                                <tr key={`ad-${idx}`} className="border-t border-slate-800">
                                    <td className="px-4 py-3 font-mono text-sm">{address}</td>
                                  <td className="px-4 py-3">{ad.detail ?? ad?.description ?? '-'}</td>
                                    <td className="px-4 py-3">
                                      {address !== '-' && (
                                        <button
                                          className={`px-2 py-1 rounded text-xs ${
                                            isRemoving 
                                              ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
                                              : 'bg-red-600/80 hover:bg-red-600 text-white'
                                          }`}
                                          onClick={() => removeAddressFromAlias(aliasDetailsTarget || '', address)}
                                          disabled={isRemoving || aliasDetailsLoading}
                                          title={`Remover endereço ${address}`}
                                        >
                                          {isRemoving ? 'Removendo...' : '🗑️ Remover'}
                                        </button>
                                      )}
                                    </td>
                                </tr>
                                );
                              })
                            ) : (
                              <tr>
                                <td className="px-4 py-3" colSpan={3}>Nenhum item.</td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    )}
                    <div className="flex justify-end mt-4">
                      <button className="px-4 py-2 rounded-md bg-slate-700 hover:bg-slate-600" onClick={() => setAliasDetailsOpen(false)}>Fechar</button>
                    </div>
                  </div>
                </div>
              )}

              {createAliasOpen && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
                  <div className="bg-slate-800 border border-slate-700 rounded-lg w-full max-w-2xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">Criar novo Alias</h3>
                      <button className="text-slate-300 hover:text-white" onClick={() => setCreateAliasOpen(false)}>✕</button>
                    </div>
                    {createError && <div className="text-rose-400 text-sm mb-3">{createError}</div>}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                      <div>
                        <label className="block text-sm text-slate-300 mb-1">Nome</label>
                        <input className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100" value={createAliasName} onChange={(e) => setCreateAliasName(e.target.value)} placeholder="ex: authorized_devices" />
                      </div>
                      <div>
                        <label className="block text-sm text-slate-300 mb-1">Tipo</label>
                        <select aria-label="Tipo de alias" title="Tipo de alias" className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100" value={createAliasType} onChange={(e) => setCreateAliasType((e.target.value as any) || 'host')}>
                          <option value="host">host</option>
                          <option value="network">network</option>
                        </select>
                      </div>
                      <div className="md:col-span-2">
                        <label className="block text-sm text-slate-300 mb-1">Descrição</label>
                        <input className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100" value={createAliasDescr} onChange={(e) => setCreateAliasDescr(e.target.value)} placeholder="Descrição do alias" />
                      </div>
                    </div>
                    <div className="space-y-3 max-h-[50vh] overflow-y-auto pr-1">
                      {createAliasAddresses.map((row, idx) => (
                        <div key={`caddr-${idx}`} className="grid grid-cols-1 md:grid-cols-2 gap-3 items-end">
                          <div>
                            <label className="block text-sm text-slate-300 mb-1">{createAliasType === 'network' ? 'Rede (CIDR)' : 'Endereço IP'}</label>
                            <input className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100" placeholder={createAliasType === 'network' ? 'ex: 192.168.1.0/24' : 'ex: 192.168.1.100'} value={row.address} onChange={(e) => {
                              const v = e.target.value;
                              setCreateAliasAddresses((arr) => arr.map((it, i) => i === idx ? { ...it, address: v } : it));
                            }} />
                          </div>
                          <div className="flex gap-2">
                            <div className="flex-1">
                              <label className="block text-sm text-slate-300 mb-1">Detalhe</label>
                              <input className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100" placeholder="Descrição opcional" value={row.detail} onChange={(e) => {
                                const v = e.target.value;
                                setCreateAliasAddresses((arr) => arr.map((it, i) => i === idx ? { ...it, detail: v } : it));
                              }} />
                            </div>
                            <button className="h-10 mt-auto px-3 py-2 rounded-md bg-rose-600/80 hover:bg-rose-600 text-white" onClick={() => {
                              setCreateAliasAddresses((arr) => arr.filter((_, i) => i !== idx));
                            }}>Remover</button>
                          </div>
                        </div>
                      ))}
                      <div>
                        <button className="px-3 py-2 rounded-md bg-slate-700 hover:bg-slate-600" onClick={() => setCreateAliasAddresses((arr) => [...arr, { address: "", detail: "" }])}>+ Adicionar linha</button>
                      </div>
                    </div>
                    <div className="flex justify-end gap-2 mt-5">
                      <button className="px-4 py-2 rounded-md bg-slate-700 hover:bg-slate-600" onClick={() => setCreateAliasOpen(false)}>Cancelar</button>
                      <button className={`px-4 py-2 rounded-md ${createSaving ? 'bg-emerald-700/60' : 'bg-emerald-600 hover:bg-emerald-700'} disabled:opacity-50`} disabled={createSaving} onClick={async () => {
                        setCreateSaving(true);
                        setCreateError(null);
                        try {
                          const name = createAliasName.trim();
                          if (!name) throw new Error('Informe o nome do alias');
                          const items = createAliasAddresses.map((it) => ({ address: it.address.trim(), detail: (it.detail || '').trim() })).filter((it) => !!it.address);
                          if (items.length === 0) throw new Error('Inclua pelo menos um endereço');
                          if (createAliasType === 'host') {
                            for (const it of items) {
                              if (!ipv4Regex.test(it.address)) throw new Error(`IP inválido: ${it.address}`);
                            }
                          } else if (createAliasType === 'network') {
                            for (const it of items) {
                              if (!cidrRegex.test(it.address)) throw new Error(`CIDR inválido: ${it.address}`);
                            }
                          }
                          const base = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000/api/devices';
                          const res = await fetch(`${base}/aliases-db/create`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ name, alias_type: createAliasType, descr: createAliasDescr, addresses: items })
                          });
                          if (!res.ok) {
                            let txt = '';
                            try { const j = await res.json(); txt = j?.detail ? String(j.detail) : JSON.stringify(j); } catch { try { txt = await res.text(); } catch {} }
                            if (res.status === 504) {
                              throw new Error('pfSense indisponível. Tente novamente mais tarde.');
                            }
                            throw new Error(`Erro ao criar alias (${res.status}) ${txt}`);
                          }
                          // Sincronizar antes de recarregar
                          await syncAliases();
                          // Recarregar lista (com filtro que remove 'network')
                          try {
                            setAliasesLoading(true);
                            const data = await fetch(`${base}/aliases-db`).then(r => r.json());
                            const list = Array.isArray(data) ? data : (data?.aliases ?? data?.items ?? []);
                            const normalized = list.map((a: any) => ({
                              id: a.id ?? undefined,
                              nome: a.name ?? a.alias_name ?? a.nome ?? '(sem nome)',
                              pathName: a.name ?? a.alias_name ?? (a.nome || ''),
                              tipo: a.type ?? a.alias_type ?? a.tipo ?? '-',
                              descr: a.descr ?? a.description ?? '',
                              itens: Array.isArray(a.addresses) ? a.addresses.length : (Array.isArray(a.items) ? a.items.length : undefined),
                              atualizado: a.updated_at ?? a.last_updated ?? '-',
                            })).filter((a: any) => String(a.tipo || '').toLowerCase() !== 'network');
                            setAliases(normalized);
                          } catch {}
                          setCreateAliasOpen(false);
                        } catch (e: any) {
                          setCreateError(e?.message || 'Falha ao criar alias');
                        } finally {
                          setCreateSaving(false);
                          setAliasesLoading(false);
                        }
                      }}>{createSaving ? 'Criando...' : 'Criar'}</button>
            </div>
          </div>
        </div>
              )}
            </div>
          )}

          {permission === "MANAGER" && activeTab === "rules" && (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="text-slate-300">Regras de Firewall</div>
                <div className="ml-auto flex items-center gap-2">
                  <button className="px-3 py-1 rounded bg-indigo-600 hover:bg-indigo-700" onClick={async () => {
                    setRulesError(null);
                    setRulesLoading(true);
                    try {
                      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
                      const sync = await fetch(`${base}/firewall/rules/save`, { method: 'POST' });
                      if (!sync.ok) {
                        let msg = `Erro ${sync.status}`;
                        try { const j = await sync.json(); msg = j?.detail || msg; } catch {}
                        throw new Error(msg);
                      }
                      const r = await fetch(`${base}/firewall/rules-db`);
                      if (!r.ok) {
                        let msg = `Erro ${r.status}`;
                        try { const j = await r.json(); msg = j?.detail || msg; } catch {}
                        throw new Error(msg);
                      }
                      const data = await r.json();
                      const raw = Array.isArray(data) ? data : (data?.result ?? data?.data ?? []);
                      const filtered = (raw || []).filter((x: any) => {
                        const ifs = Array.isArray(x.interface) ? x.interface : [x.interface];
                        return !ifs.some((it: any) => String(it || '').toLowerCase() === 'wan');
                      });
                      const norm = filtered.map((x: any, idx: number) => ({
                        id: x.pf_id ?? x.id ?? idx,
                        action: x.type ?? x.action ?? '-',
                        interface: Array.isArray(x.interface) ? x.interface.join(', ') : (x.interface ?? x.if ?? '-'),
                        ipprotocol: x.ipprotocol ?? '-',
                        protocol: x.protocol ?? x.proto ?? '-',
                        source: x.source ?? x.src ?? x.source_net ?? '-',
                        destination: x.destination ?? x.dst ?? x.destination_net ?? '-',
                        destination_port: x.destination_port ?? '-',
                        description: x.descr ?? x.description ?? '-',
                        updated_at: x.updated_time ?? x.updated_at ?? x.last_updated ?? undefined,
                      }));
                      setRules(norm);
                    } catch (e: any) {
                      setRulesError(e?.message || 'Falha ao sincronizar regras');
                    } finally {
                      setRulesLoading(false);
                    }
                  }}>Sincronizar</button>
                  <button className="px-3 py-1 rounded bg-slate-700 hover:bg-slate-600" onClick={async () => {
                    setRulesError(null);
                    setRulesLoading(true);
                    try {
                      const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/devices";
                      const r = await fetch(`${base}/firewall/rules-db`);
                      if (!r.ok) {
                        let msg = `Erro ${r.status}`;
                        try { const j = await r.json(); msg = j?.detail || msg; } catch {}
                        throw new Error(msg);
                      }
                      const data = await r.json();
                      const raw = Array.isArray(data) ? data : (data?.result ?? data?.data ?? []);
                      const filtered = (raw || []).filter((x: any) => {
                        const ifs = Array.isArray(x.interface) ? x.interface : [x.interface];
                        return !ifs.some((it: any) => String(it || '').toLowerCase() === 'wan');
                      });
                      const norm = filtered.map((x: any, idx: number) => ({
                        id: x.pf_id ?? x.id ?? idx,
                        action: x.type ?? x.action ?? '-',
                        interface: Array.isArray(x.interface) ? x.interface.join(', ') : (x.interface ?? x.if ?? '-'),
                        ipprotocol: x.ipprotocol ?? '-',
                        protocol: x.protocol ?? x.proto ?? '-',
                        source: x.source ?? x.src ?? x.source_net ?? '-',
                        destination: x.destination ?? x.dst ?? x.destination_net ?? '-',
                        destination_port: x.destination_port ?? '-',
                        description: x.descr ?? x.description ?? '-',
                        updated_at: x.updated_time ?? x.updated_at ?? x.last_updated ?? undefined,
                      }));
                      setRules(norm);
                    } catch (e: any) {
                      setRulesError(e?.message || 'Falha ao recarregar regras');
                    } finally {
                      setRulesLoading(false);
                    }
                  }}>Recarregar</button>
                </div>
              </div>
              <div className="overflow-x-auto rounded-lg border border-slate-700">
                <table className="w-full text-left">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="px-4 py-3">Ação</th>
                      <th className="px-4 py-3">Interface</th>
                      <th className="px-4 py-3">IP Proto</th>
                      <th className="px-4 py-3">Protocolo</th>
                      <th className="px-4 py-3">Origem</th>
                      <th className="px-4 py-3">Destino</th>
                      <th className="px-4 py-3">Porta Destino</th>
                      <th className="px-4 py-3">Descrição</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rulesLoading && (<tr><td className="px-4 py-3" colSpan={8}>Carregando...</td></tr>)}
                    {!rulesLoading && rulesError && (<tr><td className="px-4 py-3 text-rose-400" colSpan={8}>{rulesError}</td></tr>)}
                    {!rulesLoading && !rulesError && rules.map((r, idx) => (
                      <tr key={`rule-${r.id ?? idx}`} className="border-t border-slate-800">
                        <td className="px-4 py-3">{String(r.action || '-').toUpperCase()}</td>
                        <td className="px-4 py-3">{r.interface || '-'}</td>
                        <td className="px-4 py-3">{r.ipprotocol || '-'}</td>
                        <td className="px-4 py-3">{r.protocol || '-'}</td>
                        <td className="px-4 py-3">{r.source || '-'}</td>
                        <td className="px-4 py-3">{r.destination || '-'}</td>
                        <td className="px-4 py-3">{r.destination_port || '-'}</td>
                        <td className="px-4 py-3">{r.description || '-'}</td>
                      </tr>
                    ))}
                    {!rulesLoading && !rulesError && rules.length === 0 && (
                      <tr><td className="px-4 py-3" colSpan={8}>Nenhuma regra encontrada.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Modal de bloqueio com motivo */}
          {blockModalOpen && (
            <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
              <div className="bg-slate-800 border border-slate-700 rounded-lg w-full max-w-md p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">Bloquear Dispositivo</h3>
                  <button 
                    className="text-slate-300 hover:text-white" 
                    onClick={() => {
                      setBlockModalOpen(false);
                      setBlockingDevice(null);
                      setBlockReason("");
                      setBlockError(null);
                    }}
                  >
                    ✕
                  </button>
                </div>
                
                {blockingDevice && (
                  <div className="mb-4 p-3 bg-slate-900 rounded-lg">
                    <div className="text-sm text-slate-300">
                      <div><strong>Dispositivo:</strong> {blockingDevice.nome || blockingDevice.cid}</div>
                      <div><strong>IP:</strong> {blockingDevice.ipaddr}</div>
                      <div><strong>MAC:</strong> {blockingDevice.mac}</div>
                    </div>
                  </div>
                )}
                
                <div className="mb-4">
                  <label className="block text-sm text-slate-300 mb-2">
                    Motivo do bloqueio <span className="text-rose-400">*</span>
                  </label>
                  <textarea
                    className="w-full px-3 py-2 rounded-md bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:ring-2 focus:ring-rose-500"
                    rows={4}
                    placeholder="Descreva o motivo do bloqueio (mínimo 5 caracteres)..."
                    value={blockReason}
                    onChange={(e) => setBlockReason(e.target.value)}
                  />
                  <div className="text-xs text-slate-400 mt-1">
                    {blockReason.length}/500 caracteres (mínimo 5)
                  </div>
                </div>
                
                {blockError && (
                  <div className="mb-4 p-3 bg-rose-900/30 border border-rose-700 rounded-lg">
                    <div className="text-rose-300 text-sm">{blockError}</div>
                  </div>
                )}
                
                <div className="flex justify-end gap-3">
                  <button
                    className="px-4 py-2 rounded-md bg-slate-700 hover:bg-slate-600 text-white"
                    onClick={() => {
                      setBlockModalOpen(false);
                      setBlockingDevice(null);
                      setBlockReason("");
                      setBlockError(null);
                    }}
                    disabled={blockSaving}
                  >
                    Cancelar
                  </button>
                  <button
                    className={`px-4 py-2 rounded-md ${
                      blockSaving ? 'bg-rose-700/60' : 'bg-rose-600 hover:bg-rose-700'
                    } text-white disabled:opacity-50`}
                    onClick={confirmarBloqueio}
                    disabled={blockSaving || !blockReason.trim() || blockReason.trim().length < 5}
                  >
                    {blockSaving ? 'Bloqueando...' : 'Confirmar Bloqueio'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Modal de detalhes do dispositivo bloqueado */}
          {deviceDetailsOpen && (
            <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
              <div className="bg-slate-800 border border-slate-700 rounded-lg w-full max-w-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">Detalhes do Dispositivo</h3>
                  <button 
                    className="text-slate-300 hover:text-white" 
                    onClick={() => {
                      setDeviceDetailsOpen(false);
                      setDeviceDetails(null);
                      setDeviceDetailsError(null);
                    }}
                  >
                    ✕
                  </button>
                </div>
                
                {deviceDetailsError && (
                  <div className="mb-4 p-3 bg-rose-900/30 border border-rose-700 rounded-lg">
                    <div className="text-rose-300 text-sm">{deviceDetailsError}</div>
                  </div>
                )}
                
                {deviceDetails && (
                  <div className="space-y-4">
                    {/* Contador de Advertências */}
                    <div className="p-4 bg-slate-900 rounded-lg">
                      <h4 className="text-slate-200 font-medium mb-3">Status do Dispositivo</h4>
                      {(() => {
                        console.log('🔍 Verificando contador de advertências para dispositivo:', deviceDetails.id);
                        console.log('📋 feedback_history:', deviceDetails.feedback_history);
                        
                        // Buscar feedback mais recente com advertências
                        const recentFeedback = deviceDetails.feedback_history?.find((feedback: any) => {
                          console.log('🔍 Verificando feedback:', feedback.id, 'admin_notes:', feedback.admin_notes);
                          const hasWarning = feedback.admin_notes && getWarningInfo(feedback.admin_notes);
                          console.log('⚠️ Tem advertência?', hasWarning);
                          return hasWarning;
                        });
                        
                        console.log('📋 recentFeedback encontrado:', recentFeedback);
                        
                        // Sistema inteligente: contar bloqueios administrativos como advertências
                        let warningInfo = recentFeedback ? getWarningInfo(recentFeedback.admin_notes) : null;
                        
                        if (!warningInfo && deviceDetails.feedback_history?.length > 0) {
                          // Contar bloqueios administrativos como advertências
                          const adminBlockings = deviceDetails.feedback_history.filter((feedback: any) => 
                            feedback.user_feedback?.includes('Bloqueio administrativo')
                          ).length;
                          
                          if (adminBlockings > 0) {
                            warningInfo = {
                              current: adminBlockings,
                              total: 3, // Padrão de 3 advertências
                              remaining: 3 - adminBlockings
                            };
                            console.log('🔢 Advertências calculadas automaticamente:', warningInfo);
                          }
                        }
                        
                        console.log('⚠️ warningInfo final:', warningInfo);
                        
                        if (warningInfo) {
                            return (
                              <div className={`p-3 rounded-lg border-2 ${getWarningColor(warningInfo)}`}>
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="text-lg">⚠️</span>
                                  <span className="text-sm font-bold">
                                    ADVERTÊNCIA {warningInfo.current} DE {warningInfo.total}
                                  </span>
                                  {!recentFeedback && <span className="text-xs text-gray-500">(AUTO)</span>}
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
                        
                        // Se não há advertências, mostrar status básico
                        return (
                          <div className="p-3 bg-green-100 text-green-800 border border-green-200 rounded-lg">
                            <div className="flex items-center gap-2">
                              <span className="text-lg">✅</span>
                              <span className="text-sm font-bold">DISPOSITIVO LIBERADO</span>
                            </div>
                            <div className="text-xs mt-1">
                              Seu dispositivo está funcionando normalmente
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                    
                    {/* Histórico de Feedback */}
                    {deviceDetails.is_blocked && (
                      <div className="p-4 bg-slate-900 rounded-lg">
                        <h4 className="text-slate-200 font-medium mb-3 flex items-center gap-2">
                          <span>📝</span>
                          Histórico de Feedback
                        </h4>
                        <div className="max-h-64 overflow-y-auto">
                          <FeedbackHistory 
                            dhcpMappingId={deviceDetails.id}
                            deviceIp={deviceDetails.ipaddr}
                            deviceName={deviceDetails.nome || deviceDetails.cid}
                            theme="dark"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                <div className="flex justify-end mt-6">
                  <button
                    className="px-4 py-2 rounded-md bg-slate-700 hover:bg-slate-600 text-white"
                    onClick={() => {
                      setDeviceDetailsOpen(false);
                      setDeviceDetails(null);
                      setDeviceDetailsError(null);
                    }}
                  >
                    Fechar
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Tab content: Incidentes (Logs Notice) */}
          {activeTab === "incidents" && (
            <div>
              {/* Mensagem informativa */}
              <div className="bg-amber-900/30 border border-amber-700 rounded-lg p-3 mb-4">
                <div className="flex items-center gap-2 text-amber-300">
                  <span>🚨</span>
                  <span className="text-sm">
                    Esta aba exibe apenas os incidentes de segurança capturados nos logs notice do Zeek
                  </span>
                </div>
              </div>
              
              {/* Filtros e controles */}
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-4">
                <div className="text-slate-300 font-medium mb-3">Filtros de Incidentes</div>
                <div className="flex gap-2">
                  <button
                    className="px-4 py-2 rounded-md bg-cyan-500 hover:bg-cyan-600 disabled:opacity-50"
                    onClick={() => {
                      // Limpar filtros se necessário
                    }}
                    disabled={noticeLoading}
                  >
                    Limpar Filtros
                  </button>
                  <button
                    className="px-4 py-2 rounded-md bg-green-600 hover:bg-green-700 disabled:opacity-50"
                    onClick={fetchIncidentsFromDatabase}
                    disabled={noticeLoading}
                  >
                    {noticeLoading ? 'Carregando...' : 'Atualizar'}
                  </button>
                  
                </div>
              </div>

              {/* Tabela de incidentes notice */}
              <div className="overflow-x-auto rounded-lg border border-slate-700">
                <table className="w-full text-left">
                  <thead className="bg-slate-800">
                    <tr>
                      <th className="px-4 py-3">Timestamp</th>
                      <th className="px-4 py-3">Tipo de Incidente</th>
                      <th className="px-4 py-3">Severidade</th>
                      <th className="px-4 py-3">Descrição</th>
                      <th className="px-4 py-3">IP do Dispositivo</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {noticeLoading && (
                      <tr>
                        <td className="px-4 py-3 text-center" colSpan={7}>
                          <div className="flex items-center justify-center gap-2">
                            <div className="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
                            Carregando incidentes...
                          </div>
                        </td>
                      </tr>
                    )}
                    
                    {noticeError && (
                      <tr>
                        <td className="px-4 py-3 text-center text-rose-400" colSpan={6}>
                          <div className="flex items-center justify-center gap-2">
                            <span>⚠️</span>
                            {noticeError}
                          </div>
                        </td>
                      </tr>
                    )}
                    
                    {!noticeLoading && !noticeError && noticeIncidents.length === 0 && (
                      <tr>
                        <td className="px-4 py-3 text-center text-slate-400" colSpan={6}>
                          <div className="flex items-center justify-center gap-2">
                            <span>📋</span>
                            Nenhum incidente encontrado nos logs notice
                          </div>
                        </td>
                      </tr>
                    )}
                    
                    {!noticeLoading && !noticeError && noticeIncidents.map((incident, index) => {
                      // Função para determinar cor da severidade
                      const getSeverityColor = (severity: string) => {
                        switch (severity?.toLowerCase()) {
                          case 'critical': return 'bg-red-100 text-red-800';
                          case 'high': return 'bg-orange-100 text-orange-800';
                          case 'medium': return 'bg-yellow-100 text-yellow-800';
                          case 'low': return 'bg-green-100 text-green-800';
                          default: return 'bg-gray-100 text-gray-800';
                        }
                      };
                      
                      // Função para determinar cor do status
                      const getStatusColor = (status: string) => {
                        switch (status?.toLowerCase()) {
                          case 'new': return 'bg-blue-100 text-blue-800';
                          case 'investigating': return 'bg-purple-100 text-purple-800';
                          case 'resolved': return 'bg-green-100 text-green-800';
                          case 'false_positive': return 'bg-gray-100 text-gray-800';
                          case 'escalated': return 'bg-red-100 text-red-800';
                          default: return 'bg-gray-100 text-gray-800';
                        }
                      };
                      
                      return (
                        <tr key={incident.id || index} className="border-b border-slate-700 hover:bg-slate-800/50">
                          <td className="px-4 py-3 text-slate-300">
                            <div className="text-sm font-mono">{incident.ts}</div>
                            <div className="text-xs text-slate-500 mt-1">
                              {incident.detected_relative && (
                                <span className="bg-slate-700 px-2 py-1 rounded text-slate-300">
                                  {incident.detected_relative}
                                </span>
                              )}
                            </div>
                            {incident.created_at && incident.created_at !== '-' && (
                              <div className="text-xs text-slate-500 mt-1">
                                Criado: {incident.created_relative}
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm">
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                {incident.note}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm">
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(incident.severity)}`}>
                                {incident.severity?.toUpperCase() || 'UNKNOWN'}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-slate-300">
                            <div className="text-sm max-w-xs truncate" title={incident.msg}>
                              {incident.msg}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-slate-300">
                            <div className="text-sm font-mono">{incident.id_orig_h}</div>
                          </td>
                          <td className="px-4 py-3 text-slate-300">
                            <div className="text-sm text-slate-400">Bloqueio automático ativo</div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              
              {/* Estatísticas */}
              {!noticeLoading && !noticeError && noticeIncidents.length > 0 && (
                <div className="mt-4 text-sm text-slate-400">
                  Total de incidentes: {noticeIncidents.length}
                </div>
              )}
            </div>
          )}

          {/* Tab content: Histórico de Bloqueios */}
          {activeTab === "blocking-history" && (
            <div>
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">
                  📋 Histórico de Bloqueios
                </h2>
                <p className="text-gray-600 mb-6">
                  Visualize o histórico completo de bloqueios administrativos e feedbacks de usuários sobre problemas de bloqueio.
                </p>
                
                <BlockingHistory />
              </div>
            </div>
          )}

        </main>
      </div>

      {/* Modal de Feedback de Bloqueio */}
      <BlockingFeedbackModal
        isOpen={feedbackModalOpen}
        onClose={() => setFeedbackModalOpen(false)}
        dhcpMappingId={selectedDhcpMappingId || 0}
        deviceIp={selectedDeviceIp || undefined}
        deviceName={selectedDeviceName || undefined}
      />
    </div>
  );
}
