#!/usr/bin/env python3
"""
Script para gerar certificados SAML para autenticação CAFe.

Este script gera os certificados necessários para a configuração SAML:
- Certificado público (.pem)
- Chave privada (.pem)
- Metadados SAML
"""

import os
import subprocess
from pathlib import Path
import sys

def generate_self_signed_certificate():
    """Gera certificado auto-assinado para desenvolvimento."""
    
    # Diretório de certificados
    cert_dir = Path("../certificates")
    cert_dir.mkdir(exist_ok=True)
    
    # Caminhos dos arquivos
    key_file = cert_dir / "mykey.pem"
    cert_file = cert_dir / "mycert.pem"
    
    print("🔐 Gerando certificados SAML...")
    print("=" * 50)
    
    # Gerar chave privada
    print("📝 Gerando chave privada...")
    subprocess.run([
        "openssl", "genrsa", "-out", str(key_file), "2048"
    ], check=True)
    
    # Gerar certificado auto-assinado
    print("📜 Gerando certificado auto-assinado...")
    subprocess.run([
        "openssl", "req", "-new", "-x509", "-key", str(key_file),
        "-out", str(cert_file), "-days", "365",
        "-subj", "/C=BR/ST=RS/L=Porto Alegre/O=IoT-EDU/CN=localhost"
    ], check=True)
    
    print("✅ Certificados gerados com sucesso!")
    print(f"   Chave privada: {key_file}")
    print(f"   Certificado: {cert_file}")
    
    return key_file, cert_file

def create_saml_config():
    """Cria arquivo de configuração SAML básico."""
    
    config_content = """
# Configuração SAML para IoT-EDU
# Este arquivo contém as configurações básicas para autenticação CAFe

# Configurações do Service Provider (SP)
SP_ENTITY_ID = "http://localhost:8000/saml2/metadata/"
SP_NAME = "IoT-EDU API"
SP_DESCRIPTION = "API para gerenciamento de dispositivos IoT"

# Configurações de certificados
CERT_FILE = "certificates/mycert.pem"
KEY_FILE = "certificates/mykey.pem"

# Configurações do CAFe
CAFE_METADATA_URL = "https://ds.cafeexpresso.rnp.br/metadata/ds-metadata.xml"
CAFE_DISCO_URL = "https://ds.cafeexpresso.rnp.br/WAYF.php"

# Configurações de atributos
SAML_ATTRIBUTE_MAPPING = {
    'eduPersonPrincipalName': 'username',
    'mail': 'email',
    'givenName': 'first_name',
    'sn': 'last_name',
}
"""
    
    config_file = Path("saml_config.py")
    with open(config_file, "w") as f:
        f.write(config_content)
    
    print(f"📄 Arquivo de configuração criado: {config_file}")

def main():
    """Função principal."""
    
    print("🚀 Gerador de Certificados SAML para IoT-EDU")
    print("=" * 60)
    
    try:
        # Verificar se OpenSSL está instalado
        result = subprocess.run(["openssl", "version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ OpenSSL não encontrado. Instale o OpenSSL primeiro.")
            print("   Windows: https://slproweb.com/products/Win32OpenSSL.html")
            print("   Linux: sudo apt-get install openssl")
            print("   macOS: brew install openssl")
            return
        
        print(f"✅ OpenSSL encontrado: {result.stdout.strip()}")
        
        # Gerar certificados
        key_file, cert_file = generate_self_signed_certificate()
        
        # Criar configuração
        create_saml_config()
        
        print("\n🎉 Configuração SAML concluída!")
        print("\n📋 Próximos passos:")
        print("1. Configure o arquivo .env com as variáveis SAML")
        print("2. Registre o SP no CAFe (https://cafe.rnp.br)")
        print("3. Teste a autenticação: http://localhost:8000/auth/login")
        print("4. Verifique os metadados: http://localhost:8000/auth/metadata")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao gerar certificados: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    main() 