# 24-Hour Go-Live Runbook

## What I can and cannot do from here
- Prepared: production config, Docker deployment stack, account system, settings page, deployment scripts, smoke test.
- Cannot perform directly: SSH into your server, create DNS records, purchase/attach SSL cert, or onboard a real human user outside this environment.

## Target
- Deploy to one internet-reachable server.
- Have one real user register, log in, create one goal, and send one chat message within 24 hours.

## T+0 to T+2h: Server setup
1. Provision a Linux VM (Ubuntu 22.04+) with public IP.
2. Install Docker Engine + Compose plugin.
3. Open firewall ports:
   - 80 (HTTP)
   - 443 (HTTPS)
   - 22 (SSH, restricted)
4. Clone repository onto server.

## T+2h to T+4h: Environment and secrets
1. Copy env template:
   - cp .env.production.example .env
2. Set real values:
   - OPENAI_API_KEY
   - POSTGRES_PASSWORD
   - AWS_SECRET_ACCESS_KEY
   - CORS_ALLOWED_ORIGINS (frontend URL)
   - TRUSTED_HOSTS (API hostnames)
3. Keep .env private and out of git.

## T+4h to T+6h: Deploy app
1. Run:
   - pwsh ./scripts/deploy_prod.ps1 -EnvFile .env -ComposeFile docker-compose.prod.yml
2. Validate:
   - pwsh ./scripts/smoke_test.ps1

## T+6h to T+10h: Put behind domain + TLS
1. Point DNS A record to server IP (api.yourdomain.com).
2. Put reverse proxy in front (Nginx/Caddy/Traefik).
3. Enable HTTPS cert (Let's Encrypt).
4. Update CORS_ALLOWED_ORIGINS and TRUSTED_HOSTS if needed.

## T+10h to T+16h: First-user pilot flow
1. Invite one real user (trusted pilot).
2. Ask them to complete:
   - Register account
   - Login
   - Create first goal
   - Send one chat request
   - Visit settings page and update display name
3. Capture any error screenshots and browser console logs.

## T+16h to T+20h: Stabilize
1. Check logs:
   - docker compose -f docker-compose.prod.yml logs -f api
   - docker compose -f docker-compose.prod.yml logs -f worker
2. Fix critical errors only.
3. Re-run smoke test.

## T+20h to T+24h: Confirm success criteria
- API health endpoint returns ok.
- New account persists across logout/login.
- User-specific dashboard shows user data (not guest data).
- Pilot user confirms successful end-to-end use.

## Command quick reference
- Deploy/refresh:
  - docker compose -f docker-compose.prod.yml --env-file .env up -d --build
- Status:
  - docker compose -f docker-compose.prod.yml ps
- API logs:
  - docker compose -f docker-compose.prod.yml logs -f api
- Worker logs:
  - docker compose -f docker-compose.prod.yml logs -f worker
- Health:
   - curl http://localhost:8002/health
