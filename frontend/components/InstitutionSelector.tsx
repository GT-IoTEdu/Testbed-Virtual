"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Building2, MapPin, CheckCircle2 } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Institution {
  id: number;
  nome: string;
  cidade: string;
}

interface InstitutionSelectorProps {
  onInstitutionSelected?: () => void;
}

export default function InstitutionSelector({ onInstitutionSelected }: InstitutionSelectorProps) {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [selectedInstitutionId, setSelectedInstitutionId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

  useEffect(() => {
    fetchInstitutions();
  }, []);

  const fetchInstitutions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE}/auth/institutions`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { detail: errorText || `Erro ${response.status}` };
        }
        throw new Error(errorData.detail || `Erro ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      setInstitutions(data.institutions || []);
    } catch (err) {
      console.error("Erro ao buscar instituições:", err);
      const errorMsg = err instanceof Error ? err.message : "Erro inesperado ao carregar instituições";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!selectedInstitutionId) {
      setError("Por favor, selecione uma instituição");
      return;
    }

    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      const response = await fetch(`${API_BASE}/auth/me/institution`, {
        method: "PUT",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          institution_id: selectedInstitutionId,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { detail: errorText || `Erro ${response.status}` };
        }
        throw new Error(errorData.detail || `Erro ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      setSuccess(true);

      // Atualizar localStorage com a nova instituição
      const authUserStr = localStorage.getItem("auth:user");
      if (authUserStr) {
        const authUser = JSON.parse(authUserStr);
        authUser.institution_id = data.institution_id;
        authUser.institution_name = data.institution_name;
        authUser.institution_city = data.institution_city;
        localStorage.setItem("auth:user", JSON.stringify(authUser));
      }

      // Aguardar um pouco para mostrar a mensagem de sucesso
      setTimeout(() => {
        if (onInstitutionSelected) {
          onInstitutionSelected();
        }
        // Recarregar a página para atualizar os dados
        window.location.reload();
      }, 1000);
    } catch (err) {
      console.error("Erro ao salvar instituição:", err);
      const errorMsg = err instanceof Error ? err.message : "Erro inesperado ao salvar instituição";
      setError(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <Card className="w-full max-w-md mx-4">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center space-y-4">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <p className="text-sm text-gray-600">Carregando instituições...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-blue-600" />
            Selecione sua Instituição
          </CardTitle>
          <CardDescription>
            Para continuar, é necessário selecionar a instituição à qual você pertence.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert className="border-green-500 bg-green-50">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                Instituição selecionada com sucesso!
              </AlertDescription>
            </Alert>
          )}

          {institutions.length === 0 ? (
            <Alert>
              <AlertDescription>
                Nenhuma instituição disponível no momento. Entre em contato com o administrador.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="institution" className="text-sm font-medium">
                  Instituição
                </label>
                <Select
                  value={selectedInstitutionId?.toString() || ""}
                  onValueChange={(value) => setSelectedInstitutionId(parseInt(value))}
                >
                  <SelectTrigger id="institution">
                    <SelectValue placeholder="Selecione uma instituição" />
                  </SelectTrigger>
                  <SelectContent>
                    {institutions.map((inst) => (
                      <SelectItem key={inst.id} value={inst.id.toString()}>
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 text-gray-500" />
                          <span className="font-medium">{inst.nome}</span>
                          <span className="text-sm text-gray-500">- {inst.cidade}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button
                onClick={handleSave}
                disabled={!selectedInstitutionId || saving || success}
                className="w-full"
                size="lg"
              >
                {saving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Salvando...
                  </>
                ) : success ? (
                  <>
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    Salvo!
                  </>
                ) : (
                  "Confirmar e Continuar"
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

