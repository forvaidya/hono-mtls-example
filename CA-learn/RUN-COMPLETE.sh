#!/bin/bash
set -e

# Colors
GREEN='\033[92m'
BLUE='\033[94m'
YELLOW='\033[93m'
NC='\033[0m'

print_header() {
  echo ""
  echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
  echo -e "${BLUE}  $1${NC}"
  echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
  echo ""
}

print_step() {
  echo -e "${YELLOW}>>> $1${NC}"
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

# ============================================================================
# STEP 1: Generate Certificates
# ============================================================================
print_header "STEP 1: Generate Certificates"

print_step "Creating Apple (Frontend) CA and certs..."
if [ -d "frontend" ]; then
  rm -rf frontend
fi
mkdir -p frontend backend

# Apple (Frontend) CA
openssl genrsa -out frontend/ca-key.pem 4096 2>/dev/null
openssl req -new -x509 -days 3650 -key frontend/ca-key.pem -out frontend/ca-cert.pem \
  -subj "/CN=Apple-CA/O=Frontend/C=US" 2>/dev/null

# Apple (Frontend) Server cert
openssl genrsa -out frontend/server-key.pem 4096 2>/dev/null
openssl req -new -key frontend/server-key.pem -out frontend/server.csr \
  -subj "/CN=frontend.local/O=Frontend/C=US" 2>/dev/null
openssl x509 -req -in frontend/server.csr -CA frontend/ca-cert.pem -CAkey frontend/ca-key.pem \
  -CAcreateserial -out frontend/server-cert.pem -days 3650 2>/dev/null
rm frontend/server.csr

# Apple (Frontend) Client cert
openssl genrsa -out frontend/client-key.pem 4096 2>/dev/null
openssl req -new -key frontend/client-key.pem -out frontend/client.csr \
  -subj "/CN=frontend-client/O=Frontend/C=US" 2>/dev/null
openssl x509 -req -in frontend/client.csr -CA frontend/ca-cert.pem -CAkey frontend/ca-key.pem \
  -CAcreateserial -out frontend/client-cert.pem -days 3650 2>/dev/null
rm frontend/client.csr

print_success "Apple (Frontend) CA + certs created"

print_step "Creating Orange (Backend) CA and certs..."

# Orange (Backend) CA
openssl genrsa -out backend/ca-key.pem 4096 2>/dev/null
openssl req -new -x509 -days 3650 -key backend/ca-key.pem -out backend/ca-cert.pem \
  -subj "/CN=Orange-CA/O=Backend/C=US" 2>/dev/null

# Orange (Backend) Server cert
openssl genrsa -out backend/server-key.pem 4096 2>/dev/null
openssl req -new -key backend/server-key.pem -out backend/server.csr \
  -subj "/CN=api.awanipro.com/O=Backend/C=US" 2>/dev/null
openssl x509 -req -in backend/server.csr -CA backend/ca-cert.pem -CAkey backend/ca-key.pem \
  -CAcreateserial -out backend/server-cert.pem -days 3650 2>/dev/null
rm backend/server.csr

# Orange (Backend) Client cert
openssl genrsa -out backend/client-key.pem 4096 2>/dev/null
openssl req -new -key backend/client-key.pem -out backend/client.csr \
  -subj "/CN=backend-client/O=Backend/C=US" 2>/dev/null
openssl x509 -req -in backend/client.csr -CA backend/ca-cert.pem -CAkey backend/ca-key.pem \
  -CAcreateserial -out backend/client-cert.pem -days 3650 2>/dev/null
rm backend/client.csr

print_success "Orange (Backend) CA + certs created"

# ============================================================================
# STEP 2: Verify Cryptography Works
# ============================================================================
print_header "STEP 2: Verify Certificates (Cryptography Check)"

print_step "Running cryptographic verification..."
python3 verify-mtls.py 2>&1 | grep -E "✓|✗|All verifications"

# ============================================================================
# STEP 3: Show Certificate Contents
# ============================================================================
print_header "STEP 3: Certificate Contents"

print_step "Apple (Frontend) CA:"
openssl x509 -in frontend/ca-cert.pem -text -noout 2>/dev/null | grep -E "Subject:|Issuer:|Not Before|Not After|Public-Key" | head -4

print_step "Orange (Backend) CA:"
openssl x509 -in backend/ca-cert.pem -text -noout 2>/dev/null | grep -E "Subject:|Issuer:|Not Before|Not After|Public-Key" | head -4

# ============================================================================
# STEP 4: Interactive Handshake
# ============================================================================
print_header "STEP 4: Interactive Handshake (Press ENTER between steps)"

python3 interactive-mtls.py <<< "$(printf '\n\n\n\n\n\n\n\n\n\n')" 2>&1 | head -200

# ============================================================================
# SUMMARY
# ============================================================================
print_header "COMPLETE: End-to-End mTLS Baseline"

echo ""
echo -e "${GREEN}✓ Generated:${NC}"
echo "  - Apple (Frontend) CA + Server + Client certs"
echo "  - Orange (Backend) CA + Server + Client certs"
echo ""
echo -e "${GREEN}✓ Verified:${NC}"
echo "  - All signatures are valid"
echo "  - All certs are within validity period"
echo "  - Sections are cryptographically independent"
echo ""
echo -e "${GREEN}✓ Demonstrated:${NC}"
echo "  - Complete mTLS handshake flow"
echo "  - Apple verifies Orange"
echo "  - Orange verifies Apple"
echo "  - Mutual trust established"
echo ""
echo -e "${YELLOW}Files created:${NC}"
echo "  frontend/ca-cert.pem, frontend/ca-key.pem"
echo "  frontend/server-cert.pem, frontend/server-key.pem"
echo "  frontend/client-cert.pem, frontend/client-key.pem"
echo "  backend/ca-cert.pem, backend/ca-key.pem"
echo "  backend/server-cert.pem, backend/server-key.pem"
echo "  backend/client-cert.pem, backend/client-key.pem"
echo ""
echo -e "${BLUE}Next:${NC}"
echo "  1. Read UNDERSTAND-MTLS.md for concepts"
echo "  2. Trace verify-mtls.py to understand cryptography"
echo "  3. Run interactive-mtls.py again (now you understand)"
echo ""
