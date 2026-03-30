"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Trash2, UserPlus, Users } from "lucide-react";

interface Manager {
  id: number;
  email: string;
  nome: string;
  instituicao: string;
  permission: string;
  is_active: boolean;
  ultimo_login: string;
}

interface InstitutionManagersProps {
  institutionId: number;
  institutionName: string;
  institutionCity: string;
}

export default function InstitutionManagers({ 
  institutionId, 
  institutionName, 
  institutionCity 
}: InstitutionManagersProps) {
  const [managers, setManagers] = useState<Manager[]>([]);
  const [availableManagers, setAvailableManagers] = useState<Manager[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedManagerId, setSelectedManagerId] = useState<string>("");

  // Usar URL relativa para passar pelo proxy do Next.js
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

  const makeAuthenticatedRequest = async (url: string, options: RequestInit = {}) => {
    // O usuário já está autenticado via Google OAuth
    // As requisições usam a sessão do navegador (cookies)
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      credentials: "include", // Incluir cookies da sessão
    });

    return response;
  };

  const fetchManagers = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await makeAuthenticatedRequest(`${API_BASE}/admin/institutions/${institutionId}/managers`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Erro ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      setManagers(data.managers || []);
    } catch (err) {
      console.error('Erro ao buscar administradores:', err);
      setError(err instanceof Error ? err.message : "Erro inesperado");
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableManagers = async () => {
    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/admin/users/managers/available`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Erro ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      setAvailableManagers(data.available_managers || []);
    } catch (err) {
      console.error('Erro ao buscar administradores disponíveis:', err);
    }
  };

  const addManager = async () => {
    if (!selectedManagerId) {
      setError("Selecione um administrador para adicionar");
      return;
    }

    try {
      setError(null);
      setSuccess(null);

      const response = await makeAuthenticatedRequest(`${API_BASE}/admin/institutions/${institutionId}/managers`, {
        method: "POST",
        body: JSON.stringify({
          user_id: parseInt(selectedManagerId)
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao adicionar gestor");
      }

      const data = await response.json();
      setSuccess(data.message);
      setSelectedManagerId("");
      
      // Recarregar listas
      await fetchManagers();
      await fetchAvailableManagers();
    } catch (err) {
      console.error('Erro ao adicionar administrador:', err);
      setError(err instanceof Error ? err.message : "Erro inesperado");
    }
  };

  const removeManager = async (managerId: number, managerName: string) => {
    if (!confirm(`Tem certeza que deseja remover o administrador "${managerName}" deste campus?`)) {
      return;
    }

    try {
      setError(null);
      setSuccess(null);

      const response = await makeAuthenticatedRequest(`${API_BASE}/admin/institutions/${institutionId}/managers/${managerId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao remover gestor");
      }

      const data = await response.json();
      setSuccess(data.message);
      
      // Recarregar listas
      await fetchManagers();
      await fetchAvailableManagers();
    } catch (err) {
      console.error('Erro ao remover administrador:', err);
      setError(err instanceof Error ? err.message : "Erro inesperado");
    }
  };

  useEffect(() => {
    fetchManagers();
    fetchAvailableManagers();
  }, [institutionId]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          Administradores do Campus
        </CardTitle>
        <CardDescription>
          Gerenciar administradores de rede para {institutionName} - {institutionCity}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert>
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        )}

        {/* Adicionar Administrador */}
        <div className="flex gap-2 items-end">
          <div className="flex-1">
            <label className="text-sm font-medium">Adicionar Administrador:</label>
            <Select value={selectedManagerId} onValueChange={setSelectedManagerId}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione um administrador disponível" />
              </SelectTrigger>
              <SelectContent>
                {availableManagers.map((manager) => (
                  <SelectItem key={manager.id} value={manager.id.toString()}>
                    {manager.nome} ({manager.email})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button 
            onClick={addManager} 
            disabled={!selectedManagerId || loading}
            className="flex items-center gap-2"
          >
            <UserPlus className="h-4 w-4" />
            Adicionar
          </Button>
        </div>

        {/* Lista de Administradores */}
        <div>
          <h3 className="text-lg font-semibold mb-3">
            Administradores Ativos ({managers.length})
          </h3>
          
          {loading ? (
            <div className="text-center py-4">Carregando administradores...</div>
          ) : managers.length === 0 ? (
            <div className="text-center py-4 text-muted-foreground">
              Nenhum administrador atribuído a este campus
            </div>
          ) : (
            <div className="space-y-2">
              {managers.map((manager) => (
                <div 
                  key={manager.id} 
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{manager.nome}</span>
                      <Badge variant="secondary">ADMIN</Badge>
                      {manager.is_active ? (
                        <Badge variant="default">Ativo</Badge>
                      ) : (
                        <Badge variant="destructive">Inativo</Badge>
                      )}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {manager.email}
                    </div>
                    {manager.ultimo_login && (
                      <div className="text-xs text-muted-foreground">
                        Último login: {new Date(manager.ultimo_login).toLocaleString('pt-BR')}
                      </div>
                    )}
                  </div>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => removeManager(manager.id, manager.nome)}
                    className="flex items-center gap-1"
                  >
                    <Trash2 className="h-4 w-4" />
                    Remover
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Administradores Disponíveis */}
        {availableManagers.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold mb-3">
              Administradores Disponíveis ({availableManagers.length})
            </h3>
            <div className="text-sm text-muted-foreground">
              Estes administradores não estão atribuídos a nenhum campus e podem ser adicionados.
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
