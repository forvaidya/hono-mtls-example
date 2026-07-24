import { useAuth, useUser, SignInButton, UserButton } from '@clerk/clerk-react'
import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const { isLoaded, isSignedIn, getToken } = useAuth()
  const { user } = useUser()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!isSignedIn) return

    const fetchMe = async () => {
      setLoading(true)
      try {
        const token = await getToken()
        const res = await fetch('/api/me', {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`)
        const json = await res.json()
        setData(json)
        setError(null)
      } catch (err) {
        setError(err.message)
        setData(null)
      } finally {
        setLoading(false)
      }
    }

    fetchMe()
  }, [isSignedIn, getToken])

  if (!isLoaded) return <div style={{ padding: '40px' }}>Loading...</div>

  return (
    <div style={{ padding: '40px', fontFamily: 'system-ui' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Clerk + Hono POC</h1>
        {isSignedIn && <UserButton />}
      </div>

      {!isSignedIn ? (
        <div style={{ marginTop: '40px' }}>
          <p>Sign in with Google to continue:</p>
          <SignInButton mode="modal" />
        </div>
      ) : (
        <div style={{ marginTop: '40px' }}>
          <h2>Welcome, {user?.firstName}!</h2>
          <div style={{ background: '#f5f5f5', padding: '20px', borderRadius: '8px', marginTop: '20px' }}>
            <h3>Backend Response (/api/me)</h3>
            {loading && <p>Loading...</p>}
            {error && <p style={{ color: 'red' }}>Error: {error}</p>}
            {data && (
              <pre style={{ background: 'white', padding: '10px', borderRadius: '4px', overflow: 'auto' }}>
                {JSON.stringify(data, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
