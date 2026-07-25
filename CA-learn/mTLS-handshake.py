#!/usr/bin/env python3
"""
Real mTLS Handshake Model

Shows what happens when Apple proves to Orange it's Apple (and vice versa).

Flow:
1. Apple & Orange exchange CA certs (out-of-band)
2. Apple connects to Orange
3. Apple presents client cert (signed by apple-ca)
4. Orange verifies: "Is this signed by apple-ca?" → Yes → Trust Apple
5. Orange presents server cert (signed by orange-ca)
6. Apple verifies: "Is this signed by orange-ca?" → Yes → Trust Orange
7. ✓ Mutual trust established
"""

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
NC = '\033[0m'

def load_cert(path):
    with open(path, 'rb') as f:
        return x509.load_pem_x509_certificate(f.read(), default_backend())

def verify_cert_signature(cert, ca_cert):
    """Verify cert was signed by ca_cert. Returns (bool, reason)"""
    try:
        ca_cert.public_key().verify(
            cert.signature,
            cert.tbs_certificate_bytes,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True, "✓ Signature valid"
    except Exception as e:
        return False, f"✗ Signature invalid: {str(e)}"

def get_cn(cert):
    try:
        return cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value
    except:
        return "Unknown"

def print_header(title):
    print(f"\n{BLUE}{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}{NC}\n")

def step(n, description):
    print(f"{YELLOW}Step {n}: {description}{NC}")

# Load certificates
script_dir = Path(__file__).parent

apple_ca = load_cert(script_dir / 'frontend' / 'ca-cert.pem')
apple_client_cert = load_cert(script_dir / 'frontend' / 'client-cert.pem')
apple_server_cert = load_cert(script_dir / 'frontend' / 'server-cert.pem')

orange_ca = load_cert(script_dir / 'backend' / 'ca-cert.pem')
orange_client_cert = load_cert(script_dir / 'backend' / 'client-cert.pem')
orange_server_cert = load_cert(script_dir / 'backend' / 'server-cert.pem')

print_header("Real mTLS Handshake: Apple ↔ Orange")

# ============================================================================
# OUT-OF-BAND: CA Exchange (Setup)
# ============================================================================
print_header("PHASE 0: Out-of-Band CA Exchange (Setup)")

print(f"{YELLOW}Before any connection, Apple & Orange must exchange CA certs.{NC}\n")

step(1, "Apple publishes its CA")
print(f"  Apple uploads: apple-ca-cert.pem to S3")
print(f"    CN: {get_cn(apple_ca)}")
print(f"    Purpose: For Orange to verify Apple's certificates")
print()

step(2, "Orange publishes its CA")
print(f"  Orange uploads: orange-ca-cert.pem to S3")
print(f"    CN: {get_cn(orange_ca)}")
print(f"    Purpose: For Apple to verify Orange's certificates")
print()

step(3, "Both download CA certs")
print(f"  Apple downloads & stores: orange-ca-cert.pem")
print(f"  Orange downloads & stores: apple-ca-cert.pem")
print()

print(f"{GREEN}✓ Setup complete. Both have each other's CA.{NC}")

# ============================================================================
# REAL FLOW: Apple connects to Orange
# ============================================================================
print_header("PHASE 1: Apple (Client) Connects to Orange (Server)")

print(f"{YELLOW}Apple initiates connection to Orange at https://orange.example.com:443{NC}\n")

step(1, "Apple presents certificate to Orange")
print(f"  Apple sends: apple-client-cert.pem")
print(f"    CN: {get_cn(apple_client_cert)}")
print(f"    Signed by: Apple-CA")
print(f"    Contains: Apple's public key + claim that it's Apple")
print()

step(2, "Orange receives certificate")
print(f"  Orange receives: apple-client-cert.pem")
print()

step(3, "Orange verifies: Is this really Apple?")
print(f"  Orange asks: 'Is this cert signed by apple-ca?'")
print(f"  Orange has: apple-ca-cert.pem (from earlier download)")
print()

print(f"  Verification process:")
print(f"    1. Extract signature from apple-client-cert.pem")
print(f"    2. Compute digest of certificate data")
print(f"    3. Use apple-ca's public key to decrypt signature")
print(f"    4. Compare: computed_digest == decrypted_digest?")
print()

# Actually verify
valid, msg = verify_cert_signature(apple_client_cert, apple_ca)
symbol = f"{GREEN}✓{NC}" if valid else f"{RED}✗{NC}"
print(f"  Result: {symbol} {msg}")
print()

if valid:
    print(f"{GREEN}✓ TRUST DECISION: Yes, this is Apple{NC}")
    print(f"  Reason: Certificate is cryptographically signed by apple-ca")
    print(f"  Orange now knows: 'apple-ca vouches for this certificate'")
    print(f"  Orange accepts: This connection is from Apple")
else:
    print(f"{RED}✗ REJECT: Not from Apple{NC}")
    print(f"  Connection closes. Orange will not communicate.")

print()
print(f"  What if Apple tried to fake its cert?")
print(f"    • Apple presents: malicious-cert.pem")
print(f"    • Orange verifies with apple-ca")
print(f"    • Signature doesn't match (forged)")
print(f"    • {RED}✗ Rejected{NC}")
print()

# ============================================================================
# REAL FLOW: Orange responds
# ============================================================================
print_header("PHASE 2: Orange (Server) Presents Certificate to Apple")

print(f"{YELLOW}Orange now proves it's really Orange (mutual authentication){NC}\n")

step(1, "Orange presents certificate to Apple")
print(f"  Orange sends: orange-server-cert.pem")
print(f"    CN: {get_cn(orange_server_cert)}")
print(f"    Signed by: Orange-CA")
print(f"    Contains: Orange's public key + claim that it's Orange")
print()

step(2, "Apple receives certificate")
print(f"  Apple receives: orange-server-cert.pem")
print()

step(3, "Apple verifies: Is this really Orange?")
print(f"  Apple asks: 'Is this cert signed by orange-ca?'")
print(f"  Apple has: orange-ca-cert.pem (from earlier download)")
print()

# Actually verify
valid, msg = verify_cert_signature(orange_server_cert, orange_ca)
symbol = f"{GREEN}✓{NC}" if valid else f"{RED}✗{NC}"
print(f"  Result: {symbol} {msg}")
print()

if valid:
    print(f"{GREEN}✓ TRUST DECISION: Yes, this is Orange{NC}")
    print(f"  Reason: Certificate is cryptographically signed by orange-ca")
    print(f"  Apple now knows: 'orange-ca vouches for this certificate'")
    print(f"  Apple accepts: This connection is to Orange")
else:
    print(f"{RED}✗ REJECT: Not from Orange{NC}")
    print(f"  Connection closes. Apple will not communicate.")

# ============================================================================
# CONCLUSION
# ============================================================================
print_header("PHASE 3: Mutual Trust Established ✓")

print(f"{GREEN}✓ Apple knows: I'm talking to Orange (verified with orange-ca){NC}")
print(f"{GREEN}✓ Orange knows: I'm talking to Apple (verified with apple-ca){NC}")
print()
print(f"Both have cryptographic proof of identity.")
print(f"Now they can:")
print(f"  • Exchange sensitive data (encrypted)")
print(f"  • Trust each other")
print(f"  • Communicate securely")

# ============================================================================
# ATTACK SCENARIOS
# ============================================================================
print_header("ATTACK SCENARIOS: What if someone lies?")

print(f"\n{YELLOW}Scenario 1: Attacker (Eve) tries to impersonate Orange{NC}")
print(f"  Eve sends: eve-cert.pem (signed by eve-ca, not orange-ca)")
print(f"  Apple receives: eve-cert.pem")
print(f"  Apple verifies: 'Is this signed by orange-ca?'")
print(f"  Result: NO (eve-cert was signed by eve-ca)")

# Try to verify eve's cert with orange's CA (will fail)
eve_cert = load_cert(script_dir / 'backend' / 'client-cert.pem')  # Use any cert
valid, msg = verify_cert_signature(eve_cert, orange_ca)
if not valid:
    print(f"  {RED}✗ Rejected{NC}")
    print(f"  Eve cannot impersonate Orange (no signature from orange-ca)")
else:
    print(f"  {RED}✗ Would be accepted (only if signature matches){NC}")
print()

print(f"{YELLOW}Scenario 2: Attacker steals Orange's certificate{NC}")
print(f"  Eve obtains: orange-server-cert.pem (public cert, not secret)")
print(f"  Eve presents it to Apple")
print(f"  Apple verifies: 'Is this signed by orange-ca?'")
print(f"  Result: YES (it is a real Orange cert)")
print(f"  {YELLOW}⚠ Apple accepts it{NC}")
print()
print(f"  But: Eve doesn't have orange-server-key.pem (private key)")
print(f"  So: Eve can't actually establish secure connection")
print(f"  The cert alone is NOT enough (need the private key too)")
print()

print(f"{YELLOW}Scenario 3: Attacker doesn't have any cert{NC}")
print(f"  Eve connects to Apple with no certificate")
print(f"  Apple expects: a cert signed by orange-ca")
print(f"  Result: Connection rejected")
print(f"  {RED}✗ Eve cannot connect{NC}")
print()

# ============================================================================
# KEY INSIGHTS
# ============================================================================
print_header("KEY INSIGHTS")

print(f"""
{GREEN}1. CA Exchange is Out-of-Band{NC}
   CA certs must be exchanged BEFORE any connection.
   This is done once (via S3, email, config, etc.)
   Not part of the TLS handshake itself.

{GREEN}2. Certificates Prove Identity{NC}
   When Apple presents apple-client-cert.pem signed by apple-ca:
   • Anyone with apple-ca can verify it's really Apple
   • Forgery is cryptographically impossible
   • The signature is unbreakable math

{GREEN}3. Private Keys Must Stay Secret{NC}
   apple-server-key.pem must NEVER be shared.
   Even if cert is public, the key is what makes it work.
   Leaked key = Compromised identity

{GREEN}4. Both Sides Verify Each Other{NC}
   Apple verifies Orange's identity (TLS server auth)
   Orange verifies Apple's identity (mTLS client auth)
   This is mutual authentication.

{GREEN}5. Trust is Transitive{NC}
   If you trust apple-ca, and apple-ca signs a cert,
   you can trust that cert (by proxy).
   This is the whole idea of PKI.

{GREEN}6. DNS/Domain Names Matter{NC}
   In production, cert also includes domain name (CN field).
   Apple verifies: "Is CN == expected domain?"
   This prevents cert substitution attacks.
   (Simplified here for clarity)
""")

print_header("IN YOUR PROJECT")

print(f"""
1. One-time setup:
   • Frontend generates: frontend-ca, frontend-server, frontend-client
   • Backend generates: backend-ca, backend-server, backend-client
   • Exchange: frontend-ca.pem ↔ backend-ca.pem (via S3)

2. Runtime (local dev):
   • Vite proxy presents: frontend-client-cert.pem
   • Backend verifies: "signed by frontend-ca?" → YES
   • Backend presents: backend-server-cert.pem
   • Vite verifies: "signed by backend-ca?" → YES
   • ✓ mTLS connection established

3. Runtime (production):
   • SPA → Nginx (frontend cert)
   • Nginx verifies: "signed by frontend-ca?" → YES
   • Nginx → Backend (backend cert)
   • Backend verifies: "signed by backend-ca?" → YES
   • ✓ mTLS connection established
""")
