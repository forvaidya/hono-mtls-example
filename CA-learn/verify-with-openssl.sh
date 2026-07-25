#!/bin/bash
set -e

# Colors
GREEN='\033[92m'
RED='\033[91m'
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

print_error() {
  echo -e "${RED}✗ $1${NC}"
}

print_info() {
  echo "  $1"
}

# ============================================================================
# SCENARIO: You receive two certs from Orange (Backend)
# ============================================================================
print_header "Manual mTLS Verification with openssl"

print_info "Scenario: You (Apple/Frontend) receive certs from Orange (Backend)"
print_info ""
print_info "You receive:"
print_info "  1. backend/ca-cert.pem (Orange's CA public cert)"
print_info "  2. backend/server-cert.pem (Orange's server cert)"
print_info ""
print_info "Question: Is orange-server-cert.pem really signed by orange-ca?"
print_info ""

# ============================================================================
# STEP 1: Extract Certificate Information
# ============================================================================
print_header "STEP 1: Extract Certificate Information"

CERT_FILE="backend/server-cert.pem"
CA_FILE="backend/ca-cert.pem"

print_step "Show Orange's Server Certificate"
openssl x509 -in "$CERT_FILE" -text -noout | grep -A 5 "Subject:\|Issuer:\|Public-Key:"

print_info ""
print_step "Show Orange's CA Certificate"
openssl x509 -in "$CA_FILE" -text -noout | grep -A 5 "Subject:\|Issuer:\|Public-Key:"

# ============================================================================
# STEP 2: Extract the Signature from Server Cert
# ============================================================================
print_header "STEP 2: Extract Signature from Server Cert"

print_step "Get signature in hex format"
SIGNATURE=$(openssl x509 -in "$CERT_FILE" -text -noout | grep -A 100 "Signature Algorithm" | tail -n +2 | sed ':a;N;$!ba;s/\n//g' | sed 's/[: ]//g' | head -c 64)
print_info "Signature (first 64 hex chars): $SIGNATURE"
print_info ""
print_info "Full signature is embedded in the certificate."
print_info "This signature was created with: orange-ca-key.pem (private)"
print_info ""

# ============================================================================
# STEP 3: Extract Certificate Data (TBS - To Be Signed)
# ============================================================================
print_header "STEP 3: Extract Certificate Data (TBS)"

print_step "Get the TBS (To Be Signed) portion in DER format"
openssl asn1parse -in "$CERT_FILE" -strparse 4 -out /tmp/tbs.der 2>/dev/null
print_success "TBS data extracted to /tmp/tbs.der"
print_info ""
print_info "The TBS is the actual data that was signed:"
print_info "  - Subject (CN=api.awanipro.com)"
print_info "  - Public Key"
print_info "  - Validity dates"
print_info "  - Extensions"
print_info ""

# ============================================================================
# STEP 4: Compute SHA256 Digest of TBS
# ============================================================================
print_header "STEP 4: Compute SHA256 Digest of TBS Data"

print_step "Hash the TBS data"
TBS_DIGEST=$(openssl dgst -sha256 /tmp/tbs.der -hex | awk '{print $2}')
print_success "TBS Digest: $TBS_DIGEST"
print_info ""
print_info "This is the 'fingerprint' of the certificate data."
print_info "If anyone changes the cert data, this digest changes."
print_info ""

# ============================================================================
# STEP 5: Verify Signature with CA's Public Key
# ============================================================================
print_header "STEP 5: Verify Signature (Direct openssl Command)"

print_step "Use openssl to verify the signature"
echo ""

if openssl verify -CAfile "$CA_FILE" "$CERT_FILE" >/dev/null 2>&1; then
  print_success "Signature verification PASSED"
  print_info ""
  print_info "This means:"
  print_info "  ✓ The signature is valid"
  print_info "  ✓ The cert was signed by orange-ca-key.pem"
  print_info "  ✓ No one forged this certificate"
  print_info "  ✓ We can trust Orange"
  print_info ""
else
  print_error "Signature verification FAILED"
  print_info ""
  print_info "This means:"
  print_info "  ✗ The signature is invalid"
  print_info "  ✗ The cert was NOT signed by orange-ca-key.pem"
  print_info "  ✗ Someone forged this certificate"
  print_info "  ✗ REJECT this connection"
  print_info ""
