# Sylo SSO
## Overview
Sylo SSO (Single Sign-On) é um saas de autenticação e autorização voltado para empresas que precisam de uma solução de login completa e única para seus aplicativos e serviços. Além de oferecer autenticação básica e multifator, o Sylo SSO também inclui recursos avançados como gerenciamento de acessos de usuários simplificado (administradores conseguem via api ou painel do Sylo SSO, ativar ou desativar o acesso de seus usuários a aplicações) e suporte a protocolos de autenticação como OAuth (usuários não fornecem senha às aplicações, e sim ao sso). A empresa ainda pode obrigar o usuário a se autenticar com MFA para acessar determinados aplicativos, aumentando a segurança. O Sylo SSO é uma solução completa e fácil de usar para empresas que buscam uma maneira eficiente de gerenciar o acesso de seus usuários a aplicativos e serviços, operando como uma arquitetura de Headless Identity.

## Especificações (Regras de negócio)
Autenticação básica: Os usuários podem se autenticar usando email e senha. As senhas devem ser armazenadas de forma segura, utilizando técnicas de hashing e salting.

Autenticação multifator (MFA): Os usuários podem habilitar a autenticação multifator para aumentar a segurança de suas contas. O sistema deve suportar métodos de MFA como aplicativos autenticadores (ex: Google Authenticator) e SMS.

Gerenciamento de usuários: Os administradores podem criar, editar e excluir usuários, bem como atribuir ou revogar acessos a aplicações específicas.

Gerenciamento de aplicações: Os administradores podem registrar e gerenciar as aplicações que utilizam o Sylo SSO para autenticação, incluindo a configuração de protocolos de autenticação como OAuth.

Logs de auditoria: O sistema deve registrar eventos de autenticação, autorização e atividades dos usuários para fins de monitoramento e segurança.

Telemetria: O sistema deve rastrear o acesso dos usuários às aplicações, incluindo informações como data, hora, e tipo de acesso (autenticação, autorização, etc.) para análise e monitoramento. Estratégia de Escalabilidade: Para evitar degradação de performance do banco, os dados brutos de telemetria possuirão índices TTL (Time-To-Live) no MongoDB para expiração automática, mantendo apenas dados agregados para relatórios.

Suporte a múltiplos tenants: O sistema deve ser capaz de suportar múltiplos tenants (empresas ou organizações) utilizando a mesma instância do Sylo SSO, garantindo a separação de dados e configurações entre eles.

Redefinição de senha: Os usuários devem ser capazes de redefinir suas senhas de forma segura, utilizando um processo de recuperação que envolva a verificação de identidade (ex: envio de email com link de redefinição).

Confirmação de email: Os usuários devem confirmar seus endereços de email durante o processo de registro para garantir a validade das contas.

Suporte a protocolos de autenticação: O sistema deve suportar OAuth, permitindo que as aplicações se integrem facilmente ao Sylo SSO para autenticação de usuários sem a necessidade de fornecer senhas diretamente às aplicações. Para isso, deve haver uma página white-label de login e registro, onde o usuário se autentica e depois é redirecionado para a aplicação com um token de acesso.

Disponibilidade Omnichannel: Todas as funcionalidades devem estar disponíveis tanto via API REST quanto através de um painel administrativo web, permitindo que os administradores gerenciem usuários, aplicações e configurações de forma fácil e eficiente.

Landing page: O sistema deve incluir uma landing page para apresentar o Sylo SSO, suas funcionalidades e benefícios, além de fornecer informações de contato e suporte para potenciais clientes.

Documentação: O sistema deve incluir uma documentação completa e detalhada com scalar para a API, garantindo que os usuários possam utilizar todas as funcionalidades do Sylo SSO de forma eficiente e sem dificuldades.

API Key: O sistema deve permitir que os administradores gerem e gerenciem chaves de API para autenticação de aplicações e integração com outros sistemas, garantindo a segurança e controle de acesso às funcionalidades do Sylo SSO. Essa api key deve (bearer token) ser utilizada para autenticar as chamadas API REST. Elas devem ter permissões granulares. Regra de Segurança: A API Key deve ser exibida em texto plano apenas na geração e armazenada como hash no banco de dados.

Páginas white-label de login, registro, redefinição de senha e confirmação: O sistema deve fornecer páginas de login e registro personalizáveis (white-label) para as empresas. Para mitigar riscos de segurança (XSS), a customização será limitada a variáveis controladas (URL da logo, cores HEX, fontes) injetadas via CSS dinâmico. Essas páginas devem ser responsivas e acessíveis.

Segurança de Redirecionamento (Public Key): O administrador do tenant deve informar quais endereços URL podem acessar a página de login do usuário (usando o OAuth2). Para isso, deve-se criar uma public key que será usada na aplicação de terceiros para garantir que a chamada do sso é legítima.

Templates de Email White-label: O sistema deve ter templates HTML para os emails enviados ao usuário, como confirmação, redefinição de senha e notificações de segurança, incluindo o logo do tenant.

Validação de Token: Deve possuir um endpoint para aplicações de terceiros validarem o token de acesso do usuário, garantindo a verificação de autenticidade.

Emissão de Tokens JWT e Kill Switch: Emitir tokens de acesso (JWT) com informações relevantes sobre o usuário e permissões, assinados e com expiração configurável. Regra de Segurança: Para contornar a natureza stateless do JWT, será implementada uma "Token Deny List" no Redis. O acesso revogado insere o ID do token no Redis, garantindo o corte de acesso instantâneo.

Refresh Tokens: Emitir refresh tokens para manter sessões ativas. Devem ser armazenados de forma segura e ter expiração maior que os tokens de acesso.

Página de documentação para devs: Onde desenvolvedores podem encontrar informações detalhadas sobre integração, exemplos de código, guias e referências da API.

