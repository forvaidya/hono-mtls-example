# Hono mTLS Example

Minimal Hono backend with mTLS (client certificate verification) via nginx reverse proxy on EC2. Frontend (Vite SPA) runs on your laptop with client certificate for secure communication.

## Architecture

```
Laptop (Your Dev Machine)
  ↓
SPA (Vite, :3000)
  ├─ npm run dev:spa
  └─ Vite proxy
      ↓ HTTPS + mTLS (client cert)
EC2 Instance
  ├─ nginx (:443, verifies cert)
  │  └─ plain HTTP → :80
  └─ Hono backend (:80)
     ├─ npm run dev:backend (for local testing)
     └─ systemd service (on EC2)
```

## Startup Commands

### Frontend (on your laptop)

```bash
# Install dependencies (first time only)
cd spa && npm install

# Start SPA dev server on :3000
# Proxies /api requests to https://api.awanipro.com via mTLS
npm run dev:spa

# Restart SPA (kill :3000, start fresh)
npm run restart:spa
```

Visit: `http://localhost:3000`

### Backend (local testing only)

```bash
# Install dependencies (first time only)
npm install

# Start backend on :3001 (for local testing without EC2)
# NOT used in production (backend runs on EC2)
npm run dev:backend

# Restart backend (kill :3001, start fresh)
npm run restart:backend
```

### Both Together (local dev/testing)

```bash
# Start SPA + backend together on :3000 and :3001
npm run dev:all

# Restart both (kill both ports, start fresh)
npm run restart:all
```

### Backend on EC2 (production)

```bash
# On EC2 instance:
cd /opt/hono-mtls  # after cloning repo

# Generate certificates
chmod +x certs/generate-certs.sh
./certs/generate-certs.sh api.awanipro.com

# Start backend service
sudo systemctl start hono-backend
sudo systemctl status hono-backend

# Start nginx with mTLS
sudo systemctl restart nginx
sudo systemctl status nginx

# View logs
sudo journalctl -u hono-backend -n 50
sudo journalctl -u nginx -n 50
```

See `DEPLOY.md` for full EC2 setup guide.

## Files

- `src/index.ts` — Hono backend (plain HTTP on :80, uses Clerk auth)
- `spa/` — Vite React frontend with mTLS client certificate support
- `certs/generate-certs.sh` — Certificate generation script
- `nginx.conf` — Reverse proxy with mTLS verification (for EC2)
- `DEPLOY.md` — Complete EC2 deployment guide
- `package.json` — npm scripts for dev, restart, build

## Environment Setup

### Development (Laptop)

1. Clone this repo
2. Generate certificates: `./certs/generate-certs.sh api.awanipro.com`
3. Create `.env` in root (for backend):
   ```
   CLERK_PUBLISHABLE_KEY=pk_test_...
   CLERK_SECRET_KEY=sk_test_...
   ALLOWED_ORIGIN=http://localhost:3000
   ```
4. `npm run dev:spa` → SPA runs on :3000, proxies to EC2 backend

### Production (EC2)

1. Open security group: allow ports 80 (HTTP redirect), 443 (HTTPS)
2. Clone this repo on EC2
3. Generate certificates on EC2
4. Install nginx, copy config, restart
5. Set `.env` on EC2, start backend via systemd
6. Point DNS `api.awanipro.com` → EIP

See `DEPLOY.md` for detailed steps.

## Why mTLS?

Verify that requests carrying a Clerk JWT actually come from the real frontend, not someone with a stolen token.

## Testing

### Local (no mTLS, backend on laptop)

```bash
npm run dev:all
open http://localhost:3000
```

### Against EC2 (with mTLS)

```bash
npm run dev:spa
# SPA on :3000, proxies to EC2 backend via mTLS
open http://localhost:3000
```

### mTLS verification

```bash
# Without client cert (should fail with 403)
curl https://api.awanipro.com/health -k

# With client cert (should succeed)
curl -k \
  --cert certs/client-cert.pem \
  --key certs/client-key.pem \
  --cacert certs/ca-cert.pem \
  https://api.awanipro.com/health
```

## Troubleshooting

**SPA can't reach backend:**
- Check if certs exist: `ls certs/client-cert.pem`
- Check backend URL: vite.config.js hardcoded to `https://api.awanipro.com`
- Verify DNS resolves: `nslookup api.awanipro.com`

**Backend not starting:**
- Check logs: `sudo journalctl -u hono-backend -n 50`
- Verify Clerk keys in `.env`
- Check port 80 is free: `lsof -i :80`

**nginx mTLS failing:**
- Verify certs in `/etc/nginx/certs/`: `ls -la /etc/nginx/certs/`
- Check nginx config: `sudo nginx -t`
- View nginx logs: `sudo tail -f /var/log/nginx/error.log`

