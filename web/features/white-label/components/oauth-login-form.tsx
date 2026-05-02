"use client";

import Link from "next/link";
import { AxiosError } from "axios";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { toast } from "react-toastify";
import { z } from "zod";

import type { TenantBrandingResponse } from "@/features/white-label/api/get-branding";
import { http } from "@/lib/api/http";
import { Button } from "@/ui/button";
import { Input } from "@/ui/input";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  consentAccepted: z.boolean(),
  mfaCode: z.string().min(6).max(8).optional().or(z.literal("")),
});

type FormValues = z.infer<typeof schema>;

export function OAuthLoginForm({
  tenantSlug,
  branding,
}: {
  tenantSlug: string;
  branding: TenantBrandingResponse;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [mfaRequired, setMfaRequired] = useState(false);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "",
      password: "",
      consentAccepted: false,
      mfaCode: "",
    },
  });
  const {
    formState: { errors, isSubmitting },
    register,
    control,
    handleSubmit,
  } = form;
  const consentAccepted = useWatch({
    control,
    name: "consentAccepted",
    defaultValue: false,
  });

  const onSubmit = handleSubmit(async (values) => {
    const clientId = searchParams.get("client_id");
    const redirectUri = searchParams.get("redirect_uri");
    const state = searchParams.get("state");
    const scopes = (searchParams.get("scope") ?? "")
      .split(" ")
      .map((scope) => scope.trim())
      .filter(Boolean);

    try {
      if (clientId && redirectUri) {
        const response = await http.post("/api/v1/auth/external/authorize", {
          tenant_slug: tenantSlug,
          client_id: clientId,
          redirect_uri: redirectUri,
          email: values.email,
          password: values.password,
          scopes,
          state,
          consent_accepted: values.consentAccepted,
          mfa_code: values.mfaCode || undefined,
        });
        setMfaRequired(false);
        window.location.assign(response.data.redirect_to);
        return;
      }

      const response = await http.post("/api/v1/auth/external/login", {
        tenant_slug: tenantSlug,
        email: values.email,
        password: values.password,
        mfa_code: values.mfaCode || undefined,
      });
      setMfaRequired(false);
      toast.success("Sessao iniciada com sucesso.");
      router.push(`/admin/login?tenant=${tenantSlug}&email=${encodeURIComponent(response.data.user.email)}`);
    } catch (error) {
      const axiosError = error as AxiosError<{ error?: { message?: string; details?: { mfa_required?: boolean } } }>;
      if (axiosError.response?.data?.error?.details?.mfa_required) {
        setMfaRequired(true);
        toast.error("Informe o codigo MFA para continuar.");
        return;
      }
      toast.error(axiosError.response?.data?.error?.message ?? "Nao foi possivel autenticar neste tenant.");
    }
  });

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      <Input label="E-mail" placeholder="voce@empresa.com" error={errors.email?.message} {...register("email")} />
      <Input label="Senha" type="password" placeholder="********" error={errors.password?.message} {...register("password")} />
      {mfaRequired ? <Input label="Codigo MFA" placeholder="123456" error={errors.mfaCode?.message} {...register("mfaCode")} /> : null}
      {branding.lgpd_consent_required ? (
        <label className="flex items-start gap-3 rounded-2xl border border-border bg-white/50 px-4 py-3 text-sm leading-6 text-muted">
          <input className="mt-1 size-4 accent-[var(--accent)]" type="checkbox" {...register("consentAccepted")} />
          <span>
            Autorizo o compartilhamento dos escopos solicitados pela aplicacao satelite deste tenant.
          </span>
        </label>
      ) : null}
      <Button className="w-full" disabled={isSubmitting || (branding.lgpd_consent_required && !consentAccepted)} type="submit">
        {isSubmitting ? "Autenticando..." : "Continuar"}
      </Button>
      <div className="flex items-center justify-between text-sm text-muted">
        <Link href={`/register/${tenantSlug}`} className="hover:text-foreground">
          Criar conta
        </Link>
        <Link href={`/verify-email/${tenantSlug}`} className="hover:text-foreground">
          Verificar e-mail
        </Link>
        <Link href={`/reset-password/${tenantSlug}`} className="hover:text-foreground">
          Esqueci minha senha
        </Link>
      </div>
    </form>
  );
}
