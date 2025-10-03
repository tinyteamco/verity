import { useState } from 'react'
import { signInWithEmailAndPassword } from 'firebase/auth'
import { auth } from '../lib/firebase'
import { useNavigate } from 'react-router-dom'
import { useSetAtom } from 'jotai'
import { userIdAtom, userEmailAtom, userOrgIdAtom, userOrganizationNameAtom, userRoleAtom, userFirebaseUidAtom } from '../atoms/auth'
import { saveAuthState } from '../lib/auth-persistence'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const setUserId = useSetAtom(userIdAtom)
  const setUserEmail = useSetAtom(userEmailAtom)
  const setUserOrgId = useSetAtom(userOrgIdAtom)
  const setUserOrganizationName = useSetAtom(userOrganizationNameAtom)
  const setUserRole = useSetAtom(userRoleAtom)
  const setUserFirebaseUid = useSetAtom(userFirebaseUidAtom)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password)
      const idToken = await userCredential.user.getIdToken()

      // Store token
      localStorage.setItem('firebase_token', idToken)

      // Parse the token to get claims (simplified for testing)
      // In production, you'd fetch from backend or use Firebase token claims
      const claims = await userCredential.user.getIdTokenResult()
      const role = claims.claims.role || 'super_admin'

      // Update atoms with hardcoded values for super admin (for testing)
      const authState = {
        userId: 1,
        email,
        orgId: null,
        organizationName: null,
        role: role as 'owner' | 'admin' | 'member' | 'super_admin',
        firebaseUid: userCredential.user.uid,
      }

      setUserId(authState.userId)
      setUserEmail(authState.email)
      setUserOrgId(authState.orgId)
      setUserOrganizationName(authState.organizationName)
      setUserRole(authState.role)
      setUserFirebaseUid(authState.firebaseUid)

      // Persist to localStorage
      saveAuthState(authState)

      navigate('/')
    } catch (err: any) {
      setError(err.message || 'Failed to sign in')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: '400px', margin: '100px auto', padding: '20px' }}>
      <h1>Sign In</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '16px' }}>
          <label htmlFor="email" style={{ display: 'block', marginBottom: '8px' }}>
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ width: '100%', padding: '8px', fontSize: '16px' }}
          />
        </div>
        <div style={{ marginBottom: '16px' }}>
          <label htmlFor="password" style={{ display: 'block', marginBottom: '8px' }}>
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: '100%', padding: '8px', fontSize: '16px' }}
          />
        </div>
        {error && (
          <div style={{ color: 'red', marginBottom: '16px' }}>
            {error}
          </div>
        )}
        <button
          type="submit"
          disabled={loading}
          style={{ width: '100%', padding: '12px', fontSize: '16px', cursor: loading ? 'not-allowed' : 'pointer' }}
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>
    </div>
  )
}
