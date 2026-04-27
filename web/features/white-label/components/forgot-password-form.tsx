"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "react-toastify";
import { z } from "zod";

import { http } from "@/lib/api/http";
import { Button } from "@/ui/button";
import { Input } from "@/ui/input";

const schema = z.object({
  email: z.string().email(),
});

type FormValues = z.infer<typeof schema>;

export function ForgotPasswordForm({ tenantSlug }: { tenantSlug: string }) {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "",
    },
  });
  const {
    formState: { errors, isSubmitting },
    register,
    handleSubmit,
  } = form;

  const onSubmit = handleSubmit(async (values) => {
    try {
      await http.post("/api/external/v1/password/forgot", {
        tenant_slug: tenantSlug,
        email: values.email,
      });
      toast.success("Se a conta existir, o email de recuperacao sera enviado.");
    } catch {
      toast.error("Nao foi possivel iniciar a recuperacao.");
    }
  });

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      <Input label="E-mail" error={errors.email?.message} {...register("email")} />
      <Button className="w-full" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Enviando..." : "Enviar link de recuperacao"}
      </Button>
    </form>
  );
}
