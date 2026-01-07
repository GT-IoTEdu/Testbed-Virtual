#!/usr/bin/env python3
"""
Script automatizado para testar o sistema de permissões.
Este script executa todos os cenários de teste e valida as respostas.
"""
import requests
import json
import time
from typing import Dict, Any, List

class PermissionTester:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/devices"
        self.user_id = 1  # Usuário comum
        self.manager_id = 2  # Gestor
        self.results = []
        
    def log_result(self, test_name: str, expected_status: int, actual_status: int, 
                   success: bool, response_data: Any = None):
        """Registra o resultado de um teste."""
        result = {
            "test_name": test_name,
            "expected_status": expected_status,
            "actual_status": actual_status,
            "success": success,
            "response_data": response_data,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {test_name}")
        print(f"   Esperado: {expected_status}, Recebido: {actual_status}")
        if not success and response_data:
            print(f"   Resposta: {response_data}")
        print()
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    params: Dict = None) -> tuple:
        """Faz uma requisição HTTP e retorna status e dados."""
        url = f"{self.api_base}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
            elif method.upper() == "DELETE":
                response = requests.delete(url, params=params)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
                
            return response.status_code, response_data
            
        except requests.exceptions.ConnectionError:
            return 0, "Erro de conexão - servidor não está rodando"
        except Exception as e:
            return 0, f"Erro: {str(e)}"
    
    def setup_dhcp_data(self) -> bool:
        """Salva dados DHCP no banco (setup inicial)."""
        print("🔧 Executando setup inicial - Salvando dados DHCP...")
        status, data = self.make_request("POST", "/dhcp/save")
        
        success = status == 200
        self.log_result("Setup - Salvar Dados DHCP", 200, status, success, data)
        return success
    
    def test_user_assign_device_to_self(self) -> bool:
        """Teste: Usuário comum atribui dispositivo a si mesmo."""
        print("👤 Testando: Usuário comum atribui dispositivo a si mesmo...")
        data = {
            "user_id": self.user_id,
            "device_id": 1,
            "notes": "Dispositivo atribuído pelo próprio usuário",
            "assigned_by": self.user_id
        }
        status, response_data = self.make_request("POST", "/assignments", data=data)
        
        success = status == 200
        self.log_result("Usuário Comum - Atribuir a Si Mesmo", 200, status, success, response_data)
        return success
    
    def test_user_assign_device_to_other(self) -> bool:
        """Teste: Usuário comum tenta atribuir dispositivo a outro usuário (deve falhar)."""
        print("❌ Testando: Usuário comum tenta atribuir a outro usuário...")
        data = {
            "user_id": self.manager_id,
            "device_id": 1,
            "notes": "Tentativa não autorizada",
            "assigned_by": self.user_id
        }
        status, response_data = self.make_request("POST", "/assignments", data=data)
        
        success = status == 403
        self.log_result("Usuário Comum - Tentar Atribuir a Outro", 403, status, success, response_data)
        return success
    
    def test_manager_assign_device_to_other(self) -> bool:
        """Teste: Gestor atribui dispositivo a outro usuário."""
        print("👨‍💼 Testando: Gestor atribui dispositivo a outro usuário...")
        data = {
            "user_id": self.user_id,
            "device_id": 2,
            "notes": "Dispositivo atribuído pelo gestor",
            "assigned_by": self.manager_id
        }
        status, response_data = self.make_request("POST", "/assignments", data=data)
        
        success = status == 200
        self.log_result("Gestor - Atribuir a Outro Usuário", 200, status, success, response_data)
        return success
    
    def test_user_view_own_devices(self) -> bool:
        """Teste: Usuário comum vê seus próprios dispositivos."""
        print("👤 Testando: Usuário comum vê seus próprios dispositivos...")
        params = {"current_user_id": self.user_id}
        status, response_data = self.make_request("GET", f"/users/{self.user_id}/devices", params=params)
        
        success = status == 200
        self.log_result("Usuário Comum - Ver Seus Dispositivos", 200, status, success, response_data)
        return success
    
    def test_user_view_other_devices(self) -> bool:
        """Teste: Usuário comum tenta ver dispositivos de outro usuário (deve falhar)."""
        print("❌ Testando: Usuário comum tenta ver dispositivos de outro usuário...")
        params = {"current_user_id": self.user_id}
        status, response_data = self.make_request("GET", f"/users/{self.manager_id}/devices", params=params)
        
        success = status == 403
        self.log_result("Usuário Comum - Tentar Ver Dispositivos de Outro", 403, status, success, response_data)
        return success
    
    def test_manager_view_any_devices(self) -> bool:
        """Teste: Gestor vê dispositivos de qualquer usuário."""
        print("👨‍💼 Testando: Gestor vê dispositivos de qualquer usuário...")
        params = {"current_user_id": self.manager_id}
        status, response_data = self.make_request("GET", f"/users/{self.user_id}/devices", params=params)
        
        success = status == 200
        self.log_result("Gestor - Ver Dispositivos de Qualquer Usuário", 200, status, success, response_data)
        return success
    
    def test_user_view_own_device_users(self) -> bool:
        """Teste: Usuário comum vê usuários de seu dispositivo."""
        print("👤 Testando: Usuário comum vê usuários de seu dispositivo...")
        params = {"current_user_id": self.user_id}
        status, response_data = self.make_request("GET", "/devices/1/users", params=params)
        
        success = status == 200
        self.log_result("Usuário Comum - Ver Usuários de Seu Dispositivo", 200, status, success, response_data)
        return success
    
    def test_user_view_other_device_users(self) -> bool:
        """Teste: Usuário comum tenta ver usuários de dispositivo que não possui (deve falhar)."""
        print("❌ Testando: Usuário comum tenta ver usuários de dispositivo que não possui...")
        params = {"current_user_id": self.user_id}
        status, response_data = self.make_request("GET", "/devices/2/users", params=params)
        
        success = status == 403
        self.log_result("Usuário Comum - Tentar Ver Usuários de Dispositivo que Não Possui", 403, status, success, response_data)
        return success
    
    def test_manager_view_any_device_users(self) -> bool:
        """Teste: Gestor vê usuários de qualquer dispositivo."""
        print("👨‍💼 Testando: Gestor vê usuários de qualquer dispositivo...")
        params = {"current_user_id": self.manager_id}
        status, response_data = self.make_request("GET", "/devices/1/users", params=params)
        
        success = status == 200
        self.log_result("Gestor - Ver Usuários de Qualquer Dispositivo", 200, status, success, response_data)
        return success
    
    def test_user_remove_own_assignment(self) -> bool:
        """Teste: Usuário comum remove sua própria atribuição."""
        print("👤 Testando: Usuário comum remove sua própria atribuição...")
        params = {"current_user_id": self.user_id}
        status, response_data = self.make_request("DELETE", f"/assignments/{self.user_id}/1", params=params)
        
        success = status == 200
        self.log_result("Usuário Comum - Remover Sua Própria Atribuição", 200, status, success, response_data)
        return success
    
    def test_user_remove_other_assignment(self) -> bool:
        """Teste: Usuário comum tenta remover atribuição de outro usuário (deve falhar)."""
        print("❌ Testando: Usuário comum tenta remover atribuição de outro usuário...")
        params = {"current_user_id": self.user_id}
        status, response_data = self.make_request("DELETE", f"/assignments/{self.manager_id}/1", params=params)
        
        success = status == 403
        self.log_result("Usuário Comum - Tentar Remover Atribuição de Outro", 403, status, success, response_data)
        return success
    
    def test_manager_remove_any_assignment(self) -> bool:
        """Teste: Gestor remove atribuição de qualquer usuário."""
        print("👨‍💼 Testando: Gestor remove atribuição de qualquer usuário...")
        params = {"current_user_id": self.manager_id}
        status, response_data = self.make_request("DELETE", f"/assignments/{self.user_id}/2", params=params)
        
        success = status == 200
        self.log_result("Gestor - Remover Atribuição de Qualquer Usuário", 200, status, success, response_data)
        return success
    
    def test_search_assignments(self) -> bool:
        """Teste: Buscar atribuições por termo."""
        print("🔍 Testando: Buscar atribuições por termo...")
        params = {"query": "teste"}
        status, response_data = self.make_request("GET", "/assignments/search", params=params)
        
        success = status == 200
        self.log_result("Buscar Atribuições por Termo", 200, status, success, response_data)
        return success
    
    def test_assignment_statistics(self) -> bool:
        """Teste: Estatísticas de atribuições."""
        print("📊 Testando: Estatísticas de atribuições...")
        status, response_data = self.make_request("GET", "/assignments/statistics")
        
        success = status == 200
        self.log_result("Estatísticas de Atribuições", 200, status, success, response_data)
        return success
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes e retorna um resumo."""
        print("🚀 Iniciando testes automatizados do sistema de permissões...")
        print("=" * 80)
        
        # Setup inicial
        if not self.setup_dhcp_data():
            print("❌ Falha no setup inicial. Verifique se o servidor está rodando.")
            return {"success": False, "error": "Setup inicial falhou"}
        
        # Executar todos os testes
        tests = [
            self.test_user_assign_device_to_self,
            self.test_user_assign_device_to_other,
            self.test_manager_assign_device_to_other,
            self.test_user_view_own_devices,
            self.test_user_view_other_devices,
            self.test_manager_view_any_devices,
            self.test_user_view_own_device_users,
            self.test_user_view_other_device_users,
            self.test_manager_view_any_device_users,
            self.test_user_remove_own_assignment,
            self.test_user_remove_other_assignment,
            self.test_manager_remove_any_assignment,
            self.test_search_assignments,
            self.test_assignment_statistics
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            if test():
                passed_tests += 1
        
        # Gerar relatório
        print("=" * 80)
        print("📊 RELATÓRIO FINAL")
        print("=" * 80)
        print(f"Total de testes: {total_tests}")
        print(f"Testes aprovados: {passed_tests}")
        print(f"Testes falharam: {total_tests - passed_tests}")
        print(f"Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 TODOS OS TESTES PASSARAM! Sistema de permissões funcionando corretamente!")
        else:
            print(f"\n⚠️ {total_tests - passed_tests} teste(s) falharam. Verifique os logs acima.")
        
        return {
            "success": passed_tests == total_tests,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "results": self.results
        }

def main():
    """Função principal."""
    print("🔐 Testador Automatizado do Sistema de Permissões")
    print("=" * 80)
    
    # Verificar se o servidor está rodando
    try:
        response = requests.get("http://127.0.0.1:8000/docs", timeout=5)
        if response.status_code != 200:
            print("❌ Servidor não está respondendo corretamente.")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Servidor não está rodando. Execute 'python main.py' primeiro.")
        return
    
    # Executar testes
    tester = PermissionTester()
    result = tester.run_all_tests()
    
    # Salvar relatório
    with open("test_permissions_report.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Relatório salvo em: test_permissions_report.json")

if __name__ == "__main__":
    main()
