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

export function ResendVerificationForm({ tenantSlug }: { tenantSlug: string }) {
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
      await http.post("/api/v1/auth/external/email/resend", {
        tenant_slug: tenantSlug,
        email: values.email,
      });
      toast.success("Se a conta existir, um novo email sera enviado.");
    } catch {
      toast.error("Nao foi possivel reenviar a verificacao.");
    }
  });

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      <Input label="E-mail" error={errors.email?.message} {...register("email")} />
      <Button className="w-full" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Reenviando..." : "Reenviar verificacao"}
      </Button>
    </form>
  );
}
