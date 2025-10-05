import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getApiUrl } from '../lib/api'

interface Study {
  study_id: string
  title: string
  description: string | null
  org_id: string
  created_at: string
  updated_at: string | null
}

export function StudyDetailPage() {
  const { orgId, studyId } = useParams<{ orgId: string; studyId: string }>()
  const navigate = useNavigate()
  const [study, setStudy] = useState<Study | null>(null)
  const [loading, setLoading] = useState(true)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStudy = async () => {
    const token = localStorage.getItem('firebase_token')
    const apiUrl = getApiUrl()

    setLoading(true)
    try {
      const res = await fetch(`${apiUrl}/api/orgs/${orgId}/studies/${studyId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      const data = await res.json()
      setStudy(data)
      setTitle(data.title)
      setDescription(data.description || '')
    } catch (err) {
      console.error('[StudyDetail] Error fetching study:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleEditStudy = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return

    setSaving(true)
    setError(null)
    const token = localStorage.getItem('firebase_token')
    const apiUrl = getApiUrl()

    try {
      const res = await fetch(`${apiUrl}/api/orgs/${orgId}/studies/${studyId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title,
          description: description || undefined,
        }),
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `HTTP ${res.status}`)
      }

      // Close modal and refresh
      setShowEditModal(false)
      setError(null)
      await fetchStudy()
    } catch (err: any) {
      console.error('[EditStudy] Error:', err)
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteStudy = async () => {
    setDeleting(true)
    setError(null)
    const token = localStorage.getItem('firebase_token')
    const apiUrl = getApiUrl()

    try {
      const res = await fetch(`${apiUrl}/api/orgs/${orgId}/studies/${studyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `HTTP ${res.status}`)
      }

      // Navigate back to studies list
      navigate(`/orgs/${orgId}/studies`)
    } catch (err: any) {
      console.error('[DeleteStudy] Error:', err)
      setError(err.message)
      setDeleting(false)
    }
  }

  useEffect(() => {
    if (orgId && studyId) {
      fetchStudy()
    }
  }, [orgId, studyId])

  if (loading) {
    return <div>Loading...</div>
  }

  if (!study) {
    return <div>Study not found</div>
  }

  return (
    <div data-testid="study-detail-page">
      <h1 data-testid="study-detail-title">{study.title}</h1>

      <div style={{ marginBottom: '2rem' }}>
        <button
          data-testid="edit-study-button"
          onClick={() => setShowEditModal(true)}
        >
          Edit Study
        </button>
        <button
          data-testid="delete-study-button"
          onClick={() => setShowDeleteModal(true)}
          style={{ marginLeft: '0.5rem' }}
        >
          Delete Study
        </button>
      </div>

      {study.description && (
        <div data-testid="study-detail-description" style={{ marginBottom: '2rem' }}>
          <h3>Description</h3>
          <p>{study.description}</p>
        </div>
      )}

      <div data-testid="interview-guide-section" style={{ marginBottom: '2rem' }}>
        <h2>Interview Guide</h2>
        <p style={{ color: '#666' }}>Interview guide management coming soon...</p>
      </div>

      <div data-testid="interviews-section">
        <h2>Interviews</h2>
        <p style={{ color: '#666' }}>Interview management coming soon...</p>
      </div>

      {/* Edit Modal */}
      {showEditModal && (
        <div data-testid="study-modal" style={{
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
            <h3>Edit Study</h3>
            <form onSubmit={handleEditStudy}>
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="study-title">Study Title</label>
                <input
                  id="study-title"
                  data-testid="study-title-input"
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    marginTop: '0.25rem',
                  }}
                  autoFocus
                />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="study-description">Description</label>
                <textarea
                  id="study-description"
                  data-testid="study-description-input"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    marginTop: '0.25rem',
                    minHeight: '80px',
                  }}
                />
              </div>
              {error && (
                <div style={{ color: 'red', marginBottom: '1rem', fontSize: '0.9rem' }}>
                  {error}
                </div>
              )}
              <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false)
                    setTitle(study.title)
                    setDescription(study.description || '')
                    setError(null)
                  }}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  data-testid="study-form-submit"
                  disabled={saving || !title.trim()}
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div data-testid="delete-modal" style={{
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
            <h3>Delete Study</h3>
            <p>Are you sure you want to delete "{study.title}"?</p>
            <p style={{ color: '#666', fontSize: '0.9rem' }}>This action cannot be undone.</p>
            {error && (
              <div style={{ color: 'red', marginBottom: '1rem', fontSize: '0.9rem' }}>
                {error}
              </div>
            )}
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
              <button
                type="button"
                onClick={() => {
                  setShowDeleteModal(false)
                  setError(null)
                }}
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                data-testid="confirm-delete-button"
                onClick={handleDeleteStudy}
                disabled={deleting}
                style={{
                  backgroundColor: '#dc2626',
                  color: 'white',
                }}
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
