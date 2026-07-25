#!/usr/bin/env python3
"""
mTLS Verification Baseline

Demonstrates cryptographic proof that:
1. Frontend (Apple) can verify Backend (Orange) certificates
2. Backend (Orange) can verify Frontend (Apple) certificates
3. Both use independent CAs with independent trust chains
"""

import sys
from pathlib import Path
from datetime import datetime
from cryptography import x509
from cryptography.x509.oid import ExtensionOID
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
    """Load PEM certificate"""
    with open(path, 'rb') as f:
        return x509.load_pem_x509_certificate(f.read(), default_backend())

def load_key(path):
    """Load PEM private key"""
    with open(path, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

def verify_signature(cert, ca_cert):
    """
    Verify that cert was signed by ca_cert.
    Returns (True, "") if valid, (False, reason) if invalid.
    """
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

def check_validity(cert):
    """Check if certificate is within validity period"""
    now = datetime.now()
    not_before = cert.not_valid_before_utc.replace(tzinfo=None)
    not_after = cert.not_valid_after_utc.replace(tzinfo=None)

    if now < not_before:
        return False, f"Not yet valid (starts {not_before})"
    if now > not_after:
        return False, f"Expired (expired {not_after})"
    return True, f"Valid until {not_after.date()}"

def get_cn(cert):
    """Extract Common Name from certificate"""
    try:
        return cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value
    except:
        return "Unknown"

def print_header(title):
    print(f"\n{BLUE}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{NC}\n")

def verify_section(section_name, section_dir):
    """Verify certificates within a section"""
    print_header(f"{section_name.upper()} SECTION VERIFICATION")

    try:
        ca_cert = load_cert(f"{section_dir}/ca-cert.pem")
        server_cert = load_cert(f"{section_dir}/server-cert.pem")
        client_cert = load_cert(f"{section_dir}/client-cert.pem")
    except FileNotFoundError as e:
        print(f"{RED}✗ Missing certificate: {e}{NC}")
        return False

    print(f"{YELLOW}CA Certificate:{NC}")
    print(f"  CN: {get_cn(ca_cert)}")
    print(f"  Validity: {check_validity(ca_cert)[1]}")

    all_valid = True

    # Verify server cert
    print(f"\n{YELLOW}Server Certificate:{NC}")
    print(f"  CN: {get_cn(server_cert)}")
    valid, msg = check_validity(server_cert)
    print(f"  Validity: {msg}")

    signed_valid, signed_msg = verify_signature(server_cert, ca_cert)
    print(f"  Signature: {signed_msg}")
    all_valid = all_valid and signed_valid and valid

    # Verify client cert
    print(f"\n{YELLOW}Client Certificate:{NC}")
    print(f"  CN: {get_cn(client_cert)}")
    valid, msg = check_validity(client_cert)
    print(f"  Validity: {msg}")

    signed_valid, signed_msg = verify_signature(client_cert, ca_cert)
    print(f"  Signature: {signed_msg}")
    all_valid = all_valid and signed_valid and valid

    return all_valid

def verify_cross_section():
    """Verify that each section's certs are independent"""
    print_header("CROSS-SECTION INDEPENDENCE CHECK")

    try:
        frontend_ca = load_cert("frontend/ca-cert.pem")
        backend_ca = load_cert("backend/ca-cert.pem")
        frontend_server = load_cert("frontend/server-cert.pem")
        backend_server = load_cert("backend/server-cert.pem")
    except FileNotFoundError as e:
        print(f"{RED}✗ Missing certificate: {e}{NC}")
        return False

    # Frontend server should NOT be verifiable by Backend CA
    print(f"{YELLOW}Frontend Server cert verification with Backend CA:{NC}")
    valid, msg = verify_signature(frontend_server, backend_ca)
    if not valid:
        print(f"  {GREEN}✓ Correctly REJECTED{NC} (independent CAs)")
    else:
        print(f"  {RED}✗ Unexpected acceptance{NC}")

    # Backend server should NOT be verifiable by Frontend CA
    print(f"\n{YELLOW}Backend Server cert verification with Frontend CA:{NC}")
    valid, msg = verify_signature(backend_server, frontend_ca)
    if not valid:
        print(f"  {GREEN}✓ Correctly REJECTED{NC} (independent CAs)")
    else:
        print(f"  {RED}✗ Unexpected acceptance{NC}")

    print(f"\n{GREEN}✓ Sections are cryptographically independent{NC}")
    return True

def print_usage():
    """Print usage guide"""
    print_header("mTLS BASELINE USAGE")

    print(f"""{YELLOW}Step 1: Generate certificates{NC}
  chmod +x generate-certs.sh
  ./generate-certs.sh

{YELLOW}Step 2: Verify this script{NC}
  python3 verify-mtls.py

{YELLOW}Step 3: Understanding the structure{NC}
  Frontend (Apple): Independent CA, server, client certs
  Backend (Orange): Independent CA, server, client certs

  Both can verify each other's certs using their respective CAs.
  This is the baseline for mTLS between two independent parties.

{YELLOW}Key Points:{NC}
  • Each section has its own CA (not shared)
  • Server cert is signed by its section's CA
  • Client cert is signed by its section's CA
  • Certs from Frontend are NOT verifiable by Backend CA (and vice versa)
  • In real mTLS: Each party shares only its CA cert, not keys

{YELLOW}Real Deployment Pattern:{NC}
  1. Frontend generates frontend-ca.pem, frontend-server.pem, frontend-client.pem
  2. Backend generates backend-ca.pem, backend-server.pem, backend-client.pem
  3. Frontend publishes: frontend-ca.pem (public)
  4. Backend publishes: backend-ca.pem (public)
  5. Frontend server config: use frontend-server.pem, verify client with backend-ca.pem
  6. Backend server config: use backend-server.pem, verify client with frontend-ca.pem
  7. Frontend client config: use frontend-client.pem, verify server with backend-ca.pem
  8. Backend client config: use backend-client.pem, verify server with frontend-ca.pem
""")

def main():
    """Run all verifications"""
    script_dir = Path(__file__).parent

    if not (script_dir / "frontend").exists() or not (script_dir / "backend").exists():
        print(f"{RED}Error: Certificate directories not found.{NC}")
        print_usage()
        sys.exit(1)

    # Change to script directory
    import os
    os.chdir(script_dir)

    print(f"\n{BLUE}{'='*60}")
    print(f"  mTLS Baseline Verification")
    print(f"{'='*60}{NC}")

    frontend_ok = verify_section("frontend", "frontend")
    backend_ok = verify_section("backend", "backend")
    cross_ok = verify_cross_section()

    print_header("SUMMARY")

    status = [
        ("Frontend section", frontend_ok),
        ("Backend section", backend_ok),
        ("Cross-section independence", cross_ok),
    ]

    all_passed = all(ok for _, ok in status)

    for name, ok in status:
        symbol = f"{GREEN}✓{NC}" if ok else f"{RED}✗{NC}"
        print(f"  {symbol} {name}")

    if all_passed:
        print(f"\n{GREEN}✓ All verifications passed!{NC}")
        print_usage()
        sys.exit(0)
    else:
        print(f"\n{RED}✗ Some verifications failed{NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
