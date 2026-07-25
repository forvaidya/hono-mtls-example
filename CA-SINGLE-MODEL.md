# Single CA Model: From CA-Learn to Production

This document explains how to go from the CA-Learn baseline (two independent CAs) to the production single-CA model used in hono-mtls-example.

---

## Comparison

### CA-Learn Baseline (Teaching)
```
Apple (Frontend)          Orange (Backend)
├── apple-ca              ├── orange-ca
├── apple-server.pem      ├── orange-server.pem
├── apple-client.pem      └── orange-client.pem
└── orange-ca (fetched)   └── apple-ca (fetched)
```

**Why two CAs?** Maximum isolation. If one CA is compromised, the other is still safe.

### Production Single-CA Model (This Project)
```
Project CA (shared)
├── ca-cert.pem (root of trust)
├── server-cert.pem (backend/nginx)
├── server-key.pem
├── client-cert.pem (frontend/vite)
└── client-key.pem
```

**Why one CA?** We control both frontend and backend. Simpler management, one CA to backup.

---

## Trust Chain Comparison

### CA-Learn (Two CAs)
```
Apple → Apple-CA          Orange → Orange-CA
  ↓                         ↓
Can verify each other's    Can verify each other's
certs (with foreign CA)    certs (with foreign CA)
```

### Production (One CA)
```
Frontend → Project-CA ← Backend
  ↓                     ↓
Can verify each other's certs
(with shared CA)
```

---

## Transition Steps

### Step 1: Accept One CA

Instead of Apple-CA and Orange-CA, you have **Project-CA** that signs:
- Frontend certs (client + server)
- Backend certs (client + server)

### Step 2: Generate Certs

```bash
# One-time: Create CA
openssl genrsa -out ca-key.pem 4096
openssl req -new -x509 -days 3650 -key ca-key.pem -out ca-cert.pem \
  -subj "/CN=Project-CA/O=AwaniPro/C=US"

# Backup CA key (never share)
cp ca-key.pem ~/.backup/ca-key.pem
chmod 600 ~/.backup/ca-key.pem

# Upload public CA to S3 (once)
aws s3 cp ca-cert.pem s3://your-bucket/certs/ca-cert.pem
```

### Step 3: Sign Frontend Certs

```bash
# Backend server cert (for nginx/HTTPS)
openssl genrsa -out server-key.pem 4096
openssl req -new -key server-key.pem -out server.csr \
  -subj "/CN=api.awanipro.com/O=AwaniPro/C=US"
openssl x509 -req -in server.csr \
  -CA ca-cert.pem -CAkey ca-key.pem \
  -out server-cert.pem -days 365

# Frontend client cert (for vite proxy)
openssl genrsa -out client-key.pem 4096
openssl req -new -key client-key.pem -out client.csr \
  -subj "/CN=frontend-client/O=AwaniPro/C=US"
openssl x509 -req -in client.csr \
  -CA ca-cert.pem -CAkey ca-key.pem \
  -out client-cert.pem -days 365
```

### Step 4: Deploy

**Local Dev:**
```js
// spa/vite.config.js
const agent = new https.Agent({
  cert: fs.readFileSync('certs/client-cert.pem'),
  key: fs.readFileSync('certs/client-key.pem'),
  ca: fs.readFileSync('certs/ca-cert.pem'),      // ← Single CA
  rejectUnauthorized: false,
})
```

**EC2:**
```nginx
# nginx.conf
ssl_certificate /etc/nginx/certs/server-cert.pem;
ssl_certificate_key /etc/nginx/certs/server-key.pem;
ssl_client_certificate /etc/nginx/certs/ca-cert.pem;  # ← Single CA for verification
```

---

## Verification

Both sides verify with the SAME CA:

```
Frontend verifies Backend:
  Backend presents: server-cert.pem
  Frontend verifies with: ca-cert.pem
  ✓ Signed by Project-CA

Backend verifies Frontend:
  Frontend presents: client-cert.pem
  Backend verifies with: ca-cert.pem
  ✓ Signed by Project-CA
```

