"use client";

import { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { useAdminConsole } from "@/features/admin/hooks/use-admin-console";
import { useAdminOverview } from "@/features/dashboard/hooks/use-admin-overview";
import { Button } from "@/ui/button";
import { Card } from "@/ui/card";
import { Input } from "@/ui/input";

const tenantSchema = z.object({
  name: z.string().min(3),
  slug: z.string().min(3).regex(/^[a-z0-9-]+$/),
  contact_email: z.string().email(),
  plan: z.string().min(3),
});

const userSchema = z.object({
  name: z.string().min(3),
  email: z.string().email(),
  password: z.string().min(8),
  role: z.string().min(3),
  status: z.string().min(3),
});

const appSchema = z.object({
  name: z.string().min(2),
  description: z.string().optional(),
  redirect_uris: z.string().min(1),
  allowed_scopes: z.string().min(1),
  is_public: z.boolean(),
});

const apiKeySchema = z.object({
  name: z.string().min(2),
  scopes: z.string().min(1),
  client_app_id: z.string().optional(),
});

const roleBindingSchema = z.object({
  user_id: z.string().min(1),
  client_app_id: z.string().min(1),
  roles: z.string().min(1),
  scopes: z.string().min(1),
  status: z.string().min(3),
});

const mfaSchema = z.object({
  code: z.string().min(6).max(8),
});

const brandingSchema = z.object({
  logo_url: z.string().optional(),
  primary_color: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
  secondary_color: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
  font_family: z.string().min(2),
  support_email: z.string().email(),
  login_title: z.string().min(4),
  login_subtitle: z.string().min(8),
});

export function AdminConsole() {
  const { session, tenantsQuery, usersQuery, appsQuery, consentQuery, brandingQuery, roleBindingsQuery } = useAdminOverview();
  const {
    apiKeysQuery,
    roleBindingsQuery: roleBindingsListQuery,
    tenantMutation,
    userMutation,
    clientAppMutation,
    apiKeyMutation,
    apiKeyRevokeMutation,
    apiKeyRotateMutation,
    userUpdateMutation,
    clientAppUpdateMutation,
    tenantUpdateMutation,
    consentRevokeMutation,
    roleBindingMutation,
    roleBindingUpdateMutation,
    mfaSetupMutation,
    mfaVerifyMutation,
    mfaDisableMutation,
    mfaResendMutation,
  } = useAdminConsole();

  const tenantForm = useForm<z.infer<typeof tenantSchema>>({
    resolver: zodResolver(tenantSchema),
    defaultValues: { name: "", slug: "", contact_email: "", plan: "starter" },
  });
  const userForm = useForm<z.infer<typeof userSchema>>({
    resolver: zodResolver(userSchema),
    defaultValues: { name: "", email: "", password: "", role: "MEMBER", status: "ACTIVE" },
  });
  const appForm = useForm<z.infer<typeof appSchema>>({
    resolver: zodResolver(appSchema),
    defaultValues: { name: "", description: "", redirect_uris: "", allowed_scopes: "openid profile", is_public: true },
  });
  const apiKeyForm = useForm<z.infer<typeof apiKeySchema>>({
    resolver: zodResolver(apiKeySchema),
    defaultValues: { name: "", scopes: "tokens:introspect", client_app_id: "" },
  });
  const brandingForm = useForm<z.infer<typeof brandingSchema>>({
    resolver: zodResolver(brandingSchema),
    defaultValues: {
      logo_url: "",
      primary_color: "#f97316",
      secondary_color: "#111827",
      font_family: "Space Grotesk",
      support_email: "",
      login_title: "Acesse sua conta",
      login_subtitle: "Autenticacao centralizada para seus aplicativos.",
    },
  });
  const roleBindingForm = useForm<z.infer<typeof roleBindingSchema>>({
    resolver: zodResolver(roleBindingSchema),
    defaultValues: { user_id: "", client_app_id: "", roles: "member", scopes: "openid profile", status: "ACTIVE" },
  });
  const mfaForm = useForm<z.infer<typeof mfaSchema>>({
    resolver: zodResolver(mfaSchema),
    defaultValues: { code: "" },
  });

  const tenantId = session?.user?.tenantId;
  const latestApiKey = apiKeyMutation.data;
  const latestClientApp = clientAppMutation.data;
  const rotatedApiKey = apiKeyRotateMutation.data;
  const currentUser = usersQuery.data?.find((user) => user.id === session?.user?.id);

  useEffect(() => {
    if (!brandingQuery.data) {
      return;
    }
    brandingForm.reset({
      logo_url: brandingQuery.data.branding.logo_url ?? "",
      primary_color: brandingQuery.data.branding.primary_color,
      secondary_color: brandingQuery.data.branding.secondary_color,
      font_family: brandingQuery.data.branding.font_family,
      support_email: brandingQuery.data.branding.support_email ?? "",
      login_title: brandingQuery.data.branding.login_title,
      login_subtitle: brandingQuery.data.branding.login_subtitle,
    });
  }, [brandingForm, brandingQuery.data]);

  return (
    <section className="grid gap-4 lg:grid-cols-2">
      <Card className="rounded-[1.75rem] p-6">
        <h2 className="text-lg font-semibold">Criar tenant</h2>
        <form
          className="mt-4 space-y-3"
          onSubmit={tenantForm.handleSubmit(async (values) => {
            await tenantMutation.mutateAsync({
              ...values,
              lgpd_consent_required: true,
            });
            tenantForm.reset();
          })}
        >
          <Input label="Nome" {...tenantForm.register("name")} error={tenantForm.formState.errors.name?.message} />
          <Input label="Slug" {...tenantForm.register("slug")} error={tenantForm.formState.errors.slug?.message} />
          <Input
            label="E-mail de contato"
            {...tenantForm.register("contact_email")}
            error={tenantForm.formState.errors.contact_email?.message}
          />
          <Input label="Plano" {...tenantForm.register("plan")} error={tenantForm.formState.errors.plan?.message} />
          <Button className="w-full" disabled={tenantMutation.isPending} type="submit">
            {tenantMutation.isPending ? "Criando..." : "Criar tenant"}
          </Button>
        </form>
      </Card>

      <Card className="rounded-[1.75rem] p-6">
        <h2 className="text-lg font-semibold">Criar usuario</h2>
        <form
          className="mt-4 space-y-3"
          onSubmit={userForm.handleSubmit(async (values) => {
            if (!tenantId) {
              return;
            }
            await userMutation.mutateAsync({
              tenant_id: tenantId,
              ...values,
            });
            userForm.reset({ name: "", email: "", password: "", role: "MEMBER", status: "ACTIVE" });
          })}
        >
          <Input label="Nome" {...userForm.register("name")} error={userForm.formState.errors.name?.message} />
          <Input label="E-mail" {...userForm.register("email")} error={userForm.formState.errors.email?.message} />
          <Input label="Senha" type="password" {...userForm.register("password")} error={userForm.formState.errors.password?.message} />
          <Input label="Role" {...userForm.register("role")} error={userForm.formState.errors.role?.message} />
          <Input label="Status" {...userForm.register("status")} error={userForm.formState.errors.status?.message} />
          <Button className="w-full" disabled={userMutation.isPending || !tenantId} type="submit">
            {userMutation.isPending ? "Criando..." : "Criar usuario"}
          </Button>
        </form>
      </Card>

      <Card className="rounded-[1.75rem] p-6">
        <h2 className="text-lg font-semibold">Criar aplicacao</h2>
        <form
          className="mt-4 space-y-3"
          onSubmit={appForm.handleSubmit(async (values) => {
            if (!tenantId) {
              return;
            }
            await clientAppMutation.mutateAsync({
              tenant_id: tenantId,
              name: values.name,
              description: values.description,
              redirect_uris: values.redirect_uris.split(",").map((item) => item.trim()).filter(Boolean),
              allowed_scopes: values.allowed_scopes.split(" ").map((item) => item.trim()).filter(Boolean),
              is_public: values.is_public,
            });
          })}
        >
          <Input label="Nome" {...appForm.register("name")} error={appForm.formState.errors.name?.message} />
          <Input label="Descricao" {...appForm.register("description")} error={appForm.formState.errors.description?.message} />
          <Input
            label="Redirect URIs"
            {...appForm.register("redirect_uris")}
            error={appForm.formState.errors.redirect_uris?.message}
          />
          <Input
            label="Scopes"
            {...appForm.register("allowed_scopes")}
            error={appForm.formState.errors.allowed_scopes?.message}
          />
          <label className="flex items-center gap-3 text-sm text-muted">
            <input type="checkbox" {...appForm.register("is_public")} />
            Aplicacao publica
          </label>
          <Button className="w-full" disabled={clientAppMutation.isPending || !tenantId} type="submit">
            {clientAppMutation.isPending ? "Criando..." : "Criar aplicacao"}
          </Button>
        </form>
        {latestClientApp?.client_secret ? (
          <div className="mt-4 rounded-2xl border border-border/70 bg-surface-strong p-4 text-sm text-muted">
            <p className="font-medium text-foreground">Client secret gerado</p>
            <p className="mt-2 break-all font-mono text-xs">{latestClientApp.client_secret}</p>
          </div>
        ) : null}
      </Card>

      <Card className="rounded-[1.75rem] p-6">
        <h2 className="text-lg font-semibold">Criar API key</h2>
        <form
          className="mt-4 space-y-3"
          onSubmit={apiKeyForm.handleSubmit(async (values) => {
            if (!tenantId) {
              return;
            }
            await apiKeyMutation.mutateAsync({
              tenant_id: tenantId,
              name: values.name,
              scopes: values.scopes.split(" ").map((item) => item.trim()).filter(Boolean),
              client_app_id: values.client_app_id || null,
            });
          })}
        >
          <Input label="Nome" {...apiKeyForm.register("name")} error={apiKeyForm.formState.errors.name?.message} />
          <Input
            label="Scopes"
            {...apiKeyForm.register("scopes")}
            error={apiKeyForm.formState.errors.scopes?.message}
          />
          <Input label="Client App ID opcional" {...apiKeyForm.register("client_app_id")} />
          <Button className="w-full" disabled={apiKeyMutation.isPending || !tenantId} type="submit">
            {apiKeyMutation.isPending ? "Gerando..." : "Gerar API key"}
          </Button>
        </form>
        {latestApiKey?.secret ? (
          <div className="mt-4 rounded-2xl border border-border/70 bg-surface-strong p-4 text-sm text-muted">
            <p className="font-medium text-foreground">Segredo exibido uma unica vez</p>
            <p className="mt-2 break-all font-mono text-xs">{latestApiKey.secret}</p>
          </div>
        ) : null}
        {rotatedApiKey?.secret ? (
          <div className="mt-4 rounded-2xl border border-border/70 bg-surface-strong p-4 text-sm text-muted">
            <p className="font-medium text-foreground">Segredo da API key rotacionada</p>
            <p className="mt-2 break-all font-mono text-xs">{rotatedApiKey.secret}</p>
          </div>
        ) : null}
      </Card>

      <Card className="rounded-[1.75rem] p-6">
        <h2 className="text-lg font-semibold">Acesso por aplicacao</h2>
        <form
          className="mt-4 space-y-3"
          onSubmit={roleBindingForm.handleSubmit(async (values) => {
            if (!tenantId) {
              return;
            }
            await roleBindingMutation.mutateAsync({
              tenant_id: tenantId,
              user_id: values.user_id,
              client_app_id: values.client_app_id,
              roles: values.roles.split(" ").map((item) => item.trim()).filter(Boolean),
              scopes: values.scopes.split(" ").map((item) => item.trim()).filter(Boolean),
              status: values.status,
            });
          })}
        >
          <Input label="User ID" {...roleBindingForm.register("user_id")} error={roleBindingForm.formState.errors.user_id?.message} />
          <Input
            label="Client App ID"
            {...roleBindingForm.register("client_app_id")}
            error={roleBindingForm.formState.errors.client_app_id?.message}
          />
          <Input label="Roles" {...roleBindingForm.register("roles")} error={roleBindingForm.formState.errors.roles?.message} />
          <Input label="Scopes" {...roleBindingForm.register("scopes")} error={roleBindingForm.formState.errors.scopes?.message} />
          <Input label="Status" {...roleBindingForm.register("status")} error={roleBindingForm.formState.errors.status?.message} />
          <Button className="w-full" disabled={roleBindingMutation.isPending || !tenantId} type="submit">
            {roleBindingMutation.isPending ? "Salvando..." : "Criar acesso"}
          </Button>
        </form>
      </Card>

      <Card className="rounded-[1.75rem] p-6 lg:col-span-2">
        <h2 className="text-lg font-semibold">Operacoes rapidas</h2>
        <div className="mt-4 grid gap-4 lg:grid-cols-3">
          <div className="rounded-2xl border border-border/70 bg-surface-strong p-4">
            <p className="font-medium text-foreground">Usuarios atuais</p>
            <div className="mt-3 space-y-3 text-sm text-muted">
              {(usersQuery.data ?? []).slice(0, 6).map((user) => (
                <div key={user.id} className="rounded-xl border border-border/60 bg-white/60 px-3 py-3">
                  <p>{user.name}</p>
                  <p className="font-mono text-xs">{user.status}</p>
                  <div className="mt-3 flex gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => userUpdateMutation.mutate({ userId: user.id, payload: { status: user.status === "ACTIVE" ? "DISABLED" : "ACTIVE" } })}
                    >
                      {user.status === "ACTIVE" ? "Bloquear" : "Ativar"}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-border/70 bg-surface-strong p-4">
            <p className="font-medium text-foreground">Aplicacoes</p>
            <div className="mt-3 space-y-3 text-sm text-muted">
              {(appsQuery.data ?? []).slice(0, 6).map((app) => (
                <div key={app.id} className="rounded-xl border border-border/60 bg-white/60 px-3 py-3">
                  <p>{app.name}</p>
                  <p className="font-mono text-xs">{app.status}</p>
                  <div className="mt-3 flex gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() =>
                        clientAppUpdateMutation.mutate({
                          clientAppId: app.id,
                          payload: { status: app.status === "ACTIVE" ? "DISABLED" : "ACTIVE" },
                        })
                      }
                    >
                      {app.status === "ACTIVE" ? "Desativar" : "Ativar"}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-border/70 bg-surface-strong p-4">
            <p className="font-medium text-foreground">API Keys</p>
            <div className="mt-3 space-y-3 text-sm text-muted">
              {(apiKeysQuery.data ?? []).slice(0, 6).map((key) => (
                <div key={key.id} className="rounded-xl border border-border/60 bg-white/60 px-3 py-3">
                  <p>{key.name}</p>
                  <p className="font-mono text-xs">{key.key_prefix}</p>
                  <div className="mt-3 flex gap-2">
                    <Button type="button" variant="secondary" onClick={() => apiKeyRevokeMutation.mutate(key.id)} disabled={key.status === "REVOKED"}>
                      {key.status === "REVOKED" ? "Revogada" : "Revogar"}
                    </Button>
                    <Button type="button" variant="secondary" onClick={() => apiKeyRotateMutation.mutate(key.id)}>
                      Rotacionar
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-4 flex gap-3">
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              const currentTenant = tenantsQuery.data?.find((item) => item.id === tenantId);
              if (currentTenant) {
                tenantUpdateMutation.mutate({
                  tenantId: currentTenant.id,
                  payload: { lgpd_consent_required: !currentTenant.lgpd_consent_required },
                });
              }
            }}
            disabled={!tenantId}
          >
            Alternar exigencia LGPD
          </Button>
        </div>
      </Card>

      <Card className="rounded-[1.75rem] p-6">
        <h2 className="text-lg font-semibold">Editar branding</h2>
        <form
          className="mt-4 space-y-3"
          onSubmit={brandingForm.handleSubmit(async (values) => {
            const currentTenant = tenantsQuery.data?.find((item) => item.id === tenantId);
            if (!currentTenant) {
              return;
            }
            await tenantUpdateMutation.mutateAsync({
              tenantId: currentTenant.id,
              payload: {
                branding: {
                  ...values,
                  logo_url: values.logo_url || null,
                  support_email: values.support_email || null,
                },
              },
            });
          })}
        >
          <Input label="Logo URL" {...brandingForm.register("logo_url")} error={brandingForm.formState.errors.logo_url?.message} />
          <Input
            label="Cor primaria"
            {...brandingForm.register("primary_color")}
            error={brandingForm.formState.errors.primary_color?.message}
          />
          <Input
            label="Cor secundaria"
            {...brandingForm.register("secondary_color")}
            error={brandingForm.formState.errors.secondary_color?.message}
          />
          <Input
            label="Fonte"
            {...brandingForm.register("font_family")}
            error={brandingForm.formState.errors.font_family?.message}
          />
          <Input
            label="E-mail de suporte"
            {...brandingForm.register("support_email")}
            error={brandingForm.formState.errors.support_email?.message}
          />
          <Input
            label="Titulo do login"
            {...brandingForm.register("login_title")}
            error={brandingForm.formState.errors.login_title?.message}
          />
          <Input
            label="Subtitulo do login"
            {...brandingForm.register("login_subtitle")}
            error={brandingForm.formState.errors.login_subtitle?.message}
          />
          <Button className="w-full" disabled={tenantUpdateMutation.isPending || !tenantId} type="submit">
            {tenantUpdateMutation.isPending ? "Salvando..." : "Salvar branding"}
          </Button>
        </form>
      </Card>

      <Card className="rounded-[1.75rem] p-6">
        <h2 className="text-lg font-semibold">Consentimentos ativos</h2>
        <div className="mt-4 space-y-3 text-sm text-muted">
          {(consentQuery.data ?? []).slice(0, 8).map((consent) => (
            <div key={consent.id} className="rounded-xl border border-border/60 bg-white/60 px-3 py-3">
              <p className="font-medium text-foreground">{consent.scopes.join(", ") || "Sem escopos"}</p>
              <p>{consent.revoked_at ? "Revogado" : "Ativo"}</p>
              <div className="mt-3 flex gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => consentRevokeMutation.mutate(consent.id)}
                  disabled={Boolean(consent.revoked_at)}
                >
                  {consent.revoked_at ? "Revogado" : "Revogar"}
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card className="rounded-[1.75rem] p-6">
        <h2 className="text-lg font-semibold">MFA do administrador</h2>
        <div className="mt-4 space-y-3 text-sm text-muted">
          <p>Status atual: {currentUser?.mfa_enabled ? "Ativo" : "Inativo"}</p>
          <div className="flex flex-wrap gap-3">
            <Button type="button" variant="secondary" onClick={() => mfaSetupMutation.mutate("EMAIL")}>
              Ativar por e-mail
            </Button>
            <Button type="button" variant="secondary" onClick={() => mfaDisableMutation.mutate()} disabled={!currentUser?.mfa_enabled}>
              Desativar
            </Button>
            <Button type="button" variant="secondary" onClick={() => mfaResendMutation.mutate()} disabled={currentUser?.mfa_method !== "EMAIL"}>
              Reenviar codigo
            </Button>
          </div>
          {mfaSetupMutation.data ? (
            <div className="rounded-2xl border border-border/70 bg-surface-strong p-4">
              <p className="font-medium text-foreground">Setup de MFA</p>
              <p className="mt-2 text-xs">{mfaSetupMutation.data.method === "EMAIL" ? "Um codigo foi enviado para o e-mail do administrador." : "Use o segredo abaixo no autenticador."}</p>
              {mfaSetupMutation.data.secret ? <p className="mt-2 break-all font-mono text-xs">{mfaSetupMutation.data.secret}</p> : null}
              {mfaSetupMutation.data.otpauth_uri ? <p className="mt-2 break-all text-xs">{mfaSetupMutation.data.otpauth_uri}</p> : null}
            </div>
          ) : null}
          <form
            className="space-y-3"
            onSubmit={mfaForm.handleSubmit(async (values) => {
              await mfaVerifyMutation.mutateAsync(values.code);
              mfaForm.reset();
            })}
          >
            <Input label="Codigo do autenticador" {...mfaForm.register("code")} error={mfaForm.formState.errors.code?.message} />
            <Button className="w-full" disabled={mfaVerifyMutation.isPending} type="submit">
              {mfaVerifyMutation.isPending ? "Validando..." : "Ativar MFA"}
            </Button>
          </form>
        </div>
      </Card>

      <Card className="rounded-[1.75rem] p-6 lg:col-span-2">
        <h2 className="text-lg font-semibold">Role bindings</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2 text-sm text-muted">
          {(roleBindingsQuery.data ?? roleBindingsListQuery.data ?? []).slice(0, 8).map((binding) => (
            <div key={binding.id} className="rounded-xl border border-border/60 bg-white/60 px-3 py-3">
              <p className="font-medium text-foreground">{binding.roles.join(", ") || "Sem roles"}</p>
              <p>Scopes: {binding.scopes.join(", ") || "Todos os scopes da app"}</p>
              <p>Status: {binding.status}</p>
              <div className="mt-3 flex gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() =>
                    roleBindingUpdateMutation.mutate({
                      roleBindingId: binding.id,
                      payload: { status: binding.status === "ACTIVE" ? "DISABLED" : "ACTIVE" },
                    })
                  }
                >
                  {binding.status === "ACTIVE" ? "Desativar" : "Ativar"}
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </section>
  );
}
