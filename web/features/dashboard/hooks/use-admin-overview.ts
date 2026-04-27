"use client";

import { useQuery } from "@tanstack/react-query";

import { authStore } from "@/features/auth/store/auth-store";
import { http } from "@/lib/api/http";

export function useAdminOverview() {
  const session = authStore((state) => state.session);
  const hydrated = authStore((state) => state.hydrated);
  const tenantId = session?.user?.tenantId;

  const tenantsQuery = useQuery({
    queryKey: ["tenants"],
    queryFn: async () => {
      const response = await http.get("/api/internal/v1/tenants");
      return response.data.items as Array<{
        id: string;
        name: string;
        slug: string;
        plan: string;
        status: string;
        lgpd_consent_required: boolean;
      }>;
    },
    enabled: Boolean(session && hydrated),
  });

  const usersQuery = useQuery({
    queryKey: ["users", tenantId],
    queryFn: async () => {
      const response = await http.get("/api/internal/v1/users", {
        params: tenantId ? { tenant_id: tenantId } : undefined,
      });
      return response.data.items as Array<{
        id: string;
        name: string;
        email: string;
        role: string;
        status: string;
        email_verified: boolean;
        mfa_enabled: boolean;
        mfa_method: string | null;
      }>;
    },
    enabled: Boolean(session && hydrated),
  });

  const appsQuery = useQuery({
    queryKey: ["client-apps", tenantId],
    queryFn: async () => {
      const response = await http.get("/api/internal/v1/client-apps", {
        params: tenantId ? { tenant_id: tenantId } : undefined,
      });
      return response.data.items as Array<{ id: string; name: string; status: string; client_id: string }>;
    },
    enabled: Boolean(session && hydrated),
  });

  const auditQuery = useQuery({
    queryKey: ["audit-logs", tenantId],
    queryFn: async () => {
      const response = await http.get("/api/internal/v1/audit-logs", {
        params: tenantId ? { tenant_id: tenantId } : undefined,
      });
      return response.data.items as Array<{ id: string; action: string; actor_type: string; status: string; created_at: string }>;
    },
    enabled: Boolean(session && hydrated),
  });

  const brandingQuery = useQuery({
    queryKey: ["branding", tenantId],
    queryFn: async () => {
      if (!tenantId) {
        return null;
      }
      const tenant = tenantsQuery.data?.find((item) => item.id === tenantId);
      if (!tenant) {
        return null;
      }
      const response = await http.get(`/api/internal/v1/tenants/${tenant.slug}/branding`);
      return response.data as {
        tenant_name: string;
        tenant_slug: string;
        branding: {
          logo_url?: string | null;
          primary_color: string;
          secondary_color: string;
          font_family: string;
          support_email?: string | null;
          login_title: string;
          login_subtitle: string;
        };
      };
    },
    enabled: Boolean(session && hydrated && tenantsQuery.data?.length),
  });

  const consentQuery = useQuery({
    queryKey: ["consents", tenantId],
    queryFn: async () => {
      const response = await http.get("/api/internal/v1/consents", {
        params: tenantId ? { tenant_id: tenantId } : undefined,
      });
      return response.data.items as Array<{ id: string; scopes: string[]; revoked_at: string | null }>;
    },
    enabled: Boolean(session && hydrated),
  });

  const roleBindingsQuery = useQuery({
    queryKey: ["role-bindings", tenantId],
    queryFn: async () => {
      const response = await http.get("/api/internal/v1/role-bindings", {
        params: tenantId ? { tenant_id: tenantId } : undefined,
      });
      return response.data.items as Array<{
        id: string;
        user_id: string;
        client_app_id: string;
        roles: string[];
        scopes: string[];
        status: string;
      }>;
    },
    enabled: Boolean(session),
  });

  const telemetryQuery = useQuery({
    queryKey: ["telemetry-summary", tenantId],
    queryFn: async () => {
      const response = await http.get("/api/internal/v1/telemetry/summary", {
        params: tenantId ? { tenant_id: tenantId } : undefined,
      });
      return response.data as {
        total_events: number;
        login_events: number;
        oauth_events: number;
        failed_events: number;
        top_event_types: Array<{ event_type: string; count: number }>;
      };
    },
    enabled: Boolean(session && hydrated),
  });

  return {
    session,
    hydrated,
    tenantsQuery,
    usersQuery,
    appsQuery,
    auditQuery,
    brandingQuery,
    consentQuery,
    roleBindingsQuery,
    telemetryQuery,
  };
}
