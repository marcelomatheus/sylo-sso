import { expect, test } from "@playwright/test";

test("landing page exposes the core product message", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("link", { name: "Começar" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "OAuth2 com PKCE" })).toBeVisible();
});

test("docs page lists the integration endpoints", async ({ page }) => {
  await page.goto("/docs");
  await expect(page.getByText("POST /api/v1/auth/external/login", { exact: true })).toBeVisible();
  await expect(page.getByText("POST /api/v1/access/internal/role-bindings", { exact: true })).toBeVisible();
});

test("admin area redirects unauthenticated users to login", async ({ page }) => {
  await page.goto("/admin");
  await expect(page).toHaveURL(/\/admin\/login/);
  await expect(page.getByText("Entrar no painel do Sylo")).toBeVisible();
});

test("admin login redirects authenticated users to dashboard", async ({ context, page }) => {
  await context.addCookies([
    { name: "sylo_access_token", value: "access-token", url: "http://127.0.0.1:3000" },
    { name: "sylo_refresh_token", value: "refresh-token", url: "http://127.0.0.1:3000" },
    { name: "sylo_expires_at", value: "2099-01-01T00:00:00.000Z", url: "http://127.0.0.1:3000" },
    { name: "sylo_user_role", value: "ADMIN", url: "http://127.0.0.1:3000" },
    {
      name: "sylo_user",
      value: encodeURIComponent(JSON.stringify({ id: "admin-1", tenantId: "tenant-1", email: "admin@example.com", name: "Admin", role: "ADMIN" })),
      url: "http://127.0.0.1:3000",
    },
  ]);
  await page.goto("/admin/login");
  await expect(page).toHaveURL(/\/admin$/);
});
