import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { getApiUrl } from '../lib/api'

interface Study {
  study_id: string
  title: string
  description: string | null
  org_id: string
  created_at: string
  updated_at: string | null
}

export function StudyListPage() {
  const { orgId } = useParams<{ orgId: string }>()
  const navigate = useNavigate()
  const [studies, setStudies] = useState<Study[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const fetchStudies = async () => {
    const token = localStorage.getItem('firebase_token')
    const apiUrl = getApiUrl()

    setLoading(true)
    try {
      const res = await fetch(`${apiUrl}/api/studies`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Organization-ID': orgId!,
        },
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      const data = await res.json()
      setStudies(data.items || [])
    } catch (err) {
      console.error('[StudyList] Error fetching studies:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateStudy = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return

    setCreating(true)
    setCreateError(null)
    const token = localStorage.getItem('firebase_token')
    const apiUrl = getApiUrl()

    try {
      const res = await fetch(`${apiUrl}/api/studies`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Organization-ID': orgId!,
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

      // Close modal and reset form
      setShowCreateModal(false)
      setTitle('')
      setDescription('')
      setCreateError(null)

      // Refresh studies list
      await fetchStudies()
    } catch (err: any) {
      console.error('[CreateStudy] Error:', err)
      setCreateError(err.message)
    } finally {
      setCreating(false)
    }
  }

  useEffect(() => {
    if (orgId) {
      fetchStudies()
    }
  }, [orgId])

  return (
    <div data-testid="studies-page">
      <h1>Studies</h1>

      <button
        data-testid="create-study-button"
        onClick={() => setShowCreateModal(true)}
      >
        Create Study
      </button>

      {showCreateModal && (
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
            <h3>Create Study</h3>
            <form onSubmit={handleCreateStudy}>
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="study-title">Study Title</label>
                <input
                  id="study-title"
                  data-testid="study-title-input"
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Onboarding Feedback"
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    marginTop: '0.25rem',
                  }}
                  autoFocus
                />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="study-description">
                  Description <span style={{ color: '#666', fontSize: '0.85rem' }}>(optional)</span>
                </label>
                <textarea
                  id="study-description"
                  data-testid="study-description-input"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Brief description of the study"
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    marginTop: '0.25rem',
                    minHeight: '80px',
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
                    setTitle('')
                    setDescription('')
                    setCreateError(null)
                  }}
                  disabled={creating}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  data-testid="study-form-submit"
                  disabled={creating || !title.trim()}
                >
                  {creating ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div data-testid="studies-list">
        {loading ? (
          <p>Loading...</p>
        ) : studies.length === 0 ? (
          <p data-testid="no-studies">No studies yet</p>
        ) : (
          <ul>
            {studies.map((study) => (
              <li key={study.study_id} data-testid={`study-${study.study_id}`}>
                <Link to={`/orgs/${orgId}/studies/${study.study_id}`}>
                  {study.title}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
