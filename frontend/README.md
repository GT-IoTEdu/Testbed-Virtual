# Frontend - IoT-EDU

Este diretório contém a aplicação frontend do projeto IoT-EDU, uma interface web moderna para gerenciamento de dispositivos IoT educacionais.

## Visão Geral

O frontend do IoT-EDU é construído com Next.js e React, projetado para fornecer uma interface de usuário intuitiva para gerenciamento de dispositivos IoT. A aplicação utiliza TypeScript para tipagem estática e Tailwind CSS para estilização.

## Estrutura do Diretório

```
frontend/
├── app/                  # Diretório App Router do Next.js
│   ├── dashboard/        # Rota do dashboard
│   ├── login/            # Rota de login
│   ├── globals.css       # Estilos globais
│   ├── layout.tsx        # Layout principal
│   └── page.tsx          # Página inicial
├── components/           # Componentes React reutilizáveis
│   ├── ui/               # Componentes de UI
│   └── theme-provider.tsx # Provedor de tema
├── hooks/                # Hooks React personalizados
│   ├── use-mobile.tsx    # Hook para detecção de dispositivos móveis
│   └── use-toast.ts      # Hook para notificações toast
├── lib/                  # Bibliotecas e utilitários
│   └── utils.ts          # Funções utilitárias
├── public/               # Arquivos estáticos
├── styles/               # Estilos adicionais
├── .next/                # Build gerado pelo Next.js (ignorado no git)
├── components.json       # Configuração do shadcn/ui
├── eslint.config.mjs     # Configuração do ESLint
├── next.config.mjs       # Configuração principal do Next.js
├── next.config.ts        # Configuração tipada do Next.js
├── package.json          # Dependências e scripts
├── postcss.config.mjs    # Configuração do PostCSS
├── tailwind.config.ts    # Configuração do Tailwind CSS
└── tsconfig.json         # Configuração do TypeScript
```

## Tecnologias Utilizadas

- **Next.js**: Framework React para renderização do lado do servidor
- **React**: Biblioteca para construção de interfaces
- **TypeScript**: Superset tipado de JavaScript
- **Tailwind CSS**: Framework CSS utilitário
- **shadcn/ui**: Componentes de UI reutilizáveis e acessíveis
- **Recharts**: Biblioteca para criação de gráficos

## Instalação e Configuração

1. Navegue até o diretório frontend:
   ```bash
   cd frontend
   ```

2. Instale as dependências:
   ```bash
   npm install
   # ou
   yarn install
   # ou
   pnpm install
   # ou
   bun install
   ```

3. Execute o servidor de desenvolvimento:
   ```bash
   npm run dev
   # ou
   yarn dev
   # ou
   pnpm dev
   # ou
   bun dev
   ```

4. Acesse a aplicação em `http://localhost:3000`

## Scripts Disponíveis

Verifique o `package.json` para todos os scripts disponíveis, incluindo:

- `dev`: Inicia o servidor de desenvolvimento
- `build`: Cria uma versão de produção
- `start`: Inicia o servidor de produção
- `lint`: Executa a verificação de linting

## Hooks Personalizados

- **useMobile**: Detecta se o dispositivo é móvel
- **useToast**: Fornece funcionalidade de notificações toast

## Configuração

### components.json

Configura os componentes do shadcn/ui, definindo estilos, aliases e outras opções.

### tailwind.config.ts

Contém a configuração do Tailwind CSS, incluindo temas, plugins e extensões.

### next.config.mjs e next.config.ts

Configurações do Next.js para build, rotas e outras funcionalidades.

## Convenções de Código

- Use TypeScript para todos os novos componentes e funções
- Siga as convenções de nomenclatura estabelecidas
- Utilize os componentes UI existentes quando possível
- Mantenha a acessibilidade em mente ao desenvolver interfaces

## Integração com Backend

O frontend se comunica com o backend por meio de APIs RESTful. Verifique a documentação do backend para detalhes sobre os endpoints disponíveis.

## Documentação Adicional

- [Next.js Documentation](https://nextjs.org/docs) - documentação oficial do Next.js
- [React Documentation](https://react.dev) - documentação oficial do React
- [Tailwind CSS Documentation](https://tailwindcss.com/docs) - documentação do Tailwind CSS
- [TypeScript Documentation](https://www.typescriptlang.org/docs) - documentação do TypeScript

---

Para mais informações sobre o projeto completo, consulte o README principal do repositório.