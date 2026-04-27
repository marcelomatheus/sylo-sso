import { notFound } from "next/navigation";

import { getBranding } from "@/features/white-label/api/get-branding";
import { PublicRegistrationForm } from "@/features/white-label/components/public-registration-form";

export const dynamic = "force-dynamic";

export default async function TenantRegistrationPage({
  params,
}: {
  params: Promise<{ tenantSlug: string }>;
}) {
  const { tenantSlug } = await params;
  const branding = await getBranding(tenantSlug);

  if (!branding) {
    notFound();
  }

  return (
    <main className="min-h-screen py-10">
      <section className="shell grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="panel rounded-[2rem] p-6 sm:p-8">
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">{branding.tenant_name}</p>
          <h1 className="mt-4 text-4xl font-semibold tracking-[-0.05em]">Criar conta no tenant</h1>
          <p className="mt-4 max-w-xl text-sm leading-7 text-muted">
            Cadastre-se para acessar os aplicativos integrados ao ecossistema deste tenant.
          </p>
        </div>
        <div className="panel rounded-[2rem] p-6 sm:p-8">
          <PublicRegistrationForm tenantSlug={tenantSlug} lgpdRequired={branding.lgpd_consent_required} />
        </div>
      </section>
    </main>
  );
}
