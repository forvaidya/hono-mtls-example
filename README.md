# Hono mTLS Example

Minimal Hono backend with mTLS (client certificate verification) via nginx reverse proxy.

## Quick Start

```bash
# Generate certs
chmod +x certs/generate-certs.sh
./certs/generate-certs.sh api.example.com

# Local dev (localhost:3001, no mTLS)
npm install
npm run dev

# EC2 deployment
# See DEPLOY.md for full guide
```

## Files

- `src/index.ts` — Hono backend (plain HTTP on :80)
- `certs/generate-certs.sh` — Certificate generation
- `nginx.conf` — Reverse proxy with mTLS verification
- `spa/` — Vite frontend with client certificate support
- `DEPLOY.md` — EC2 deployment steps

## Architecture

```
Browser/SPA (client cert)
    ↓ HTTPS (mTLS)
nginx (:443, verifies cert)
    ↓ plain HTTP
Hono backend (:80)
```

## Why mTLS?

Verify that requests carrying a Clerk JWT actually come from the real frontend.

