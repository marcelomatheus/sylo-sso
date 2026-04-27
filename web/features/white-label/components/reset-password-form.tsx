"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "react-toastify";
import { z } from "zod";

import { http } from "@/lib/api/http";
import { Button } from "@/ui/button";
import { Input } from "@/ui/input";

const schema = z
  .object({
    password: z.string().min(8),
    confirmPassword: z.string().min(8),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: "As senhas precisam ser iguais.",
    path: ["confirmPassword"],
  });

type FormValues = z.infer<typeof schema>;

export function ResetPasswordForm({
  tenantSlug,
  token,
}: {
  tenantSlug: string;
  token: string;
}) {
  const router = useRouter();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      password: "",
      confirmPassword: "",
    },
  });
  const {
    formState: { errors, isSubmitting },
    register,
    handleSubmit,
  } = form;

  const onSubmit = handleSubmit(async (values) => {
    try {
      await http.post("/api/external/v1/password/reset", {
        tenant_slug: tenantSlug,
        token,
        new_password: values.password,
      });
      toast.success("Senha atualizada com sucesso.");
      router.push(`/login/${tenantSlug}`);
    } catch {
      toast.error("Nao foi possivel redefinir a senha.");
    }
  });

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      <Input label="Nova senha" type="password" error={errors.password?.message} {...register("password")} />
      <Input
        label="Confirme a nova senha"
        type="password"
        error={errors.confirmPassword?.message}
        {...register("confirmPassword")}
      />
      <Button className="w-full" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Atualizando..." : "Atualizar senha"}
      </Button>
    </form>
  );
}
