"use client";

import { useSearchParams } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "react-toastify";
import { z } from "zod";

import { http } from "@/lib/api/http";
import { Button } from "@/ui/button";
import { Input } from "@/ui/input";

const schema = z.object({
  name: z.string().min(3),
  email: z.string().email(),
  password: z.string().min(8),
  consentAccepted: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

export function PublicRegistrationForm({ tenantSlug, lgpdRequired }: { tenantSlug: string; lgpdRequired: boolean }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      email: "",
      password: "",
      consentAccepted: false,
    },
  });
  const {
    formState: { errors, isSubmitting },
    register,
    handleSubmit,
  } = form;

  const onSubmit = handleSubmit(async (values) => {
    const clientId = searchParams.get("client_id");
    const redirectUri = searchParams.get("redirect_uri");
    const state = searchParams.get("state");
    const scopes = (searchParams.get("scope") ?? "")
      .split(" ")
      .map((scope) => scope.trim())
      .filter(Boolean);
    try {
      const response = await http.post("/api/v1/auth/external/register", {
        tenant_slug: tenantSlug,
        name: values.name,
        email: values.email,
        password: values.password,
        client_id: clientId || undefined,
        redirect_uri: redirectUri || undefined,
        state: state || undefined,
        scopes,
        consent_accepted: values.consentAccepted,
      });
      toast.success("Conta criada com sucesso.");
      const redirectQuery = response.data.next_step?.redirect_uri
        ? `?redirect_uri=${encodeURIComponent(response.data.next_step.redirect_uri)}${response.data.next_step.state ? `&state=${encodeURIComponent(response.data.next_step.state)}` : ""}`
        : "";
      router.push(`/verify-email/${tenantSlug}${redirectQuery}`);
    } catch {
      toast.error("Nao foi possivel concluir o cadastro.");
    }
  });

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      <Input label="Nome" error={errors.name?.message} {...register("name")} />
      <Input label="E-mail" error={errors.email?.message} {...register("email")} />
      <Input label="Senha" type="password" error={errors.password?.message} {...register("password")} />
      {lgpdRequired && searchParams.get("client_id") ? (
        <label className="flex items-start gap-3 rounded-2xl border border-border bg-white/50 px-4 py-3 text-sm leading-6 text-muted">
          <input className="mt-1 size-4 accent-[var(--accent)]" type="checkbox" {...register("consentAccepted")} />
          <span>Autorizo o compartilhamento dos escopos solicitados pela aplicacao satelite.</span>
        </label>
      ) : null}
      <Button className="w-full" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Criando conta..." : "Criar conta"}
      </Button>
    </form>
  );
}
