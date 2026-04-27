import { notFound } from "next/navigation";

import { getBranding } from "@/features/white-label/api/get-branding";
import { ResetPasswordForm } from "@/features/white-label/components/reset-password-form";

export const dynamic = "force-dynamic";

export default async function ResetPasswordConfirmPage({
  params,
  searchParams,
}: {
  params: Promise<{ tenantSlug: string }>;
  searchParams: Promise<{ token?: string }>;
}) {
  const { tenantSlug } = await params;
  const { token } = await searchParams;
  const branding = await getBranding(tenantSlug);

  if (!branding || !token) {
    notFound();
  }

  return (
    <main className="min-h-screen py-10">
      <section className="shell grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="panel rounded-[2rem] p-6 sm:p-8">
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">{branding.tenant_name}</p>
          <h1 className="mt-4 text-4xl font-semibold tracking-[-0.05em]">Definir nova senha</h1>
          <p className="mt-4 max-w-xl text-sm leading-7 text-muted">
            Escolha uma nova senha para restaurar o acesso a sua conta neste tenant.
          </p>
        </div>
        <div className="panel rounded-[2rem] p-6 sm:p-8">
          <ResetPasswordForm tenantSlug={tenantSlug} token={token} />
        </div>
      </section>
    </main>
  );
}
