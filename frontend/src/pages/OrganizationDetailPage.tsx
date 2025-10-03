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
  user_id: number
  email: string
  role: string
  firebase_uid: string
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
        setUsers(Array.isArray(data) ? data : [])
        setLoadingUsers(false)
      })
      .catch((err) => {
        console.error('[OrgDetail] Error fetching users:', err)
        setLoadingUsers(false)
      })

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
          <ul>
            {users.map((u) => (
              <li key={u.user_id}>
                {u.email} ({u.role})
              </li>
            ))}
          </ul>
        )}
        <button data-testid="add-user-button">Add User</button>
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
