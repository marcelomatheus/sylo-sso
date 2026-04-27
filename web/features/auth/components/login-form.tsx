"use client";

import { useLoginForm } from "@/features/auth/hooks/use-login-form";
import { Button } from "@/ui/button";
import { Input } from "@/ui/input";

export function LoginForm() {
  const { form, onSubmit, mfaRequired } = useLoginForm();
  const {
    formState: { errors, isSubmitting },
    register,
  } = form;

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      <Input label="Tenant slug" placeholder="acme" error={errors.tenantSlug?.message} {...register("tenantSlug")} />
      <Input
        label="E-mail"
        placeholder="admin@empresa.com"
        error={errors.email?.message}
        {...register("email")}
      />
      <Input
        label="Senha"
        type="password"
        placeholder="********"
        error={errors.password?.message}
        {...register("password")}
      />
      {mfaRequired ? (
        <Input
          label="Codigo MFA"
          placeholder="123456"
          error={errors.mfaCode?.message}
          {...register("mfaCode")}
        />
      ) : null}
      <Button className="w-full" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Entrando..." : "Entrar"}
      </Button>
    </form>
  );
}
