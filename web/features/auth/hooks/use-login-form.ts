"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { AxiosError } from "axios";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "react-toastify";
import { z } from "zod";

import { authStore } from "@/features/auth/store/auth-store";
import { http } from "@/lib/api/http";

const loginSchema = z.object({
  tenantSlug: z.string().min(3),
  email: z.string().email(),
  password: z.string().min(8),
  mfaCode: z.string().min(6).max(8).optional().or(z.literal("")),
});

type LoginValues = z.infer<typeof loginSchema>;

export function useLoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [mfaRequired, setMfaRequired] = useState(false);
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      tenantSlug: "",
      email: "",
      password: "",
      mfaCode: "",
    },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      const response = await http.post("/oauth/v1/login", {
        tenant_slug: values.tenantSlug,
        email: values.email,
        password: values.password,
        mfa_code: values.mfaCode || undefined,
      });
      console.log("Login response:", response);
      setMfaRequired(false);
      authStore.getState().setSession({
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
        expiresAt: response.data.expires_at,
        user: {
          id: response.data.user.id,
          tenantId: response.data.user.tenant_id,
          email: response.data.user.email,
          name: response.data.user.name,
          role: response.data.user.role,
        },
      });
      toast.success("Sessao iniciada com sucesso.");
      router.push(searchParams.get("next") || "/admin");
    } catch (error) {
      const axiosError = error as AxiosError<{ error?: { message?: string; details?: { mfa_required?: boolean } } }>;
      if (axiosError.response?.data?.error?.details?.mfa_required) {
        setMfaRequired(true);
        toast.error("Informe o codigo do autenticador para concluir o login.");
        return;
      }
      toast.error(axiosError.response?.data?.error?.message ?? "Nao foi possivel autenticar no momento.");
    }
  });

  return { form, onSubmit, mfaRequired };
}
