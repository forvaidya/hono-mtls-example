# Certificate Management: Standalone Approach

Separate certificate generation from application bootstrap. Manual S3 control.

---

## Current State (What We're Moving Away From)

```
bootstrap → auto-detect certs → auto-fetch from S3 → auto-generate if missing
```

**Problem:** Certs tightly coupled to app startup.

---

## New State (Proposed)

```
┌─────────────────────────────────────────────────────────┐
│ Cert Lifecycle (Manual, Separate from App)              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. GENERATE (one-time)                                 │
│     ./scripts/generate-certs.sh                         │
│     → Creates: certs/ca-cert.pem, server-*.pem, etc     │
│                                                          │
│  2. VERIFY (check they're valid)                        │
│     cd CA-learn && python3 verify-mtls.py               │
│     → ✓ Signatures valid, certs good                   │
│                                                          │
│  3. BACKUP (save CA key)                                │
│     cp certs/ca-key.pem ~/.backup/ca-key.pem            │
│     → CA key stays local (never in repo)                │
│                                                          │
│  4. UPLOAD TO S3 (manual, when ready)                   │
│     aws s3 cp certs/ca-cert.pem s3://bucket/...        │
│     → Public CA cert uploaded for others to download   │
│                                                          │
│  5. APP BOOTSTRAP (assumes certs exist)                 │
│     npm run dev                                          │
│     → Just loads pre-existing certs (doesn't generate) │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
hono-mtls-example/
├── certs/                          ← Generated (not committed to git)
│   ├── ca-cert.pem                 (public, shareable)
│   ├── ca-key.pem                  (private, backed up locally)
│   ├── server-cert.pem             (public, served to clients)
│   ├── server-key.pem              (private, EC2 only)
│   ├── client-cert.pem             (public, sent during handshake)
│   └── client-key.pem              (private, dev machine only)
│
├── scripts/
│   └── generate-certs.sh           ← Standalone cert generation
│
├── CA-learn/                       ← Teaching baseline (reference)
│   └── ...
│
├── src/
│   └── index.ts                    ← App expects certs to exist
│
├── spa/vite.config.js              ← App expects certs to exist
│
└── .gitignore                      ← certs/ directory excluded
```

---

## Workflow

### Phase 1: Setup (One-Time)

```bash
# 1. Generate certs (standalone script, no app involved)
./scripts/generate-certs.sh api.awanipro.com

# 2. Verify they work (using CA-learn)
cd CA-learn
python3 verify-mtls.py
# Output: ✓ All verifications passed

# 3. Backup CA key (manual)
cp certs/ca-key.pem ~/.backup/ca-key.pem

# 4. Upload public CA to S3 (YOUR responsibility)
aws s3 cp certs/ca-cert.pem s3://your-bucket/certs/ca-cert.pem

# 5. Remove private key from working directory
rm certs/ca-key.pem
# (Keep only backup copy)

# 6. Git commit (only public certs, not keys)
git add certs/ca-cert.pem certs/server-cert.pem certs/client-cert.pem
git commit -m "Add public certificates"
```

### Phase 2: Local Development

```bash
# Certs already exist from Phase 1
npm run dev:all
# Vite proxy loads certs/client-cert.pem, certs/ca-cert.pem
# Backend can verify client certs
# ✓ Ready to develop
```

### Phase 3: Rotation (Annually)

```bash
# Re-generate leaf certs (CA key from backup)
cp ~/.backup/ca-key.pem certs/ca-key.pem
./scripts/generate-certs.sh api.awanipro.com

# Verify
cd CA-learn && python3 verify-mtls.py

# Backup again
cp certs/ca-key.pem ~/.backup/ca-key.pem
rm certs/ca-key.pem

# Upload updated server cert to EC2
scp certs/server-cert.pem certs/server-key.pem ec2-user@YOUR_IP:/tmp/

# SSH and update nginx
ssh ec2-user@YOUR_IP
  sudo cp /tmp/server-cert.pem /etc/nginx/certs/
  sudo cp /tmp/server-key.pem /etc/nginx/certs/
  sudo systemctl reload nginx

# Commit locally
git add certs/server-cert.pem
git commit -m "Rotate server certificate"
```

---

## What Changed (vs Current)

