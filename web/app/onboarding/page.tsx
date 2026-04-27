import { OnboardingForm } from "@/features/onboarding/components/onboarding-form";

export default function OnboardingPage() {
  return (
    <main className="shell py-12">
      <section className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="panel rounded-[2rem] p-6 sm:p-8">
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">Launch</p>
          <h1 className="mt-4 text-4xl font-semibold tracking-[-0.05em]">Bootstrap do primeiro tenant</h1>
          <p className="mt-4 max-w-xl text-sm leading-7 text-muted">
            Esse fluxo cria o tenant inicial, o primeiro usuario administrador e devolve a sessao que libera o uso do
            painel interno.
          </p>
          <ul className="mt-6 space-y-3 text-sm text-muted">
            <li>Tenant com branding inicial e plano de entrada.</li>
            <li>Usuario admin com senha em Argon2.</li>
            <li>JWT com refresh token opaco pronto para uso no frontend.</li>
          </ul>
        </div>
        <div className="panel rounded-[2rem] p-6 sm:p-8">
          <OnboardingForm />
        </div>
      </section>
    </main>
  );
}
