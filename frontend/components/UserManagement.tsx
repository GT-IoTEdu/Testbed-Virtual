"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Users, Shield, Search, RefreshCw, UserPlus, UserMinus, Filter } from "lucide-react";
import { toast } from "sonner";
import { useUserManagement } from "@/hooks/useAdmin";

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

export default function UserManagementComponent() {
  const { users, userStats, loading, error, fetchUsers, fetchUserStats, updateUserPermission, updateUserStatus } = useUserManagement();
  const [searchTerm, setSearchTerm] = useState("");
  const [permissionFilter, setPermissionFilter] = useState<string>("all");
  const [updatingUser, setUpdatingUser] = useState<number | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      await Promise.all([
        fetchUsers(100),
        fetchUserStats()
      ]);
    } catch (error) {
      console.error("Erro ao carregar dados:", error);
    }
  };

  const handleUpdatePermission = async (userId: number, newPermission: string) => {
    setUpdatingUser(userId);
    try {
      await updateUserPermission(userId, newPermission);
    } catch (error) {
      console.error("Erro ao atualizar permissão:", error);
    } finally {
      setUpdatingUser(null);
    }
  };

  const handleUpdateStatus = async (userId: number, isActive: boolean) => {
    setUpdatingUser(userId);
    try {
      await updateUserStatus(userId, isActive);
    } catch (error) {
      console.error("Erro ao atualizar status:", error);
    } finally {
      setUpdatingUser(null);
    }
  };

  const getPermissionBadgeVariant = (permission: string) => {
    switch (permission) {
      case "SUPERUSER":
        return "destructive";
      case "ADMIN":
        return "default";
      case "USER":
        return "secondary";
      default:
        return "outline";
    }
  };

  const getPermissionIcon = (permission: string) => {
    switch (permission) {
      case "SUPERUSER":
        return <Shield className="h-4 w-4" />;
      case "ADMIN":
        return <Users className="h-4 w-4" />;
      case "USER":
        return <UserPlus className="h-4 w-4" />;
      default:
        return null;
    }
  };

  const getStatusBadgeVariant = (isActive: boolean) => {
    return isActive ? "default" : "secondary";
  };

  const getStatusIcon = (isActive: boolean) => {
    return isActive ? (
      <div className="h-2 w-2 bg-green-500 rounded-full" />
    ) : (
      <div className="h-2 w-2 bg-red-500 rounded-full" />
    );
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.nome?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.instituicao?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.institution_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.institution_city?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesPermission = permissionFilter === "all" || user.permission === permissionFilter;
    
    return matchesSearch && matchesPermission;
  });

  return (
    <div className="space-y-6">
      {/* Estatísticas Rápidas */}
      {userStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{userStats.total_users}</div>
              <p className="text-xs text-muted-foreground">Usuários</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Usuários</CardTitle>
              <UserPlus className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{userStats.permission_stats.USER}</div>
              <p className="text-xs text-muted-foreground">Comuns</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Gestores</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{userStats.permission_stats.MANAGER}</div>
              <p className="text-xs text-muted-foreground">Com acesso</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Administradores</CardTitle>
              <Shield className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{userStats.permission_stats.ADMIN}</div>
              <p className="text-xs text-muted-foreground">Com controle</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Controles */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Gerenciamento de Usuários</span>
            <Button
              variant="outline"
              size="sm"
              onClick={loadData}
              disabled={loading}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Atualizar
            </Button>
          </CardTitle>
          <CardDescription>
            Gerencie permissões e visualize informações dos usuários
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Filtros */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Buscar usuários..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={permissionFilter} onValueChange={setPermissionFilter}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Filtrar por permissão" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas as permissões</SelectItem>
                <SelectItem value="USER">Usuários</SelectItem>
                <SelectItem value="ADMIN">Administradores</SelectItem>
                <SelectItem value="SUPERUSER">Superusuários</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Tabela de Usuários */}
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Usuário</TableHead>
                  <TableHead>Instituição</TableHead>
                  <TableHead>Cidade</TableHead>
                  <TableHead>Permissão</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Último Login</TableHead>
                  <TableHead>Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
                      Carregando usuários...
                    </TableCell>
                  </TableRow>
                ) : error ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      <Alert variant="destructive">
                        <AlertDescription>{error}</AlertDescription>
                      </Alert>
                    </TableCell>
                  </TableRow>
                ) : filteredUsers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                      Nenhum usuário encontrado
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredUsers.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{user.nome || "Nome não informado"}</div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        {user.institution_name || user.instituicao || "Não informado"}
                      </TableCell>
                      <TableCell>
                        {user.institution_city ? user.institution_city : "-"}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getPermissionBadgeVariant(user.permission)}>
                          {getPermissionIcon(user.permission)}
                          <span className="ml-1">{user.permission}</span>
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(user.is_active)}>
                          {getStatusIcon(user.is_active)}
                          <span className="ml-1">{user.is_active ? "Ativo" : "Inativo"}</span>
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {user.ultimo_login ? (
                          new Date(user.ultimo_login).toLocaleDateString("pt-BR")
                        ) : (
                          <span className="text-gray-400">Nunca</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          {/* Dropdown de Permissões */}
                          {!user.is_admin && (
                            <Select
                              value={user.permission}
                              onValueChange={(newPermission) => handleUpdatePermission(user.id, newPermission)}
                              disabled={updatingUser === user.id}
                            >
                              <SelectTrigger className="w-[120px]">
                                <SelectValue placeholder="Permissão" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="USER">
                                  <div className="flex items-center">
                                    <UserPlus className="h-4 w-4 mr-2" />
                                    Usuário
                                  </div>
                                </SelectItem>
                                <SelectItem value="ADMIN">
                                  <div className="flex items-center">
                                    <Users className="h-4 w-4 mr-2" />
                                    Administrador
                                  </div>
                                </SelectItem>
                                <SelectItem value="SUPERUSER">
                                  <div className="flex items-center">
                                    <Shield className="h-4 w-4 mr-2" />
                                    Superusuário
                                  </div>
                                </SelectItem>
                              </SelectContent>
                            </Select>
                          )}
                          
                          {user.permission === "SUPERUSER" && (
                            <span className="text-sm text-gray-500">Superusuário</span>
                          )}
                          
                          {/* Botões de Status */}
                          {!user.is_admin && (
                            <Button
                              size="sm"
                              variant={user.is_active ? "destructive" : "default"}
                              onClick={() => handleUpdateStatus(user.id, !user.is_active)}
                              disabled={updatingUser === user.id}
                            >
                              {updatingUser === user.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : user.is_active ? (
                                <UserMinus className="h-4 w-4" />
                              ) : (
                                <UserPlus className="h-4 w-4" />
                              )}
                              <span className="ml-1">
                                {user.is_active ? "Desativar" : "Ativar"}
                              </span>
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Informações Adicionais */}
          {filteredUsers.length > 0 && (
            <div className="mt-4 text-sm text-gray-500 text-center">
              Mostrando {filteredUsers.length} de {users.length} usuários
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
