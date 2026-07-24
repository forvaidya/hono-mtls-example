# EC2 mTLS Deployment Guide

This guide walks through deploying the Hono backend to EC2 with mTLS (client certificate verification).

## Prerequisites

- EC2 instance running a Linux distro (Ubuntu 22.04 LTS recommended)
- Domain name pointing to an EIP (e.g., `api.awanipro.com`)
- SSH access to the instance
- `git` and `node` installed on the instance

## Step 1: Generate Certificates (Local)

```bash
cd pure-expt-no-cloudflare
chmod +x certs/generate-certs.sh
./certs/generate-certs.sh api.awanipro.com  # replace with your domain
```

This creates:
- `certs/ca-cert.pem` — CA certificate (public, safe to commit)
- `certs/server-cert.pem`, `certs/server-key.pem` — for nginx on EC2
- `certs/client-cert.pem`, `certs/client-key.pem` — for frontend Vite proxy

**Never commit the `.pem` files.** Only the script is tracked in git.

## Step 2: Create EC2 Instance & Allocate EIP

1. Launch EC2 instance (Ubuntu 22.04 LTS, t3.micro for testing)
2. Create Elastic IP (EIP)
3. Associate EIP with the instance
4. Create DNS A record: `api.awanipro.com` → EIP IP address
5. Open inbound security group rules:
   - Port 80 (HTTP) — for redirect to HTTPS
   - Port 443 (HTTPS) — for client connections
   - Port 22 (SSH) — for your access only

## Step 3: Copy Code & Certificates to EC2

```bash
# From your local machine
scp -r -i /path/to/key.pem pure-expt-no-cloudflare ec2-user@YOUR_EIP:/home/ec2-user/

# SSH into the instance
ssh -i /path/to/key.pem ec2-user@YOUR_EIP
```

Alternatively, if you don't want to scp certs, regenerate them on the EC2 instance:

```bash
cd ~/pure-expt-no-cloudflare
./certs/generate-certs.sh api.awanipro.com
```

## Step 4: Install Dependencies

```bash
cd ~/pure-expt-no-cloudflare

# Install Node dependencies
npm install

# Install nginx
sudo apt update
sudo apt install -y nginx
```

## Step 5: Set Up Nginx

```bash
# Copy certificates to nginx directory
sudo mkdir -p /etc/nginx/certs
sudo cp ~/pure-expt-no-cloudflare/certs/server-cert.pem /etc/nginx/certs/
sudo cp ~/pure-expt-no-cloudflare/certs/server-key.pem /etc/nginx/certs/
sudo cp ~/pure-expt-no-cloudflare/certs/ca-cert.pem /etc/nginx/certs/
sudo chown root:root /etc/nginx/certs/*
sudo chmod 600 /etc/nginx/certs/*-key.pem

# Replace nginx config
sudo cp ~/pure-expt-no-cloudflare/nginx.conf /etc/nginx/nginx.conf

# Update domain in nginx config (if different)
sudo sed -i 's/api.awanipro.com/YOUR_DOMAIN/g' /etc/nginx/nginx.conf

# Test nginx config
sudo nginx -t

# Start nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Step 6: Set Up Backend Service

Create a systemd service to keep the backend running:

```bash
# Create service file
sudo tee /etc/systemd/system/hono-backend.service > /dev/null <<EOF
[Unit]
Description=Hono Backend API
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/pure-expt-no-cloudflare
Environment="NODE_ENV=production"
ExecStart=/usr/bin/node --import tsx src/index.ts
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable hono-backend
sudo systemctl start hono-backend

# Check status
sudo systemctl status hono-backend
```

Set your environment variables:

```bash
# Create .env file on EC2
cat > ~/pure-expt-no-cloudflare/.env <<EOF
CLERK_PUBLISHABLE_KEY=your_key_here
CLERK_SECRET_KEY=your_secret_here
ALLOWED_ORIGIN=https://YOUR_SPA_DOMAIN
EOF
```

## Step 7: Verify Locally

Before deploying the SPA, test mTLS from your dev machine:

```bash
# Test without client cert (should fail with 403)
curl -k https://api.awanipro.com/health

# Test with client cert (should succeed with 200)
curl -k \
  --cert ~/pure-expt-no-cloudflare/certs/client-cert.pem \
  --key ~/pure-expt-no-cloudflare/certs/client-key.pem \
  --cacert ~/pure-expt-no-cloudflare/certs/ca-cert.pem \
  https://api.awanipro.com/health
```

## Step 8: Deploy SPA

Update your SPA's Vite config to point to the EC2 domain and use mTLS certs (already done in `spa/vite.config.js`). Test:

```bash
cd spa
npm run dev
# Navigate to http://localhost:3000/sign-in to trigger auth
```

The Vite proxy will use the client certificate to call `/api/me` via mTLS.

## Troubleshooting

**nginx fails to start:**
```bash
sudo nginx -t  # check config syntax
sudo journalctl -u nginx -n 50  # view logs
```

**Backend not reachable:**
```bash
sudo systemctl status hono-backend
sudo journalctl -u hono-backend -n 50
```

**mTLS handshake fails:**
- Confirm nginx has the correct CA cert: `sudo cat /etc/nginx/certs/ca-cert.pem | openssl x509 -text -noout`
- Confirm backend is running on :80: `curl -s http://localhost:80/health` from the EC2 instance
- Check nginx error log: `sudo tail -f /var/log/nginx/error.log`

**SPA can't reach backend:**
- Confirm certs exist in `/certs/` on your local machine
- Check Vite config is using the correct domain
- Verify DNS A record resolves: `nslookup api.awanipro.com`

## Certificate Rotation

Certificates expire after 365 days. To regenerate:

```bash
# Local
./certs/generate-certs.sh api.awanipro.com

# Copy new certs to EC2
scp -i /path/to/key.pem certs/*.pem ec2-user@YOUR_EIP:/tmp/
ssh -i /path/to/key.pem ec2-user@YOUR_EIP
  sudo cp /tmp/server-cert.pem /tmp/server-key.pem /etc/nginx/certs/
  sudo systemctl reload nginx
```
