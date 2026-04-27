"use client";

import { useOnboardingForm } from "@/features/onboarding/hooks/use-onboarding-form";
import { Button } from "@/ui/button";
import { Input } from "@/ui/input";

export function OnboardingForm() {
  const { form, onSubmit } = useOnboardingForm();
  const {
    formState: { errors, isSubmitting },
    register,
  } = form;

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      <Input label="Nome do tenant" error={errors.tenantName?.message} {...register("tenantName")} />
      <Input label="Slug do tenant" error={errors.tenantSlug?.message} {...register("tenantSlug")} />
      <Input label="E-mail de contato" error={errors.contactEmail?.message} {...register("contactEmail")} />
      <Input label="Nome do admin" error={errors.adminName?.message} {...register("adminName")} />
      <Input label="E-mail do admin" error={errors.adminEmail?.message} {...register("adminEmail")} />
      <Input
        label="Senha inicial"
        type="password"
        error={errors.adminPassword?.message}
        {...register("adminPassword")}
      />
      <Button className="w-full" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Criando..." : "Criar tenant e entrar"}
      </Button>
    </form>
  );
}
