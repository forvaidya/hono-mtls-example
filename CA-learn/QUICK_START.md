# Quick Start: CA-Learn

Pure cryptographic proof: **Apple verifies Orange, Orange verifies Apple.**

## 2 Minutes

```bash
cd CA-learn
./generate-certs.sh
python3 verify-mtls.py
```

Done. ✓

## What Happened

**Generated:**
- `frontend/` — Apple's CA, server cert, client cert
- `backend/` — Orange's CA, server cert, client cert

**Verified:**
- ✓ Apple's CA can verify Apple's certs
- ✓ Orange's CA can verify Orange's certs
- ✓ Apple's certs are independent from Orange's (cross-verify fails as expected)

## The Proof

```
Apple CA                    Orange CA
  │                           │
  ├─ verifies ✓               ├─ verifies ✓
  │ Apple's server cert       │ Orange's server cert
  │                           │
  ├─ verifies ✓               ├─ verifies ✓
  │ Apple's client cert       │ Orange's client cert
  │                           │
  └─ does NOT verify ✗        └─ does NOT verify ✗
    Orange's certs (good!)      Apple's certs (good!)
```

## One Concept

Both parties have their own **root of trust (CA)** that signs all their certificates.

**Trust is NOT shared:**
- Orange cannot verify Apple's certs (different CAs)
- Apple cannot verify Orange's certs (different CAs)

**Until they exchange CAs:**
- Orange sends `orange-ca.pem` to Apple
- Apple sends `apple-ca.pem` to Orange
- Now each can verify the other's certs

## Files

```
frontend/ca-cert.pem    ← Apple's root (public)
backend/ca-cert.pem     ← Orange's root (public)
```

These two files enable mutual trust in real deployments.

```
frontend/*-key.pem      ← Keep private
backend/*-key.pem       ← Keep private
```

These never leave home.

## In Your Project

1. **Baseline:** Understand these two independent CAs
2. **Simplify (optional):** Use one CA for both sections
3. **Deploy:** Upload public CAs to S3, keep keys local

See `DEPLOYMENT_GUIDE.md` for details.
