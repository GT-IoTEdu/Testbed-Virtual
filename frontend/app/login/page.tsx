"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Wifi, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  // Novo estado para controlar se o login CAFe está habilitado
  const [cafeEnabled, setCafeEnabled] = useState(false);
  const popupRef = useRef<Window | null>(null);
  const gotMessageRef = useRef(false);
  const pollTimerRef = useRef<number | null>(null);
  const timeoutRef = useRef<number | null>(null);

  async function handleGoogleLogin() {
    setIsLoading(true);
    try {
      console.log("Iniciando login com Google...");

      // Verifica se o backend está acessível antes de abrir o popup
      try {
        const response = await fetch("http://localhost:8000/api/auth/health", {
          method: "HEAD",
          mode: "no-cors",
        });
        console.log("Backend está acessível");
      } catch (err) {
        console.error("Erro ao verificar backend:", err);
        alert(
          "Servidor backend não está acessível. Verifique se está rodando em http://localhost:8000"
        );
        setIsLoading(false);
        return;
      }

      // Abre uma nova janela para o fluxo OAuth
      const popup = window.open(
        "http://localhost:8000/api/auth/google/login",
        "googleLogin",
        "width=500,height=600"
      );

      if (!popup) {
        console.error("Popup bloqueado pelo navegador!");
        alert("Permita popups para este site para fazer login com Google");
        setIsLoading(false);
        return;
      }

      console.log("Popup aberto, aguardando autenticação...");
      popupRef.current = popup;

      // Listener para receber mensagem do popup
      const onMessage = function onMessage(event: MessageEvent) {
        console.log("Mensagem recebida:", event.data);
        console.log("Origem da mensagem:", event.origin);

        if (event.data?.provider === "google") {
          gotMessageRef.current = true;
          setIsLoading(false);
          console.log("Usuário autenticado:", event.data);
          window.removeEventListener("message", onMessage);

          // Persistir dados básicos com segurança no navegador e redirecionar sem querystring
          try {
            const payload = {
              provider: "google",
              name: event.data.name || "",
              email: event.data.email || "",
              picture: event.data.picture || "",
              user_id: event.data.user_id || null,
              permission: event.data.permission || "USER",
            };
            window.localStorage.setItem("auth:user", JSON.stringify(payload));
          } catch (e) {
            console.warn("Falha ao salvar dados do usuário no localStorage:", e);
          }
          router.push("/dashboard");
        }

        if (event.data?.error) {
          setIsLoading(false);
          console.error("Erro no login Google:", event.data.error);
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
          pollTimerRef.current = null;
          if (!gotMessageRef.current) {
            console.warn("Popup fechado sem finalizar login.");
            setIsLoading(false);
            window.removeEventListener("message", onMessage);
          }
        }
      }, 500);

      // Timeout de segurança: encerra loading se nada acontecer em 60s
      if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
      // @ts-ignore
      timeoutRef.current = window.setTimeout(() => {
        if (!gotMessageRef.current) {
          console.warn("Tempo de login excedido.");
          try { popupRef.current?.close(); } catch {}
          setIsLoading(false);
          window.removeEventListener("message", onMessage);
          alert("Não foi possível completar o login. Tente novamente.");
        }
      }, 60000);
    } catch (err) {
      setIsLoading(false);
      console.error("Erro ao iniciar login Google:", err);
      if (err instanceof Error) {
        alert(`Erro ao iniciar login: ${err.message}`);
      } else {
        alert("Erro ao iniciar login Google.");
      }
    }
  }

  useEffect(() => {
    return () => {
      if (pollTimerRef.current) {
        window.clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
      {/* Header com navegação de volta para a landing page */}
      <header className="px-6 py-4 flex items-center">
        <Link
          href="/"
          className="flex items-center text-blue-400 hover:text-blue-300 transition-colors"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          <span>Voltar</span>
        </Link>
      </header>

      {/* Conteúdo principal centralizado */}
      <main className="flex-1 flex flex-col items-center justify-center p-6">
        <div className="text-center mb-10">
          {/* Removido o h1 com "Login - GT-IoT EDU" */}
          <div className="flex items-center justify-center space-x-3">
            <div className="relative">
              <Wifi className="h-10 w-10 text-blue-400" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
            </div>
            <span className="text-4xl font-bold text-blue-400">GT IoT EDU</span>
          </div>
        </div>

        {/* Login Options */}
        <div className="w-full max-w-md space-y-6">
          {/* CAFe Login */}
          <Card
            className={`border border-slate-700 bg-slate-800/30 p-4 text-center ${
              !cafeEnabled ? "cursor-not-allowed opacity-70" : ""
            }`}
          >
            <div className="mb-4">
              <Image
                src="/images/cafe-logo.png"
                alt="CAFe - Comunidade Acadêmica Federada"
                width={240}
                height={80}
                className="mx-auto"
              />
            </div>
            <Button
              disabled={!cafeEnabled}
              className={`w-full text-white ${
                cafeEnabled
                  ? "bg-blue-600 hover:bg-blue-700"
                  : "bg-blue-600/50 hover:bg-blue-600/50 cursor-not-allowed"
              }`}
              onClick={() => {
                if (cafeEnabled) {
                  // Lógica para autenticação com CAFe
                  alert("Redirecionando para autenticação CAFe...");
                }
              }}
            >
              Clique aqui para acessar pelo login institucional
            </Button>
            {!cafeEnabled && (
              <p className="text-xs text-slate-400 mt-2">
                Opção desabilitada temporariamente
              </p>
            )}

            {/* Botão para alternar estado (apenas para testes/desenvolvimento)
            <button 
              onClick={(e) => {
                e.preventDefault();
                setCafeEnabled(!cafeEnabled);
              }}
              className="text-xs text-slate-500 mt-4 hover:text-blue-400 transition-colors underline"
            >
              {cafeEnabled ? "Desabilitar" : "Habilitar"} login CAFe (apenas para testes)
            </button> */}
          </Card>

          {/* Google Login */}
          <Card className="border border-slate-700 bg-slate-800/30 p-4 text-center">
            <h2 className="text-xl font-semibold text-white mb-4">
              Login com Google
            </h2>
            <Button
              className="w-full bg-white hover:bg-gray-100 text-slate-800 flex items-center justify-center space-x-2"
              onClick={handleGoogleLogin}
              disabled={isLoading}
            >
              {!isLoading && (
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    fill="#4285F4"
                  />
                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />
                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>
              )}
              {isLoading ? "Conectando..." : "Continuar com o Google"}
            </Button>
            {isLoading && (
              <div className="mt-4 space-y-2">
                <p className="text-sm text-slate-300">Se o popup não abriu, use as opções abaixo:</p>
                <div className="flex gap-2 justify-center">
                  <Button
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                    onClick={() => {
                      try {
                        const p = window.open(
                          "http://localhost:8000/api/auth/google/login",
                          "googleLogin",
                          "width=500,height=600"
                        );
                        if (p) {
                          p.focus();
                          popupRef.current = p;
                        }
                      } catch {}
                    }}
                  >
                    Reabrir popup
                  </Button>
                  <Button
                    className="bg-slate-600 hover:bg-slate-700 text-white"
                    onClick={() => {
                      try { popupRef.current?.close(); } catch {}
                      if (pollTimerRef.current) {
                        window.clearInterval(pollTimerRef.current);
                        pollTimerRef.current = null;
                      }
                      if (timeoutRef.current) {
                        window.clearTimeout(timeoutRef.current);
                        timeoutRef.current = null;
                      }
                      setIsLoading(false);
                    }}
                  >
                    Cancelar
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Footer */}
        <div className="mt-10 text-center">
          <Link href="#" className="text-blue-400 hover:text-blue-300 text-sm">
            Aviso de Privacidade
          </Link>
          <p className="text-xs text-slate-500 mt-2">
            © 2025 GT-IoTEDU Todos os direitos reservados.
          </p>
        </div>
      </main>
    </div>
  );
}
