#!/usr/bin/env python3
"""
Interactive mTLS Handshake Simulation

Shows the real flow step-by-step with user interaction.
Simulates S3 downloads, certificate exchange, verification.
"""

import sys
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
NC = '\033[0m'

def load_cert(path):
    with open(path, 'rb') as f:
        return x509.load_pem_x509_certificate(f.read(), default_backend())

def verify_cert_signature(cert, ca_cert):
    """Returns (bool, reason)"""
    try:
        ca_cert.public_key().verify(
            cert.signature,
            cert.tbs_certificate_bytes,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True, "Signature is valid"
    except:
        return False, "Signature verification failed"

def get_cn(cert):
    try:
        return cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value
    except:
        return "Unknown"

def pause():
    """Wait for user to press Enter"""
    input(f"{YELLOW}Press ENTER to continue...{NC}")
    print()

def print_header(title):
    print(f"\n{BLUE}{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}{NC}\n")

def print_step(n, title):
    print(f"{BOLD}{YELLOW}>>> STEP {n}: {title}{NC}")
    print()

def print_action(action):
    print(f"{YELLOW}  → {action}{NC}")

def print_success(msg):
    print(f"{GREEN}  ✓ {msg}{NC}")

def print_error(msg):
    print(f"{RED}  ✗ {msg}{NC}")

def print_info(msg):
    print(f"  {msg}")

# Load certificates
script_dir = Path(__file__).parent

apple_ca = load_cert(script_dir / 'frontend' / 'ca-cert.pem')
apple_client_cert = load_cert(script_dir / 'frontend' / 'client-cert.pem')
orange_ca = load_cert(script_dir / 'backend' / 'ca-cert.pem')
orange_server_cert = load_cert(script_dir / 'backend' / 'server-cert.pem')

# ============================================================================
# INTRO
# ============================================================================
print_header("Interactive mTLS Handshake: Apple ↔ Orange")

print(f"""{BOLD}Scenario:{NC}
  Apple wants to talk to Orange securely.
  Both need to prove they are who they claim to be.

{BOLD}This walkthrough shows:{NC}
  1. How Orange downloads Apple's public CA cert
  2. How Orange verifies Apple's identity
  3. How Apple downloads Orange's public CA cert
  4. How Apple verifies Orange's identity
  5. Why this is secure

{BOLD}Think of it like:{NC}
  You check someone's passport (cert) against an official registry (CA).
  If it matches, you know they're real.

""")

pause()

# ============================================================================
# PHASE 0: CA EXCHANGE
# ============================================================================
print_header("PHASE 0: CA Exchange (Out-of-Band Setup)")

print(f"""{BOLD}Before any connection, both sides must exchange CAs.{NC}

This happens ONCE, via a trusted channel (S3, email, git, etc).
It's NOT part of the TLS handshake itself.

""")

print_step(1, "Apple Publishes Its CA Certificate")
print_action("Apple generates: apple-ca-key.pem (private) + apple-ca-cert.pem (public)")
print_action("Apple uploads to S3: s3://company-bucket/certs/apple-ca-cert.pem")
print_info(f"  Cert CN: {get_cn(apple_ca)}")
print_info(f"  Purpose: For Orange to verify Apple's certificates")
print()

pause()

print_step(2, "Orange Publishes Its CA Certificate")
print_action("Orange generates: orange-ca-key.pem (private) + orange-ca-cert.pem (public)")
print_action("Orange uploads to S3: s3://company-bucket/certs/orange-ca-cert.pem")
print_info(f"  Cert CN: {get_cn(orange_ca)}")
print_info(f"  Purpose: For Apple to verify Orange's certificates")
print()

pause()

# ============================================================================
# PHASE 1: ORANGE VERIFIES APPLE
# ============================================================================
print_header("PHASE 1: Orange Verifies Apple's Identity")

print(f"""{BOLD}Apple wants to connect to Orange.{NC}
Apple sends: apple-client-cert.pem (proof of identity)
Orange needs to verify: "Is this really Apple?"

""")

print_step(1, "Orange Receives Apple's Certificate")
print_action("Apple connects and sends: apple-client-cert.pem")
print_info(f"  Cert CN: {get_cn(apple_client_cert)}")
print_info(f"  Status: Received by Orange")
print()

pause()

print_step(2, "Orange Downloads Apple's CA from S3")
print_action("Orange: aws s3 cp s3://company-bucket/certs/apple-ca-cert.pem")
print_action("Simulating download...")
import time
for i in range(3):
    print_action(f"  Downloading... {(i+1)*30}%")
    time.sleep(0.3)
print_success(f"Downloaded: apple-ca-cert.pem")
print_info(f"  CA CN: {get_cn(apple_ca)}")
print()

pause()

print_step(3, "Orange Asks: Is This Cert Signed by Apple's CA?")
print_info("Orange's verification process:")
print_info("  1. Extract signature from apple-client-cert.pem")
print_info("  2. Compute digest: SHA256(certificate_data)")
print_info("  3. Decrypt signature with apple-ca's PUBLIC key")
print_info("  4. Compare: computed_digest == decrypted_digest?")
print()

pause()

print_step(4, "Orange Performs Verification")
print_action("Verifying signature...")
import time
time.sleep(0.5)

valid, msg = verify_cert_signature(apple_client_cert, apple_ca)

if valid:
    print_success(msg)
    print_info("  Computed digest:  0x1a2b3c4d5e6f7g8h9i0j...")
    print_info("  Decrypted digest: 0x1a2b3c4d5e6f7g8h9i0j...")
    print_info("  ✓ They match!")
    print()
    print_success("TRUST DECISION: YES, this is really Apple")
    print_info("  Reason: Only Apple's private key could create this signature")
    print_info("  Orange now accepts: Connection from Apple")
else:
    print_error(msg)
    print_info("  Digest mismatch → Someone forged this cert")
    print_error("TRUST DECISION: NO, reject this connection")

print()
pause()

# ============================================================================
# PHASE 2: APPLE VERIFIES ORANGE
# ============================================================================
print_header("PHASE 2: Apple Verifies Orange's Identity")

print(f"""{BOLD}Orange now proves to Apple it's really Orange.{NC}
Orange sends: orange-server-cert.pem (proof of identity)
Apple needs to verify: "Is this really Orange?"

""")

print_step(1, "Orange Sends Its Certificate to Apple")
print_action("Orange: Here's my certificate for you to verify")
print_info(f"  Cert CN: {get_cn(orange_server_cert)}")
print_info(f"  Status: Received by Apple")
print()

pause()

print_step(2, "Apple Downloads Orange's CA from S3")
print_action("Apple: aws s3 cp s3://company-bucket/certs/orange-ca-cert.pem")
print_action("Simulating download...")
import time
for i in range(3):
    print_action(f"  Downloading... {(i+1)*30}%")
    time.sleep(0.3)
print_success(f"Downloaded: orange-ca-cert.pem")
print_info(f"  CA CN: {get_cn(orange_ca)}")
print()

pause()

print_step(3, "Apple Asks: Is This Cert Signed by Orange's CA?")
print_info("Apple's verification process:")
print_info("  1. Extract signature from orange-server-cert.pem")
print_info("  2. Compute digest: SHA256(certificate_data)")
print_info("  3. Decrypt signature with orange-ca's PUBLIC key")
print_info("  4. Compare: computed_digest == decrypted_digest?")
print()

pause()

print_step(4, "Apple Performs Verification")
print_action("Verifying signature...")
import time
time.sleep(0.5)

valid, msg = verify_cert_signature(orange_server_cert, orange_ca)

if valid:
    print_success(msg)
    print_info("  Computed digest:  0x9z8y7x6w5v4u3t...")
    print_info("  Decrypted digest: 0x9z8y7x6w5v4u3t...")
    print_info("  ✓ They match!")
    print()
    print_success("TRUST DECISION: YES, this is really Orange")
    print_info("  Reason: Only Orange's private key could create this signature")
    print_info("  Apple now accepts: Connection to Orange")
else:
    print_error(msg)
    print_info("  Digest mismatch → Someone forged this cert")
    print_error("TRUST DECISION: NO, reject this connection")

print()
pause()

# ============================================================================
# PHASE 3: SECURE COMMUNICATION
# ============================================================================
print_header("PHASE 3: Secure Communication Established")

print(f"""{GREEN}✓ Mutual Trust Established{NC}

{GREEN}Apple knows:{NC}
  "I am talking to Orange (orange-ca vouched for it)"

{GREEN}Orange knows:{NC}
  "I am talking to Apple (apple-ca vouched for it)"

{GREEN}Both can now:{NC}
  • Exchange sensitive data
  • Encrypt communication
  • Trust each other's identity

""")

pause()

# ============================================================================
# WHY THIS IS SECURE
# ============================================================================
print_header("WHY THIS IS SECURE")

print(f"""{BOLD}Q: What if Eve tries to impersonate Orange?{NC}

Eve's attack:
  1. Eve creates: eve-server-cert.pem claiming to be Orange
  2. Eve tries to sign it with her own key
  3. Eve sends it to Apple

Apple's defense:
  1. Apple receives: eve-server-cert.pem
  2. Apple asks: "Is this signed by orange-ca?"
  3. Apple verifies with orange-ca's public key
  4. Signature doesn't match (Eve's signature ≠ Orange's signature)
  5. Apple rejects Eve

{RED}✗ Eve's attack FAILS{NC}
   Why? Because Eve doesn't have orange-ca-key.pem
   She can't create a signature that orange-ca can verify

""")

pause()

print(f"""{BOLD}Q: What if Eve steals Orange's certificate?{NC}

Eve steals:
  1. orange-server-cert.pem (public, not secret)

But Eve does NOT have:
  1. orange-server-key.pem (private key)

Result:
  • Eve can present the cert to Apple
  • Apple will verify it (signature is real)
  • But Eve can't establish a secure connection
  • (She doesn't have the private key for TLS encryption)

{YELLOW}⚠ Cert alone is not enough{NC}
   You need BOTH the cert AND the private key

""")

pause()

print(f"""{BOLD}Q: What if Eve intercepts the CA exchange?{NC}

Example:
  1. Eve intercepts: apple-ca-cert.pem during download
  2. Eve replaces it with: eve-ca-cert.pem

But:
  • Orange already downloaded the REAL apple-ca-cert.pem
  • Orange uses it to verify Apple's cert
  • If Eve tries to fake Apple, Orange will reject it
  • (Eve's signature won't match real apple-ca)

{YELLOW}⚠ Timing matters{NC}
   CA exchange must happen ONCE, securely
   Then both sides have the real CA certs

""")

pause()

# ============================================================================
# KEY INSIGHTS
# ============================================================================
print_header("KEY INSIGHTS")

print(f"""
{GREEN}1. Private Keys = Identity{NC}
   apple-ca-key.pem is the source of Apple's authority
   Only Apple has it
   If leaked → impersonation possible
   If lost → can't create new certificates

{GREEN}2. Public Certs = Proof{NC}
   apple-ca-cert.pem proves the identity
   Anyone with it can verify Apple's claims
   Safe to share (contains public key, not private)

{GREEN}3. CA Exchange is Critical{NC}
   Must happen ONCE before any mTLS connection
   Via trusted channel (S3, email, git, etc)
   Not part of TLS handshake itself

{GREEN}4. Signature = Unforgeable Math{NC}
   Only apple-ca-key can create signatures verifiable by apple-ca-cert
   Forgery is cryptographically impossible
   This is RSA signature, not guessing

{GREEN}5. Mutual Authentication{NC}
   Both sides verify each other (not just one-way)
   Apple proves to Orange (client auth)
   Orange proves to Apple (server auth)

{GREEN}6. Chain of Trust{NC}
   If you trust apple-ca,
   and apple-ca signs apple-client-cert,
   then you can trust apple-client-cert
   This is transitive trust

""")

pause()

# ============================================================================
# SUMMARY
# ============================================================================
print_header("SUMMARY")

print(f"""
{BOLD}The Complete Flow:{NC}

  ONCE (Setup):
    ┌─ Apple generates CA
    ├─ Orange generates CA
    ├─ Exchange CAs via S3 (public, safe)
    └─ Both download each other's CA

  PER CONNECTION (Runtime):
    ┌─ Apple sends cert (signed by apple-ca)
    ├─ Orange verifies: "Is it signed by apple-ca?" → YES ✓
    ├─ Orange sends cert (signed by orange-ca)
    ├─ Apple verifies: "Is it signed by orange-ca?" → YES ✓
    ├─ Encryption keys exchanged
    └─ Secure communication established

{BOLD}Files in CA-Learn:{NC}
  generate-certs.sh      ← Create the CAs and certs
  verify-mtls.py         ← Verify signatures work
  mTLS-handshake.py      ← Detailed explanation
  interactive-mtls.py    ← This interactive walkthrough
  FLOW.txt               ← Complete diagram

{BOLD}In Your Project:{NC}
  • S3 stores: apple-ca-cert.pem, orange-ca-cert.pem (public)
  • Vite proxy: uses apple-client-cert.pem to connect to backend
  • Backend: uses orange-server-cert.pem to serve HTTPS
  • Both verify each other's certs using downloaded CAs

""")

print(f"{GREEN}✓ mTLS Explained{NC}")
print()
