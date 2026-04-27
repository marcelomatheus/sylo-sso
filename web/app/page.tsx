import Link from "next/link";
import { ArrowRight, LockKeyhole, ShieldCheck, Workflow } from "lucide-react";
import Image from "next/image";
import { ButtonLink } from "@/ui/button";
import { Card } from "@/ui/card";

const pillars = [
  {
    title: "OAuth2 com PKCE",
    description: "Fluxo de authorization code, refresh token rotacionado e introspecao protegida por API Key.",
    icon: LockKeyhole,
  },
  {
    title: "Multi-tenant de verdade",
    description: "Separacao por tenant, branding white-label e unicidade de usuarios por tenant, nao global.",
    icon: ShieldCheck,
  },
  {
    title: "Operacao B2B",
    description: "Painel admin, logs de auditoria, onboarding guiado e base para observabilidade e rate limiting.",
    icon: Workflow,
  },
];

export default function HomePage() {
  return (
    <main className="pb-20">
      <section className="shell pt-8">
        <div className="panel rounded-[2rem] border px-6 py-5 sm:px-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl space-y-5">
              <Image src="/logo.png" alt="Sylo SSO" width={300} height={100} />
              <h1 className="text-4xl font-semibold tracking-[-0.05em] sm:text-6xl">
                Identidade headless para equipes B2B que não aceitam gambiarra no login.
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-muted">
                OAuth2 com PKCE e painel admnistrativo para gestão de usuários e acessos, tudo pronto para escalar com sua empresa. Diga adeus às soluções de autenticação frágeis e mal integradas, e dê as boas-vindas a uma base sólida e segura para o crescimento do seu negócio.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <ButtonLink href="/onboarding">Começar</ButtonLink>
              <ButtonLink href="/admin/login" variant="secondary">
                Entrar no painel
              </ButtonLink>
            </div>
          </div>
        </div>
      </section>

      <section className="shell mt-8 grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <Card className="rounded-[2rem] p-6 sm:p-8">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">Foundation</p>
              <h2 className="mt-3 text-2xl font-semibold">Base operacional pronta para evoluir</h2>
            </div>
            <ArrowRight className="hidden size-6 text-accent sm:block" />
          </div>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <div className="rounded-3xl border border-border/80 bg-surface-strong p-5">
              <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">Backend</p>
              <p className="mt-3 text-sm leading-7 text-muted">
                Application factory, MongoEngine com modelos de identidade, guards reutilizaveis e suite inicial de testes.
              </p>
            </div>
            <div className="rounded-3xl border border-border/80 bg-surface-strong p-5">
              <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">Frontend</p>
              <p className="mt-3 text-sm leading-7 text-muted">
                Next.js com React Query, Zustand, Axios com refresh e paginas iniciais para login, dashboard e onboarding.
              </p>
            </div>
          </div>
        </Card>

        <Card className="rounded-[2rem] p-6 sm:p-8">
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">Rotas iniciais</p>
          <ul className="mt-5 space-y-3 text-sm text-muted">
            <li>`/api/internal/v1/bootstrap` para o primeiro admin.</li>
            <li>`/oauth/v1/login`, `/authorize`, `/token`, `/revoke`.</li>
            <li>`/api/external/v1/tokens/introspect` com API Key.</li>
            <li>`/docs/openapi.json` e UI automática em `/docs/`.</li>
          </ul>
          <div className="mt-6">
            <Link href="/docs" className="inline-flex items-center gap-2 text-sm font-medium text-accent-strong">
              Ver guia de integracao <ArrowRight className="size-4" />
            </Link>
          </div>
        </Card>
      </section>

      <section className="shell mt-8 grid gap-4 md:grid-cols-3">
        {pillars.map(({ icon: Icon, title, description }) => (
          <Card key={title} className="rounded-[2rem] p-6">
            <Icon className="size-8 text-accent" />
            <h3 className="mt-5 text-xl font-semibold">{title}</h3>
            <p className="mt-3 text-sm leading-7 text-muted">{description}</p>
          </Card>
        ))}
      </section>
    </main>
  );
}
