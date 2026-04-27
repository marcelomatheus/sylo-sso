"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "react-toastify";

import { http } from "@/lib/api/http";
import { Button } from "@/ui/button";

export function VerifyEmailAction({
  tenantSlug,
  token,
}: {
  tenantSlug: string;
  token: string;
}) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleVerify = async () => {
    setLoading(true);
    try {
      const response = await http.post("/api/external/v1/email/verify", {
        tenant_slug: tenantSlug,
        token,
      });
      toast.success("E-mail confirmado com sucesso.");
      if (response.data.redirect_to) {
        window.location.assign(response.data.redirect_to);
        return;
      }
      router.push(`/login/${tenantSlug}`);
    } catch {
      toast.error("Nao foi possivel confirmar o e-mail.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button className="w-full" disabled={loading} type="button" onClick={handleVerify}>
      {loading ? "Confirmando..." : "Confirmar e-mail"}
    </Button>
  );
}
