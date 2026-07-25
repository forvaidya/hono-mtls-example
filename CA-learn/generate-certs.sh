#!/bin/bash
set -e

# Self-contained: find script directory regardless of where it's called from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DOMAIN="${1:-api.awanipro.com}"
DAYS=3650

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

mkdir -p frontend backend

echo -e "${BLUE}=== Frontend Section ===${NC}"

# Frontend CA
echo -e "${GREEN}Generating Frontend CA...${NC}"
openssl genrsa -out frontend/ca-key.pem 4096
openssl req -new -x509 -days $DAYS -key frontend/ca-key.pem -out frontend/ca-cert.pem \
  -subj "/CN=Frontend-CA/O=Frontend/C=US"

# Frontend Server (for frontend:8000)
echo -e "${GREEN}Generating Frontend Server cert...${NC}"
openssl genrsa -out frontend/server-key.pem 4096
openssl req -new -key frontend/server-key.pem -out frontend/server.csr \
  -subj "/CN=frontend.local/O=Frontend/C=US"
openssl x509 -req -in frontend/server.csr -CA frontend/ca-cert.pem -CAkey frontend/ca-key.pem \
  -CAcreateserial -out frontend/server-cert.pem -days $DAYS
rm frontend/server.csr

# Frontend Client (mTLS client cert)
echo -e "${GREEN}Generating Frontend Client cert...${NC}"
openssl genrsa -out frontend/client-key.pem 4096
openssl req -new -key frontend/client-key.pem -out frontend/client.csr \
  -subj "/CN=frontend-client/O=Frontend/C=US"
openssl x509 -req -in frontend/client.csr -CA frontend/ca-cert.pem -CAkey frontend/ca-key.pem \
  -CAcreateserial -out frontend/client-cert.pem -days $DAYS
rm frontend/client.csr

echo -e "${BLUE}=== Backend Section ===${NC}"

# Backend CA
echo -e "${GREEN}Generating Backend CA...${NC}"
openssl genrsa -out backend/ca-key.pem 4096
openssl req -new -x509 -days $DAYS -key backend/ca-key.pem -out backend/ca-cert.pem \
  -subj "/CN=Backend-CA/O=Backend/C=US"

# Backend Server (for backend:3001)
echo -e "${GREEN}Generating Backend Server cert...${NC}"
openssl genrsa -out backend/server-key.pem 4096
openssl req -new -key backend/server-key.pem -out backend/server.csr \
  -subj "/CN=$DOMAIN/O=Backend/C=US"
openssl x509 -req -in backend/server.csr -CA backend/ca-cert.pem -CAkey backend/ca-key.pem \
  -CAcreateserial -out backend/server-cert.pem -days $DAYS
rm backend/server.csr

# Backend Client (mTLS client cert)
echo -e "${GREEN}Generating Backend Client cert...${NC}"
openssl genrsa -out backend/client-key.pem 4096
openssl req -new -key backend/client-key.pem -out backend/client.csr \
  -subj "/CN=backend-client/O=Backend/C=US"
openssl x509 -req -in backend/client.csr -CA backend/ca-cert.pem -CAkey backend/ca-key.pem \
  -CAcreateserial -out backend/client-cert.pem -days $DAYS
rm backend/client.csr

echo -e "${BLUE}=== Summary ===${NC}"
echo -e "${GREEN}Frontend:${NC}"
echo "  CA: frontend/ca-cert.pem"
echo "  Server: frontend/server-cert.pem + frontend/server-key.pem"
echo "  Client: frontend/client-cert.pem + frontend/client-key.pem"
echo ""
echo -e "${GREEN}Backend:${NC}"
echo "  CA: backend/ca-cert.pem"
echo "  Server: backend/server-cert.pem + backend/server-key.pem"
echo "  Client: backend/client-cert.pem + backend/client-key.pem"
echo ""
echo -e "${BLUE}All certificates generated. Use verify-mtls.py to test cross-validation.${NC}"
