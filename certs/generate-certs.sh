#!/bin/bash
set -e

# Generate mTLS certificates for Hono + Nginx
# Usage: ./generate-certs.sh [domain]
# Default domain: api.awanipro.com

DOMAIN="${1:-api.awanipro.com}"
cd "$(dirname "$0")"

echo "Generating mTLS certificates for domain: $DOMAIN"

# 1. Generate CA key and cert
echo "1. Generating CA certificate..."
openssl genrsa -out ca-key.pem 2048
openssl req -new -x509 -days 365 -key ca-key.pem -out ca-cert.pem \
  -subj "/CN=SimpleHono-CA"

# 2. Generate server key and certificate (for nginx/EC2)
echo "2. Generating server certificate..."
openssl genrsa -out server-key.pem 2048
openssl req -new -key server-key.pem -out server.csr \
  -subj "/CN=$DOMAIN"
openssl x509 -req -days 365 -in server.csr \
  -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial \
  -out server-cert.pem

# 3. Generate client key and certificate (for frontend/Vite proxy)
echo "3. Generating client certificate..."
openssl genrsa -out client-key.pem 2048
openssl req -new -key client-key.pem -out client.csr \
  -subj "/CN=frontend-client"
openssl x509 -req -days 365 -in client.csr \
  -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial \
  -out client-cert.pem

# Clean up CSR files
rm -f server.csr client.csr ca-cert.srl

echo "✓ Certificates generated successfully"
echo "  - CA: ca-cert.pem (public, safe to commit)"
echo "  - Server: server-cert.pem, server-key.pem (deploy to EC2)"
echo "  - Client: client-cert.pem, client-key.pem (for frontend proxy)"
