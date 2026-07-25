# CA-Learn: Cryptographic mTLS Baseline

Pure cryptographic proof that **Apple can verify Orange** and **Orange can verify Apple**.

No servers, no networking—just certificate generation and verification.

## Quick Start

```bash
# Generate certificates (one-time)
./generate-certs.sh

# Verify: Apple proves Orange's certs, Orange proves Apple's certs
python3 verify-mtls.py
```

**Output:**
```
✓ Frontend (Apple) section
  ✓ CA is valid
  ✓ Server cert signed by Frontend CA
  ✓ Client cert signed by Frontend CA

✓ Backend (Orange) section
  ✓ CA is valid
  ✓ Server cert signed by Backend CA
  ✓ Client cert signed by Backend CA

✓ Cross-verification
  ✓ Frontend server cert NOT verifiable by Backend CA (independence proven)
  ✓ Backend server cert NOT verifiable by Frontend CA (independence proven)
```

## What This Proves

### Cryptographic Trust Chain

**Apple (Frontend) CA:**
```
frontend-ca.pem (root of trust)
  ├─ signs frontend-server.pem ✓
  └─ signs frontend-client.pem ✓
```

**Orange (Backend) CA:**
```
backend-ca.pem (root of trust)
  ├─ signs backend-server.pem ✓
  └─ signs backend-client.pem ✓
```

### Mutual Verification

**Apple verifies Orange:**
```
Orange presents: backend-server.pem
Apple verifies with: backend-ca.pem
  ✓ Signature is valid
  ✓ Within validity period
  ✓ Trust established
```

**Orange verifies Apple:**
```
Apple presents: frontend-client.pem
Orange verifies with: frontend-ca.pem
  ✓ Signature is valid
  ✓ Within validity period
  ✓ Trust established
```

### Independence

**Apple cert + Orange CA:**
```
frontend-server.pem (signed by frontend-ca)
verify against backend-ca.pem
  ✗ FAILS (not signed by this CA)
  ✓ Proves independence
```

**Orange cert + Apple CA:**
```
backend-server.pem (signed by backend-ca)
verify against frontend-ca.pem
  ✗ FAILS (not signed by this CA)
  ✓ Proves independence
```

## File Structure

```
CA-learn/
├── frontend/
│   ├── ca-cert.pem          ← Apple's root CA (public)
│   ├── ca-key.pem           ← Apple's CA private key (backup only)
│   ├── server-cert.pem      ← Apple's server cert (signed by ca)
│   ├── server-key.pem       ← Apple's server key (private)
│   ├── client-cert.pem      ← Apple's client cert (signed by ca)
│   └── client-key.pem       ← Apple's client key (private)
├── backend/
│   ├── ca-cert.pem          ← Orange's root CA (public)
│   ├── ca-key.pem           ← Orange's CA private key (backup only)
│   ├── server-cert.pem      ← Orange's server cert (signed by ca)
│   ├── server-key.pem       ← Orange's server key (private)
│   ├── client-cert.pem      ← Orange's client cert (signed by ca)
│   └── client-key.pem       ← Orange's client key (private)
├── generate-certs.sh        ← Create all certs
└── verify-mtls.py           ← Prove Apple ↔ Orange works
```

## How It Works

### Certificate Generation (generate-certs.sh)

1. **Create CA (root of trust):**
   ```bash
   openssl genrsa -out ca-key.pem 4096          # Private key
   openssl req -new -x509 -days 3650 \
     -key ca-key.pem -out ca-cert.pem           # Public cert
   ```

2. **Create server cert (signed by CA):**
   ```bash
   openssl genrsa -out server-key.pem 4096      # Private key
   openssl req -new -key server-key.pem -out server.csr
   openssl x509 -req -in server.csr \
     -CA ca-cert.pem -CAkey ca-key.pem \
     -out server-cert.pem                       # Public cert (signed)
   ```

3. **Create client cert (signed by same CA):**
   ```bash
   openssl genrsa -out client-key.pem 4096
   openssl req -new -key client-key.pem -out client.csr
   openssl x509 -req -in client.csr \
     -CA ca-cert.pem -CAkey ca-key.pem \
     -out client-cert.pem                       # Public cert (signed)
   ```

### Cryptographic Verification (verify-mtls.py)

For each certificate, verify:
1. **Signature is valid** — cert was signed by its CA
2. **Within validity period** — cert hasn't expired
3. **Cross-section fails** — certs from one section can't be verified by other CA

## Use Cases

### Local Development
- Use `frontend-*` certs for Vite dev proxy
- Use `backend-*` certs for backend mTLS config
- Both sections trust their respective CAs

### EC2 Production
- Upload `*-ca-cert.pem` to S3 (public, shareable)
- Keep `*-key.pem` local (never in git, never in S3)
- Each environment generates its own leaf certs

### Kubernetes
- Create Secrets from cert/key pairs
- Pass CA cert as ConfigMap
- Pods verify each other with CA cert

## Concepts

### Self-Signed CA
A CA that signs itself (not signed by higher authority). Used for internal/testing purposes.

### Leaf Certificates
End-entity certs (server, client) signed by a CA. Cannot sign other certs.

### Certificate Chain
Path of trust: Leaf Cert → CA → Root CA (or self-signed root).

### mTLS (Mutual TLS)
Both client and server present certificates and verify each other's validity.

## Files to Keep / Destroy

### Always Keep (in .gitignore)
- `frontend/*-key.pem` — Private keys (never commit)
- `backend/*-key.pem` — Private keys (never commit)

### Safe to Commit
- `generate-certs.sh` — Script (regenerates everything)
- `verify-mtls.py` — Verification script
- Documentation

### Backup (not in git)
- `frontend/ca-key.pem` — Backup locally only
- `backend/ca-key.pem` — Backup locally only

## Testing from Any Directory

```bash
# Works from anywhere (self-contained):
python3 /path/to/CA-learn/verify-mtls.py

# Must run from CA-learn directory:
cd /path/to/CA-learn
./generate-certs.sh
```

## Real mTLS Flow (with these certs)

```
Frontend Client                         Backend Server
     │                                       │
     ├─ Presents: frontend-client.pem       │
     │                                       │
     └──────────────────────────────────────>│
                                             │
                                             ├─ Verify with: frontend-ca.pem
                                             │  (received separately)
                                             │
                                             ├─ Presents: backend-server.pem
                                             │
                                    <────────┤
     │                                       │
     ├─ Verify with: backend-ca.pem          │
     │  (received separately)                │
     │                                       │
     ✓ mTLS connection established ✓
```

## Next Steps

1. **Understand:** Run `verify-mtls.py` and read the output
2. **Apply:** Read `DEPLOYMENT_GUIDE.md` to use in your project
3. **Deep dive:** Read `ARCHITECTURE.txt` for diagrams and patterns

## Troubleshooting

### "Signature invalid" from verify-mtls.py
- Cert was not signed by the CA being used to verify it
- Check: `openssl verify -CAfile frontend/ca-cert.pem frontend/server-cert.pem`

### "ModuleNotFoundError: No module named 'cryptography'"
```bash
pip install cryptography
```

### Certs created in wrong directory
- `generate-certs.sh` now auto-detects its location (fixed)
- Make sure script is executable: `chmod +x generate-certs.sh`
