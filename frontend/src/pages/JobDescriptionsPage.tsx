import { useEffect, useRef, useState, type FormEvent } from 'react'
import { api, getApiErrorMessage, type ApiResponse, type PaginatedResponse } from '../lib/api'
import { useToast } from '../lib/useToast'
import Spinner from '../components/Spinner'

type JobDescription = {
  id: string
  user_id: string
  title: string
  company: string | null
  role: string | null
  content: string
  created_at: string
  updated_at: string
}

type JobDescriptionFormState = {
  title: string
  company: string
  role: string
  content: string
}

const initialFormState: JobDescriptionFormState = {
  title: '',
  company: '',
  role: '',
  content: '',
}

function JobDescriptionsPage() {
  const { showToast } = useToast()
  const [jobDescriptions, setJobDescriptions] = useState<JobDescription[]>([])
  const [formState, setFormState] = useState<JobDescriptionFormState>(initialFormState)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const titleInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    let isMounted = true

    async function loadJobDescriptions() {
      try {
        setIsLoading(true)
        setErrorMessage('')

        const response = await api.get<ApiResponse<PaginatedResponse<JobDescription>>>(
          '/job-descriptions',
        )

        if (!isMounted) {
          return
        }

        const items = response.data.data?.items ?? []
        setJobDescriptions(items)

        if (items.length > 0) {
          setSelectedId((currentSelectedId) => currentSelectedId ?? items[0].id)
        }
      } catch (error) {
        if (!isMounted) {
          return
        }

        setErrorMessage(
          getApiErrorMessage(error, 'We could not load your job descriptions. Please try again.'),
        )
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    void loadJobDescriptions()

    return () => {
      isMounted = false
    }
  }, [])

  function updateField(field: keyof JobDescriptionFormState, value: string) {
    setFormState((currentState) => ({
      ...currentState,
      [field]: value,
    }))
  }

  function validateForm() {
    if (!formState.title.trim()) {
      return 'Please give this job description a title.'
    }

    if (formState.content.trim().length < 50) {
      return 'Job description content must be at least 50 characters.'
    }

    return ''
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    setErrorMessage('')

    const validationMessage = validateForm()
    if (validationMessage) {
      setErrorMessage(validationMessage)
      return
    }

    setIsSubmitting(true)

    const payload = {
      title: formState.title.trim(),
      company: formState.company.trim() || null,
      role: formState.role.trim() || null,
      content: formState.content.trim(),
    }

    try {
      if (editingId) {
        const response = await api.patch<ApiResponse<JobDescription>>(
          `/job-descriptions/${editingId}`,
          payload,
        )

        const updatedJobDescription = response.data.data
        if (!updatedJobDescription) {
          setErrorMessage('The backend did not return the updated job description.')
          return
        }

        setJobDescriptions((current) =>
          current.map((jobDescription) =>
            jobDescription.id === updatedJobDescription.id ? updatedJobDescription : jobDescription,
          ),
        )
        setSelectedId(updatedJobDescription.id)
        setEditingId(null)
        setFormState(initialFormState)
        showToast('Changes saved.')
        return
      }

      const response = await api.post<ApiResponse<JobDescription>>('/job-descriptions', payload)

      const createdJobDescription = response.data.data
      if (!createdJobDescription) {
        setErrorMessage('The backend did not return the created job description.')
        return
      }

      setJobDescriptions((current) => [createdJobDescription, ...current])
      setSelectedId(createdJobDescription.id)
      setFormState(initialFormState)
      showToast('Job description saved.')
      titleInputRef.current?.focus()
    } catch (error) {
      showToast(
        getApiErrorMessage(
          error,
          editingId
            ? 'We could not save your changes. Please try again.'
            : 'We could not save this job description. Please try again.',
        ),
        'error',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  function startEditing(jobDescription: JobDescription) {
    setErrorMessage('')
    setConfirmingDeleteId(null)
    setEditingId(jobDescription.id)
    setFormState({
      title: jobDescription.title,
      company: jobDescription.company ?? '',
      role: jobDescription.role ?? '',
      content: jobDescription.content,
    })
    titleInputRef.current?.focus()
  }

  function cancelEditing() {
    setEditingId(null)
    setFormState(initialFormState)
    setErrorMessage('')
  }

  function selectJobDescription(id: string) {
    setSelectedId(id)
    setConfirmingDeleteId(null)
  }

  async function handleDelete(id: string) {
    setIsDeleting(true)

    try {
      await api.delete(`/job-descriptions/${id}`)

      const remaining = jobDescriptions.filter((jobDescription) => jobDescription.id !== id)
      setJobDescriptions(remaining)
      setSelectedId(remaining[0]?.id ?? null)
      setConfirmingDeleteId(null)

      if (editingId === id) {
        setEditingId(null)
        setFormState(initialFormState)
      }

      showToast('Job description deleted.')
    } catch (error) {
      showToast(
        getApiErrorMessage(error, 'We could not delete this job description. Please try again.'),
        'error',
      )
    } finally {
      setIsDeleting(false)
    }
  }

  const selectedJobDescription =
    jobDescriptions.find((jobDescription) => jobDescription.id === selectedId) ?? null

  return (
    <main className="page workspace-page">
      <section className="workspace-panel">
        <div className="workspace-header">
          <div>
            <p className="eyebrow">Job descriptions</p>
            <h1>Target roles you are applying to.</h1>
            <p className="hero-text">
              Save a job description for each role, then run an analysis against one of your
              resumes.
            </p>
          </div>
        </div>

        {errorMessage ? (
          <p className="form-message form-message-error workspace-message" role="alert">
            {errorMessage}
          </p>
        ) : null}

        <div className="workspace-layout">
          <div className="workspace-column">
            <div className="workspace-card">
              <div className="workspace-card-header">
                <h2>{editingId ? 'Edit job description' : 'Add a job description'}</h2>
                <p className="workspace-card-copy">
                  {editingId
                    ? 'Update any field, then save your changes.'
                    : 'Company and role are optional, but they make it easier to tell roles apart later.'}
                </p>
              </div>

              <form className="workspace-form" onSubmit={handleSubmit}>
                <label className="form-field" htmlFor="jdTitle">
                  <span>Title</span>
                  <input
                    ref={titleInputRef}
                    id="jdTitle"
                    name="jdTitle"
                    type="text"
                    placeholder="Senior Backend Engineer"
                    value={formState.title}
                    onChange={(event) => updateField('title', event.target.value)}
                  />
                </label>

                <label className="form-field" htmlFor="jdCompany">
                  <span>Company (optional)</span>
                  <input
                    id="jdCompany"
                    name="jdCompany"
                    type="text"
                    placeholder="Acme Corp"
                    value={formState.company}
                    onChange={(event) => updateField('company', event.target.value)}
                  />
                </label>

                <label className="form-field" htmlFor="jdRole">
                  <span>Role (optional)</span>
                  <input
                    id="jdRole"
                    name="jdRole"
                    type="text"
                    placeholder="Backend"
                    value={formState.role}
                    onChange={(event) => updateField('role', event.target.value)}
                  />
                </label>

                <label className="form-field" htmlFor="jdContent">
                  <span>Job description content</span>
                  <textarea
                    id="jdContent"
                    name="jdContent"
                    placeholder="Paste the job posting text here..."
                    value={formState.content}
                    onChange={(event) => updateField('content', event.target.value)}
                    rows={14}
                  />
                </label>

                <div className="form-actions">
                  <button
                    className="button button-primary form-submit"
                    type="submit"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? (
                      <Spinner label="Saving..." />
                    ) : editingId ? (
                      'Save changes'
                    ) : (
                      'Save job description'
                    )}
                  </button>
                  {editingId ? (
                    <button
                      className="button button-secondary"
                      type="button"
                      onClick={cancelEditing}
                      disabled={isSubmitting}
                    >
                      Cancel
                    </button>
                  ) : null}
                </div>
              </form>
            </div>
          </div>

          <div className="workspace-column workspace-column-wide">
            <div className="workspace-card">
              <div className="workspace-card-header workspace-card-header-row">
                <div>
                  <h2>Your saved job descriptions</h2>
                  <p className="workspace-card-copy">Select one to review it.</p>
                </div>
                <span className="workspace-stat">
                  {isLoading ? 'Loading...' : `${jobDescriptions.length} saved`}
                </span>
              </div>

              {isLoading ? (
                <div className="workspace-empty-state">
                  <Spinner label="Loading your job descriptions..." />
                </div>
              ) : jobDescriptions.length === 0 ? (
                <div className="workspace-empty-state">
                  <h3>No job descriptions yet.</h3>
                  <p>Save one using the form and it will appear here.</p>
                </div>
              ) : (
                <div className="resume-workspace">
                  <div className="resume-list">
                    {jobDescriptions.map((jobDescription) => (
                      <button
                        key={jobDescription.id}
                        type="button"
                        className={`resume-list-item ${
                          selectedId === jobDescription.id ? 'is-selected' : ''
                        }`}
                        onClick={() => selectJobDescription(jobDescription.id)}
                      >
                        <strong>{jobDescription.title}</strong>
                        <span>
                          {[jobDescription.company, jobDescription.role]
                            .filter(Boolean)
                            .join(' · ') || 'No company or role set'}
                        </span>
                      </button>
                    ))}
                  </div>

                  {selectedJobDescription ? (
                    <article className="resume-preview">
                      <div className="resume-preview-header">
                        <div>
                          <p className="resume-preview-label">Selected job description</p>
                          <h3>{selectedJobDescription.title}</h3>
                        </div>
                        <p className="resume-preview-meta">
                          Created{' '}
                          {new Date(selectedJobDescription.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="resume-preview-actions">
                        {confirmingDeleteId === selectedJobDescription.id ? (
                          <>
                            <span className="resume-preview-confirm">
                              Delete this job description? This cannot be undone.
                            </span>
                            <button
                              type="button"
                              className="button button-small button-secondary"
                              onClick={() => setConfirmingDeleteId(null)}
                              disabled={isDeleting}
                            >
                              Cancel
                            </button>
                            <button
                              type="button"
                              className="button button-small button-danger-solid"
                              onClick={() => void handleDelete(selectedJobDescription.id)}
                              disabled={isDeleting}
                            >
                              {isDeleting ? <Spinner label="Deleting..." /> : 'Delete'}
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              className="button button-small button-secondary"
                              onClick={() => startEditing(selectedJobDescription)}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              className="button button-small button-danger"
                              onClick={() => setConfirmingDeleteId(selectedJobDescription.id)}
                            >
                              Delete
                            </button>
                          </>
                        )}
                      </div>
                      <div className="resume-preview-body">
                        <pre>{selectedJobDescription.content}</pre>
                      </div>
                    </article>
                  ) : null}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}

export default JobDescriptionsPage
