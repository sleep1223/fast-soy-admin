# Deployment

## Docker Compose (recommended)

```bash
git clone https://github.com/sleep1223/fast-soy-admin
cd fast-soy-admin
just docker-db-init
just up  # == docker compose up -d
```

Run `initdb` only once for a fresh database. The final `just up` starts the full stack and lets the app write default users, menus, roles, APIs, and business seed data.

| Service | Port | Purpose |
|---|---|---|
| nginx | 1880 | Frontend + API reverse proxy |
| app | 9999 | FastAPI backend |
| redis | 6379 | Cache |

### Logs

```bash
just logs          # == docker compose logs -f --tail=100
just logs app      # == docker compose logs -f --tail=100 app
just logs app 200  # == docker compose logs -f --tail=200 app
```

### Update

```bash
git pull
just down && just rebuild  # == docker compose down && docker compose up -d --build
```

## Manual deployment

### Backend

```bash
uv sync --no-dev

# Granian (recommended; matches docker setup)
uv run granian --interface asgi --host 0.0.0.0 --port 9999 --workers 4 app:app

# Or uvicorn
uv run uvicorn app:app --host 0.0.0.0 --port 9999 --workers 4
```

::: warning Behind a reverse proxy
Set `PROXY_HEADERS_ENABLED=true` and `TRUSTED_HOSTS` so granian reconciles `X-Forwarded-For` / `X-Forwarded-Proto` and the real client IP reaches [fastapi-guard](https://fastapi-guard.com/)'s rate limiting. Otherwise every request looks like it comes from the proxy IP and gets banned.
:::

### Frontend

```bash
cd web && pnpm install && pnpm build
# Deploy dist/ to your web server
```

### Nginx

```nginx
server {
    listen 80;
    root /path/to/web/dist;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:9999;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Key production checklist

- [ ] `.env` `SECRET_KEY` rotated to a secure random value (note: this also invalidates historical sqids and JWTs)
- [ ] `APP_DEBUG=false` (hides `/openapi.json` / Swagger)
- [ ] `DB_URL` switched to PostgreSQL or MySQL (with appropriate driver installed)
- [ ] `REDIS_URL` set with strong password
- [ ] `PROXY_HEADERS_ENABLED=true` + `TRUSTED_HOSTS` if behind nginx / gateway
- [ ] `CORS_ORIGINS` restricted to actual frontend origins
- [ ] `RADAR_ENABLED=false` unless Radar is explicitly required; when enabled, verify only `R_ADMIN` / `R_SUPER` can access `/__radar/api/*`
- [ ] Logs rotated / shipped (default goes to `logs/`, retention 30 days)
- [ ] Migrations applied: `just mm` after deploy
- [ ] Multi-worker setup verified: only the leader writes seeds (check `app:init_done` in Redis)

## Radar response when upgrading an affected deployment

Radar is disabled by default. Confirm `RADAR_ENABLED` in `.env` / `.env.docker` after upgrading, and enable it only when the diagnostic need is understood. If enabled, anonymous and regular-user calls to `/__radar/api/*` must fail; only `R_ADMIN` and `R_SUPER` should succeed.

If an older public deployment ran with Radar enabled:

1. review Nginx, gateway, or WAF logs for historical `/__radar/api` access;
2. invalidate potentially exposed tokens and reset passwords, API keys, or other credentials first; if signing-key exposure is suspected or global invalidation is required, assess the Sqids impact before rotating `SECRET_KEY`;
3. remember that the fix sanitizes old rows when read but does not rewrite existing plaintext in the database;
4. Radar tables live in the database selected by `DB_URL` and are covered by its normal backup / restore process. Before removing `radar_requests` and its cascading `radar_queries` / `radar_user_logs`, take a backup, define the exact scope, and obtain separate approval for the destructive operation. The patch performs no automatic cleanup or schema change.

See [Radar sensitive-data boundaries and historical-data handling](/en/ops/radar#handling-historical-data-after-upgrade).

## See also

- [Configuration](/en/ops/config) — env vars
- [Switching DB](/en/ops/database) — drivers
- [Monitoring](/en/ops/radar) — Radar / Guard tuning
