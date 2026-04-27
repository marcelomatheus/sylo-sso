# Deploy de producao

Este diretorio contem uma base de deploy para VPS usando:

- `docker compose`
- `Traefik` como proxy reverso
- `cloudflared` para publicar a stack por Cloudflare Tunnel

## Arquivos

- `docker-compose.prod.yml`: stack de producao
- `traefik/traefik.yml`: configuracao estatica do Traefik
- `traefik/dynamic.yml`: middlewares e seguranca basica
- `cloudflared/config.yml`: publicacao via tunnel
- `.env.prod.example`: variaveis de ambiente esperadas

## Observacoes

- Ajuste `SYLO_DOMAIN`, `CF_TUNNEL_ID` e `CF_TUNNEL_CREDENTIALS_FILE`.
- Para Mailgun e Sentry, preencha as credenciais reais no arquivo `.env.prod`.
- O frontend foi configurado para servir via `NEXT_PUBLIC_API_BASE_URL=https://api.<dominio>`.
