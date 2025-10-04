import { useParams, Navigate, Link } from 'react-router-dom'
import { useAtom } from 'jotai'
import { userAtom } from '../atoms/auth'
import { useState, useEffect } from 'react'

interface Organization {
  org_id: string
  name: string
  created_at: string
}

interface User {
  user_id: string
  email: string
  role: string
  created_at: string
}

interface Study {
  study_id: number
  name: string
  created_at: string
}

export function OrganizationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [user] = useAtom(userAtom)
  const [org, setOrg] = useState<Organization | null>(null)
  const [users, setUsers] = useState<User[]>([])
  const [studies, setStudies] = useState<Study[]>([])
  const [loadingOrg, setLoadingOrg] = useState(true)
  const [loadingUsers, setLoadingUsers] = useState(true)
  const [loadingStudies, setLoadingStudies] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Add User modal state
  const [showAddUserModal, setShowAddUserModal] = useState(false)
  const [showUserSuccessModal, setShowUserSuccessModal] = useState(false)
  const [userEmail, setUserEmail] = useState('')
  const [userRole, setUserRole] = useState('admin')
  const [passwordResetLink, setPasswordResetLink] = useState('')
  const [addingUser, setAddingUser] = useState(false)

  const fetchUsers = () => {
    if (!user || !id) return

    const token = localStorage.getItem('firebase_token')
    const backendPort = parseInt(localStorage.getItem('__E2E_BACKEND_PORT__') || '0') || 8000

    setLoadingUsers(true)
    fetch(`http://localhost:${backendPort}/api/orgs/${id}/users`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        setUsers(data.items || [])
        setLoadingUsers(false)
      })
      .catch((err) => {
        console.error('[OrgDetail] Error fetching users:', err)
        setLoadingUsers(false)
      })
  }

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!userEmail.trim() || !userRole) return

    setAddingUser(true)
    const token = localStorage.getItem('firebase_token')
    const backendPort = parseInt(localStorage.getItem('__E2E_BACKEND_PORT__') || '0') || 8000

    try {
      const res = await fetch(`http://localhost:${backendPort}/api/orgs/${id}/users`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: userEmail, role: userRole }),
      })

      if (!res.ok) {
        const errorText = await res.text()
        throw new Error(`HTTP ${res.status}: ${errorText}`)
      }

      const data = await res.json()

      // Close add user modal and reset form
      setShowAddUserModal(false)
      setUserEmail('')
      setUserRole('admin')

      // Show success modal with password reset link
      if (data.password_reset_link) {
        setPasswordResetLink(data.password_reset_link)
        setShowUserSuccessModal(true)
      }

      // Refresh users list
      fetchUsers()
    } catch (err: any) {
      console.error('[AddUser] Error:', err)
      alert(`Failed to add user: ${err.message}`)
    } finally {
      setAddingUser(false)
    }
  }

  useEffect(() => {
    if (!user || !id) return

    const token = localStorage.getItem('firebase_token')
    const backendPort = parseInt(localStorage.getItem('__E2E_BACKEND_PORT__') || '0') || 8000

    // Fetch organization details
    fetch(`http://localhost:${backendPort}/api/orgs/${id}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (!res.ok) {
          if (res.status === 404) throw new Error('Organization not found')
          if (res.status === 403) throw new Error('You don\'t have permission to view this organization')
          throw new Error(`HTTP ${res.status}`)
        }
        return res.json()
      })
      .then((data) => {
        setOrg(data)
        setLoadingOrg(false)
      })
      .catch((err) => {
        console.error('[OrgDetail] Error fetching organization:', err)
        setError(err.message)
        setLoadingOrg(false)
      })

    // Fetch users
    fetchUsers()

    // Fetch studies
    fetch(`http://localhost:${backendPort}/api/studies?org_id=${id}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        setStudies(Array.isArray(data) ? data : [])
        setLoadingStudies(false)
      })
      .catch((err) => {
        console.error('[OrgDetail] Error fetching studies:', err)
        setLoadingStudies(false)
      })
  }, [user, id])

  if (!user || user.role !== 'super_admin') {
    return <Navigate to="/login" replace />
  }

  if (loadingOrg) {
    return (
      <div>
        <Link to="/">← Back to Dashboard</Link>
        <p>Loading organization...</p>
      </div>
    )
  }

  if (error || !org) {
    return (
      <div>
        <h1>Organization Not Found</h1>
        {error && <p>{error}</p>}
        <Link to="/">Back to Dashboard</Link>
      </div>
    )
  }

  return (
    <div data-testid="org-detail-page">
      <Link to="/">← Back to Dashboard</Link>

      <h1 data-testid="org-detail-name">{org.name}</h1>
      <p>Created: {new Date(org.created_at).toLocaleDateString()}</p>

      <div data-testid="org-users-section" style={{ marginTop: '2rem' }}>
        <h2>Users</h2>
        {loadingUsers ? (
          <p>Loading users...</p>
        ) : users.length === 0 ? (
          <p>No users yet</p>
        ) : (
          <ul data-testid="org-users-list">
            {users.map((u) => (
              <li key={u.user_id} data-user-email={u.email}>
                {u.email} (<span data-testid="user-role">{u.role}</span>)
              </li>
            ))}
          </ul>
        )}
        <button
          data-testid="add-user-button"
          onClick={() => setShowAddUserModal(true)}
        >
          Add User
        </button>

        {/* Add User Modal */}
        {showAddUserModal && (
          <div data-testid="add-user-modal" style={{
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
              <h3>Add User to Organization</h3>
              <form onSubmit={handleAddUser}>
                <div style={{ marginBottom: '1rem' }}>
                  <label htmlFor="user-email">User Email</label>
                  <input
                    id="user-email"
                    data-testid="user-email-input"
                    type="email"
                    value={userEmail}
                    onChange={(e) => setUserEmail(e.target.value)}
                    placeholder="user@example.com"
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      marginTop: '0.25rem',
                    }}
                    autoFocus
                  />
                </div>
                <div style={{ marginBottom: '1rem' }}>
                  <label htmlFor="user-role">Role</label>
                  <select
                    id="user-role"
                    data-testid="user-role-select"
                    value={userRole}
                    onChange={(e) => setUserRole(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      marginTop: '0.25rem',
                    }}
                  >
                    <option value="admin">Admin</option>
                    <option value="member">Member</option>
                  </select>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddUserModal(false)
                      setUserEmail('')
                      setUserRole('admin')
                    }}
                    disabled={addingUser}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    data-testid="add-user-submit"
                    disabled={addingUser || !userEmail.trim()}
                  >
                    {addingUser ? 'Adding...' : 'Add User'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* User Success Modal */}
        {showUserSuccessModal && (
          <div data-testid="user-success-modal" style={{
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
              <h3>✅ User Added Successfully!</h3>
              <p>The user has been added and their account has been provisioned.</p>

              <div style={{ marginTop: '1.5rem', marginBottom: '1.5rem' }}>
                <h4>Password Setup Link</h4>
                <p style={{ fontSize: '0.9rem', color: '#666' }}>
                  Send this link to the user to set up their password:
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
                  data-testid="user-success-modal-close"
                  onClick={() => setShowUserSuccessModal(false)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <div data-testid="org-studies-section" style={{ marginTop: '2rem' }}>
        <h2>Studies</h2>
        {loadingStudies ? (
          <p>Loading studies...</p>
        ) : studies.length === 0 ? (
          <p>No studies yet</p>
        ) : (
          <ul>
            {studies.map((s) => (
              <li key={s.study_id}>
                {s.name}
              </li>
            ))}
          </ul>
        )}
        <button data-testid="create-study-button">Create Study</button>
      </div>
    </div>
  )
}
