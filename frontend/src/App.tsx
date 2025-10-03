import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom'
import { useAtom, useSetAtom } from 'jotai'
import { userAtom, userIdAtom, userEmailAtom, userOrgIdAtom, userOrganizationNameAtom, userRoleAtom, userFirebaseUidAtom } from './atoms/auth'
import { organizationsAtom } from './atoms/organizations'
import { LoginPage } from './pages/LoginPage'
import { OrganizationDetailPage } from './pages/OrganizationDetailPage'
import { loadAuthState } from './lib/auth-persistence'
import { useEffect, useState } from 'react'

function Dashboard() {
  const [user] = useAtom(userAtom)
  const [organizations, setOrganizations] = useAtom(organizationsAtom)
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [orgName, setOrgName] = useState('')
  const [creating, setCreating] = useState(false)

  const fetchOrganizations = () => {
    if (!user || user.role !== 'super_admin') return

    const token = localStorage.getItem('firebase_token')
    // Use E2E backend port from localStorage, or default to 8000
    const backendPort = parseInt(localStorage.getItem('__E2E_BACKEND_PORT__') || '0') || 8000

    setLoading(true)
    fetch(`http://localhost:${backendPort}/api/orgs`, {
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
    if (!orgName.trim()) return

    setCreating(true)
    const token = localStorage.getItem('firebase_token')
    // Use E2E backend port from localStorage, or default to 8000
    const backendPort = parseInt(localStorage.getItem('__E2E_BACKEND_PORT__') || '0') || 8000

    console.log('[CreateOrg] Creating org:', orgName, 'on port:', backendPort)

    try {
      const res = await fetch(`http://localhost:${backendPort}/api/orgs`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: orgName }),
      })

      console.log('[CreateOrg] Response status:', res.status)

      if (!res.ok) {
        const errorText = await res.text()
        console.error('[CreateOrg] Error response:', errorText)
        throw new Error(`HTTP ${res.status}: ${errorText}`)
      }

      const data = await res.json()
      console.log('[CreateOrg] Created org:', data)

      // Close modal and reset form
      setShowCreateModal(false)
      setOrgName('')

      // Refresh organizations list
      fetchOrganizations()
    } catch (err: any) {
      console.error('[CreateOrg] Error:', err)
      console.error('[CreateOrg] Error type:', err.name)
      console.error('[CreateOrg] Error message:', err.message)
      alert(`Failed to create organization: ${err.message}`)
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
                    <label htmlFor="org-name">Organization Name</label>
                    <input
                      id="org-name"
                      data-testid="org-name-input"
                      type="text"
                      value={orgName}
                      onChange={(e) => setOrgName(e.target.value)}
                      placeholder="Enter organization name"
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        marginTop: '0.25rem',
                      }}
                      autoFocus
                    />
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                    <button
                      type="button"
                      onClick={() => {
                        setShowCreateModal(false)
                        setOrgName('')
                      }}
                      disabled={creating}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      data-testid="create-org-submit"
                      disabled={creating || !orgName.trim()}
                    >
                      {creating ? 'Creating...' : 'Create'}
                    </button>
                  </div>
                </form>
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
                    <Link to={`/orgs/${org.org_id}`}>{org.name}</Link>
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

  // Restore auth state on mount
  useEffect(() => {
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
      </Routes>
    </BrowserRouter>
  )
}

export default App
