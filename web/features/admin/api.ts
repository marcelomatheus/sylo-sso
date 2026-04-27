"use client";

import { http } from "@/lib/api/http";

export type TenantRecord = {
  id: string;
  name: string;
  slug: string;
  contact_email: string;
  plan: string;
  status: string;
  lgpd_consent_required: boolean;
  branding?: {
    logo_url?: string | null;
    primary_color: string;
    secondary_color: string;
    font_family: string;
    support_email?: string | null;
    login_title: string;
    login_subtitle: string;
  };
};

export type UserRecord = {
  id: string;
  tenant_id: string;
  email: string;
  name: string;
  role: string;
  status: string;
  email_verified?: boolean;
  mfa_enabled?: boolean;
};

export type ClientAppRecord = {
  id: string;
  tenant_id: string;
  name: string;
  description?: string | null;
  client_id: string;
  is_public: boolean;
  redirect_uris: string[];
  allowed_scopes: string[];
  status: string;
  client_secret?: string;
};

export type ApiKeyRecord = {
  id: string;
  tenant_id: string;
  client_app_id: string | null;
  name: string;
  key_prefix: string;
  scopes: string[];
  status: string;
  secret?: string;
};

export type RoleBindingRecord = {
  id: string;
  tenant_id: string;
  user_id: string;
  client_app_id: string;
  roles: string[];
  scopes: string[];
  status: string;
};

export async function createTenant(payload: {
  name: string;
  slug: string;
  contact_email: string;
  plan: string;
  lgpd_consent_required: boolean;
}) {
  const response = await http.post("/api/internal/v1/tenants", payload);
  return response.data as TenantRecord;
}

export async function updateTenant(tenantId: string, payload: Partial<TenantRecord>) {
  const response = await http.patch(`/api/internal/v1/tenants/${tenantId}`, payload);
  return response.data as TenantRecord;
}

export async function createUser(payload: {
  tenant_id: string;
  email: string;
  name: string;
  password: string;
  role: string;
  status: string;
}) {
  const response = await http.post("/api/internal/v1/users", payload);
  return response.data as UserRecord;
}

export async function updateUser(userId: string, payload: Partial<UserRecord> & { password?: string }) {
  const response = await http.patch(`/api/internal/v1/users/${userId}`, payload);
  return response.data as UserRecord;
}

export async function createClientApp(payload: {
  tenant_id: string;
  name: string;
  description?: string;
  redirect_uris: string[];
  allowed_scopes: string[];
  is_public: boolean;
}) {
  const response = await http.post("/api/internal/v1/client-apps", payload);
  return response.data as ClientAppRecord;
}

export async function updateClientApp(clientAppId: string, payload: Partial<ClientAppRecord>) {
  const response = await http.patch(`/api/internal/v1/client-apps/${clientAppId}`, payload);
  return response.data as ClientAppRecord;
}

export async function listApiKeys(tenantId?: string) {
  const response = await http.get("/api/internal/v1/api-keys", {
    params: tenantId ? { tenant_id: tenantId } : undefined,
  });
  return response.data.items as ApiKeyRecord[];
}

export async function createApiKey(payload: {
  tenant_id: string;
  client_app_id?: string | null;
  name: string;
  scopes: string[];
}) {
  const response = await http.post("/api/internal/v1/api-keys", payload);
  return response.data as ApiKeyRecord;
}

export async function revokeApiKey(apiKeyId: string) {
  const response = await http.post(`/api/internal/v1/api-keys/${apiKeyId}/revoke`);
  return response.data as ApiKeyRecord;
}

export async function rotateApiKey(apiKeyId: string) {
  const response = await http.post(`/api/internal/v1/api-keys/${apiKeyId}/rotate`);
  return response.data as ApiKeyRecord;
}

export async function revokeConsent(consentId: string) {
  const response = await http.post(`/api/internal/v1/consents/${consentId}/revoke`);
  return response.data as { id: string; revoked_at: string | null };
}

export async function listRoleBindings(tenantId?: string) {
  const response = await http.get("/api/internal/v1/role-bindings", {
    params: tenantId ? { tenant_id: tenantId } : undefined,
  });
  return response.data.items as RoleBindingRecord[];
}

export async function createRoleBinding(payload: {
  tenant_id: string;
  user_id: string;
  client_app_id: string;
  roles: string[];
  scopes: string[];
  status: string;
}) {
  const response = await http.post("/api/internal/v1/role-bindings", payload);
  return response.data as RoleBindingRecord;
}

export async function updateRoleBinding(roleBindingId: string, payload: Partial<RoleBindingRecord>) {
  const response = await http.patch(`/api/internal/v1/role-bindings/${roleBindingId}`, payload);
  return response.data as RoleBindingRecord;
}

export async function setupMfa(method: "EMAIL" | "TOTP" = "EMAIL") {
  const response = await http.post("/api/internal/v1/me/mfa/setup", { method });
  return response.data as { secret: string; otpauth_uri: string; already_enabled: boolean; method: "EMAIL" | "TOTP"; delivery?: string };
}

export async function verifyMfa(code: string) {
  const response = await http.post("/api/internal/v1/me/mfa/verify", { code });
  return response.data as { status: string };
}

export async function disableMfa() {
  const response = await http.post("/api/internal/v1/me/mfa/disable");
  return response.data as { status: string };
}

export async function resendMfa() {
  const response = await http.post("/api/internal/v1/me/mfa/resend");
  return response.data as { status: string };
}
