"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "react-toastify";
import { z } from "zod";

import { authStore } from "@/features/auth/store/auth-store";
import { http } from "@/lib/api/http";

const onboardingSchema = z.object({
  tenantName: z.string().min(3),
  tenantSlug: z.string().min(3).regex(/^[a-z0-9-]+$/),
  contactEmail: z.string().email(),
  adminName: z.string().min(3),
  adminEmail: z.string().email(),
  adminPassword: z.string().min(8),
});

type OnboardingValues = z.infer<typeof onboardingSchema>;

export function useOnboardingForm() {
  const router = useRouter();
  const form = useForm<OnboardingValues>({
    resolver: zodResolver(onboardingSchema),
    defaultValues: {
      tenantName: "",
      tenantSlug: "",
      contactEmail: "",
      adminName: "",
      adminEmail: "",
      adminPassword: "",
    },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      const response = await http.post("/api/v1/tenants/internal/bootstrap", {
        tenant: {
          name: values.tenantName,
          slug: values.tenantSlug,
          contact_email: values.contactEmail,
          plan: "starter",
        },
        admin_name: values.adminName,
        admin_email: values.adminEmail,
        admin_password: values.adminPassword,
      });
      authStore.getState().setSession({
        accessToken: response.data.session.access_token,
        refreshToken: response.data.session.refresh_token,
        expiresAt: response.data.session.expires_at,
        user: {
          id: response.data.admin_user.id,
          tenantId: response.data.admin_user.tenant_id,
          email: response.data.admin_user.email,
          name: response.data.admin_user.name,
          role: response.data.admin_user.role,
        },
      });
      toast.success("Tenant inicial criado com sucesso.");
      router.push("/admin");
    } catch {
      toast.error("Falha ao executar o bootstrap inicial.");
    }
  });

  return { form, onSubmit };
}
