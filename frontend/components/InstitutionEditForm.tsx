"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Save, X } from "lucide-react";

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
  snort_base_url?: string;
  snort_key?: string;
  ip_range_start: string;
  ip_range_end: string;
  is_active: boolean;
}

interface InstitutionEditFormProps {
  institution: Institution;
  onSave: (updatedInstitution: Institution) => void;
  onCancel: () => void;
}

export default function InstitutionEditForm({ 
  institution, 
  onSave, 
  onCancel 
}: InstitutionEditFormProps) {
  const [formData, setFormData] = useState({
    nome: institution.nome,
    cidade: institution.cidade,
    pfsense_base_url: institution.pfsense_base_url,
    pfsense_key: institution.pfsense_key,
    zeek_base_url: institution.zeek_base_url,
    zeek_key: institution.zeek_key,
    suricata_base_url: institution.suricata_base_url || "",
    suricata_key: institution.suricata_key || "",
    snort_base_url: institution.snort_base_url || "",
    snort_key: institution.snort_key || "",
    ip_range_start: institution.ip_range_start,
    ip_range_end: institution.ip_range_end,
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const validateForm = () => {
    if (!formData.nome.trim()) {
      setError("Nome da instituição é obrigatório");
      return false;
    }
    if (!formData.cidade.trim()) {
      setError("Cidade é obrigatória");
      return false;
    }
    if (!formData.pfsense_base_url.trim()) {
      setError("URL do pfSense é obrigatória");
      return false;
    }
    if (!formData.pfsense_key.trim()) {
      setError("Chave do pfSense é obrigatória");
      return false;
    }
    if (!formData.zeek_base_url.trim()) {
      setError("URL do Zeek é obrigatória");
      return false;
    }
    if (!formData.zeek_key.trim()) {
      setError("Chave do Zeek é obrigatória");
      return false;
    }
    if (!formData.ip_range_start.trim()) {
      setError("IP inicial é obrigatório");
      return false;
    }
    if (!formData.ip_range_end.trim()) {
      setError("IP final é obrigatório");
      return false;
    }

    // Validar formato de IP
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipRegex.test(formData.ip_range_start)) {
      setError("Formato de IP inicial inválido");
      return false;
    }
    if (!ipRegex.test(formData.ip_range_end)) {
      setError("Formato de IP final inválido");
      return false;
    }

    // Validar URLs (Suricata é opcional, mas se preenchido deve ser válido)
    try {
      new URL(formData.pfsense_base_url);
      new URL(formData.zeek_base_url);
      if (formData.suricata_base_url && formData.suricata_base_url.trim()) {
        new URL(formData.suricata_base_url);
      }
      if (formData.snort_base_url && formData.snort_base_url.trim()) {
        new URL(formData.snort_base_url);
      }
    } catch {
      setError("URLs devem ter formato válido (ex: http://192.168.1.1)");
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/admin/institutions/${institution.id}`, {
        method: "PUT",
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao atualizar instituição");
      }

      const data = await response.json();
      onSave(data.institution);
    } catch (err) {
      console.error('Erro ao atualizar instituição:', err);
      setError(err instanceof Error ? err.message : "Erro inesperado");
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Editar Instituição</CardTitle>
        <CardDescription>
          Atualize as informações de {institution.nome} - {institution.cidade}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="nome">Nome da Instituição</Label>
              <Input
                id="nome"
                value={formData.nome}
                onChange={(e) => handleInputChange("nome", e.target.value)}
                placeholder="Ex: Unipampa"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="cidade">Cidade</Label>
              <Input
                id="cidade"
                value={formData.cidade}
                onChange={(e) => handleInputChange("cidade", e.target.value)}
                placeholder="Ex: Alegrete"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="pfsense_base_url">URL Base pfSense</Label>
            <Input
              id="pfsense_base_url"
              value={formData.pfsense_base_url}
              onChange={(e) => handleInputChange("pfsense_base_url", e.target.value)}
              placeholder="Ex: http://192.168.1.1"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="pfsense_key">Chave pfSense</Label>
            <Input
              id="pfsense_key"
              value={formData.pfsense_key}
              onChange={(e) => handleInputChange("pfsense_key", e.target.value)}
              placeholder="Chave de acesso ao pfSense"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="zeek_base_url">URL Base Zeek</Label>
            <Input
              id="zeek_base_url"
              value={formData.zeek_base_url}
              onChange={(e) => handleInputChange("zeek_base_url", e.target.value)}
              placeholder="Ex: http://192.168.1.2"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="zeek_key">Chave Zeek</Label>
            <Input
              id="zeek_key"
              value={formData.zeek_key}
              onChange={(e) => handleInputChange("zeek_key", e.target.value)}
              placeholder="Chave de acesso ao Zeek"
              required
            />
          </div>

          {/* Configurações Suricata (Opcional) */}
          <div className="space-y-4 border-t pt-4">
            <h3 className="text-lg font-medium">Configurações Suricata (Opcional)</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="suricata_base_url">URL Base Suricata</Label>
                <Input
                  id="suricata_base_url"
                  type="url"
                  value={formData.suricata_base_url}
                  onChange={(e) => handleInputChange("suricata_base_url", e.target.value)}
                  placeholder="Ex: http://192.168.1.128:8001"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="suricata_key">Chave Suricata (API Key)</Label>
                <Input
                  id="suricata_key"
                  type="password"
                  value={formData.suricata_key}
                  onChange={(e) => handleInputChange("suricata_key", e.target.value)}
                  placeholder="Chave de acesso (api_key)"
                />
              </div>
            </div>
            <p className="text-sm text-slate-500">
              Configure a URL e API key do Suricata para receber alertas em tempo real via SSE.
            </p>
          </div>

          {/* Configurações Snort (Opcional) */}
          <div className="space-y-4 border-t pt-4">
            <h3 className="text-lg font-medium">Configurações Snort (Opcional)</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="snort_base_url">URL Base Snort</Label>
                <Input
                  id="snort_base_url"
                  type="url"
                  value={formData.snort_base_url}
                  onChange={(e) => handleInputChange("snort_base_url", e.target.value)}
                  placeholder="Ex: http://192.168.1.128:8001"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="snort_key">Chave Snort (API Key)</Label>
                <Input
                  id="snort_key"
                  type="password"
                  value={formData.snort_key}
                  onChange={(e) => handleInputChange("snort_key", e.target.value)}
                  placeholder="Chave de acesso (api_key)"
                />
              </div>
            </div>
            <p className="text-sm text-slate-500">
              Configure a URL e API key do Snort para receber alertas em tempo real via SSE (/sse/snort).
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="ip_range_start">IP Inicial</Label>
              <Input
                id="ip_range_start"
                value={formData.ip_range_start}
                onChange={(e) => handleInputChange("ip_range_start", e.target.value)}
                placeholder="Ex: 192.168.1.1"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="ip_range_end">IP Final</Label>
              <Input
                id="ip_range_end"
                value={formData.ip_range_end}
                onChange={(e) => handleInputChange("ip_range_end", e.target.value)}
                placeholder="Ex: 192.168.1.200"
                required
              />
            </div>
          </div>

          <div className="flex gap-2 pt-4">
            <Button type="submit" disabled={loading} className="flex items-center gap-2">
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              {loading ? "Salvando..." : "Salvar Alterações"}
            </Button>
            
            <Button type="button" variant="outline" onClick={onCancel}>
              <X className="h-4 w-4 mr-2" />
              Cancelar
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
