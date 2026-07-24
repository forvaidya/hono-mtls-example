import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

const certsDir = path.join(import.meta.dirname, '..', 'certs')
const hasCerts = fs.existsSync(path.join(certsDir, 'client-cert.pem'))

const proxyConfig = {
  changeOrigin: true,
  cookieDomainRewrite: 'localhost',
}

// For production (EC2), use mTLS with client certificate
if (hasCerts) {
  Object.assign(proxyConfig, {
    cert: fs.readFileSync(path.join(certsDir, 'client-cert.pem')),
    key: fs.readFileSync(path.join(certsDir, 'client-key.pem')),
    ca: fs.readFileSync(path.join(certsDir, 'ca-cert.pem')),
    rejectUnauthorized: false, // ponytail: dev only, self-signed certs; use true in prod with CA-signed certs
  })
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    allowedHosts: ['oidc.awanipro.com'],
    proxy: {
      '/api': {
        target: hasCerts ? 'https://api.awanipro.com' : 'http://localhost:3001',
        ...proxyConfig,
      },
      '/health': {
        target: hasCerts ? 'https://api.awanipro.com' : 'http://localhost:3001',
        ...proxyConfig,
      },
    },
  },
})
