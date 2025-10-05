import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom'
import { useAtom, useSetAtom } from 'jotai'
import { userAtom, userIdAtom, userEmailAtom, userOrgIdAtom, userOrganizationNameAtom, userRoleAtom, userFirebaseUidAtom } from './atoms/auth'
import { organizationsAtom } from './atoms/organizations'
import { LoginPage } from './pages/LoginPage'
import { OrganizationDetailPage } from './pages/OrganizationDetailPage'
import { StudyListPage } from './pages/StudyListPage'
import { StudyDetailPage } from './pages/StudyDetailPage'
import { loadAuthState } from './lib/auth-persistence'
import { getApiUrl } from './lib/api'
import { initializeAuth } from './lib/auth-init'
import { useEffect, useState } from 'react'

function Dashboard() {
  const [user] = useAtom(userAtom)
  const [organizations, setOrganizations] = useAtom(organizationsAtom)
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showSuccessModal, setShowSuccessModal] = useState(false)
  const [orgName, setOrgName] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [description, setDescription] = useState('')
  const [ownerEmail, setOwnerEmail] = useState('')
  const [passwordResetLink, setPasswordResetLink] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const fetchOrganizations = () => {
    if (!user || user.role !== 'super_admin') return

    const token = localStorage.getItem('firebase_token')
    const apiUrl = getApiUrl()

    setLoading(true)
    fetch(`${apiUrl}/api/orgs`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        // API returns array directly
        setOrganizations(Array.isArray(data) ? data : [])
        setLoading(false)
      })
      .catch((err) => {
        console.error('[Dashboard] Error fetching organizations:', err)
        setLoading(false)
      })
  }

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!orgName.trim() || !displayName.trim() || !ownerEmail.trim()) return

    setCreating(true)
    setCreateError(null)
    const token = localStorage.getItem('firebase_token')
    const apiUrl = getApiUrl()

    console.log('[CreateOrg] Creating org:', { name: orgName, display_name: displayName, description, owner_email: ownerEmail }, 'API URL:', apiUrl)

    try {
      const res = await fetch(`${apiUrl}/api/orgs`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: orgName,
          display_name: displayName,
          description: description || undefined,
          owner_email: ownerEmail,
        }),
      })

      console.log('[CreateOrg] Response status:', res.status)

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }))
        console.error('[CreateOrg] Error response:', errorData)
        throw new Error(errorData.detail || `HTTP ${res.status}`)
      }

      const data = await res.json()
      console.log('[CreateOrg] Created org:', data)

      // Close create modal and reset form
      setShowCreateModal(false)
      setOrgName('')
      setDisplayName('')
      setDescription('')
      setOwnerEmail('')
      setCreateError(null)

      // Show success modal with password reset link
      if (data.owner && data.owner.password_reset_link) {
        setPasswordResetLink(data.owner.password_reset_link)
        setShowSuccessModal(true)
      }

      // Refresh organizations list
      fetchOrganizations()
    } catch (err: any) {
      console.error('[CreateOrg] Error:', err)
      setCreateError(err.message)
    } finally {
      setCreating(false)
    }
  }

  useEffect(() => {
    fetchOrganizations()
  }, [user])

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role === 'super_admin') {
    return (
      <div data-testid="admin-dashboard">
        <h1>Super Admin Dashboard</h1>
        <p data-testid="admin-email">{user.email}</p>

        <div data-testid="organizations-section">
          <h2>Organizations</h2>
          <button
            data-testid="create-org-button"
            onClick={() => setShowCreateModal(true)}
          >
            Create Organization
          </button>

          {showCreateModal && (
            <div data-testid="create-org-modal" style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0,0,0,0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <div style={{
                backgroundColor: 'white',
                padding: '2rem',
                borderRadius: '8px',
                minWidth: '400px',
              }}>
                <h3>Create Organization</h3>
                <form onSubmit={handleCreateOrg}>
                  <div style={{ marginBottom: '1rem' }}>
                    <label htmlFor="org-name">
                      Organization Slug <span style={{ color: '#666', fontSize: '0.85rem' }}>(lowercase, hyphens only)</span>
                    </label>
                    <input
                      id="org-name"
                      data-testid="org-name-input"
                      type="text"
                      value={orgName}
                      onChange={(e) => setOrgName(e.target.value.toLowerCase())}
                      placeholder="my-company"
                      pattern="[a-z0-9-]+"
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        marginTop: '0.25rem',
                      }}
                      autoFocus
                    />
                  </div>
                  <div style={{ marginBottom: '1rem' }}>
                    <label htmlFor="display-name">Display Name</label>
                    <input
                      id="display-name"
                      data-testid="display-name-input"
                      type="text"
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      placeholder="My Company Inc."
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        marginTop: '0.25rem',
                      }}
                    />
                  </div>
                  <div style={{ marginBottom: '1rem' }}>
                    <label htmlFor="description">
                      Description <span style={{ color: '#666', fontSize: '0.85rem' }}>(optional)</span>
                    </label>
                    <textarea
                      id="description"
                      data-testid="description-input"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="A brief description of the organization"
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        marginTop: '0.25rem',
                        minHeight: '60px',
                      }}
                    />
                  </div>
                  <div style={{ marginBottom: '1rem' }}>
                    <label htmlFor="owner-email">Owner Email</label>
                    <input
                      id="owner-email"
                      data-testid="owner-email-input"
                      type="email"
                      value={ownerEmail}
                      onChange={(e) => setOwnerEmail(e.target.value)}
                      placeholder="owner@example.com"
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        marginTop: '0.25rem',
                      }}
                    />
                  </div>
                  {createError && (
                    <div style={{ color: 'red', marginBottom: '1rem', fontSize: '0.9rem' }}>
                      {createError}
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                    <button
                      type="button"
                      onClick={() => {
                        setShowCreateModal(false)
                        setOrgName('')
                        setDisplayName('')
                        setDescription('')
                        setOwnerEmail('')
                        setCreateError(null)
                      }}
                      disabled={creating}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      data-testid="create-org-submit"
                      disabled={creating || !orgName.trim() || !displayName.trim() || !ownerEmail.trim()}
                    >
                      {creating ? 'Creating...' : 'Create'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {showSuccessModal && (
            <div data-testid="success-modal" style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0,0,0,0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <div style={{
                backgroundColor: 'white',
                padding: '2rem',
                borderRadius: '8px',
                minWidth: '500px',
                maxWidth: '600px',
              }}>
                <h3>✅ Organization Created Successfully!</h3>
                <p>The organization has been created and the owner account has been provisioned.</p>

                <div style={{ marginTop: '1.5rem', marginBottom: '1.5rem' }}>
                  <h4>Password Setup Link</h4>
                  <p style={{ fontSize: '0.9rem', color: '#666' }}>
                    Send this link to the organization owner to set up their password:
                  </p>
                  <div style={{
                    backgroundColor: '#f5f5f5',
                    padding: '1rem',
                    borderRadius: '4px',
                    wordBreak: 'break-all',
                    fontSize: '0.85rem',
                  }}>
                    <code data-testid="password-reset-link">{passwordResetLink}</code>
                  </div>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(passwordResetLink)
                      alert('Link copied to clipboard!')
                    }}
                    style={{ marginTop: '0.5rem' }}
                  >
                    Copy Link
                  </button>
                </div>

                <p style={{ fontSize: '0.85rem', color: '#666' }}>
                  ⚠️ This link expires in 1 hour
                </p>

                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                  <button
                    data-testid="success-modal-close"
                    onClick={() => setShowSuccessModal(false)}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}

          <div data-testid="organizations-list">
            {loading ? (
              <p>Loading...</p>
            ) : organizations.length === 0 ? (
              <p data-testid="no-orgs">No organizations yet</p>
            ) : (
              <ul>
                {organizations.map((org) => (
                  <li key={org.org_id} data-testid={`org-${org.org_id}`}>
                    <Link to={`/orgs/${org.org_id}`}>{org.display_name}</Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div data-testid="user-dashboard">
      <h1>Dashboard</h1>
      <p data-testid="user-email">{user.email}</p>
      <p data-testid="org-name">{user.organizationName}</p>
    </div>
  )
}

function App() {
  const setUserId = useSetAtom(userIdAtom)
  const setUserEmail = useSetAtom(userEmailAtom)
  const setUserOrgId = useSetAtom(userOrgIdAtom)
  const setUserOrganizationName = useSetAtom(userOrganizationNameAtom)
  const setUserRole = useSetAtom(userRoleAtom)
  const setUserFirebaseUid = useSetAtom(userFirebaseUidAtom)
  const [authRestored, setAuthRestored] = useState(false)

  // Initialize auth and restore state on mount
  useEffect(() => {
    // Initialize Firebase auth listener for automatic token refresh
    initializeAuth()

    // Restore auth state from localStorage
    const authState = loadAuthState()
    if (authState) {
      setUserId(authState.userId)
      setUserEmail(authState.email)
      setUserOrgId(authState.orgId)
      setUserOrganizationName(authState.organizationName)
      setUserRole(authState.role)
      setUserFirebaseUid(authState.firebaseUid)
    }
    setAuthRestored(true)
  }, [setUserId, setUserEmail, setUserOrgId, setUserOrganizationName, setUserRole, setUserFirebaseUid])

  if (!authRestored) {
    return <div>Loading...</div>
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<Dashboard />} />
        <Route path="/orgs/:id" element={<OrganizationDetailPage />} />
        <Route path="/orgs/:orgId/studies" element={<StudyListPage />} />
        <Route path="/orgs/:orgId/studies/:studyId" element={<StudyDetailPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
