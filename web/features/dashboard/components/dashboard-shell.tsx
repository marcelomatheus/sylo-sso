"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAdminOverview } from "@/features/dashboard/hooks/use-admin-overview";
import { AdminConsole } from "@/features/admin/components/admin-console";
import { Button } from "@/ui/button";
import { Card } from "@/ui/card";

export function DashboardShell() {
  const router = useRouter();
  const { session, hydrated, tenantsQuery, usersQuery, appsQuery, auditQuery, brandingQuery, consentQuery, telemetryQuery } = useAdminOverview();

  useEffect(() => {
    if (hydrated && !session) {
      router.replace("/admin/login");
    }
  }, [hydrated, router, session]);

  if (!hydrated || !session) {
    return null;
  }

  const cards = [
    { label: "Tenants", value: tenantsQuery.data?.length ?? 0 },
    { label: "Usuarios", value: usersQuery.data?.length ?? 0 },
    { label: "Aplicacoes", value: appsQuery.data?.length ?? 0 },
    { label: "Eventos", value: auditQuery.data?.length ?? 0 },
  ];

  return (
    <div className="space-y-6">
      <div className="panel rounded-[2rem] p-6 sm:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">Admin Dashboard</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-[-0.04em]">{session.user?.name}</h1>
            <p className="mt-3 text-sm leading-7 text-muted">
              Tenant ativo: <strong>{session.user?.tenantId}</strong>. Use este painel para revisar entidades principais e
              acessar a documentacao tecnica.
            </p>
          </div>
          {brandingQuery.data ? (
            <div className="rounded-[1.5rem] border border-border/70 bg-white/60 px-5 py-4">
              <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">Branding</p>
              <p className="mt-2 text-sm text-foreground">{brandingQuery.data.tenant_name}</p>
              <div className="mt-3 flex gap-2">
                <span className="size-5 rounded-full border border-black/10" style={{ background: brandingQuery.data.branding.primary_color }} />
                <span className="size-5 rounded-full border border-black/10" style={{ background: brandingQuery.data.branding.secondary_color }} />
              </div>
            </div>
          ) : null}
          <div className="flex gap-3">
            <Button asChild variant="secondary">
              <Link href="/docs">Docs</Link>
            </Button>
          </div>
        </div>
      </div>

      <section className="grid gap-4 md:grid-cols-4">
        {cards.map((card) => (
          <Card key={card.label} className="rounded-[1.75rem] p-5">
            <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">{card.label}</p>
            <p className="mt-4 text-3xl font-semibold">{card.value}</p>
          </Card>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-[1fr_1fr]">
        <Card className="rounded-[1.75rem] p-6">
          <h2 className="text-lg font-semibold">Usuarios</h2>
          <div className="mt-4 space-y-3 text-sm text-muted">
            {(usersQuery.data ?? []).map((user) => (
              <div key={user.id} className="rounded-2xl border border-border/70 bg-surface-strong px-4 py-3">
                <p className="font-medium text-foreground">{user.name}</p>
                <p>{user.email}</p>
                <p className="font-mono text-xs uppercase tracking-[0.18em]">{user.role}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card className="rounded-[1.75rem] p-6">
          <h2 className="text-lg font-semibold">Audit Log</h2>
          <div className="mt-4 space-y-3 text-sm text-muted">
            {(auditQuery.data ?? []).slice(0, 8).map((event) => (
              <div key={event.id} className="rounded-2xl border border-border/70 bg-surface-strong px-4 py-3">
                <p className="font-medium text-foreground">{event.action}</p>
                <p>{event.status}</p>
                <p className="font-mono text-xs uppercase tracking-[0.18em]">{event.actor_type}</p>
              </div>
            ))}
          </div>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1fr_1fr]">
        <Card className="rounded-[1.75rem] p-6">
          <h2 className="text-lg font-semibold">Consentimentos</h2>
          <div className="mt-4 space-y-3 text-sm text-muted">
            {(consentQuery.data ?? []).slice(0, 8).map((consent) => (
              <div key={consent.id} className="rounded-2xl border border-border/70 bg-surface-strong px-4 py-3">
                <p className="font-medium text-foreground">{consent.scopes.join(", ") || "Sem escopos"}</p>
                <p>{consent.revoked_at ? "Revogado" : "Ativo"}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card className="rounded-[1.75rem] p-6">
          <h2 className="text-lg font-semibold">Telemetria</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-border/70 bg-surface-strong px-4 py-3">
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-muted">Total</p>
              <p className="mt-2 text-2xl font-semibold text-foreground">{telemetryQuery.data?.total_events ?? 0}</p>
            </div>
            <div className="rounded-2xl border border-border/70 bg-surface-strong px-4 py-3">
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-muted">Falhas</p>
              <p className="mt-2 text-2xl font-semibold text-foreground">{telemetryQuery.data?.failed_events ?? 0}</p>
            </div>
            <div className="rounded-2xl border border-border/70 bg-surface-strong px-4 py-3">
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-muted">Logins</p>
              <p className="mt-2 text-2xl font-semibold text-foreground">{telemetryQuery.data?.login_events ?? 0}</p>
            </div>
            <div className="rounded-2xl border border-border/70 bg-surface-strong px-4 py-3">
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-muted">OAuth</p>
              <p className="mt-2 text-2xl font-semibold text-foreground">{telemetryQuery.data?.oauth_events ?? 0}</p>
            </div>
          </div>
        </Card>
      </section>

      <AdminConsole />
    </div>
  );
}
