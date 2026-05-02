import { Card } from "@/ui/card";

const steps = [
  "Crie o tenant inicial em /onboarding ou via POST /api/v1/tenants/internal/bootstrap.",
  "Autentique o administrador em /api/v1/auth/external/login para obter access e refresh tokens.",
  "Se quiser endurecer o acesso do painel, ative MFA por e-mail em /api/v1/users/internal/me/mfa/setup e valide o codigo em /verify.",
  "Cadastre uma Client App e API keys no painel administrativo ou via rotas internas.",
  "Defina Role Bindings para usuarios MEMBER acessarem apenas as aplicacoes e scopes autorizados.",
  "Use /api/v1/auth/external/authorize para obter authorization code e /api/v1/auth/external/token para trocar por access token.",
  "Para usuarios finais, use as paginas white-label de login, cadastro, verificacao e reset de senha.",
  "Proteja introspecao de token com API Key gerada em /api/v1/applications/internal/api-keys.",
];

const examples = {
  authorize: `POST /api/v1/auth/external/authorize
{
  "tenant_slug": "acme",
  "client_id": "client_123",
  "redirect_uri": "https://app.acme.com/callback",
  "email": "member@acme.com",
  "password": "Sup3rSecret!",
  "scopes": ["openid", "profile"],
  "consent_accepted": true,
  "mfa_code": "123456"
}`,
  register: `POST /api/v1/auth/external/register
{
  "tenant_slug": "acme",
  "client_id": "client_123",
  "redirect_uri": "https://app.acme.com/callback",
  "state": "opaque-state",
  "name": "Novo Usuario",
  "email": "novo@acme.com",
  "password": "Sup3rSecret!",
  "scopes": ["openid"],
  "consent_accepted": true
}`,
  roleBinding: `POST /api/v1/access/internal/role-bindings
{
  "tenant_id": "tenant_id",
  "user_id": "user_id",
  "client_app_id": "client_app_id",
  "roles": ["member"],
  "scopes": ["openid", "profile"],
  "status": "ACTIVE"
}`,
};

export default function DocsPage() {
  return (
    <main className="shell py-12">
      <div className="panel rounded-[2rem] p-6 sm:p-8">
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">Developer Docs</p>
        <h1 className="mt-4 text-4xl font-semibold tracking-[-0.05em]">Guia rapido de integracao</h1>
        <div className="mt-8 grid gap-4 lg:grid-cols-2">
          <Card className="rounded-[1.75rem] p-6">
            <h2 className="text-lg font-semibold">Fluxo recomendado</h2>
            <ol className="mt-4 space-y-3 text-sm leading-7 text-muted">
              {steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </Card>
          <Card className="rounded-[1.75rem] p-6">
            <h2 className="text-lg font-semibold">Endpoints principais</h2>
            <ul className="mt-4 space-y-3 font-mono text-xs text-muted">
              <li>POST /api/v1/tenants/internal/bootstrap</li>
              <li>POST /api/v1/auth/external/login</li>
              <li>POST /api/v1/auth/external/authorize</li>
              <li>POST /api/v1/auth/external/token</li>
              <li>POST /api/v1/users/internal/me/mfa/setup</li>
              <li>POST /api/v1/users/internal/me/mfa/verify</li>
              <li>POST /api/v1/access/internal/role-bindings</li>
              <li>POST /api/v1/auth/external/register</li>
              <li>POST /api/v1/auth/external/email/verify</li>
              <li>POST /api/v1/auth/external/password/reset</li>
              <li>POST /api/v1/auth/external/tokens/introspect</li>
              <li>GET /docs/openapi.json</li>
            </ul>
          </Card>
        </div>
        <div className="mt-4 grid gap-4 lg:grid-cols-3">
          <Card className="rounded-[1.75rem] p-6">
            <h2 className="text-lg font-semibold">Authorize com MFA</h2>
            <pre className="mt-4 overflow-x-auto rounded-2xl bg-surface-strong p-4 text-xs leading-6 text-muted">
              <code>{examples.authorize}</code>
            </pre>
          </Card>
          <Card className="rounded-[1.75rem] p-6">
            <h2 className="text-lg font-semibold">Cadastro via app satelite</h2>
            <pre className="mt-4 overflow-x-auto rounded-2xl bg-surface-strong p-4 text-xs leading-6 text-muted">
              <code>{examples.register}</code>
            </pre>
          </Card>
          <Card className="rounded-[1.75rem] p-6">
            <h2 className="text-lg font-semibold">Role binding</h2>
            <pre className="mt-4 overflow-x-auto rounded-2xl bg-surface-strong p-4 text-xs leading-6 text-muted">
              <code>{examples.roleBinding}</code>
            </pre>
          </Card>
        </div>
      </div>
    </main>
  );
}
