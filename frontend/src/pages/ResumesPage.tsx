import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import {
  api,
  getApiErrorMessage,
  postFormData,
  type ApiResponse,
  type PaginatedResponse,
} from '../lib/api'

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

const MAX_PDF_SIZE_BYTES = 5 * 1024 * 1024
type ResumeSource = 'text' | 'pdf'

function ResumesPage() {
  const [resumes, setResumes] = useState<Resume[]>([])
  const [formState, setFormState] = useState<ResumeFormState>(initialFormState)
  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null)
  const [editingResumeId, setEditingResumeId] = useState<string | null>(null)
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [resumeSource, setResumeSource] = useState<ResumeSource>('text')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const titleInputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
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
  }, [])

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

    if (resumeSource === 'pdf' && !editingResumeId) {
      if (!selectedFile) {
        return 'Please choose a PDF file to upload.'
      }
      if (selectedFile.type !== 'application/pdf') {
        return 'Only PDF files are accepted.'
      }
      if (selectedFile.size > MAX_PDF_SIZE_BYTES) {
        return 'File size exceeds the maximum of 5 MB.'
      }
      return ''
    }

    if (formState.content.trim().length < 50) {
      return 'Resume content must be at least 50 characters.'
    }

    return ''
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null)
  }

  function switchSource(source: ResumeSource) {
    setResumeSource(source)
    setSelectedFile(null)
    setErrorMessage('')
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

    const payload = {
      title: formState.title.trim(),
      content: formState.content.trim(),
    }

    try {
      if (resumeSource === 'pdf' && !editingResumeId && selectedFile) {
        const uploadData = new FormData()
        uploadData.append('file', selectedFile)
        uploadData.append('title', formState.title.trim())

        const response = await postFormData<ApiResponse<Resume>>('/resumes/upload', uploadData)

        const uploadedResume = response.data.data
        if (!uploadedResume) {
          setErrorMessage('The backend did not return the uploaded resume.')
          return
        }

        setResumes((currentResumes) => [uploadedResume, ...currentResumes])
        setSelectedResumeId(uploadedResume.id)
        setFormState(initialFormState)
        setSelectedFile(null)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
        setSuccessMessage('Resume uploaded.')
        return
      }

      if (editingResumeId) {
        const response = await api.patch<ApiResponse<Resume>>(
          `/resumes/${editingResumeId}`,
          payload,
        )

        const updatedResume = response.data.data
        if (!updatedResume) {
          setErrorMessage('The backend did not return the updated resume.')
          return
        }

        setResumes((currentResumes) =>
          currentResumes.map((resume) =>
            resume.id === updatedResume.id ? updatedResume : resume,
          ),
        )
        setSelectedResumeId(updatedResume.id)
        setEditingResumeId(null)
        setFormState(initialFormState)
        setSuccessMessage('Changes saved.')
        return
      }

      const response = await api.post<ApiResponse<Resume>>('/resumes', payload)

      const createdResume = response.data.data
      if (!createdResume) {
        setErrorMessage('The backend did not return the created resume.')
        return
      }

      setResumes((currentResumes) => [createdResume, ...currentResumes])
      setSelectedResumeId(createdResume.id)
      setFormState(initialFormState)
      setSuccessMessage('Resume saved.')
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(
          error,
          editingResumeId
            ? 'We could not save your changes. Please try again.'
            : resumeSource === 'pdf'
              ? 'We could not upload your resume. Please try again.'
              : 'We could not save your resume. Please try again.',
        ),
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  function startEditing(resume: Resume) {
    setErrorMessage('')
    setSuccessMessage('')
    setConfirmingDeleteId(null)
    setEditingResumeId(resume.id)
    setResumeSource('text')
    setSelectedFile(null)
    setFormState({ title: resume.title, content: resume.content })
    titleInputRef.current?.focus()
  }

  function cancelEditing() {
    setEditingResumeId(null)
    setFormState(initialFormState)
    setErrorMessage('')
  }

  function selectResume(resumeId: string) {
    setSelectedResumeId(resumeId)
    setConfirmingDeleteId(null)
  }

  async function handleDelete(resumeId: string) {
    setErrorMessage('')
    setSuccessMessage('')
    setIsDeleting(true)

    try {
      await api.delete(`/resumes/${resumeId}`)

      const remainingResumes = resumes.filter((resume) => resume.id !== resumeId)
      setResumes(remainingResumes)
      setSelectedResumeId(remainingResumes[0]?.id ?? null)
      setConfirmingDeleteId(null)

      if (editingResumeId === resumeId) {
        setEditingResumeId(null)
        setFormState(initialFormState)
      }

      setSuccessMessage('Resume deleted.')
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, 'We could not delete this resume. Please try again.'),
      )
    } finally {
      setIsDeleting(false)
    }
  }

  const selectedResume = resumes.find((resume) => resume.id === selectedResumeId) ?? null

  return (
    <main className="page workspace-page">
      <section className="workspace-panel">
        <div className="workspace-header">
          <div>
            <p className="eyebrow">Resumes</p>
            <h1>Your resume versions.</h1>
            <p className="hero-text">
              Keep a tailored version of your resume for each role you are targeting.
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
                <h2>{editingResumeId ? 'Edit resume' : 'Create a resume'}</h2>
                <p className="workspace-card-copy">
                  {editingResumeId
                    ? 'Update the title or content, then save your changes.'
                    : 'Give each version a clear title so you can tell them apart later.'}
                </p>
              </div>

              {!editingResumeId ? (
                <div className="source-tabs" role="tablist" aria-label="Resume source">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={resumeSource === 'text'}
                    className={`source-tab ${resumeSource === 'text' ? 'is-active' : ''}`}
                    onClick={() => switchSource('text')}
                  >
                    Paste text
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={resumeSource === 'pdf'}
                    className={`source-tab ${resumeSource === 'pdf' ? 'is-active' : ''}`}
                    onClick={() => switchSource('pdf')}
                  >
                    Upload PDF
                  </button>
                </div>
              ) : null}

              <form className="workspace-form" onSubmit={handleSubmit}>
                <label className="form-field" htmlFor="resumeTitle">
                  <span>Resume title</span>
                  <input
                    ref={titleInputRef}
                    id="resumeTitle"
                    name="resumeTitle"
                    type="text"
                    placeholder="Software Engineer Resume v1"
                    value={formState.title}
                    onChange={(event) => updateField('title', event.target.value)}
                  />
                </label>

                {resumeSource === 'pdf' && !editingResumeId ? (
                  <label className="form-field" htmlFor="resumeFile">
                    <span>PDF file</span>
                    <input
                      ref={fileInputRef}
                      id="resumeFile"
                      name="resumeFile"
                      type="file"
                      accept="application/pdf"
                      onChange={handleFileChange}
                    />
                    <span className="form-field-hint">
                      {selectedFile ? selectedFile.name : 'PDF only, up to 5 MB.'}
                    </span>
                  </label>
                ) : (
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
                )}

                <div className="form-actions">
                  <button
                    className="button button-primary form-submit"
                    type="submit"
                    disabled={isSubmitting}
                  >
                    {isSubmitting
                      ? resumeSource === 'pdf' && !editingResumeId
                        ? 'Uploading...'
                        : 'Saving...'
                      : editingResumeId
                        ? 'Save changes'
                        : resumeSource === 'pdf'
                          ? 'Upload resume'
                          : 'Save resume'}
                  </button>
                  {editingResumeId ? (
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
                  <h2>Your saved resumes</h2>
                  <p className="workspace-card-copy">
                    Select a version to review, edit, or delete it.
                  </p>
                </div>
                <span className="workspace-stat">
                  {isLoading ? 'Loading...' : `${resumes.length} saved`}
                </span>
              </div>

              {isLoading ? (
                <div className="workspace-empty-state">
                  <h3>Loading your resumes...</h3>
                </div>
              ) : resumes.length === 0 ? (
                <div className="workspace-empty-state">
                  <h3>No resumes yet.</h3>
                  <p>Save your first resume using the form and it will appear here.</p>
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
                        onClick={() => selectResume(resume.id)}
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
                      <div className="resume-preview-actions">
                        {confirmingDeleteId === selectedResume.id ? (
                          <>
                            <span className="resume-preview-confirm">
                              Delete this resume? This cannot be undone.
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
                              onClick={() => void handleDelete(selectedResume.id)}
                              disabled={isDeleting}
                            >
                              {isDeleting ? 'Deleting...' : 'Delete'}
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              className="button button-small button-secondary"
                              onClick={() => startEditing(selectedResume)}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              className="button button-small button-danger"
                              onClick={() => setConfirmingDeleteId(selectedResume.id)}
                            >
                              Delete
                            </button>
                          </>
                        )}
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
