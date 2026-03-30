"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Building2, MapPin, Globe, Key, Trash2, Edit, ToggleLeft, ToggleRight, Users } from "lucide-react";
import InstitutionManagers from "./InstitutionManagers";
import InstitutionEditForm from "./InstitutionEditForm";

interface Institution {
  id: number;
  nome: string;
  cidade: string;
  pfsense_base_url: string;
  pfsense_key: string;
  zeek_base_url: string;
  zeek_key: string;
  suricata_base_url?: string;
  suricata_key?: string;
  ip_range_start: string;
  ip_range_end: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  managers_count?: number;
}

export default function InstitutionList() {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedInstitution, setSelectedInstitution] = useState<Institution | null>(null);
  const [editingInstitution, setEditingInstitution] = useState<Institution | null>(null);

  // Usar URL relativa para passar pelo proxy do Next.js
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

  const makeAuthenticatedRequest = async (url: string, options: RequestInit = {}) => {
    // O usuário já está autenticado via Google OAuth
    // As requisições usam a sessão do navegador (cookies)
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
        credentials: "include", // Incluir cookies da sessão
      });

      return response;
    } catch (error) {
      console.error("Erro na requisição:", error);
      throw error;
    }
  };

  const fetchInstitutions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const url = `${API_BASE}/admin/institutions`;
      console.log('Buscando instituições em:', url);
      
      const response = await makeAuthenticatedRequest(url, {
        method: "GET",
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { detail: errorText || `Erro ${response.status}` };
        }
        throw new Error(errorData.detail || `Erro ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log('Response data:', data);
      
      setInstitutions(data.institutions || []);
    } catch (err) {
      console.error('Fetch error:', err);
      const errorMsg = err instanceof Error ? err.message : "Erro inesperado";
      setError(errorMsg);
      console.error("Erro completo:", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleInstitutionStatus = async (id: number) => {
    try {
      console.log('Toggling status for institution:', id);
      
      const response = await makeAuthenticatedRequest(`${API_BASE}/admin/institutions/${id}/toggle-status`, {
        method: "PUT",
      });

      console.log('Toggle response status:', response.status);
      console.log('Toggle response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Toggle error response:', errorText);
        throw new Error(`Erro ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log('Toggle response data:', data);

      // Recarregar lista
      await fetchInstitutions();
    } catch (err) {
      console.error('Toggle error:', err);
      setError(err instanceof Error ? err.message : "Erro inesperado");
    }
  };

  const deleteInstitution = async (id: number, nome: string) => {
    if (!confirm(`Tem certeza que deseja excluir a instituição "${nome}"? Esta ação é irreversível!`)) {
      return;
    }

    try {
      console.log('Deleting institution:', id, nome);
      
      const response = await makeAuthenticatedRequest(`${API_BASE}/admin/institutions/${id}`, {
        method: "DELETE",
      });

      console.log('Delete response status:', response.status);
      console.log('Delete response ok:', response.ok);

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Delete error response:', errorData);
        throw new Error(errorData.detail || "Erro ao excluir instituição");
      }

      const data = await response.json();
      console.log('Delete response data:', data);

      // Recarregar lista
      await fetchInstitutions();
    } catch (err) {
      console.error('Delete error:', err);
      setError(err instanceof Error ? err.message : "Erro inesperado");
    }
  };

  const handleInstitutionUpdate = (updatedInstitution: Institution) => {
    setInstitutions(prev => 
      prev.map(inst => 
        inst.id === updatedInstitution.id ? updatedInstitution : inst
      )
    );
    setEditingInstitution(null);
  };

  useEffect(() => {
    fetchInstitutions();
  }, []);

  const groupedInstitutions = institutions.reduce((acc, institution) => {
    const key = institution.nome;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(institution);
    return acc;
  }, {} as Record<string, Institution[]>);

  console.log('Institutions state:', institutions);
  console.log('Grouped institutions:', groupedInstitutions);

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          <span>Carregando instituições...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Instituições Cadastradas ({institutions.length})
          </CardTitle>
          <CardDescription>
            Gerencie as instituições cadastradas no sistema
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {institutions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              Nenhuma instituição cadastrada ainda.
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(groupedInstitutions).map(([institutionName, campi]) => (
                <div key={institutionName} className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Building2 className="h-5 w-5 text-blue-600" />
                    <h2 className="text-xl font-bold text-gray-800">{institutionName}</h2>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                      {campi.length} campus{campi.length > 1 ? 'es' : ''}
                    </span>
                  </div>
                  
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {campi.map((institution) => (
                      <Card key={institution.id} className="border-l-4 border-l-green-500">
                        <CardContent className="p-4">
                          {/* Cabeçalho: Nome e Status */}
                          <div className="flex justify-between items-center mb-4 bg-gray-800 p-3 rounded-lg">
                            <div>
                              <h3 className="text-lg font-semibold text-white">{institution.cidade}</h3>
                              <p className="text-sm text-white font-medium">{institution.nome}</p>
                            </div>
                            <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                              institution.is_active 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {institution.is_active ? 'Ativo' : 'Inativo'}
                            </div>
                          </div>

                          {/* Botões de Ação */}
                          <div className="flex gap-2 mb-4">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedInstitution(institution)}
                              className="text-blue-600 hover:text-blue-700 flex-1"
                              title="Gerenciar gestores"
                            >
                              <Users className="h-4 w-4 mr-1" />
                              <span className="text-xs">
                                {institution.managers_count || 0} gestores
                              </span>
                            </Button>
                            
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setEditingInstitution(institution)}
                              className="text-green-600 hover:text-green-700"
                              title="Editar instituição"
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => toggleInstitutionStatus(institution.id)}
                              title={institution.is_active ? "Desativar" : "Ativar"}
                            >
                              {institution.is_active ? (
                                <ToggleRight className="h-4 w-4" />
                              ) : (
                                <ToggleLeft className="h-4 w-4" />
                              )}
                            </Button>
                            
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => deleteInstitution(institution.id, institution.nome)}
                              className="text-red-600 hover:text-red-700"
                              title="Excluir instituição"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>

                          {/* Dados Técnicos */}
                          <div className="space-y-3 pt-3 border-t border-gray-200">
                            <div className="flex items-center gap-2 text-sm">
                              <Globe className="h-4 w-4 text-blue-600" />
                              <span className="font-semibold text-gray-800">pfSense:</span>
                              <span className="font-mono text-xs text-gray-700 bg-gray-100 px-2 py-1 rounded border">
                                {institution.pfsense_base_url}
                              </span>
                            </div>
                            
                            <div className="flex items-center gap-2 text-sm">
                              <Key className="h-4 w-4 text-purple-600" />
                              <span className="font-semibold text-gray-800">Zeek:</span>
                              <span className="font-mono text-xs text-gray-700 bg-gray-100 px-2 py-1 rounded border">
                                {institution.zeek_base_url}
                              </span>
                            </div>
                            
                            <div className="flex items-center gap-2 text-sm">
                              <MapPin className="h-4 w-4 text-green-600" />
                              <span className="font-semibold text-gray-800">Range IP:</span>
                              <span className="font-mono text-xs text-gray-700 bg-gray-100 px-2 py-1 rounded border">
                                {institution.ip_range_start} - {institution.ip_range_end}
                              </span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal/Seção para gerenciar gestores */}
      {selectedInstitution && (
        <div className="mt-6">
          <InstitutionManagers
            institutionId={selectedInstitution.id}
            institutionName={selectedInstitution.nome}
            institutionCity={selectedInstitution.cidade}
          />
          <div className="mt-4 text-center">
            <Button 
              variant="outline" 
              onClick={() => setSelectedInstitution(null)}
            >
              Fechar Gestores
            </Button>
          </div>
        </div>
      )}

      {/* Formulário de edição */}
      {editingInstitution && (
        <div className="mt-6">
          <InstitutionEditForm
            institution={editingInstitution}
            onSave={handleInstitutionUpdate}
            onCancel={() => setEditingInstitution(null)}
          />
        </div>
      )}
    </div>
  );
}
