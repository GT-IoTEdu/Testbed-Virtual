[Instalacao_PFSense-1.pdf](https://github.com/user-attachments/files/26518264/Instalacao_PFSense-1.pdf)﻿
# Sistema de Registro IoT com Autenticação CAFe e pfSense

## Diagrama de Arquitetura
![Diagrama de Arquitetura do Sistema](https://github.com/GT-IoTEdu/API/blob/main/diagramas/images/Arquitetura_v1.png)

*Diagrama completo dos componentes e fluxos do sistema*

## Visão Geral
Sistema integrado para gerenciamento seguro de dispositivos IoT em ambientes acadêmicos, combinando:
- ✅ Autenticação federada via CAFe
- 🔐 Gerenciamento automatizado de regras no pfSense
- 🤖 Monitoramento inteligente de tráfego com IA
- 📊 Painel administrativo de dispositivos IoTs cadastrados


# 🚀 Guia Completo de Instalação

  

Este guia detalha o processo completo de instalação do sistema do zero, incluindo banco de dados vazio e pfSense sem configurações.

  

## 📋 Pré-requisitos

  

- ✅ Python 3.9+ instalado

- ✅ MySQL/MariaDB instalado e rodando

- ✅ pfSense configurado com API REST v2 habilitada

- ✅ Acesso ao banco de dados MySQL

- ✅ Acesso ao pfSense (interface web e API)

  

## 🔧 Passo 1: Configuração e instalação de depedencias

### Optional: Usar um ambiente virtual

```bash
pip install virtualenv
python3 -m venv venv
source venv/bin/activate
```

---

## ⚙️ Instalação

```bash
git clone https://github.com/GT-IoTEdu/Testbed-Virtual.git
cd Testebed-virtual
pip install --upgrade pip
pip install -r requirements.txt
# ou
pip install .
```
## ⚙️ Configuração 

### 1.Abra o arquivo env_example.txt na pasta backend, modifique ele com base nas configurações desejadas, e o renomeie para .env


### 2. Faça o download do virtual box e siga os seguintes passos descritos no pdf para instalar o pfsense [Instalacao_PFSense-1.pdf](https://github.com/user-attachments/files/26518266/Instalacao_PFSense-1.pdf)

### 3. Crie uma rede no virtual box através da interface  da opção arquivos-> ferramentas,

### 4. Atribua um ip estático a rede LAN e utilize a interface criada no passo anterior
<img width="761" height="393" alt="image" src="https://github.com/user-attachments/assets/d10df236-8d2c-4bae-801c-d84f6f2d0ab9" />

### 5. Acesse a interface web do pfsense no seu navegador com base no ip atribuido, na aba de serviços entre no DHCP SERVER e realize a configuração de uma rede, como exemplo:
<img width="846" height="377" alt="image" src="https://github.com/user-attachments/assets/01db81c5-5ae1-4d9c-b785-b1e931aa5b88" />

### 6. Crie um tap para a interface LAN do pfsense:
```bash
# substitua vboxnet0 pela sua interface
sudo tc qdisc add dev vboxnet0 ingress

# Crie uma rede docker
docker network create tap_test


# Verifique o ID
docker network ls

# Verifique o nome da interface no hospedeiro com base no id fornecido
ip a


# Faça o tap:
sudo tc filter add dev vboxnet0 parent ffff: protocol all u32 match u8 0 0 action mirred egress mirror dev br-234ef4b18abd

# No Docker compose mude o nome da interface na linha:
      ZEEK_INTERFACE: br-234ef4b18abd
```

## ⚙️ Execução 

### Para realizar a execução use o script deploy.sh


```bash
./deploy.sh
```

 
