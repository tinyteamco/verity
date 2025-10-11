import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom'
import { useAtom, useSetAtom } from 'jotai'
import { userAtom, userIdAtom, userEmailAtom, userOrgIdAtom, userOrganizationNameAtom, userRoleAtom, userFirebaseUidAtom } from './atoms/auth'
import { organizationsAtom } from './atoms/organizations'
import { LoginPage } from './pages/LoginPage'
import { OrganizationDetailPage } from './pages/OrganizationDetailPage'
import { InterviewsPage } from './pages/InterviewsPage'
import { loadAuthState } from './lib/auth-persistence'
import { getApiUrl } from './lib/api'
import { initializeAuth } from './lib/auth-init'
import { auth } from './lib/firebase'
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

function Dashboard() {
  const navigate = useNavigate()
  const [user] = useAtom(userAtom)
  const setUserId = useSetAtom(userIdAtom)
  const setUserEmail = useSetAtom(userEmailAtom)
  const setUserOrgId = useSetAtom(userOrgIdAtom)
  const setUserOrganizationName = useSetAtom(userOrganizationNameAtom)
  const setUserRole = useSetAtom(userRoleAtom)
  const setUserFirebaseUid = useSetAtom(userFirebaseUidAtom)
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

  const handleLogout = async () => {
    // Sign out from Firebase
    await auth.signOut()

    // Clear localStorage
    localStorage.removeItem('firebase_token')
    localStorage.removeItem('auth_state')

    // Clear user atoms
    setUserId(null)
    setUserEmail(null)
    setUserOrgId(null)
    setUserOrganizationName(null)
    setUserRole(null)
    setUserFirebaseUid(null)

    // Navigate to login
    navigate('/login')
  }

  if (user.role === 'super_admin') {
    return (
      <div data-testid="admin-dashboard" className="container mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Super Admin Dashboard</h1>
            <p data-testid="admin-email" className="text-muted-foreground">{user.email}</p>
          </div>
          <Button variant="outline" onClick={handleLogout}>
            Logout
          </Button>
        </div>

        <Card data-testid="organizations-section">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Organizations</CardTitle>
              <Button
                data-testid="create-org-button"
                onClick={() => setShowCreateModal(true)}
              >
                Create Organization
              </Button>
            </div>
          </CardHeader>
          <CardContent>

          <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
            <DialogContent data-testid="create-org-modal">
              <DialogHeader>
                <DialogTitle>Create Organization</DialogTitle>
                <DialogDescription>Add a new organization to the platform</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreateOrg} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="org-name">
                    Organization Slug <span className="text-xs text-muted-foreground">(lowercase, hyphens only)</span>
                  </Label>
                  <Input
                    id="org-name"
                    data-testid="org-name-input"
                    type="text"
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value.toLowerCase())}
                    placeholder="my-company"
                    pattern="[a-z0-9-]+"
                    autoFocus
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="display-name">Display Name</Label>
                  <Input
                    id="display-name"
                    data-testid="display-name-input"
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="My Company Inc."
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">
                    Description <span className="text-xs text-muted-foreground">(optional)</span>
                  </Label>
                  <Textarea
                    id="description"
                    data-testid="description-input"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="A brief description of the organization"
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="owner-email">Owner Email</Label>
                  <Input
                    id="owner-email"
                    data-testid="owner-email-input"
                    type="email"
                    value={ownerEmail}
                    onChange={(e) => setOwnerEmail(e.target.value)}
                    placeholder="owner@example.com"
                  />
                </div>
                {createError && (
                  <div className="text-sm text-destructive">
                    {createError}
                  </div>
                )}
                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
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
                  </Button>
                  <Button
                    type="submit"
                    data-testid="create-org-submit"
                    disabled={creating || !orgName.trim() || !displayName.trim() || !ownerEmail.trim()}
                  >
                    {creating ? 'Creating...' : 'Create'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>

          <Dialog open={showSuccessModal} onOpenChange={setShowSuccessModal}>
            <DialogContent data-testid="success-modal" className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>✅ Organization Created Successfully!</DialogTitle>
                <DialogDescription>
                  The organization has been created and the owner account has been provisioned.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Password Setup Link</h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    Send this link to the organization owner to set up their password:
                  </p>
                  <div className="bg-muted p-4 rounded-md break-all text-sm font-mono">
                    <code data-testid="password-reset-link">{passwordResetLink}</code>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      navigator.clipboard.writeText(passwordResetLink)
                      alert('Link copied to clipboard!')
                    }}
                    className="mt-2"
                  >
                    Copy Link
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground">
                  ⚠️ This link expires in 1 hour
                </p>
              </div>
              <DialogFooter>
                <Button
                  data-testid="success-modal-close"
                  onClick={() => setShowSuccessModal(false)}
                >
                  Close
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

            <div data-testid="organizations-list" className="mt-4">
              {loading ? (
                <p className="text-muted-foreground">Loading...</p>
              ) : organizations.length === 0 ? (
                <p data-testid="no-orgs" className="text-muted-foreground">No organizations yet</p>
              ) : (
                <div className="space-y-2">
                  {organizations.map((org) => (
                    <div key={org.org_id} data-testid={`org-${org.org_id}`} className="p-3 border rounded-md hover:bg-muted/50 transition-colors">
                      <Link to={`/orgs/${org.org_id}`} className="text-lg font-medium hover:underline">{org.display_name}</Link>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Non-super-admin users should be redirected to their org detail page
  if (user.orgId) {
    return <Navigate to={`/orgs/${user.orgId}`} replace />
  }

  // Fallback for users without org (shouldn't happen)
  return (
    <div data-testid="user-dashboard">
      <h1>Dashboard</h1>
      <p data-testid="user-email">{user.email}</p>
      <p className="text-destructive">No organization assigned</p>
      <Button variant="outline" onClick={handleLogout}>
        Logout
      </Button>
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
        <Route path="/orgs/:orgId/studies/:studyId/interviews" element={<InterviewsPage />} />
        <Route path="/orgs/:orgId/studies/:studyId/interviews/:interviewId" element={<InterviewsPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
