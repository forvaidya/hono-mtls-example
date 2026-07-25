# CA-Learn: Real mTLS Baseline

Shows **how Apple proves it's Apple to Orange, and Orange proves it's Orange to Apple**—the complete real-world mTLS handshake.

## Files

| File | Purpose |
|------|---------|
| `generate-certs.sh` | Create Apple's CA+certs and Orange's CA+certs (self-contained, works from anywhere) |
| `verify-mtls.py` | Cryptographic proof: Apple's certs are valid, Orange's certs are valid, they're independent |
| `mTLS-handshake.py` | **REAL FLOW:** Apple proves to Orange (and vice versa) via certificate verification |
| `FLOW.txt` | Complete ASCII diagram: Phases 0-2 with cryptography details |
| `README.md` | Detailed explanation of how mTLS trust works |
| `QUICK_START.md` | 2-minute quick start |
| `ARCHITECTURE.txt` | ASCII diagrams of the cryptographic chain |
| `frontend/` | Apple's certificates (generated) |
| `backend/` | Orange's certificates (generated) |

## Quick Flow

```bash
./generate-certs.sh           # Create all certs
python3 verify-mtls.py        # Verify certs are valid & independent
python3 mTLS-handshake.py     # See the real handshake in action
```

## What You Learn

1. **verify-mtls.py:** Cryptography works (signatures are valid)
2. **mTLS-handshake.py:** How it's actually used (proof of identity)

## What Gets Created

### Certificates

```
Apple (Frontend)
  ├─ CA cert (root of trust)
  ├─ CA key (private, backup only)
  ├─ Server cert (signed by CA)
  ├─ Server key (private)
  ├─ Client cert (signed by CA)
  └─ Client key (private)

Orange (Backend)
  ├─ CA cert (root of trust)
  ├─ CA key (private, backup only)
  ├─ Server cert (signed by CA)
  ├─ Server key (private)
  ├─ Client cert (signed by CA)
  └─ Client key (private)
```

### Proofs

**verify-mtls.py proves:**
1. ✓ Apple's CA signs Apple's server cert
2. ✓ Apple's CA signs Apple's client cert
3. ✓ Orange's CA signs Orange's server cert
4. ✓ Orange's CA signs Orange's client cert
5. ✓ Apple's CA does NOT sign Orange's certs (independence)
6. ✓ Orange's CA does NOT sign Apple's certs (independence)

## The Three Layers

### Layer 1: Crypto (verify-mtls.py)
Pure math: verify signatures are valid.
- Does the cert have a valid signature?
- Is the cert within its validity period?
- Are different CAs truly independent?

### Layer 2: Protocol (mTLS-handshake.py)
Real world: How identity is proven using crypto.
- Phase 0: CA exchange (out-of-band)
- Phase 1: Apple proves to Orange it's Apple
- Phase 2: Orange proves to Apple it's Orange
- Phase 3: Trust established

### Layer 3: Application (your code)
Integration: Use these certs in Vite, Nginx, Node.
- Vite proxy uses apple-client-cert to call backend
- Backend verifies with apple-ca-cert
- Backend serves orange-server-cert
- Vite verifies with orange-ca-cert

## Self-Contained

Both scripts work from anywhere:
```bash
python3 /path/to/CA-learn/verify-mtls.py  # Works from /tmp, /home, anywhere
./path/to/CA-learn/generate-certs.sh      # Creates certs in CA-learn/ directory
```

## Key Insight

Each party (Apple, Orange) has its own **root of trust (CA)**.

**Without CA exchange:** No trust (default)
**After CA exchange:** Mutual trust (via signature verification)

```
Signature = encrypt(data_digest, private_key)
Verification = decrypt(signature, public_key) == data_digest
```

If verification succeeds → Cert was signed by this CA → Trust established.

## Use in Production

1. Generate certs once per section
2. Exchange CA certs publicly (upload to S3)
3. Keep private keys local (never commit, never share)
4. Use certs for mTLS in actual services

## Dependencies

- `bash` (for generate-certs.sh)
- `openssl` (system command, for cert generation)
- `python3` (for verify-mtls.py)
- `cryptography` Python package (for signature verification)

All available on macOS/Linux by default (cryptography may need `pip install cryptography`).

## Learn More

- **Quick understanding:** `QUICK_START.md`
- **How it works:** `README.md`
- **Cryptographic details:** `ARCHITECTURE.txt`
