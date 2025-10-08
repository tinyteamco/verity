import { useParams, Navigate, Link, useNavigate } from 'react-router-dom'
import { useAtom, useSetAtom } from 'jotai'
import { userAtom, userIdAtom, userEmailAtom, userOrgIdAtom, userOrganizationNameAtom, userRoleAtom, userFirebaseUidAtom } from '../atoms/auth'
import { getApiUrl, generateStudy } from '../lib/api'
import { auth } from '../lib/firebase'
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface Organization {
  org_id: string
  name: string // slug
  display_name: string
  description?: string
  created_at: string
}

interface User {
  user_id: string
  email: string
  role: string
  created_at: string
}

interface Study {
  study_id: string
  title: string
  description: string | null
  org_id: string
  created_at: string
  updated_at: string | null
}

export function OrganizationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [user] = useAtom(userAtom)
  const setUserId = useSetAtom(userIdAtom)
  const setUserEmail = useSetAtom(userEmailAtom)
  const setUserOrgId = useSetAtom(userOrgIdAtom)
  const setUserOrganizationName = useSetAtom(userOrganizationNameAtom)
  const setUserRole = useSetAtom(userRoleAtom)
  const setUserFirebaseUid = useSetAtom(userFirebaseUidAtom)
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
  const [newUserEmail, setNewUserEmail] = useState('')
  const [newUserRole, setNewUserRole] = useState('admin')
  const [passwordResetLink, setPasswordResetLink] = useState('')
  const [addingUser, setAddingUser] = useState(false)

  // Study modal state
  const [showCreateStudyModal, setShowCreateStudyModal] = useState(false)
  const [showEditStudyModal, setShowEditStudyModal] = useState(false)
  const [showDeleteStudyModal, setShowDeleteStudyModal] = useState(false)
  const [selectedStudy, setSelectedStudy] = useState<Study | null>(null)
  const [studyTitle, setStudyTitle] = useState('')
  const [studyDescription, setStudyDescription] = useState('')
  const [savingStudy, setSavingStudy] = useState(false)
  const [deletingStudy, setDeletingStudy] = useState(false)
  const [studyError, setStudyError] = useState<string | null>(null)

  // Generate Study modal state
  const [showGenerateStudyModal, setShowGenerateStudyModal] = useState(false)
  const [topic, setTopic] = useState('')
  const [generatingStudy, setGeneratingStudy] = useState(false)
  const [generateError, setGenerateError] = useState<string | null>(null)
  const [topicValidationError, setTopicValidationError] = useState<string | null>(null)

  const fetchUsers = () => {
    // Only super admins can view users
    if (!user || !id || user.role !== 'super_admin') {
      setLoadingUsers(false)
      return
    }

    const token = localStorage.getItem('firebase_token')
    const apiUrl = getApiUrl()

    setLoadingUsers(true)
    fetch(`${apiUrl}/api/orgs/${id}/users`, {
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
    if (!newUserEmail.trim() || !newUserRole) return

    setAddingUser(true)
    const token = localStorage.getItem('firebase_token')
    const apiUrl = getApiUrl()

    try {
      const res = await fetch(`${apiUrl}/api/orgs/${id}/users`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: newUserEmail, role: newUserRole }),
      })

      if (!res.ok) {
        const errorText = await res.text()
        throw new Error(`HTTP ${res.status}: ${errorText}`)
      }

      const data = await res.json()

      // Close add user modal and reset form
      setShowAddUserModal(false)
      setNewUserEmail('')
      setNewUserRole('admin')

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

  const fetchStudies = () => {
    if (!user || !id) return

    const token = localStorage.getItem('firebase_token')
    const apiUrl = getApiUrl()

    setLoadingStudies(true)
    fetch(`${apiUrl}/api/orgs/${id}/studies`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        setStudies(data.items || [])
        setLoadingStudies(false)
      })
      .catch((err) => {
        console.error('[OrgDetail] Error fetching studies:', err)
        setLoadingStudies(false)
      })
  }

  const handleCreateStudy = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!studyTitle.trim()) return

    setSavingStudy(true)
    setStudyError(null)
    const token = localStorage.getItem('firebase_token')
    const apiUrl = getApiUrl()

    try {
      const res = await fetch(`${apiUrl}/api/orgs/${id}/studies`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: studyTitle,
          description: studyDescription || undefined,
        }),
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `HTTP ${res.status}`)
      }

      // Close modal and reset form
      setShowCreateStudyModal(false)
      setStudyTitle('')
      setStudyDescription('')
      setStudyError(null)

      // Refresh studies list
      fetchStudies()
    } catch (err: any) {
      console.error('[CreateStudy] Error:', err)
      setStudyError(err.message)
    } finally {
      setSavingStudy(false)
    }
  }

  const handleEditStudy = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedStudy || !studyTitle.trim()) return

    setSavingStudy(true)
    setStudyError(null)
    const token = localStorage.getItem('firebase_token')
    const apiUrl = getApiUrl()

    try {
      const res = await fetch(`${apiUrl}/api/orgs/${id}/studies/${selectedStudy.study_id}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: studyTitle,
          description: studyDescription || undefined,
        }),
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `HTTP ${res.status}`)
      }

      // Close modal and reset
      setShowEditStudyModal(false)
      setSelectedStudy(null)
      setStudyTitle('')
      setStudyDescription('')
      setStudyError(null)

      // Refresh studies list
      fetchStudies()
    } catch (err: any) {
      console.error('[EditStudy] Error:', err)
      setStudyError(err.message)
    } finally {
      setSavingStudy(false)
    }
  }

  const handleDeleteStudy = async () => {
    if (!selectedStudy) return

    setDeletingStudy(true)
    setStudyError(null)
    const token = localStorage.getItem('firebase_token')
    const apiUrl = getApiUrl()

    try {
      const res = await fetch(`${apiUrl}/api/orgs/${id}/studies/${selectedStudy.study_id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `HTTP ${res.status}`)
      }

      // Close modal and reset
      setShowDeleteStudyModal(false)
      setSelectedStudy(null)
      setStudyError(null)

      // Refresh studies list
      fetchStudies()
    } catch (err: any) {
      console.error('[DeleteStudy] Error:', err)
      setStudyError(err.message)
    } finally {
      setDeletingStudy(false)
    }
  }

  const handleGenerateStudy = async (e: React.FormEvent) => {
    e.preventDefault()

    // Validate topic
    const trimmedTopic = topic.trim()
    if (!trimmedTopic) {
      setTopicValidationError('Topic is required')
      return
    }
    if (trimmedTopic.length < 10) {
      setTopicValidationError('Topic must be at least 10 characters')
      return
    }
    if (trimmedTopic.length > 500) {
      setTopicValidationError('Topic must be less than 500 characters')
      return
    }

    setGeneratingStudy(true)
    setGenerateError(null)
    setTopicValidationError(null)

    const token = localStorage.getItem('firebase_token')
    if (!token || !id) {
      setGenerateError('Authentication required')
      setGeneratingStudy(false)
      return
    }

    // Set up timeout (60 seconds)
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 60000)

    try {
      await generateStudy(id, trimmedTopic, token)

      clearTimeout(timeoutId)

      // Close modal and reset form
      setShowGenerateStudyModal(false)
      setTopic('')
      setGenerateError(null)
      setTopicValidationError(null)

      // Refresh studies list
      fetchStudies()

      // Study now appears in the list after fetchStudies completes
    } catch (err: any) {
      clearTimeout(timeoutId)

      if (err.name === 'AbortError') {
        setGenerateError('Generation took too long. Please try again or create a study manually.')
      } else {
        setGenerateError(err.message || 'Failed to generate study. Please try again.')
      }
    } finally {
      setGeneratingStudy(false)
    }
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

  useEffect(() => {
    if (!user || !id) return

    const token = localStorage.getItem('firebase_token')
    const apiUrl = getApiUrl()

    // Fetch organization details
    fetch(`${apiUrl}/api/orgs/${id}`, {
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
    fetchStudies()
  }, [user, id])

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (loadingOrg) {
    return (
      <div className="container mx-auto p-6">
        <Link to="/" className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-block">← Back to Dashboard</Link>
        <p className="text-muted-foreground">Loading organization...</p>
      </div>
    )
  }

  if (error || !org) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-3xl font-bold mb-2">Organization Not Found</h1>
        {error && <p className="text-destructive mb-4">{error}</p>}
        <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">Back to Dashboard</Link>
      </div>
    )
  }

  return (
    <div data-testid="org-detail-page" className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between mb-4">
        <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">← Back to Dashboard</Link>
        <Button variant="outline" onClick={handleLogout}>
          Logout
        </Button>
      </div>

      <div>
        <h1 data-testid="org-detail-name" className="text-3xl font-bold">{org.display_name}</h1>
        {org.description && <p className="text-muted-foreground mt-2">{org.description}</p>}
        <p className="text-sm text-muted-foreground mt-1">Created: {new Date(org.created_at).toLocaleDateString()}</p>
      </div>

      {/* Users section - only visible to super admins */}
      {user.role === 'super_admin' && (
        <Card data-testid="org-users-section">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Users</CardTitle>
              <Button
                data-testid="add-user-button"
                onClick={() => setShowAddUserModal(true)}
              >
                Add User
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loadingUsers ? (
              <p className="text-muted-foreground">Loading users...</p>
            ) : users.length === 0 ? (
              <p className="text-muted-foreground">No users yet</p>
            ) : (
              <div data-testid="org-users-list" className="space-y-2">
                {users.map((u) => (
                  <div key={u.user_id} data-user-email={u.email} className="p-3 border rounded-md">
                    <span className="font-medium">{u.email}</span> <span className="text-muted-foreground">(<span data-testid="user-role">{u.role}</span>)</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Add User Modal */}
      <Dialog open={showAddUserModal} onOpenChange={setShowAddUserModal}>
        <DialogContent data-testid="add-user-modal">
          <DialogHeader>
            <DialogTitle>Add User to Organization</DialogTitle>
            <DialogDescription>Invite a new user to this organization</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddUser} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="user-email">User Email</Label>
              <Input
                id="user-email"
                data-testid="user-email-input"
                type="email"
                value={newUserEmail}
                onChange={(e) => setNewUserEmail(e.target.value)}
                placeholder="user@example.com"
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-role">Role</Label>
              <Select value={newUserRole} onValueChange={setNewUserRole}>
                <SelectTrigger id="user-role" data-testid="user-role-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="member">Member</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowAddUserModal(false)
                  setNewUserEmail('')
                  setNewUserRole('admin')
                }}
                disabled={addingUser}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                data-testid="add-user-submit"
                disabled={addingUser || !newUserEmail.trim()}
              >
                {addingUser ? 'Adding...' : 'Add User'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* User Success Modal */}
      <Dialog open={showUserSuccessModal} onOpenChange={setShowUserSuccessModal}>
        <DialogContent data-testid="user-success-modal" className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>✅ User Added Successfully!</DialogTitle>
            <DialogDescription>
              The user has been added and their account has been provisioned.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">Password Setup Link</h4>
              <p className="text-sm text-muted-foreground mb-3">
                Send this link to the user to set up their password:
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
              data-testid="user-success-modal-close"
              onClick={() => setShowUserSuccessModal(false)}
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Card data-testid="org-studies-section">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Studies</CardTitle>
            <div className="flex gap-2">
              <Button
                data-testid="generate-study-button"
                onClick={() => setShowGenerateStudyModal(true)}
              >
                Generate Study
              </Button>
              <Button
                data-testid="create-study-button"
                onClick={() => setShowCreateStudyModal(true)}
                variant="outline"
              >
                Create Study Manually
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loadingStudies ? (
            <p className="text-muted-foreground">Loading studies...</p>
          ) : studies.length === 0 ? (
            <p data-testid="no-studies" className="text-muted-foreground">No studies yet</p>
          ) : (
            <div data-testid="studies-list" className="space-y-2">
              {studies.map((s) => (
                <div key={s.study_id} data-testid={`study-${s.study_id}`} className="p-3 border rounded-md flex items-center justify-between">
                  <span
                    className="font-medium cursor-pointer hover:underline"
                    onClick={() => {
                      setSelectedStudy(s)
                      setStudyTitle(s.title)
                      setStudyDescription(s.description || '')
                      setShowEditStudyModal(true)
                    }}
                  >
                    {s.title}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSelectedStudy(s)
                      setShowDeleteStudyModal(true)
                    }}
                  >
                    Delete
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Generate Study Modal */}
      <Dialog open={showGenerateStudyModal} onOpenChange={setShowGenerateStudyModal}>
        <DialogContent data-testid="generate-study-modal">
          <DialogHeader>
            <DialogTitle>Generate Study</DialogTitle>
            <DialogDescription>Describe what you want to learn, and we'll create a study with an interview guide for you</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleGenerateStudy} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="topic">What do you want to learn?</Label>
              <Textarea
                id="topic"
                data-testid="topic-input"
                value={topic}
                onChange={(e) => {
                  setTopic(e.target.value)
                  setTopicValidationError(null)
                }}
                placeholder="e.g., How do people shop in supermarkets?"
                rows={4}
                autoFocus
              />
              {topicValidationError && (
                <p className="text-sm text-red-500">{topicValidationError}</p>
              )}
            </div>

            {generateError && (
              <div className="space-y-2">
                <p className="text-sm text-red-500">{generateError}</p>
                <div className="flex gap-2">
                  <Button
                    type="submit"
                    disabled={generatingStudy}
                  >
                    Retry
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowGenerateStudyModal(false)
                      setShowCreateStudyModal(true)
                      setTopic('')
                      setGenerateError(null)
                    }}
                  >
                    Create Manually
                  </Button>
                </div>
              </div>
            )}

            {!generateError && (
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowGenerateStudyModal(false)
                    setTopic('')
                    setGenerateError(null)
                    setTopicValidationError(null)
                  }}
                  disabled={generatingStudy}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  data-testid="generate-study-submit"
                  disabled={generatingStudy}
                >
                  {generatingStudy ? (
                    <span data-testid="generation-loading">Generating your study...</span>
                  ) : (
                    'Generate Study'
                  )}
                </Button>
              </DialogFooter>
            )}
          </form>
        </DialogContent>
      </Dialog>

      {/* Create Study Modal */}
      <Dialog open={showCreateStudyModal} onOpenChange={setShowCreateStudyModal}>
        <DialogContent data-testid="create-study-modal">
          <DialogHeader>
            <DialogTitle>Create Study Manually</DialogTitle>
            <DialogDescription>Add a new study to this organization</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateStudy} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="study-title">Study Title</Label>
              <Input
                id="study-title"
                data-testid="study-title-input"
                type="text"
                value={studyTitle}
                onChange={(e) => setStudyTitle(e.target.value)}
                placeholder="My Research Study"
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="study-description">
                Description <span className="text-xs text-muted-foreground">(optional)</span>
              </Label>
              <Textarea
                id="study-description"
                data-testid="study-description-input"
                value={studyDescription}
                onChange={(e) => setStudyDescription(e.target.value)}
                placeholder="A brief description of the study"
                rows={3}
              />
            </div>
            {studyError && (
              <div className="text-sm text-destructive">
                {studyError}
              </div>
            )}
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowCreateStudyModal(false)
                  setStudyTitle('')
                  setStudyDescription('')
                  setStudyError(null)
                }}
                disabled={savingStudy}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                data-testid="create-study-submit"
                disabled={savingStudy || !studyTitle.trim()}
              >
                {savingStudy ? 'Creating...' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Study Modal */}
      <Dialog open={showEditStudyModal} onOpenChange={setShowEditStudyModal}>
        <DialogContent data-testid="edit-study-modal">
          <DialogHeader>
            <DialogTitle>Edit Study</DialogTitle>
            <DialogDescription>Update study details</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEditStudy} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="edit-study-title">Study Title</Label>
              <Input
                id="edit-study-title"
                data-testid="study-title-input"
                type="text"
                value={studyTitle}
                onChange={(e) => setStudyTitle(e.target.value)}
                placeholder="My Research Study"
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-study-description">
                Description <span className="text-xs text-muted-foreground">(optional)</span>
              </Label>
              <Textarea
                id="edit-study-description"
                data-testid="study-description-input"
                value={studyDescription}
                onChange={(e) => setStudyDescription(e.target.value)}
                placeholder="A brief description of the study"
                rows={3}
              />
            </div>
            {studyError && (
              <div className="text-sm text-destructive">
                {studyError}
              </div>
            )}
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowEditStudyModal(false)
                  setSelectedStudy(null)
                  setStudyTitle('')
                  setStudyDescription('')
                  setStudyError(null)
                }}
                disabled={savingStudy}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                data-testid="edit-study-submit"
                disabled={savingStudy || !studyTitle.trim()}
              >
                {savingStudy ? 'Saving...' : 'Save'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Study Modal */}
      <Dialog open={showDeleteStudyModal} onOpenChange={setShowDeleteStudyModal}>
        <DialogContent data-testid="delete-study-modal">
          <DialogHeader>
            <DialogTitle>Delete Study</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedStudy?.title}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          {studyError && (
            <div className="text-sm text-destructive">
              {studyError}
            </div>
          )}
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setShowDeleteStudyModal(false)
                setSelectedStudy(null)
                setStudyError(null)
              }}
              disabled={deletingStudy}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              data-testid="delete-study-confirm"
              onClick={handleDeleteStudy}
              disabled={deletingStudy}
            >
              {deletingStudy ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
