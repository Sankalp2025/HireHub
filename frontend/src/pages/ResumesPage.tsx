import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { isLoggedIn } from '../lib/auth'
import { api, getApiErrorMessage, type ApiResponse, type PaginatedResponse } from '../lib/api'

type Resume = {
  id: string
  user_id: string
  title: string
  content: string
  created_at: string
  updated_at: string
}

type ResumeFormState = {
  title: string
  content: string
}

const initialFormState: ResumeFormState = {
  title: '',
  content: '',
}

function ResumesPage() {
  const loggedIn = isLoggedIn()
  const [resumes, setResumes] = useState<Resume[]>([])
  const [formState, setFormState] = useState<ResumeFormState>(initialFormState)
  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(loggedIn)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    if (!loggedIn) {
      setIsLoading(false)
      setResumes([])
      return
    }

    let isMounted = true

    async function loadResumes() {
      try {
        setIsLoading(true)
        setErrorMessage('')

        const response = await api.get<ApiResponse<PaginatedResponse<Resume>>>('/resumes')

        if (!isMounted) {
          return
        }

        const items = response.data.data?.items ?? []
        setResumes(items)

        if (items.length > 0) {
          setSelectedResumeId((currentSelectedId) => currentSelectedId ?? items[0].id)
        }
      } catch (error) {
        if (!isMounted) {
          return
        }

        setErrorMessage(
          getApiErrorMessage(error, 'We could not load your resumes. Please try again.'),
        )
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    void loadResumes()

    return () => {
      isMounted = false
    }
  }, [loggedIn])

  function updateField(field: keyof ResumeFormState, value: string) {
    setFormState((currentState) => ({
      ...currentState,
      [field]: value,
    }))
  }

  function validateForm() {
    if (!formState.title.trim()) {
      return 'Please give this resume a title.'
    }

    if (formState.content.trim().length < 50) {
      return 'Resume content must be at least 50 characters.'
    }

    return ''
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    setErrorMessage('')
    setSuccessMessage('')

    const validationMessage = validateForm()
    if (validationMessage) {
      setErrorMessage(validationMessage)
      return
    }

    setIsSubmitting(true)

    try {
      const response = await api.post<ApiResponse<Resume>>('/resumes', {
        title: formState.title.trim(),
        content: formState.content.trim(),
      })

      const createdResume = response.data.data
      if (!createdResume) {
        setErrorMessage('The backend did not return the created resume.')
        return
      }

      setResumes((currentResumes) => [createdResume, ...currentResumes])
      setSelectedResumeId(createdResume.id)
      setFormState(initialFormState)
      setSuccessMessage('Resume saved successfully.')
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, 'We could not save your resume. Please try again.'),
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  const selectedResume = resumes.find((resume) => resume.id === selectedResumeId) ?? null

  if (!loggedIn) {
    return (
      <main className="page">
        <section className="workspace-panel">
          <p className="eyebrow">Resumes</p>
          <h1>Please log in to manage your resumes.</h1>
          <p className="hero-text">
            This page is built against the protected backend resume endpoints, so you need
            an authenticated session before we can load or save anything.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" to="/login">
              Go to login
            </Link>
            <Link className="button button-secondary" to="/register">
              Create account
            </Link>
          </div>
        </section>
      </main>
    )
  }

  return (
    <main className="page workspace-page">
      <section className="workspace-panel">
        <div className="workspace-header">
          <div>
            <p className="eyebrow">Resumes</p>
            <h1>Build and manage your resume versions.</h1>
            <p className="hero-text">
              This page already follows the backend contract: it loads paginated resume
              data and submits new resumes to the protected API.
            </p>
          </div>
        </div>

        {errorMessage ? (
          <p className="form-message form-message-error workspace-message" role="alert">
            {errorMessage}
          </p>
        ) : null}

        {successMessage ? (
          <p className="form-message form-message-success workspace-message" role="status">
            {successMessage}
          </p>
        ) : null}

        <div className="workspace-layout">
          <div className="workspace-column">
            <div className="workspace-card">
              <div className="workspace-card-header">
                <h2>Create a resume</h2>
                <p className="workspace-card-copy">
                  Start with a version label so later you can tailor multiple resumes for
                  different roles.
                </p>
              </div>

              <form className="workspace-form" onSubmit={handleSubmit}>
                <label className="form-field" htmlFor="resumeTitle">
                  <span>Resume title</span>
                  <input
                    id="resumeTitle"
                    name="resumeTitle"
                    type="text"
                    placeholder="Software Engineer Resume v1"
                    value={formState.title}
                    onChange={(event) => updateField('title', event.target.value)}
                  />
                </label>

                <label className="form-field" htmlFor="resumeContent">
                  <span>Resume content</span>
                  <textarea
                    id="resumeContent"
                    name="resumeContent"
                    placeholder="Paste your resume text here..."
                    value={formState.content}
                    onChange={(event) => updateField('content', event.target.value)}
                    rows={14}
                  />
                </label>

                <button className="button button-primary form-submit" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Saving resume...' : 'Save resume'}
                </button>
              </form>
            </div>
          </div>

          <div className="workspace-column workspace-column-wide">
            <div className="workspace-card">
              <div className="workspace-card-header workspace-card-header-row">
                <div>
                  <h2>Your saved resumes</h2>
                  <p className="workspace-card-copy">
                    Select a version to review it while you keep building out your
                    portfolio-ready workflow.
                  </p>
                </div>
                <span className="workspace-stat">
                  {isLoading ? 'Loading...' : `${resumes.length} saved`}
                </span>
              </div>

              {isLoading ? (
                <div className="workspace-empty-state">
                  <h3>Loading your resumes...</h3>
                  <p>The frontend is asking the backend for your saved resume list.</p>
                </div>
              ) : resumes.length === 0 ? (
                <div className="workspace-empty-state">
                  <h3>No resumes yet.</h3>
                  <p>
                    Save your first resume on this page and it will appear here. This is
                    the first step toward building the full analysis flow.
                  </p>
                </div>
              ) : (
                <div className="resume-workspace">
                  <div className="resume-list">
                    {resumes.map((resume) => (
                      <button
                        key={resume.id}
                        type="button"
                        className={`resume-list-item ${
                          selectedResumeId === resume.id ? 'is-selected' : ''
                        }`}
                        onClick={() => setSelectedResumeId(resume.id)}
                      >
                        <strong>{resume.title}</strong>
                        <span>
                          Updated {new Date(resume.updated_at).toLocaleDateString()}
                        </span>
                      </button>
                    ))}
                  </div>

                  {selectedResume ? (
                    <article className="resume-preview">
                      <div className="resume-preview-header">
                        <div>
                          <p className="resume-preview-label">Selected resume</p>
                          <h3>{selectedResume.title}</h3>
                        </div>
                        <p className="resume-preview-meta">
                          Created {new Date(selectedResume.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="resume-preview-body">
                        <pre>{selectedResume.content}</pre>
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

export default ResumesPage
