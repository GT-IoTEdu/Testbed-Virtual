import { useState, useCallback } from "react";
import { toast } from "sonner";

interface User {
  id: number;
  email: string;
  nome: string;
  instituicao: string;
  institution_id: number | null;
  institution_name: string | null;
  institution_city: string | null;
  permission: "USER" | "ADMIN" | "SUPERUSER";
  ultimo_login: string | null;
  is_active: boolean;
  is_admin: boolean;
  is_manager: boolean;
  is_user: boolean;
  is_active_user: boolean;
}

interface UserStats {
  total_users: number;
  permission_stats: {
    USER: number;
    MANAGER: number;
    ADMIN: number;
  };
  active_users: number;
  inactive_users: number;
  recent_logins_30_days: number;
  generated_at: string;
}

interface AdminInfo {
  email: string;
  nome: string;
  instituicao: string;
  permission: string;
  ultimo_login: string | null;
  created_at: string | null;
}

interface AdminLoginResponse {
  access_token: string;
  token_type: string;
  admin_info: AdminInfo;
}

// Usar URL relativa para passar pelo proxy do Next.js
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

// Hook para autenticação administrativa
export const useAdminAuth = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (email: string, password: string): Promise<AdminLoginResponse | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/admin/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.trim(),
          password: password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao fazer login");
      }

      const data: AdminLoginResponse = await response.json();
      
      // Salvar token no localStorage
      localStorage.setItem("admin_token", data.access_token);
      localStorage.setItem("admin_info", JSON.stringify(data.admin_info));
      
      return data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Erro ao fazer login";
      setError(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("admin_token");
    localStorage.removeItem("admin_info");
  }, []);

  const getToken = useCallback(() => {
    return localStorage.getItem("admin_token");
  }, []);

  const getAdminInfo = useCallback((): AdminInfo | null => {
    const adminInfoStr = localStorage.getItem("admin_info");
    if (!adminInfoStr) return null;
    
    try {
      return JSON.parse(adminInfoStr);
    } catch {
      return null;
    }
  }, []);

  const isAuthenticated = useCallback(() => {
    return !!getToken();
  }, [getToken]);

  return {
    login,
    logout,
    getToken,
    getAdminInfo,
    isAuthenticated,
    loading,
    error,
  };
};

// Hook para gerenciamento de usuários
export const useUserManagement = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = useCallback(async (limit: number = 100) => {
    setLoading(true);
    setError(null);

    try {
      const url = `${API_BASE}/admin/users?limit=${limit}`;
      console.log("Buscando usuários em:", url);
      
      const response = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // Incluir cookies da sessão Google OAuth
      });

      console.log("Resposta recebida:", response.status, response.statusText);

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Sessão expirada. Faça login novamente.");
        }
        const errorText = await response.text();
        console.error("Erro na resposta:", errorText);
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { detail: errorText || `Erro ${response.status}` };
        }
        throw new Error(errorData.detail || "Erro ao carregar usuários");
      }

      const data = await response.json();
      setUsers(data.users || []);
      return data.users || [];
    } catch (error) {
      console.error("Erro ao buscar usuários:", error);
      const errorMessage = error instanceof Error ? error.message : "Erro ao carregar usuários";
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchUserStats = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/admin/users/stats`, {
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // Incluir cookies da sessão Google OAuth
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Sessão expirada. Faça login novamente.");
        }
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao carregar estatísticas");
      }

      const data = await response.json();
      setUserStats(data.statistics);
      return data.statistics;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Erro ao carregar estatísticas";
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateUserPermission = useCallback(async (userId: number, newPermission: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/admin/users/${userId}/permission`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // Incluir cookies da sessão Google OAuth
        body: JSON.stringify({
          user_id: userId,
          new_permission: newPermission,
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Sessão expirada. Faça login novamente.");
        }
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao atualizar permissão");
      }

      const data = await response.json();
      toast.success(data.message);
      
      // Atualizar lista de usuários
      await fetchUsers();
      await fetchUserStats();
      
      return data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Erro ao atualizar permissão";
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [fetchUsers, fetchUserStats]);

  const updateUserStatus = useCallback(async (userId: number, isActive: boolean) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/admin/users/${userId}/status`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // Incluir cookies da sessão Google OAuth
        body: JSON.stringify({
          user_id: userId,
          is_active: isActive,
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Sessão expirada. Faça login novamente.");
        }
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao atualizar status");
      }

      const data = await response.json();
      toast.success(data.message);
      
      // Atualizar lista de usuários
      await fetchUsers();
      await fetchUserStats();
      
      return data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Erro ao atualizar status";
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [fetchUsers, fetchUserStats]);

  return {
    users,
    userStats,
    loading,
    error,
    fetchUsers,
    fetchUserStats,
    updateUserPermission,
    updateUserStatus,
  };
};

// Hook para informações administrativas
export const useAdminInfo = () => {
  const [adminInfo, setAdminInfo] = useState<AdminInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAdminInfo = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/admin/info`, {
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // Incluir cookies da sessão Google OAuth
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Sessão expirada. Faça login novamente.");
        }
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao carregar informações administrativas");
      }

      const data = await response.json();
      setAdminInfo(data.admin_info);
      return data.admin_info;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Erro ao carregar informações";
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const validateConfig = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/admin/validate-config`, {
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // Incluir cookies da sessão Google OAuth
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Sessão expirada. Faça login novamente.");
        }
        const errorData = await response.json();
        throw new Error(errorData.detail || "Erro ao validar configuração");
      }

      const data = await response.json();
      return data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Erro ao validar configuração";
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    adminInfo,
    loading,
    error,
    fetchAdminInfo,
    validateConfig,
  };
};

// Hook para verificação de acesso administrativo
export const useAdminAccess = () => {
  const [hasAccess, setHasAccess] = useState(false);
  const [loading, setLoading] = useState(true);

  const checkAccess = useCallback(async () => {
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/admin/info`, {
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // Incluir cookies da sessão Google OAuth
      });

      if (!response.ok) {
        setHasAccess(false);
        return false;
      }

      setHasAccess(true);
      return true;
    } catch (error) {
      console.error("Erro ao verificar acesso administrativo:", error);
      setHasAccess(false);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    hasAccess,
    loading,
    checkAccess,
  };
};
