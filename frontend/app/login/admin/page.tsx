"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Shield, ArrowLeft, AlertCircle } from "lucide-react";
import { toast } from "sonner";

export default function AdminLoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const popupRef = useRef<Window | null>(null);
  const gotMessageRef = useRef(false);
  const pollTimerRef = useRef<number | null>(null);
  const timeoutRef = useRef<number | null>(null);

  // Usar URL relativa para passar pelo proxy do Next.js
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

  useEffect(() => {
    // Limpar intervalos ao desmontar
    return () => {
      if (pollTimerRef.current) {
        window.clearInterval(pollTimerRef.current);
      }
      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  async function handleGoogleLogin() {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log("Iniciando login administrativo com Google...");

      // Verifica se o backend está acessível antes de abrir o popup
      try {
        const response = await fetch(`${API_BASE}/auth/health`, {
          method: "HEAD",
          mode: "no-cors",
        });
        console.log("Backend está acessível");
      } catch (err) {
        console.error("Erro ao verificar backend:", err);
        setError("Servidor backend não está acessível. Verifique se está rodando.");
        setIsLoading(false);
        toast.error("Servidor backend não está acessível");
        return;
      }

      // Abre uma nova janela para o fluxo OAuth
      const popup = window.open(
        `${API_BASE}/auth/google/login`,
        "googleLogin",
        "width=500,height=600"
      );

      if (!popup) {
        console.error("Popup bloqueado pelo navegador!");
        setError("Permita popups para este site para fazer login com Google");
        setIsLoading(false);
        toast.error("Permita popups para este site");
        return;
      }

      console.log("Popup aberto, aguardando autenticação...");
      popupRef.current = popup;
      gotMessageRef.current = false;

      // Listener para receber mensagem do popup
      const onMessage = function onMessage(event: MessageEvent) {
        console.log("Mensagem recebida:", event.data);
        console.log("Origem da mensagem:", event.origin);

        if (event.data?.provider === "google") {
          gotMessageRef.current = true;
          setIsLoading(false);
          console.log("Usuário autenticado:", event.data);
          window.removeEventListener("message", onMessage);

          const email = event.data.email;
          const permission = event.data.permission;

          // Verificar se o usuário é administrador - fazer verificação adicional no backend
          try {
            // Verificar no backend se o email corresponde ao admin configurado
            const verifyResponse = await fetch(`${API_BASE}/admin/verify`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              credentials: "include",
              body: JSON.stringify({ email: email }),
            });

            const verifyData = await verifyResponse.json();
            const isAdmin = verifyData.is_admin === true || permission === "SUPERUSER";

            if (isAdmin) {
              // Persistir dados no localStorage com permissão SUPERUSER garantida
              const payload = {
                provider: "google",
                name: event.data.name || "",
                email: email,
                picture: event.data.picture || "",
                user_id: event.data.user_id || null,
                permission: "SUPERUSER", // Garantir que sempre será SUPERUSER
              };
              window.localStorage.setItem("auth:user", JSON.stringify(payload));
              toast.success("Login administrativo realizado com sucesso!");
              router.push("/dashboard/admin");
            } else {
              // Usuário não é admin
              setError("Este email não está configurado como administrador. Verifique a configuração ADMIN_ACCESS no servidor.");
              toast.error("Acesso negado: Email não é administrador");
            }
          } catch (e) {
            console.error("Erro ao verificar acesso administrativo:", e);
            setError("Erro ao verificar acesso administrativo. Tente novamente.");
            toast.error("Erro ao verificar acesso administrativo");
          }
        }

        if (event.data?.error) {
          setIsLoading(false);
          console.error("Erro no login Google:", event.data.error);
          setError(event.data.error || "Erro ao fazer login");
          toast.error(event.data.error || "Erro ao fazer login");
          window.removeEventListener("message", onMessage);
        }
      };
      window.addEventListener("message", onMessage, { once: true });

      // Poll fechamento do popup
      if (pollTimerRef.current) window.clearInterval(pollTimerRef.current);
      // @ts-ignore - setInterval retorna number no browser
      pollTimerRef.current = window.setInterval(() => {
        if (!popupRef.current || popupRef.current.closed) {
          window.clearInterval(pollTimerRef.current!);
          if (!gotMessageRef.current) {
            setIsLoading(false);
            console.log("Popup fechado sem autenticação");
          }
        }
      }, 500);

      // Timeout de segurança (5 minutos)
      if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
      // @ts-ignore - setTimeout retorna number no browser
      timeoutRef.current = window.setTimeout(() => {
        if (popupRef.current && !popupRef.current.closed) {
          popupRef.current.close();
        }
        if (!gotMessageRef.current) {
          setIsLoading(false);
          setError("Tempo limite excedido. Tente novamente.");
          toast.error("Tempo limite excedido");
        }
      }, 5 * 60 * 1000);
    } catch (error) {
      console.error("Erro no login administrativo:", error);
      const errorMessage = error instanceof Error ? error.message : "Erro ao fazer login";
      setError(errorMessage);
      setIsLoading(false);
      toast.error(errorMessage);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-red-100 rounded-full flex items-center justify-center">
            <Shield className="h-6 w-6 text-red-600" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Acesso Administrativo
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Faça login com sua conta Google para acessar o painel administrativo
          </p>
        </div>

        {/* Login Card */}
        <Card>
          <CardHeader>
            <CardTitle>Login Administrativo</CardTitle>
            <CardDescription>
              Use sua conta Google configurada como administrador
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button
                type="button"
                onClick={handleGoogleLogin}
                className="w-full"
                disabled={isLoading}
                variant="outline"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Fazendo login...
                  </>
                ) : (
                  <>
                    <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                      <path
                        fill="currentColor"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="currentColor"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="currentColor"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      />
                      <path
                        fill="currentColor"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      />
                    </svg>
                    Entrar com Google
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center space-y-2">
          <Button
            variant="ghost"
            onClick={() => router.push("/login")}
            className="text-sm text-gray-600 hover:text-gray-900"
            disabled={isLoading}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Voltar ao login normal
          </Button>
          
          <p className="text-xs text-gray-500">
            Acesso restrito a administradores do sistema
          </p>
          <p className="text-xs text-gray-400">
            O email do administrador deve estar configurado em ADMIN_ACCESS
          </p>
        </div>
      </div>
    </div>
  );
}
