# Sylo SSO - Sistema de Gestão de Identidade e Acesso

## Visão Geral

O **Sylo SSO** é uma solução SaaS de gestão de identidade e acesso (IAM) de alto desempenho, desenhada especificamente para ecossistemas B2B. Operando sob o paradigma de *Headless Identity*, o sistema centraliza a autenticação e autorização, permitindo que empresas (**Tenants**) giram o acesso dos seus utilizadores a múltiplas aplicações satélites com máxima segurança e soberania de dados.

---

## Regras de Negócio e Lógica do Sistema completo

Esta secção detalha as normas operacionais e de segurança que regem o comportamento do Sylo SSO, conforme estabelecido no plano de desenvolvimento.

### 1. Governança de Identidade e Autenticação
* **Unicidade de Identidade:** Um utilizador é único dentro de um **Tenant** através do seu e-mail. É permitida a existência do mesmo e-mail em diferentes Tenants, tratando-os como entidades isoladas.
* **Autenticação Multi-fator (MFA):** O sistema suporta obrigatoriedade de MFA (via TOTP/Apps Autenticadores ou SMS). O fluxo de login só é concluído após a validação bem-sucedida do segundo fator, caso o utilizador ou a aplicação o exijam.
* **Segurança de Credenciais:** As palavras-passe são processadas utilizando algoritmos de hashing com salting (Argon2), garantindo que dados em texto plano nunca residam na base de dados.

### 2. Segurança de Tokens e Sessões (Kill Switch)
* **JWT Stateless com Revogação Ativa:** Embora o sistema utilize JSON Web Tokens (JWT) para manter a natureza *stateless*, foi implementada uma **Token Deny List** no Redis.
* **Kill Switch:** Quando um administrador revoga o acesso de um utilizador ou uma sessão é encerrada, o identificador do token (JTI) é enviado para o Redis. Todas as validações subsequentes falharão instantaneamente, mesmo que o token ainda esteja dentro do prazo de validade cronológico.

### 3. Gestão de API Keys
* **Princípio da Visualização Única:** Ao gerar uma API Key para integrações externas, a chave é exibida em texto plano **apenas uma vez**.
* **Armazenamento Seguro:** Na base de dados, a API Key é armazenada como um hash. O sistema valida as chaves recebidas via cabeçalho `Authorization` comparando o hash enviado com o hash guardado, impossibilitando a recuperação da chave original em caso de fuga de dados da base de dados.

### 4. Telemetria e Ciclo de Vida de Dados
* **Escalabilidade de Logs:** O sistema diferencia logs de auditoria de logs de telemetria.
* **Expiração Automática (TTL):** Os dados de telemetria bruta (navegação, cliques, acessos técnicos) possuem índices **Time-To-Live (TTL)** no MongoDB. Estes dados expiram e são removidos automaticamente para evitar a degradação da performance.
* **Agregação Financeira:** Apenas os dados agregados necessários para faturação e relatórios de alto nível são preservados permanentemente.

### 5. Personalização White-Label e Segurança XSS
* **Customização Restrita:** Para garantir a segurança e evitar ataques de *Cross-Site Scripting* (XSS), a personalização das páginas de login pelos Tenants é limitada a variáveis estruturais: URL do logótipo, cores em formato HEX e seleção de fontes pré-aprovadas.
* **Injeção Dinâmica de CSS:** Estas variáveis são injetadas via CSS dinâmico, garantindo que o Tenant não possa injetar scripts maliciosos no fluxo de autenticação.

### 6. Fluxo de Autorização e Redirecionamento
* **Validação por Chave Pública:** Durante o fluxo OAuth2, a aplicação de terceiros deve utilizar uma **Public Key** vinculada ao Tenant para validar a legitimidade da resposta do SSO.
* **Lista de Origens Autorizadas:** O redirecionamento após a autenticação só é permitido para URLs previamente registadas e validadas pelo administrador do Tenant na plataforma.

### 7. Auditoria Imutável
* **Rastreabilidade Total:** O `AuditLog` é uma entidade de escrita única (*append-only*). Cada evento crítico (alteração de password, deleção de utilizador, falhas de login) regista obrigatoriamente o endereço IP, o User Agent, a data/hora exata e o tipo de mutação realizada.

---

## Stack Tecnológica

### Backend (Python/Flask)
* **Core:** Flask com `flask-openapi3` para documentação rigorosa e validação.
* **Persistência:** MongoDB via `MongoEngine`.
* **Performance:** Redis para caching de configurações White-label e gestão da Deny List.
* **Assincronismo:** Celery e Redis para disparo de e-mails transacionais e processamento de tarefas pesadas de fundo.
* **Observabilidade:** Integração com Sentry para APM e rastreio de erros.

### Frontend (Next.js)
* **Arquitetura:** React com Next.js seguindo o padrão *Bulletproof*.
* **UI/UX:** Tailwind CSS com componentes baseados em Radix UI (`shadcn/ui`) e animações com Framer Motion.
* **Data Fetching:** TanStack React Query para gestão eficiente de estado do servidor e caching.

---

## Estrutura do Projeto

* `server/`: API Backend estruturada com o padrão *Application Factory*.
* `web/`: Aplicação Frontend (Painel Administrativo, Onboarding e Páginas de Auth).

## Configuração e Instalação

### Backend
1. Navegue até à pasta `server/`.
2. Configure o ambiente virtual: `python -m venv venv`.
3. Ative o ambiente e instale as dependências: `pip install -r requirements.txt`.
4. Inicialize os dados básicos (Admin e Tenant Root): `python -m flask seed`.
5. Inicie o servidor: `python -m flask run`.

### Frontend
1. Navegue até à pasta `web/`.
2. Instale as dependências: `npm install`.
3. Inicie o ambiente de desenvolvimento: `npm run dev`.

---

## Documentação da API
Aceda à documentação interativa através dos seguintes endpoints (com o servidor ativo):
* **Scalar Reference:** `/docs/scalar`
* **Swagger UI:** `/docs`
* **OpenAPI Specification:** `/openapi.json`

## Docker Compose
`docker-compose.yml` sobe MongoDB, Redis, API Flask, worker Celery e frontend Next.js para desenvolvimento local.
Para produção, considere o deploy com Traefik e Cloudflare Tunnel, consulte [deploy/README.md](deploy/README.md).

## Testes
Backend:

```bash
cd server
python -m pytest -p no:cacheprovider tests

```
