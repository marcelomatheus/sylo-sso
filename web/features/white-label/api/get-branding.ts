import { config } from "@/lib/config";

export type TenantBrandingResponse = {
  tenant_name: string;
  tenant_slug: string;
  lgpd_consent_required: boolean;
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

export async function getBranding(tenantSlug: string): Promise<TenantBrandingResponse | null> {
  const response = await fetch(`${config.apiBaseUrl}/api/external/v1/tenants/${tenantSlug}/branding`, {
    next: { revalidate: 60 },
  });
  if (!response.ok) {
    return null;
  }
  return response.json() as Promise<TenantBrandingResponse>;
}
