#!/bin/bash
set -e

echo "🚀 Starting hono-mtls-example setup on EC2..."

# Check if running on EC2
if [ ! -f /.dockerenv ]; then
  echo "✓ Running on EC2 (not in container)"
fi

# Install system packages
echo "📦 Installing system packages..."
sudo apt update
sudo apt install -y curl nginx nodejs npm

# Verify Node installation
echo "✓ Node version: $(node -v)"
echo "✓ npm version: $(npm -v)"

# Install Node dependencies
echo "📦 Installing Node dependencies..."
npm install

# Generate certificates
echo "🔐 Generating mTLS certificates..."
DOMAIN="${1:-api.awanipro.com}"
echo "Using domain: $DOMAIN"

chmod +x certs/generate-certs.sh
./certs/generate-certs.sh "$DOMAIN"

if [ ! -f "certs/ca-cert.pem" ]; then
  echo "❌ Certificate generation failed"
  exit 1
fi
echo "✓ Certificates generated"

# Copy certs to nginx
echo "📁 Copying certificates to nginx..."
sudo mkdir -p /etc/nginx/certs
sudo cp certs/*.pem /etc/nginx/certs/
sudo chown root:root /etc/nginx/certs/*
sudo chmod 600 /etc/nginx/certs/*-key.pem
echo "✓ Certificates copied to /etc/nginx/certs/"

# Copy nginx config
echo "⚙️  Installing nginx config..."
sudo cp nginx.conf /etc/nginx/nginx.conf
echo "✓ nginx config installed"

# Test nginx config
echo "🧪 Testing nginx configuration..."
sudo nginx -t || {
  echo "❌ nginx config test failed"
  exit 1
}
echo "✓ nginx config is valid"

# Create .env if it doesn't exist
if [ ! -f .env ]; then
  echo "📝 Creating .env file..."
  cat > .env <<'EOF'
CLERK_PUBLISHABLE_KEY=pk_test_REPLACE_WITH_YOUR_KEY
CLERK_SECRET_KEY=sk_test_REPLACE_WITH_YOUR_KEY
NODE_ENV=production
BACKEND_URL=https://api.awanipro.com
ALLOWED_ORIGIN=http://localhost:3000
EOF
  echo "⚠️  .env created with placeholder values"
  echo "   UPDATE CLERK_PUBLISHABLE_KEY and CLERK_SECRET_KEY before starting"
else
  echo "✓ .env already exists"
fi

# Set up systemd service
echo "⚙️  Setting up systemd service..."
REPO_PATH=$(pwd)
sudo tee /etc/systemd/system/hono-backend.service > /dev/null <<EOF
[Unit]
Description=Hono Backend API with mTLS
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=$REPO_PATH
Environment="NODE_ENV=production"
ExecStart=/usr/bin/node --import tsx src/index.ts
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
echo "✓ Systemd service installed"

# Enable and start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable nginx hono-backend
sudo systemctl restart nginx
sudo systemctl start hono-backend

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Update .env with your Clerk keys:"
echo "      nano $(pwd)/.env"
echo ""
echo "   2. Restart backend:"
echo "      sudo systemctl restart hono-backend"
echo ""
echo "   3. Check status:"
echo "      sudo systemctl status nginx"
echo "      sudo systemctl status hono-backend"
echo ""
echo "   4. View logs:"
echo "      sudo journalctl -u hono-backend -n 50"
echo "      sudo journalctl -u nginx -n 50"
echo ""
echo "   5. Test mTLS (from your laptop):"
echo "      curl -k --cert certs/client-cert.pem --key certs/client-key.pem --cacert certs/ca-cert.pem https://api.awanipro.com/health"
echo ""
