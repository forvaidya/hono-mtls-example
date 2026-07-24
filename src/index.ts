import 'dotenv/config'
import { Hono } from 'hono'
import { serve } from '@hono/node-server'
import { clerkMiddleware, getAuth } from '@hono/clerk-auth'
import { cors } from 'hono/cors'
import { Clerk } from '@clerk/backend'

const app = new Hono()

app.use('*', cors({
  origin: process.env.ALLOWED_ORIGIN || 'http://localhost:3000',
  credentials: true,
}))
app.use('*', clerkMiddleware())

// Get authenticated user info
app.get('/api/me', async (c) => {
  const auth = getAuth(c)
  if (!auth?.userId) return c.json({ error: 'Unauthorized' }, 401)

  const clerk = Clerk({ apiKey: process.env.CLERK_SECRET_KEY })
  const user = await clerk.users.getUser(auth.userId)

  return c.json({ message: `Welcome ${user.emailAddresses[0].emailAddress}` })
})

// Public health check
app.get('/health', (c) => {
  return c.json({ status: 'ok' })
})

// Backend config (for easy identification during testing)
app.get('/config', (c) => {
  return c.json({
    env: process.env.NODE_ENV || 'development',
    backendUrl: process.env.BACKEND_URL || `http://localhost:3001`,
    mtlsEnabled: !!process.env.BACKEND_URL,
  })
})

const port = 3001
const backendUrl = process.env.BACKEND_URL || `http://localhost:${port}`
const env = process.env.NODE_ENV || 'development'

console.log(`[${env.toUpperCase()}] Server running on ${backendUrl}`)
serve({ fetch: app.fetch, port })