---

## Security Model

### What's Secret (Never Share)
- `ca-key.pem` — The signing key (backup locally only)
- `server-key.pem` — Backend TLS key (EC2 only)
- `client-key.pem` — Frontend TLS key (dev machine only)

### What's Public (Safe to Share)
- `ca-cert.pem` — Upload to S3 (verifies all certs)
- `server-cert.pem` — Served to clients
- `client-cert.pem` — Sent during TLS handshake

---

## Certificate Lifecycle

### Creation (One-Time)
1. Generate CA (10-year validity)
2. Generate server + client certs (1-year validity)
3. Upload CA cert to S3
4. Store CA key locally (backup)

### Rotation (Annually)
```bash
# Only rotate leaf certs, keep CA
./certs/generate-certs.sh api.awanipro.com

# Update EC2
scp certs/server-cert.pem certs/server-key.pem ec2-user@YOUR_EIP:/tmp/
ssh -i key.pem ec2-user@YOUR_EIP
  sudo cp /tmp/server-* /etc/nginx/certs/
  sudo systemctl reload nginx

# Update local dev
# (automatically picks up new certs from certs/ directory)
```

### Emergency (CA Compromise)
```bash
# Create new CA
openssl genrsa -out ca-key-v2.pem 4096
openssl req -new -x509 -days 3650 -key ca-key-v2.pem -out ca-cert-v2.pem \
  -subj "/CN=Project-CA-v2/O=AwaniPro/C=US"

# Re-sign all leaf certs with new CA
openssl x509 -req -in server.csr \
  -CA ca-cert-v2.pem -CAkey ca-key-v2.pem \
  -out server-cert.pem -days 365

# Upload new CA to S3
aws s3 cp ca-cert-v2.pem s3://your-bucket/certs/ca-cert.pem

# Redeploy everywhere
```

---

## Comparison Table

| Aspect | CA-Learn (Two CAs) | Production (Single CA) |
|--------|-------------------|------------------------|
| **CAs** | Apple-CA, Orange-CA | Project-CA |
| **Certs** | 6 (3 per section) | 3 (1 CA, 2 leaves) |
| **Complexity** | Higher (teaches concepts) | Lower (simpler to manage) |
| **Isolation** | Maximum (if one CA leaks) | Assumes both owned by you |
| **Backup** | 2 CA keys | 1 CA key |
| **S3 Upload** | 2 CA certs | 1 CA cert |
| **Rotation** | 2 cycles | 1 cycle |
| **Use Case** | Learning, multi-tenant | Single org, shared control |

---

## When to Use Single CA

✓ **Use single CA when:**
- Both frontend and backend are your own
- Same org/team controls both
- Simpler operations preferred
- Single trust anchor acceptable

✗ **Use multiple CAs when:**
- Frontend and backend by different orgs
- Need maximum isolation
- One party wants independent CA control
- Regulatory/compliance requires separation

---

## Implementation Checklist

- [ ] Generate one CA (10-year validity)
- [ ] Generate server cert (1-year, renewable)
- [ ] Generate client cert (1-year, renewable)
- [ ] Backup CA key locally
- [ ] Upload CA cert to S3 (public)
- [ ] Configure Vite proxy with client cert + CA
- [ ] Configure Nginx with server cert + CA
- [ ] Test local dev (Vite → Backend)
- [ ] Test EC2 (SPA → Nginx → Backend)
- [ ] Document CA key backup location
- [ ] Set annual cert rotation reminder

---

## See Also

- **CA-Learn/INDEX.md** — Complete mTLS baseline (teaching model)
- **CA-Learn/interactive-mtls.py** — Step-by-step walkthrough
- **DEPLOY.md** — EC2 deployment with mTLS
- **README.md** — Project overview
