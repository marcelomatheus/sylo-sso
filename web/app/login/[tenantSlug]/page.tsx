import Image from "next/image";
import { notFound } from "next/navigation";

import { getBranding } from "@/features/white-label/api/get-branding";
import { OAuthLoginForm } from "@/features/white-label/components/oauth-login-form";

export const dynamic = "force-dynamic";

export default async function TenantLoginPage({
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
    <main
      className="min-h-screen py-10"
      style={{
        background: `linear-gradient(180deg, ${branding.branding.secondary_color}12 0%, #f7f1e7 34%, #efe5d6 100%)`,
      }}
    >
      <section className="shell grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="panel rounded-[2rem] p-6 sm:p-8">
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">{branding.tenant_name}</p>
          <h1
            className="mt-4 text-4xl font-semibold tracking-[-0.05em]"
            style={{ color: branding.branding.secondary_color, fontFamily: branding.branding.font_family }}
          >
            {branding.branding.login_title}
          </h1>
          <p className="mt-4 max-w-xl text-sm leading-7 text-muted">{branding.branding.login_subtitle}</p>
          <div className="mt-8 rounded-[1.75rem] border border-border bg-white/60 p-5">
            <p className="text-sm text-muted">
              Tenant slug: <strong>{branding.tenant_slug}</strong>
            </p>
            <p className="mt-2 text-sm text-muted">
              Suporte: <strong>{branding.branding.support_email ?? "nao informado"}</strong>
            </p>
          </div>
        </div>
        <div className="panel rounded-[2rem] p-6 sm:p-8">
          {branding.branding.logo_url ? (
            <div className="mb-6">
              <Image src={branding.branding.logo_url} alt={branding.tenant_name} width={160} height={48} unoptimized />
            </div>
          ) : null}
          <OAuthLoginForm tenantSlug={tenantSlug} branding={branding} />
        </div>
      </section>
    </main>
  );
}
