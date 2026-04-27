import { Suspense } from "react";

import { LoginForm } from "@/features/auth/components/login-form";

export default function AdminLoginPage() {
  return (
    <main className="shell py-12">
      <section className="mx-auto max-w-xl">
        <div className="panel rounded-[2rem] p-6 sm:p-8">
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">Admin Access</p>
          <h1 className="mt-4 text-3xl font-semibold tracking-[-0.04em]">Entrar no painel do Sylo</h1>
          <p className="mt-3 text-sm leading-7 text-muted">
            Use o tenant slug e as credenciais do administrador para acessar o painel interno.
          </p>
          <div className="mt-8">
            <Suspense fallback={null}>
              <LoginForm />
            </Suspense>
          </div>
        </div>
      </section>
    </main>
  );
}