### Before (Embedded)
```typescript
// src/index.ts (current)
const app = new Hono()
// App just uses certs if they exist
// (No explicit cert management)
```

### After (Standalone)
```
Certs are SEPARATE from app code:
- Generate independently (scripts/generate-certs.sh)
- Verify independently (CA-learn/verify-mtls.py)
- Upload independently (aws s3 cp)
- App just assumes they exist (no changes needed)
```

---

## S3 Management Strategy (For You to Decide)

### Option A: Manual Upload (Full Control)
```bash
# You decide when and what to upload
aws s3 cp certs/ca-cert.pem s3://bucket/...
# Pros: Complete control
# Cons: Manual every time
```

### Option B: CI/CD Pipeline
```yaml
# .github/workflows/cert-rotation.yml
# Auto-upload new certs after generation
# Pros: Automatic on schedule
# Cons: Requires CI setup
```

### Option C: Terraform/IaC
```hcl
# terraform/s3.tf
# Define S3 bucket, lifecycle, versioning
# Pros: Infrastructure as code
# Cons: Another tool to learn
```

**For now:** Use Option A (manual). You'll read up and decide later.

---

## Files to Touch

```
scripts/generate-certs.sh     ← Already exists, standalone ✓
.gitignore                    ← Already excludes certs/ca-key.pem ✓
CA-learn/verify-mtls.py       ← Use to verify your certs
certs/                        ← Generated locally, not in git
~/.backup/                    ← CA key backup (local machine only)
```

---

## Checklist

- [ ] Run `./scripts/generate-certs.sh api.awanipro.com`
- [ ] Run `cd CA-learn && python3 verify-mtls.py`
- [ ] Backup: `cp certs/ca-key.pem ~/.backup/`
- [ ] Upload: `aws s3 cp certs/ca-cert.pem s3://...`
- [ ] Remove: `rm certs/ca-key.pem`
- [ ] Commit public certs to git
- [ ] Start app: `npm run dev:all` (no changes needed)
- [ ] Test mTLS works locally
- [ ] Decide on S3 strategy (later, after reading)

---

## Next Steps

1. **Read up on:**
   - S3 lifecycle policies (versioning, expiration)
   - CI/CD cert rotation (GitHub Actions, etc)
   - Secrets management (not storing keys in S3)
   - AWS IAM for cert access

2. **Then decide on:**
   - Manual S3 uploads or automated?
   - How to handle cert rotation?
   - Where to store CA key backup?
   - How to distribute CA cert to EC2?

3. **Documentation to create:**
   - S3 setup guide (bucket, lifecycle, permissions)
   - EC2 cert deployment guide
   - Rotation runbook
   - Emergency recovery (if CA key leaked)

---

## Security Notes

**Never in S3:**
- `*-key.pem` files (private keys)
- `ca-key.pem` (CA signing key)

**Only in S3:**
- `ca-cert.pem` (public, for verification)
- `server-cert.pem` (public, served to clients)
- `client-cert.pem` (sent during TLS, but public)

**Backup locally:**
- `ca-key.pem` (encrypted, in `~/.backup/`, restricted permissions)

---

## Example: Manual Workflow (Today)

```bash
# Day 1: Setup
./scripts/generate-certs.sh api.awanipro.com
cd CA-learn && python3 verify-mtls.py
cp certs/ca-key.pem ~/.backup/ca-key.pem
aws s3 cp certs/ca-cert.pem s3://your-bucket/certs/
rm certs/ca-key.pem
git add certs/ca-cert.pem certs/server-cert.pem certs/client-cert.pem
git commit -m "Add public certificates"
npm run dev:all
# ✓ Works

# Day 365: Rotation
cp ~/.backup/ca-key.pem certs/ca-key.pem
./scripts/generate-certs.sh api.awanipro.com
cd CA-learn && python3 verify-mtls.py
cp certs/ca-key.pem ~/.backup/ca-key.pem
# ... deploy to EC2 ...
rm certs/ca-key.pem
git add certs/server-cert.pem
git commit -m "Rotate server certificate"
# ✓ Works
```

---

## See Also

- **CA-SINGLE-MODEL.md** — Why single CA works for this project
- **CA-learn/INDEX.md** — Complete mTLS baseline
- **DEPLOY.md** — EC2 deployment guide
- **scripts/generate-certs.sh** — Standalone cert generation
