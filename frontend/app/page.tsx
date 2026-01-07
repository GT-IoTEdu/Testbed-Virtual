import {
  Wifi,
  Shield,
  Smartphone,
  Network,
  Users,
  Settings,
  TrendingUp,
  Star,
  Zap,
  CheckCircle,
  User,
  Code,
  Globe,
  Clock,
  Database,
  Cpu,
  Router,
  Thermometer,
  Camera,
  Lightbulb,
  Home,
  Car,
  Activity,
  Bluetooth,
  Radio,
  Satellite,
  MonitorSpeaker,
  Gauge,
  CloudUpload,
  Server,
  Layers,
} from "lucide-react";
import Link from "next/link"
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Image from "next/image";

export default function GTIoTEDULanding() {
  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Navigation */}
      <nav className="flex items-center justify-between px-6 py-4 bg-slate-900/95 backdrop-blur-sm fixed w-full top-0 z-50">
        <div className="flex items-center space-x-2">
          <div className="relative">
            <Wifi className="h-8 w-8 text-blue-400" />
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
          </div>
          <span className="text-xl font-bold">GT IoT EDU</span>
        </div>

        <div className="hidden md:flex items-center space-x-8">
          <a href="#contexto" className="hover:text-blue-400 transition-colors">
            Contexto
          </a>
          <a href="#proposta" className="hover:text-blue-400 transition-colors">
            Proposta
          </a>
          <a
            href="#tecnologias"
            className="hover:text-blue-400 transition-colors"
          >
            Tecnologias
          </a>
          <a href="#parceria" className="hover:text-blue-400 transition-colors">
            Parceria RNP
          </a>
          <a href="#apoio" className="hover:text-blue-400 transition-colors">
            Apoio
          </a>
          <a href="#equipe" className="hover:text-blue-400 transition-colors">
            Equipe
          </a>
        </div>

        <div className="flex items-center space-x-4">
          <Link href="/login">
            <Button
              variant="outline"
              className="border-slate-600 text-white hover:bg-slate-800 bg-transparent"
            >
              Login
            </Button>
          </Link>
          {/* Remover o botão de tema abaixo */}
          {/* <button className="p-2 rounded-lg border border-slate-600 hover:bg-slate-800">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"
                clipRule="evenodd"
              />
            </svg>
          </button> */}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-24 pb-16 px-6 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/20 via-transparent to-transparent"></div>

        {/* Floating IoT Icons */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-10 animate-bounce delay-100">
            <Smartphone className="w-8 h-8 text-blue-400/30" />
          </div>
          <div className="absolute top-32 right-20 animate-bounce delay-300">
            <Camera className="w-6 h-6 text-green-400/30" />
          </div>
          <div className="absolute top-40 left-1/4 animate-bounce delay-500">
            <Thermometer className="w-7 h-7 text-purple-400/30" />
          </div>
          <div className="absolute top-60 right-1/3 animate-bounce delay-700">
            <Lightbulb className="w-6 h-6 text-yellow-400/30" />
          </div>
          <div className="absolute bottom-40 left-16 animate-bounce delay-200">
            <Home className="w-8 h-8 text-teal-400/30" />
          </div>
          <div className="absolute bottom-32 right-16 animate-bounce delay-600">
            <Car className="w-7 h-7 text-orange-400/30" />
          </div>
        </div>

        <div className="max-w-6xl mx-auto text-center relative z-10">
          <Badge className="mb-8 bg-blue-600/20 text-blue-300 border-blue-500/30 px-4 py-2">
            <div className="flex items-center">
              <Network className="w-4 h-4 mr-2" />
              IoT para Educação
              <div className="w-2 h-2 bg-green-400 rounded-full ml-2 animate-pulse"></div>
            </div>
          </Badge>

          <h1 className="text-6xl md:text-8xl font-bold mb-8">
            <span className="text-white">GT IoT</span>
            <br />
            <span className="bg-gradient-to-r from-blue-400 via-green-400 to-blue-600 bg-clip-text text-transparent">
              EDU
            </span>
          </h1>

          <p className="text-xl md:text-2xl text-slate-300 mb-12 max-w-4xl mx-auto leading-relaxed">
            Plataforma inovadora para{" "}
            <span className="text-blue-400 font-semibold">
              simplificar e proteger
            </span>{" "}
            o uso de dispositivos IoT em
            <span className="text-green-400 font-semibold">
              {" "}
              instituições acadêmicas
            </span>
            , oferecendo
            <span className="text-blue-400 font-semibold">
              {" "}
              cadastro fácil e redes otimizadas
            </span>
            .
          </p>

          {/* IoT Device Icons Row */}
          <div className="flex justify-center items-center space-x-8 mb-12 opacity-60">
            <div className="flex items-center space-x-2">
              <Wifi className="w-6 h-6 text-blue-400" />
              <span className="text-sm text-slate-400">WiFi</span>
            </div>
            <div className="flex items-center space-x-2">
              <Bluetooth className="w-6 h-6 text-blue-400" />
              <span className="text-sm text-slate-400">Bluetooth</span>
            </div>
            <div className="flex items-center space-x-2">
              <Radio className="w-6 h-6 text-green-400" />
              <span className="text-sm text-slate-400">LoRa</span>
            </div>
            <div className="flex items-center space-x-2">
              <Satellite className="w-6 h-6 text-purple-400" />
              <span className="text-sm text-slate-400">5G</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              size="lg"
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 text-lg"
            >
              Explore a Plataforma
              <svg
                className="w-5 h-5 ml-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </Button>
          </div>
        </div>
      </section>

      {/* Context Section */}
      <section id="contexto" className="py-16 px-6 bg-slate-800">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <Badge className="mb-6 bg-green-600/20 text-green-300 border-green-500/30 px-4 py-2">
              <Settings className="w-4 h-4 mr-2" />
              Contexto
            </Badge>
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-white">
              Sobre o Projeto
            </h2>
            <p className="text-xl text-slate-300 max-w-4xl mx-auto">
              O crescimento exponencial de dispositivos IoT em ambientes
              acadêmicos trouxe novos desafios de gestão, segurança e
              usabilidade. Nossa solução visa democratizar o acesso à tecnologia
              IoT de forma segura e eficiente.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h3 className="text-2xl font-bold text-white mb-6">
                Desafios Atuais
              </h3>
              <div className="space-y-4">
                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-red-600/20 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                    <Settings className="w-4 h-4 text-red-400" />
                  </div>
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-1">
                      Complexidade de Configuração
                    </h4>
                    <p className="text-slate-400">
                      Processos burocráticos e técnicos que dificultam a adoção
                      de dispositivos IoT
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-orange-600/20 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                    <Shield className="w-4 h-4 text-orange-400" />
                  </div>
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-1">
                      Segurança Inadequada
                    </h4>
                    <p className="text-slate-400">
                      Falta de protocolos padronizados para dispositivos IoT em
                      redes acadêmicas
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-yellow-600/20 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                    <Users className="w-4 h-4 text-yellow-400" />
                  </div>
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-1">
                      Dependência de TI
                    </h4>
                    <p className="text-slate-400">
                      Usuários dependem constantemente da equipe técnica para
                      configurações básicas
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-900/30 to-green-900/30 rounded-2xl p-8 border border-blue-700/30">
              <h3 className="text-2xl font-bold text-white mb-6">
                Nossa Solução
              </h3>
              <p className="text-slate-300 mb-6">
                Uma plataforma intuitiva que permite aos usuários registrar e
                gerenciar seus dispositivos IoT de forma autônoma, com segurança
                integrada e redes otimizadas especificamente para o ambiente
                educacional.
              </p>

              {/* IoT Device Types - Grid expandido para 5 colunas */}
              <div className="grid grid-cols-5 gap-4">
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-600/20 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <Thermometer className="w-6 h-6 text-blue-400" />
                  </div>
                  <div className="text-xs text-slate-400">Sensores</div>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-green-600/20 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <Camera className="w-6 h-6 text-green-400" />
                  </div>
                  <div className="text-xs text-slate-400">Câmeras</div>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-purple-600/20 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <Lightbulb className="w-6 h-6 text-purple-400" />
                  </div>
                  <div className="text-xs text-slate-400">Smart Devices</div>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-orange-600/20 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <MonitorSpeaker className="w-6 h-6 text-orange-400" />
                  </div>
                  <div className="text-xs text-slate-400">Audio/Video</div>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-red-600/20 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <Home className="w-6 h-6 text-red-400" />
                  </div>
                  <div className="text-xs text-slate-400">Automação</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Proposal Section */}
      <section id="proposta" className="py-16 px-6 bg-slate-900">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <Badge className="mb-6 bg-blue-600/20 text-blue-300 border-blue-500/30 px-4 py-2">
              <Zap className="w-4 h-4 mr-2" />
              Proposta
            </Badge>
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-white">
              Nossa Proposta
            </h2>
            <p className="text-2xl text-blue-400 font-semibold max-w-4xl mx-auto">
              Simplificar e proteger o uso de dispositivos IoT em instituições
              acadêmicas.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            <Card className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border-blue-700/50">
              <CardContent className="p-8">
                <div className="flex items-center mb-6">
                  <div className="w-16 h-16 bg-blue-600/20 rounded-2xl flex items-center justify-center mr-4">
                    <Clock className="w-8 h-8 text-blue-400" />
                  </div>
                  <div className="flex space-x-2">
                    <Smartphone className="w-6 h-6 text-blue-400/60" />
                    <Wifi className="w-6 h-6 text-blue-400/60" />
                    <CheckCircle className="w-6 h-6 text-green-400" />
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-white mb-4">
                  Cadastro Fácil e Sem Burocracia
                </h3>
                <p className="text-slate-300 mb-6">
                  Usuários registram seus dispositivos em segundos, sem precisar
                  da equipe de TI.
                </p>
                <div className="space-y-3">
                  <div className="flex items-center text-blue-300">
                    <CheckCircle className="w-5 h-5 mr-3" />
                    <span>Interface intuitiva e amigável</span>
                  </div>
                  <div className="flex items-center text-blue-300">
                    <CheckCircle className="w-5 h-5 mr-3" />
                    <span>Processo automatizado de validação</span>
                  </div>
                  <div className="flex items-center text-blue-300">
                    <CheckCircle className="w-5 h-5 mr-3" />
                    <span>Configuração automática de rede</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-green-900/50 to-green-800/30 border-green-700/50">
              <CardContent className="p-8">
                <div className="flex items-center mb-6">
                  <div className="w-16 h-16 bg-green-600/20 rounded-2xl flex items-center justify-center mr-4">
                    <Network className="w-8 h-8 text-green-400" />
                  </div>
                  <div className="flex space-x-2">
                    <Router className="w-6 h-6 text-green-400/60" />
                    <Shield className="w-6 h-6 text-green-400/60" />
                    <Activity className="w-6 h-6 text-green-400" />
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-white mb-4">
                  Redes Otimizadas para IoT
                </h3>
                <p className="text-slate-300 mb-6">
                  Dispositivos conectados com segurança, eficiência e
                  responsabilidade do usuário.
                </p>
                <div className="space-y-3">
                  <div className="flex items-center text-green-300">
                    <CheckCircle className="w-5 h-5 mr-3" />
                    <span>Segmentação automática de rede</span>
                  </div>
                  <div className="flex items-center text-green-300">
                    <CheckCircle className="w-5 h-5 mr-3" />
                    <span>Monitoramento em tempo real</span>
                  </div>
                  <div className="flex items-center text-green-300">
                    <CheckCircle className="w-5 h-5 mr-3" />
                    <span>Políticas de segurança integradas</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          
          <div className="mt-16 text-center">
            <h3 className="text-2xl font-bold text-white mb-8">
              Ecossistema IoT Suportado
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 bg-blue-600/20 rounded-2xl flex items-center justify-center mb-3 hover:scale-110 transition-transform">
                  <Thermometer className="w-8 h-8 text-blue-400" />
                </div>
                <span className="text-sm text-slate-400">Sensores</span>
              </div>
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 bg-green-600/20 rounded-2xl flex items-center justify-center mb-3 hover:scale-110 transition-transform">
                  <Camera className="w-8 h-8 text-green-400" />
                </div>
                <span className="text-sm text-slate-400">Câmeras</span>
              </div>
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 bg-purple-600/20 rounded-2xl flex items-center justify-center mb-3 hover:scale-110 transition-transform">
                  <Lightbulb className="w-8 h-8 text-purple-400" />
                </div>
                <span className="text-sm text-slate-400">Iluminação</span>
              </div>
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 bg-orange-600/20 rounded-2xl flex items-center justify-center mb-3 hover:scale-110 transition-transform">
                  <MonitorSpeaker className="w-8 h-8 text-orange-400" />
                </div>
                <span className="text-sm text-slate-400">Audio/Video</span>
              </div>
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 bg-teal-600/20 rounded-2xl flex items-center justify-center mb-3 hover:scale-110 transition-transform">
                  <Gauge className="w-8 h-8 text-teal-400" />
                </div>
                <span className="text-sm text-slate-400">Medidores</span>
              </div>
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 bg-red-600/20 rounded-2xl flex items-center justify-center mb-3 hover:scale-110 transition-transform">
                  <Home className="w-8 h-8 text-red-400" />
                </div>
                <span className="text-sm text-slate-400">Automação</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Technologies Section */}
      <section id="tecnologias" className="py-16 px-6 bg-slate-800">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <Badge className="mb-6 bg-slate-600/20 text-slate-300 border-slate-500/30 px-4 py-2">
              <Cpu className="w-4 h-4 mr-2" />
              Stack Tecnológico
            </Badge>
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-white">
              Tecnologias Utilizadas
            </h2>
            <p className="text-xl text-slate-300 max-w-4xl mx-auto">
              Tecnologias modernas e robustas para garantir performance,
              segurança e escalabilidade em ambientes IoT.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            <Card className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border-blue-700/50 text-center p-6 hover:scale-105 transition-transform">
              <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex items-center justify-center mx-auto mb-3">
                <Code className="w-6 h-6 text-blue-400" />
              </div>
              <h4 className="text-sm font-bold text-white mb-1">React</h4>
              <p className="text-xs text-slate-400">Frontend Framework</p>
            </Card>

            <Card className="bg-gradient-to-br from-green-900/50 to-green-800/30 border-green-700/50 text-center p-6 hover:scale-105 transition-transform">
              <div className="w-12 h-12 bg-green-600/20 rounded-xl flex items-center justify-center mx-auto mb-3">
                <Server className="w-6 h-6 text-green-400" />
              </div>
              <h4 className="text-sm font-bold text-white mb-1">Node.js</h4>
              <p className="text-xs text-slate-400">Backend Runtime</p>
            </Card>

            <Card className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border-purple-700/50 text-center p-6 hover:scale-105 transition-transform">
              <div className="w-12 h-12 bg-purple-600/20 rounded-xl flex items-center justify-center mx-auto mb-3">
                <Database className="w-6 h-6 text-purple-400" />
              </div>
              <h4 className="text-sm font-bold text-white mb-1">PostgreSQL</h4>
              <p className="text-xs text-slate-400">Database</p>
            </Card>

            <Card className="bg-gradient-to-br from-orange-900/50 to-orange-800/30 border-orange-700/50 text-center p-6 hover:scale-105 transition-transform">
              <div className="w-12 h-12 bg-orange-600/20 rounded-xl flex items-center justify-center mx-auto mb-3">
                <Radio className="w-6 h-6 text-orange-400" />
              </div>
              <h4 className="text-sm font-bold text-white mb-1">MQTT</h4>
              <p className="text-xs text-slate-400">IoT Protocol</p>
            </Card>

            <Card className="bg-gradient-to-br from-teal-900/50 to-teal-800/30 border-teal-700/50 text-center p-6 hover:scale-105 transition-transform">
              <div className="w-12 h-12 bg-teal-600/20 rounded-xl flex items-center justify-center mx-auto mb-3">
                <Layers className="w-6 h-6 text-teal-400" />
              </div>
              <h4 className="text-sm font-bold text-white mb-1">Docker</h4>
              <p className="text-xs text-slate-400">Containerization</p>
            </Card>

            <Card className="bg-gradient-to-br from-red-900/50 to-red-800/30 border-red-700/50 text-center p-6 hover:scale-105 transition-transform">
              <div className="w-12 h-12 bg-red-600/20 rounded-xl flex items-center justify-center mx-auto mb-3">
                <Network className="w-6 h-6 text-red-400" />
              </div>
              <h4 className="text-sm font-bold text-white mb-1">Redis</h4>
              <p className="text-xs text-slate-400">Cache & Queue</p>
            </Card>

            <Card className="bg-gradient-to-br from-yellow-900/50 to-yellow-800/30 border-yellow-700/50 text-center p-6 hover:scale-105 transition-transform">
              <div className="w-12 h-12 bg-yellow-600/20 rounded-xl flex items-center justify-center mx-auto mb-3">
                <Activity className="w-6 h-6 text-yellow-400" />
              </div>
              <h4 className="text-sm font-bold text-white mb-1">InfluxDB</h4>
              <p className="text-xs text-slate-400">Time Series DB</p>
            </Card>

            <Card className="bg-gradient-to-br from-indigo-900/50 to-indigo-800/30 border-indigo-700/50 text-center p-6 hover:scale-105 transition-transform">
              <div className="w-12 h-12 bg-indigo-600/20 rounded-xl flex items-center justify-center mx-auto mb-3">
                <CloudUpload className="w-6 h-6 text-indigo-400" />
              </div>
              <h4 className="text-sm font-bold text-white mb-1">Kubernetes</h4>
              <p className="text-xs text-slate-400">Orchestration</p>
            </Card>
          </div>
        </div>
      </section>

      {/* RNP Partnership Section */}
      <section id="parceria" className="py-16 px-6 bg-slate-900">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <Badge className="mb-6 bg-blue-600/20 text-blue-300 border-blue-500/30 px-4 py-2">
              <Network className="w-4 h-4 mr-2" />
              Parceria Estratégica
            </Badge>
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-white">
              Rede Parceira
            </h2>
          </div>

          <div className="max-w-4xl mx-auto">
            <Card className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border-blue-700/50 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-transparent"></div>
              <CardContent className="p-12 text-center relative z-10">
                <div className="w-64 h-40 mx-auto mb-8 relative">
                  <Image
                    src="/images/rnp.png"
                    alt="RNP Logo"
                    fill
                    style={{ objectFit: "contain" }}
                    className="drop-shadow-lg"
                  />
                </div>
                <h3 className="text-3xl font-bold text-white mb-4">RNP</h3>
                <p className="text-xl text-blue-300 font-semibold mb-6">
                  Rede Nacional de Ensino e Pesquisa
                </p>
                <p className="text-slate-300 mb-8 text-lg leading-relaxed">
                  Parceria estratégica com a RNP para desenvolvimento e
                  implementação da plataforma GT IoT EDU, aproveitando a
                  infraestrutura nacional de rede acadêmica para conectar
                  dispositivos IoT de forma segura e eficiente em instituições
                  de ensino superior.
                </p>

                <div className="grid md:grid-cols-3 gap-6 mb-8">
                  <div className="text-center">
                    <div className="w-16 h-16 bg-blue-600/20 rounded-2xl flex items-center justify-center mx-auto mb-3">
                      <Globe className="w-8 h-8 text-blue-400" />
                    </div>
                    <h4 className="text-lg font-bold text-white mb-2">
                      Infraestrutura Nacional
                    </h4>
                    <p className="text-slate-400 text-sm">
                      Rede de alta velocidade conectando universidades
                    </p>
                  </div>
                  <div className="text-center">
                    <div className="w-16 h-16 bg-green-600/20 rounded-2xl flex items-center justify-center mx-auto mb-3">
                      <Shield className="w-8 h-8 text-green-400" />
                    </div>
                    <h4 className="text-lg font-bold text-white mb-2">
                      Segurança Avançada
                    </h4>
                    <p className="text-slate-400 text-sm">
                      Protocolos de segurança para ambiente acadêmico
                    </p>
                  </div>
                  <div className="text-center">
                    <div className="w-16 h-16 bg-purple-600/20 rounded-2xl flex items-center justify-center mx-auto mb-3">
                      <Users className="w-8 h-8 text-purple-400" />
                    </div>
                    <h4 className="text-lg font-bold text-white mb-2">
                      Comunidade Acadêmica
                    </h4>
                    <p className="text-slate-400 text-sm">
                      Suporte especializado para instituições
                    </p>
                  </div>
                </div>

                <Button
                  size="lg"
                  className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3"
                >
                  Saiba Mais sobre a Parceria
                  <Network className="w-5 h-5 ml-2" />
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Support Section */}
      <section id="apoio" className="py-16 px-6 bg-slate-800">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <Badge className="mb-6 bg-green-600/20 text-green-300 border-green-500/30 px-4 py-2">
              <Star className="w-4 h-4 mr-2" />
              Apoiadores
            </Badge>
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-white">
              Apoio Institucional
            </h2>
            <p className="text-xl text-slate-300 max-w-4xl mx-auto">
              Projeto desenvolvido com o apoio de importantes instituições de
              ensino superior do Brasil.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
          
            <Card className="bg-gradient-to-br from-green-900/50 to-green-800/30 border-green-700/50 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-green-600/10 to-transparent"></div>
              <CardContent className="p-8 text-center relative z-10">
                <div className="w-64 h-44 mx-auto mb-6 relative">
                  <Image
                    src="/images/unipampa.png"
                    alt="UNIPAMPA Logo"
                    fill
                    style={{
                      objectFit: "contain",
                      objectPosition: "center",
                      backgroundColor: "transparent",
                    }}
                    className="drop-shadow-lg"
                  />
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">UNIPAMPA</h3>
                <p className="text-green-300 font-semibold mb-4">
                  Universidade Federal do Pampa
                </p>
              </CardContent>
            </Card>

        
            <Card className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border-blue-700/50 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-transparent"></div>
              <CardContent className="p-8 text-center relative z-10">
                <div className="w-64 h-44 mx-auto mb-6 relative">
                  <Image
                    src="/images/ufrgs.png"
                    alt="UFRGS Logo"
                    fill
                    style={{
                      objectFit: "contain",
                      objectPosition: "center bottom", // Posicionado mais para baixo
                      backgroundColor: "transparent",
                    }}
                    className="drop-shadow-lg"
                  />
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">UFRGS</h3>
                <p className="text-blue-300 font-semibold mb-4">
                  Universidade Federal do Rio Grande do Sul
                </p>
              </CardContent>
            </Card>

           
            <Card className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border-purple-700/50 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-600/10 to-transparent"></div>
              <CardContent className="p-8 text-center relative z-10">
                <div className="w-64 h-44 mx-auto mb-6 relative">
                  <Image
                    src="/images/ufu.png"
                    alt="UFU Logo"
                    fill
                    style={{
                      objectFit: "contain",
                      objectPosition: "center",
                      backgroundColor: "transparent",
                    }}
                    className="drop-shadow-lg"
                  />
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">UFU</h3>
                <p className="text-purple-300 font-semibold mb-4">
                  Universidade Federal de Uberlândia
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section id="equipe" className="py-16 px-6 bg-slate-900">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <Badge className="mb-6 bg-purple-600/20 text-purple-300 border-purple-500/30 px-4 py-2">
              <Users className="w-4 h-4 mr-2" />
              Equipe
            </Badge>
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-white">
              Equipe
            </h2>
            <p className="text-xl text-slate-300 max-w-4xl mx-auto">
              Conheça os pesquisadores e desenvolvedores por trás do projeto.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border-blue-700/50">
              <CardContent className="p-6 text-center">
                <div className="w-16 h-16 bg-blue-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <User className="w-8 h-8 text-blue-400" />
                </div>
                <h4 className="text-lg font-bold text-white mb-2">
                  João Silva
                </h4>
                <p className="text-blue-300 text-sm font-semibold mb-3">
                  Professor
                </p>
                <p className="text-slate-400 text-xs">
                  Doutor em Ciência da Computação com foco em Cibersegurança.
                  Professor na Universidade Federal do Pampa.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border-purple-700/50">
              <CardContent className="p-6 text-center">
                <div className="w-16 h-16 bg-purple-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <User className="w-8 h-8 text-purple-400" />
                </div>
                <h4 className="text-lg font-bold text-white mb-2">
                  Maria Bethania
                </h4>
                <p className="text-purple-300 text-sm font-semibold mb-3">
                  Professor
                </p>
                <p className="text-slate-400 text-xs">
                  Doutor em Ciência da Computação com foco em Cibersegurança.
                  Professor na Universidade Federal do Pampa.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-green-900/50 to-green-800/30 border-green-700/50">
              <CardContent className="p-6 text-center">
                <div className="w-16 h-16 bg-green-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <User className="w-8 h-8 text-green-400" />
                </div>
                <h4 className="text-lg font-bold text-white mb-2">Jorge Ben</h4>
                <p className="text-green-300 text-sm font-semibold mb-3">
                  Professor
                </p>
                <p className="text-slate-400 text-xs">
                  Doutor em Ciência da Computação com foco em Cibersegurança.
                  Professor na Universidade Federal do Pampa.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-orange-900/50 to-orange-800/30 border-orange-700/50">
              <CardContent className="p-6 text-center">
                <div className="w-16 h-16 bg-orange-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <User className="w-8 h-8 text-orange-400" />
                </div>
                <h4 className="text-lg font-bold text-white mb-2">
                  João Silva
                </h4>
                <p className="text-orange-300 text-sm font-semibold mb-3">
                  Professor
                </p>
                <p className="text-slate-400 text-xs">
                  Doutor em Ciência da Computação com foco em Cibersegurança.
                  Professor na Universidade Federal do Pampa.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-teal-900/50 to-teal-800/30 border-teal-700/50">
              <CardContent className="p-6 text-center">
                <div className="w-16 h-16 bg-teal-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <User className="w-8 h-8 text-teal-400" />
                </div>
                <h4 className="text-lg font-bold text-white mb-2">
                  Maria Bethania
                </h4>
                <p className="text-teal-300 text-sm font-semibold mb-3">
                  Professor
                </p>
                <p className="text-slate-400 text-xs">
                  Doutor em Ciência da Computação com foco em Cibersegurança.
                  Professor na Universidade Federal do Pampa.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-red-900/50 to-red-800/30 border-red-700/50">
              <CardContent className="p-6 text-center">
                <div className="w-16 h-16 bg-red-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <User className="w-8 h-8 text-red-400" />
                </div>
                <h4 className="text-lg font-bold text-white mb-2">Jorge Ben</h4>
                <p className="text-red-300 text-sm font-semibold mb-3">
                  Professor
                </p>
                <p className="text-slate-400 text-xs">
                  Doutor em Ciência da Computação com foco em Cibersegurança.
                  Professor na Universidade Federal do Pampa.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 bg-slate-900 border-t border-slate-700">
        <div className="max-w-6xl mx-auto text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <div className="relative">
              <Wifi className="h-6 w-6 text-blue-400" />
              <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            </div>
            <span className="text-lg font-bold">GT IoT EDU</span>
          </div>
          <p className="text-slate-400 text-sm">
            © 2025 GT-IoTEDU Todos os direitos reservados.
          </p>
        </div>
      </footer>
    </div>
  );
}