Página de cadastro de tenant: Onde as empresas podem se registrar para utilizar o Sylo SSO.

Processo de onboarding: Fluxo para novos tenants configurarem preferências, adicionarem usuários, registrarem aplicações e personalizarem as páginas white-label.

Fluxo de registro de usuários de terceiros: A aplicação satélite envia requisição para o endpoint de registro incluindo dados, redirect-page e public key. O Sylo SSO valida, cria a conta, envia email de confirmação e senha. Após confirmação e MFA opcional, redireciona o usuário de volta com token válido.

Unicidade de Email: Usuários só podem ter um email por tenant, mas podem ter o mesmo email em tenants diferentes.

## Entidades
User: Representa um usuário do sistema, contendo name, email, phone, senha (hashing), plan e status MFA.

Tenant: Empresa ou organização. Pode ter múltiplos usuários e aplicações associadas.

ClientApp: Aplicação satélite registrada no SSO. Contém nome, descrição e status de ativação.

RoleBinding: Associação entre um usuário, um tenant e uma aplicação, definindo permissões e acessos.

AuditLog: Registra eventos de autenticação, autorização e atividades críticas.

TelemetryLog: Rastreia o acesso e uso para análise financeira e monitoramento.

AuthSession / OAuthToken: Entidade auxiliar necessária para gerenciar o vínculo da sessão e permitir a funcionalidade do Kill Switch.

## Bibliotecas e Tecnologias principais
### Backend (flask)
flask-openapi3
swagger
scalar
pydantic
mongoengine
docker
redis
api do mailgun (envio de emails)
celery (processamento assíncrono)
sentry (APM e observabilidade)

### Frontend (Next.js)
tanstack react-query
react-hook-form
zod-resolver
zustand
lucide-react
motion (animações)
react-toastify
tailwindcss (para estilização, com suporte a dark mode e customização via CSS dinâmico para as páginas white-label)
shadcn/ui (para a fundação de componentes radix)

## Arquitetura e Padrões de Projeto
Frontend e backend separados, comunicação via API REST. Todo o código escrito em inglês, seguindo as melhores práticas. Texto exibido ao usuário em pt-br. Sem comentários além dos necessários para o swagger.
### Frontend
Está na pasta web da raiz.
Padrão bulletproof: funcionalidade organizada em pasta específica (componentes, hooks, api, testes).
Sem lógica nos componentes: Toda a lógica deve ser implementada em hooks.
Gerenciamento com React Query (cache), React Hook Form (formulários), Zod (validação), Zustand (estado global de autenticação).
Instância Axios com interceptors para injeção e renovação de tokens (refresh).

### Backend
Está na pasta server da raiz.
Arquitetura modular em camadas (Application Factory):
Models: Entidades do MongoEngine.
Domain (Entidades): Lógica de negócio com schema (pydantic), routes (flask-openapi3) e service (regras).
Utils: Funções auxiliares (criptografia, JWT).
Config: Variáveis de ambiente e banco de dados.
100% obrigatório o uso de type annotations.
Documentação Swagger nativa nas rotas via docstrings (sem necessidade de arquivos de comentários extras).
Estrutura de Endpoints Separados:

/api/internal/v1/...: Uso interno (frontend admin).

/api/external/v1/...: Uso externo (aplicações terceiras via API Key).

/oauth/v1/...: Endpoints de fluxo de login e token.

Guards: Reutilizáveis para controle de acesso (interno, externo, roles).
Testes: Estrutura completa de testes unitários (focados em services) e integração (comunicação com BD e filas).
Tratamento de Erros: Estrutura de captação retornando códigos HTTP apropriados (400 validação, 401 autenticação, 403 autorização, 500 erro interno). Registro de erros 5xx no sistema de log/APM (Sentry).
Estratégia de Cache
Configurações de aparência do Tenant (White-label) devem ser cacheadas no Redis. O banco de dados só será consultado em caso de alteração, garantindo carregamento instantâneo da tela de login.

## Mensageria
Fila de mensagens utilizando Redis e Celery para processar tarefas assíncronas (envio de emails, notificações, logs pesados). O backend publica a mensagem, o worker separado consome e executa para não comprometer a thread principal do Flask.

## Requisitos de Segurança e LGPD
- Rate limiting por tenant (via Redis) contra ataques de força bruta.
- Armazenamento seguro de senhas (hashing e salting).
- Criptografia de dados sensíveis.
- Políticas de acesso e autenticação robustas.
- Auditoria e monitoramento de atividades suspeitas.
- Conformidade com a LGPD (autorização explícita do usuário após login/registro sobre o acesso de informações pela aplicação satélite).

## Deploy
- Frontend na Vercel.
- Backend numa VPS com docker-compose (Traefik como proxy reverso) e Cloudflare Tunnels (agent tunnel). Inclua redis e o banco de dados MongoDB na mesma VPS para simplicidade, mas com configuração para fácil migração futura para serviços gerenciados (ex: MongoDB Atlas, Redis Cloud) se necessário.

## UI e UX
- Design responsivo e acessível.
- Interface intuitiva. Inspiração no design da Cloudflare versão dark e referência visual estabelecida (![Pinterest](https://i.pinimg.com/1200x/46/88/5d/46885d7dea43bd2bdd75b0d02a9fa4d3.jpg)).
- Pasta ui no frontend com componentes padrão (form, input, button) reutilizáveis e seguindo práticas de acessibilidade.
- Para componentes complexos, usar o ecossistema Radix UI (via shadcn/ui). Ícones via lucide-react. Notificações via react-toastify.
- Mutações sempre acompanhadas de notificações visuais.
- Páginas de autenticação (white-label) personalizáveis pela identidade visual da empresa assinante (com logo e cores).