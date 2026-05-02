# Sylo SSO Web

Painel administrativo, onboarding e superficies publicas white-label do Sylo SSO.

## Stack

- Next.js App Router
- React Query
- Zustand
- Axios com refresh
- React Hook Form + Zod
- Tailwind CSS

## Getting started

1. Copie `.env.local.example` para `.env.local`.
2. Instale dependencias:

```bash
npm install
```

3. Rode o servidor de desenvolvimento:

```bash
npm run dev
```

4. Acesse `http://localhost:3000`.

## Rotas principais

- `/`
- `/onboarding`
- `/admin/login`
- `/admin`
- `/docs`
- `/login/[tenantSlug]`
- `/register/[tenantSlug]`
- `/reset-password/[tenantSlug]`
- `/verify-email/[tenantSlug]`

## Scripts

```bash
npm run dev
npm run build
npm run lint
```

## Integracao esperada

- `NEXT_PUBLIC_API_BASE_URL` deve apontar para a API Flask.
- O login administrativo usa `/api/v1/auth/external/login`.
- O painel consome `/api/v1/...` por dominio.
- As paginas white-label consomem `/api/v1/tenants/external/...` e `/api/v1/auth/external/...`.

## Estado do escopo

Para o gap analysis entre o frontend atual e o plano original, consulte [../docs/scope-audit.md](../docs/scope-audit.md).