fi

# ============================================================================
# STEP 6: What Happens Inside openssl verify
# ============================================================================
print_header "STEP 6: What openssl verify Does Internally"

print_info "When you run: openssl verify -CAfile ca-cert.pem server-cert.pem"
print_info ""
print_info "1. Extract signature from server-cert.pem"
print_info "2. Extract TBS (To Be Signed) data from server-cert.pem"
print_info "3. Compute SHA256 digest of TBS: 0x1a2b3c4d5e6f..."
print_info "4. Extract CA's public key from ca-cert.pem"
print_info "5. Decrypt signature with CA's public key"
print_info "6. Compare: computed_digest == decrypted_digest?"
print_info "7. If match → ✓ Valid, if no match → ✗ Invalid"
print_info ""

# ============================================================================
# STEP 7: Prove Independence
# ============================================================================
print_header "STEP 7: Prove Certificates Are Independent"

print_step "Try to verify Orange's cert with Apple's CA (should FAIL)"
if openssl verify -CAfile frontend/ca-cert.pem "$CERT_FILE" >/dev/null 2>&1; then
  print_error "Unexpected: Certificate verified with wrong CA!"
else
  print_success "Correctly REJECTED (different CA, as expected)"
  print_info "Orange's cert is signed by orange-ca-key"
  print_info "Not by apple-ca-key"
  print_info "So it can't be verified with apple-ca-cert"
  print_info "This proves independence."
fi

print_info ""

# ============================================================================
# STEP 8: Show What Happens If You Tamper
# ============================================================================
print_header "STEP 8: What If Someone Tampers?"

print_step "Create a fake tampered certificate"
cp "$CERT_FILE" /tmp/fake-cert.pem

# Try to tamper (change one bit in the cert file)
print_info "Simulating tampering (would change the cert data)..."
print_info "If someone changed even one byte of the certificate,"
print_info "the signature verification would fail."
print_info ""
print_info "Why? Because:"
print_info "  1. Original digest: 0x1a2b3c4d5e6f7g8h9i0j..."
print_info "  2. Tampered digest: 0x1a2b3c4d5e6f7g8h9i0k (different!)"
print_info "  3. Decrypted signature: 0x1a2b3c4d5e6f7g8h9i0j (original)"
print_info "  4. Comparison: 0x1a2b3c... ≠ 0x1a2b3c... → ✗ FAIL"
print_info ""

# ============================================================================
# SUMMARY
# ============================================================================
print_header "Summary: Verification Complete"

print_info "You received from Orange:"
print_info "  • orange-ca-cert.pem (contains orange-ca's PUBLIC key)"
print_info "  • orange-server-cert.pem (Orange's identity)"
print_info ""
print_info "You verified:"
print_info "  ✓ Signature is valid (only orange-ca-key could create it)"
print_info "  ✓ Certificate is authentic (not forged)"
print_info "  ✓ Orange is who they claim to be"
print_info ""
print_info "Result: You can now trust Orange and communicate securely"
print_info ""
print_info "The key insight:"
print_info "  Without orange-ca-cert.pem → Can't verify Orange's cert"
print_info "  With orange-ca-cert.pem → Can verify Orange's cert"
print_info "  → This is why CA exchange is critical"
print_info ""

# ============================================================================
# SHOW THE ACTUAL OPENSSL COMMANDS
# ============================================================================
print_header "Reference: Commands You Can Run"

echo -e "${YELLOW}Verify Orange's cert with Orange's CA:${NC}"
echo "  openssl verify -CAfile backend/ca-cert.pem backend/server-cert.pem"
echo ""

echo -e "${YELLOW}Verify Apple's cert with Apple's CA:${NC}"
echo "  openssl verify -CAfile frontend/ca-cert.pem frontend/server-cert.pem"
echo ""

echo -e "${YELLOW}View cert details:${NC}"
echo "  openssl x509 -in backend/server-cert.pem -text -noout"
echo ""

echo -e "${YELLOW}View CA details:${NC}"
echo "  openssl x509 -in backend/ca-cert.pem -text -noout"
echo ""

echo -e "${YELLOW}Compare two certificates (check issuer):${NC}"
echo "  openssl x509 -in backend/server-cert.pem -noout -issuer"
echo "  openssl x509 -in backend/ca-cert.pem -noout -subject"
echo ""
