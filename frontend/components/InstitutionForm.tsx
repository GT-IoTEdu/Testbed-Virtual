"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Building2, Save, AlertCircle } from "lucide-react";

interface InstitutionData {
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
}

export default function InstitutionForm() {
  const [formData, setFormData] = useState<InstitutionData>({
    nome: "",
    cidade: "",
    pfsense_base_url: "",
    pfsense_key: "",
    zeek_base_url: "",
    zeek_key: "",
    suricata_base_url: "",
    suricata_key: "",
    snort_base_url: "",
    snort_key: "",
    ip_range_start: "",
    ip_range_end: ""
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

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

  const handleInputChange = (field: keyof InstitutionData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // Limpar mensagens de erro/sucesso ao editar
    if (error) setError(null);
    if (success) setSuccess(null);
  };

  const validateForm = (): boolean => {
    if (!formData.nome.trim()) {
      setError("Nome da instituição é obrigatório");
      return false;
    }
    
    // Validação removida - permitir múltiplos campi da mesma instituição
    if (!formData.cidade.trim()) {
      setError("Cidade é obrigatória");
      return false;
    }
    if (!formData.pfsense_base_url.trim()) {
      setError("URL base do pfSense é obrigatória");
      return false;
    }
    if (!formData.pfsense_key.trim()) {
      setError("Chave do pfSense é obrigatória");
      return false;
    }
    if (!formData.zeek_base_url.trim()) {
      setError("URL base do Zeek é obrigatória");
      return false;
    }
    if (!formData.zeek_key.trim()) {
      setError("Chave do Zeek é obrigatória");
      return false;
    }
    if (!formData.ip_range_start.trim()) {
      setError("IP inicial do range é obrigatório");
      return false;
    }
    if (!formData.ip_range_end.trim()) {
      setError("IP final do range é obrigatório");
      return false;
    }

    // Validar formato dos IPs
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipRegex.test(formData.ip_range_start)) {
      setError("Formato do IP inicial inválido");
      return false;
    }
    if (!ipRegex.test(formData.ip_range_end)) {
      setError("Formato do IP final inválido");
      return false;
    }

    // Validar URLs
    try {
      new URL(formData.pfsense_base_url);
      new URL(formData.zeek_base_url);
      if (formData.suricata_base_url) {
        new URL(formData.suricata_base_url);
      }
      if (formData.snort_base_url) {
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
    setSuccess(null);

    try {
      const response = await makeAuthenticatedRequest(`${API_BASE}/admin/institutions`, {
        method: "POST",
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        // Tratar erro específico de nome duplicado
        if (response.status === 400 && errorData.detail && errorData.detail.includes("já existe")) {
          throw new Error(`Já existe uma instituição com o nome "${formData.nome}". Escolha outro nome.`);
        }
        throw new Error(errorData.detail || "Erro ao cadastrar instituição");
      }

      setSuccess("Instituição cadastrada com sucesso!");
      
      // Limpar formulário após sucesso
      setFormData({
        nome: "",
        cidade: "",
        pfsense_base_url: "",
        pfsense_key: "",
        zeek_base_url: "",
        zeek_key: "",
        suricata_base_url: "",
        suricata_key: "",
        snort_base_url: "",
        snort_key: "",
        ip_range_start: "",
        ip_range_end: ""
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Building2 className="h-5 w-5" />
          Cadastro de Instituição
        </CardTitle>
        <CardDescription>
          Cadastre uma nova instituição com suas configurações de rede
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Informações Básicas */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Informações Básicas</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="nome">Nome da Instituição *</Label>
                <Input
                  id="nome"
                  type="text"
                  placeholder="Ex: Unipampa"
                  value={formData.nome}
                  onChange={(e) => handleInputChange("nome", e.target.value)}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="cidade">Cidade *</Label>
                <Input
                  id="cidade"
                  type="text"
                  placeholder="Ex: Alegrete"
                  value={formData.cidade}
                  onChange={(e) => handleInputChange("cidade", e.target.value)}
                  required
                />
              </div>
            </div>
          </div>

          {/* Configurações pfSense */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Configurações pfSense</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="pfsense_url">URL Base pfSense *</Label>
                <Input
                  id="pfsense_url"
                  type="url"
                  placeholder="Ex: http://192.168.1.1"
                  value={formData.pfsense_base_url}
                  onChange={(e) => handleInputChange("pfsense_base_url", e.target.value)}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="pfsense_key">Chave pfSense *</Label>
                <Input
                  id="pfsense_key"
                  type="password"
                  placeholder="Chave de acesso"
                  value={formData.pfsense_key}
                  onChange={(e) => handleInputChange("pfsense_key", e.target.value)}
                  required
                />
              </div>
            </div>
          </div>

          {/* Configurações Zeek */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Configurações Zeek</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="zeek_url">URL Base Zeek *</Label>
                <Input
                  id="zeek_url"
                  type="url"
                  placeholder="Ex: http://192.168.1.2"
                  value={formData.zeek_base_url}
                  onChange={(e) => handleInputChange("zeek_base_url", e.target.value)}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="zeek_key">Chave Zeek *</Label>
                <Input
                  id="zeek_key"
                  type="password"
                  placeholder="Chave de acesso"
                  value={formData.zeek_key}
                  onChange={(e) => handleInputChange("zeek_key", e.target.value)}
                  required
                />
              </div>
            </div>
          </div>

          {/* Configurações Suricata */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Configurações Suricata (Opcional)</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="suricata_url">URL Base Suricata</Label>
                <Input
                  id="suricata_url"
                  type="url"
                  placeholder="Ex: http://192.168.1.128:8001"
                  value={formData.suricata_base_url || ""}
                  onChange={(e) => handleInputChange("suricata_base_url", e.target.value)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="suricata_key">Chave Suricata (API Key)</Label>
                <Input
                  id="suricata_key"
                  type="password"
                  placeholder="Chave de acesso (api_key)"
                  value={formData.suricata_key || ""}
                  onChange={(e) => handleInputChange("suricata_key", e.target.value)}
                />
              </div>
            </div>
            <p className="text-sm text-slate-400">
              Configure a URL e API key do Suricata para receber alertas em tempo real via SSE.
            </p>
          </div>

          {/* Configurações Snort */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Configurações Snort (Opcional)</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="snort_url">URL Base Snort</Label>
                <Input
                  id="snort_url"
                  type="url"
                  placeholder="Ex: http://192.168.1.128:8001"
                  value={formData.snort_base_url || ""}
                  onChange={(e) => handleInputChange("snort_base_url", e.target.value)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="snort_key">Chave Snort (API Key)</Label>
                <Input
                  id="snort_key"
                  type="password"
                  placeholder="Chave de acesso (api_key)"
                  value={formData.snort_key || ""}
                  onChange={(e) => handleInputChange("snort_key", e.target.value)}
                />
              </div>
            </div>
            <p className="text-sm text-slate-400">
              Configure a URL e API key do Snort para receber alertas em tempo real via SSE (/sse/snort).
            </p>
          </div>

          {/* Range de IPs */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Range de IPs da Instituição</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="ip_start">IP Inicial *</Label>
                <Input
                  id="ip_start"
                  type="text"
                  placeholder="Ex: 192.168.1.1"
                  value={formData.ip_range_start}
                  onChange={(e) => handleInputChange("ip_range_start", e.target.value)}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="ip_end">IP Final *</Label>
                <Input
                  id="ip_end"
                  type="text"
                  placeholder="Ex: 192.168.1.200"
                  value={formData.ip_range_end}
                  onChange={(e) => handleInputChange("ip_range_end", e.target.value)}
                  required
                />
              </div>
            </div>
          </div>

          {/* Mensagens de erro e sucesso */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert className="border-green-200 bg-green-50 text-green-800">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{success}</AlertDescription>
            </Alert>
          )}

          {/* Botão de submit */}
          <div className="flex justify-end">
            <Button 
              type="submit" 
              disabled={loading}
              className="min-w-[120px]"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Salvando...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Cadastrar
                </>
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
