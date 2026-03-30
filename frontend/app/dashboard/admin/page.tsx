"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Shield, Settings, RefreshCw, LogOut } from "lucide-react";
import UserManagementComponent from "@/components/UserManagement";
import InstitutionForm from "@/components/InstitutionForm";
import InstitutionList from "@/components/InstitutionList";
import InstitutionEditForm from "@/components/InstitutionEditForm";

interface AdminInfo {
  email: string;
  nome: string;
  instituicao: string;
  permission: string;
  ultimo_login: string | null;
  institution_id: number | null;
  institution_name: string | null;
  institution_city: string | null;
  created_at: string | null;
}

interface UserFromStorage {
  provider: string;
  name: string;
  email: string;
  picture?: string;
  user_id: number | null;
  permission: string;
}

interface Institution {
  id: number;
  nome: string;
  cidade: string;
  pfsense_base_url: string;
  pfsense_key: string;
  zeek_base_url: string;
  zeek_key: string;
  ip_range_start: string;
  ip_range_end: string;
  is_active: boolean;
}

export default function AdminDashboardPage() {
  const [adminInfo, setAdminInfo] = useState<AdminInfo | null>(null);
  const [userFromStorage, setUserFromStorage] = useState<UserFromStorage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [myInstitution, setMyInstitution] = useState<Institution | null>(null);
  const [loadingInstitution, setLoadingInstitution] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const router = useRouter();

  // Usar URL relativa para passar pelo proxy do Next.js
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

  // Carregar dados do usuário do localStorage
  useEffect(() => {
    try {
      const authUserStr = localStorage.getItem("auth:user");
      if (authUserStr) {
        const authUser = JSON.parse(authUserStr) as UserFromStorage;
        // Verificar se é superusuário
        if (authUser.permission === "SUPERUSER") {
          setUserFromStorage(authUser);
        }
      }
    } catch (error) {
      console.error("Erro ao carregar dados do usuário do localStorage:", error);
    }
  }, []);

  // Verificar se é administrador
  useEffect(() => {
    const checkAdminAccess = async () => {
      try {
        const response = await fetch(`${API_BASE}/admin/info`);
        if (!response.ok) {
          router.push("/login");
          return;
        }
        const data = await response.json();
        setAdminInfo(data.admin_info);
      } catch (error) {
        console.error("Erro ao verificar acesso administrativo:", error);
        router.push("/login");
      }
    };

    checkAdminAccess();
  }, [API_BASE, router]);

  // Carregar dados iniciais
  useEffect(() => {
    if (adminInfo || userFromStorage) {
      setLoading(false);
    }
  }, [adminInfo, userFromStorage]);

  // Carregar dados da rede atribuída ao admin (apenas para ADMIN ou MANAGER, não SUPERUSER)
  useEffect(() => {
    const loadMyInstitution = async () => {
      // Só carregar se for ADMIN ou MANAGER (não SUPERUSER) e tiver institution_id
      // SUPERUSER nunca deve carregar dados da rede, mesmo que tenha institution_id
      if (adminInfo?.permission === "SUPERUSER" || (adminInfo?.permission !== "ADMIN" && adminInfo?.permission !== "MANAGER") || !adminInfo?.institution_id) {
        return;
      }

      setLoadingInstitution(true);
      try {
        const response = await fetch(`${API_BASE}/admin/institutions/${adminInfo.institution_id}`, {
          credentials: "include",
        });
        
        if (response.ok) {
          const data = await response.json();
          setMyInstitution(data.institution);
        } else {
          console.error("Erro ao carregar dados da rede");
        }
      } catch (error) {
        console.error("Erro ao carregar dados da rede:", error);
      } finally {
        setLoadingInstitution(false);
      }
    };

    loadMyInstitution();
  }, [adminInfo?.permission, adminInfo?.institution_id, API_BASE]);

  // Função para salvar alterações da rede
  const handleInstitutionSave = (updatedInstitution: Institution) => {
    setMyInstitution(updatedInstitution);
    setEditMode(false);
  };

  // Função para cancelar edição
  const handleInstitutionCancel = () => {
    setEditMode(false);
    // Recarregar dados da rede (apenas se for ADMIN ou MANAGER com institution_id)
    if ((adminInfo?.permission === "ADMIN" || adminInfo?.permission === "MANAGER") && adminInfo?.institution_id) {
      fetch(`${API_BASE}/admin/institutions/${adminInfo.institution_id}`, {
        credentials: "include",
      })
        .then((res) => res.json())
        .then((data) => setMyInstitution(data.institution))
        .catch((err) => console.error("Erro ao recarregar dados:", err));
    }
  };

  // Função de logout
  const handleLogout = useCallback(async () => {
    // Tentar chamar endpoint de logout no backend (ignorar erros silenciosamente)
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        credentials: "include",
      }).catch(() => {
        // Ignorar erros de rede silenciosamente
      });
    } catch {
      // Ignorar qualquer erro
    }

    // Limpar dados do localStorage
    try {
      localStorage.removeItem("auth:user");
      localStorage.removeItem("admin_token");
      localStorage.removeItem("admin_info");
    } catch {
      // Ignorar erros ao limpar localStorage
    }

    // Redirecionar para login
    router.push("/login");
  }, [API_BASE, router]);

  // Obter nome e email do administrador logado
  const adminName = userFromStorage?.name || adminInfo?.nome || "Administrador do Sistema";
  const adminEmail = userFromStorage?.email || adminInfo?.email || "";
  
  // Verificar permissão atual (prioridade: userFromStorage > adminInfo)
  const currentPermission = userFromStorage?.permission || adminInfo?.permission;
  
  // Verificar se é ADMIN ou MANAGER (não SUPERUSER) e tem rede atribuída
  // Nota: MANAGER pode existir no banco de dados antigo, mas o sistema atual usa ADMIN
  // SUPERUSER nunca deve ver o menu "Minha Rede", mesmo que tenha institution_id
  // SUPERUSER já tem a aba "Instituições" para gerenciar redes e atribuir administradores
  const isSuperUser = currentPermission === "SUPERUSER" || userFromStorage?.permission === "SUPERUSER";
  const isAdminWithNetwork = !isSuperUser
    && (currentPermission === "ADMIN" || currentPermission === "MANAGER") 
    && adminInfo?.institution_id;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Carregando dashboard administrativo...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Alert className="max-w-md">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard Administrativo</h1>
              <p className="text-gray-600 mt-1">
                Bem-vindo, {adminName} ({adminEmail})
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                onClick={() => window.location.reload()}
                disabled={loading}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Atualizar
              </Button>
              <Button
                variant="outline"
                onClick={() => router.push("/dashboard")}
              >
                Voltar ao Dashboard
              </Button>
              <Button
                variant="outline"
                onClick={handleLogout}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Sair
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className={`grid w-full ${isAdminWithNetwork && !isSuperUser ? 'grid-cols-4' : 'grid-cols-3'}`}>
            <TabsTrigger value="overview">Visão Geral</TabsTrigger>
            <TabsTrigger value="users">Usuários</TabsTrigger>
            {isAdminWithNetwork && !isSuperUser && (
              <TabsTrigger value="my-network">Minha Rede</TabsTrigger>
            )}
            <TabsTrigger value="settings">Instituições</TabsTrigger>
          </TabsList>

          {/* Visão Geral */}
          <TabsContent value="overview" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Bem-vindo ao Dashboard Administrativo</CardTitle>
                <CardDescription>
                  Sistema de gerenciamento de usuários e permissões
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <p className="text-gray-600">
                    Use as abas abaixo para gerenciar o sistema:
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 border rounded-lg">
                      <h3 className="font-semibold text-blue-600">👥 Usuários</h3>
                      <p className="text-sm text-gray-600">Gerencie permissões e visualize informações dos usuários</p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <h3 className="font-semibold text-purple-600">🏢 Instituições</h3>
                      <p className="text-sm text-gray-600">Cadastre e gerencie campus e gestores de rede</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Usuários */}
          <TabsContent value="users" className="space-y-6">
            <UserManagementComponent />
          </TabsContent>

          {/* Minha Rede - Apenas para ADMIN (não SUPERUSER) com rede atribuída */}
          {isAdminWithNetwork && !isSuperUser && (
            <TabsContent value="my-network" className="space-y-6">
              {loadingInstitution ? (
                <Card>
                  <CardContent className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin mr-2" />
                    <p className="text-gray-600">Carregando dados da rede...</p>
                  </CardContent>
                </Card>
              ) : myInstitution ? (
                editMode ? (
                  <InstitutionEditForm
                    institution={myInstitution}
                    onSave={handleInstitutionSave}
                    onCancel={handleInstitutionCancel}
                  />
                ) : (
                  <Card>
                    <CardHeader>
                      <div className="flex justify-between items-center">
                        <div>
                          <CardTitle>Minha Rede</CardTitle>
                          <CardDescription>
                            {myInstitution.nome} - {myInstitution.cidade}
                          </CardDescription>
                        </div>
                        <Button onClick={() => setEditMode(true)}>
                          Editar Rede
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="text-sm font-medium text-gray-500">Nome</label>
                            <p className="text-gray-900">{myInstitution.nome}</p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-gray-500">Cidade</label>
                            <p className="text-gray-900">{myInstitution.cidade}</p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-gray-500">URL Base pfSense</label>
                            <p className="text-gray-900 break-all">{myInstitution.pfsense_base_url}</p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-gray-500">URL Base Zeek</label>
                            <p className="text-gray-900 break-all">{myInstitution.zeek_base_url}</p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-gray-500">IP Inicial</label>
                            <p className="text-gray-900">{myInstitution.ip_range_start}</p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-gray-500">IP Final</label>
                            <p className="text-gray-900">{myInstitution.ip_range_end}</p>
                          </div>
                          <div>
                            <label className="text-sm font-medium text-gray-500">Status</label>
                            <p className={`inline-block px-2 py-1 rounded text-sm ${myInstitution.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                              {myInstitution.is_active ? 'Ativa' : 'Inativa'}
                            </p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              ) : (
                <Card>
                  <CardContent className="py-8">
                    <Alert>
                      <AlertDescription>
                        Não foi possível carregar os dados da rede atribuída.
                      </AlertDescription>
                    </Alert>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          )}

          {/* Instituições */}
          <TabsContent value="settings" className="space-y-6">
            <InstitutionForm />
            <InstitutionList />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
