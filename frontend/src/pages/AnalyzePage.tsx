import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useToast } from '../lib/useToast'
import Spinner from '../components/Spinner'
import { api, getApiErrorMessage, type ApiResponse, type PaginatedResponse } from '../lib/api'
import type { AnalysisResult } from '../lib/analysisTypes'
import AnalysisResultView from '../components/AnalysisResultView'

type Resume = {
  id: string
  title: string
}

type JobDescription = {
  id: string
  title: string
  company: string | null
  role: string | null
}

function AnalyzePage() {
  const { showToast } = useToast()
  const [resumes, setResumes] = useState<Resume[]>([])
  const [jobDescriptions, setJobDescriptions] = useState<JobDescription[]>([])
  const [resumeId, setResumeId] = useState('')
  const [jdId, setJdId] = useState('')
  const [isLoadingOptions, setIsLoadingOptions] = useState(true)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [result, setResult] = useState<AnalysisResult | null>(null)

  useEffect(() => {
    let isMounted = true

    async function loadOptions() {
      try {
        setIsLoadingOptions(true)
        setErrorMessage('')

        const [resumesResponse, jobDescriptionsResponse] = await Promise.all([
          api.get<ApiResponse<PaginatedResponse<Resume>>>('/resumes'),
          api.get<ApiResponse<PaginatedResponse<JobDescription>>>('/job-descriptions'),
        ])

        if (!isMounted) {
          return
        }

        const loadedResumes = resumesResponse.data.data?.items ?? []
        const loadedJobDescriptions = jobDescriptionsResponse.data.data?.items ?? []

        setResumes(loadedResumes)
        setJobDescriptions(loadedJobDescriptions)
        setResumeId((current) => current || (loadedResumes[0]?.id ?? ''))
        setJdId((current) => current || (loadedJobDescriptions[0]?.id ?? ''))
      } catch (error) {
        if (!isMounted) {
          return
        }

        setErrorMessage(
          getApiErrorMessage(error, 'We could not load your resumes and job descriptions.'),
        )
      } finally {
        if (isMounted) {
          setIsLoadingOptions(false)
        }
      }
    }

    void loadOptions()

    return () => {
      isMounted = false
    }
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage('')

    if (!resumeId || !jdId) {
      setErrorMessage('Select a resume and a job description to compare.')
      return
    }

    setIsAnalyzing(true)
    setResult(null)

    try {
      const response = await api.post<ApiResponse<AnalysisResult>>('/analyses', {
        resume_id: resumeId,
        jd_id: jdId,
      })

      const analysis = response.data.data
      if (!analysis) {
        setErrorMessage('The backend did not return an analysis result.')
        return
      }

      setResult(analysis)
    } catch (error) {
      showToast(
        getApiErrorMessage(error, 'We could not run this analysis. Please try again.'),
        'error',
      )
    } finally {
      setIsAnalyzing(false)
    }
  }

  const hasOptions = resumes.length > 0 && jobDescriptions.length > 0

  return (
    <main className="page workspace-page">
      <section className="workspace-panel">
        <div className="workspace-header">
          <div>
            <p className="eyebrow">Analysis</p>
            <h1>Compare a resume against a job description.</h1>
            <p className="hero-text">
              Pick a saved resume and a saved job description to see how closely they match.
            </p>
          </div>
        </div>

        {errorMessage ? (
          <p className="form-message form-message-error workspace-message" role="alert">
            {errorMessage}
          </p>
        ) : null}

        {isLoadingOptions ? (
          <div className="workspace-empty-state">
            <Spinner label="Loading your resumes and job descriptions..." />
          </div>
        ) : !hasOptions ? (
          <div className="workspace-empty-state">
            <h3>You need at least one resume and one job description.</h3>
            <p>Save both, then come back here to run an analysis.</p>
            <div className="hero-actions">
              <Link className="button button-primary" to="/resumes">
                Go to resumes
              </Link>
              <Link className="button button-secondary" to="/job-descriptions">
                Go to job descriptions
              </Link>
            </div>
          </div>
        ) : (
          <div className="workspace-layout">
            <div className="workspace-column">
              <div className="workspace-card">
                <div className="workspace-card-header">
                  <h2>Choose what to compare</h2>
                  <p className="workspace-card-copy">
                    Both lists are drawn from what you have already saved.
                  </p>
                </div>

                <form className="workspace-form" onSubmit={handleSubmit}>
                  <label className="form-field" htmlFor="resumeSelect">
                    <span>Resume</span>
                    <select
                      id="resumeSelect"
                      name="resumeSelect"
                      value={resumeId}
                      onChange={(event) => setResumeId(event.target.value)}
                    >
                      {resumes.map((resume) => (
                        <option key={resume.id} value={resume.id}>
                          {resume.title}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="form-field" htmlFor="jdSelect">
                    <span>Job description</span>
                    <select
                      id="jdSelect"
                      name="jdSelect"
                      value={jdId}
                      onChange={(event) => setJdId(event.target.value)}
                    >
                      {jobDescriptions.map((jobDescription) => (
                        <option key={jobDescription.id} value={jobDescription.id}>
                          {jobDescription.title}
                          {jobDescription.company ? ` · ${jobDescription.company}` : ''}
                        </option>
                      ))}
                    </select>
                  </label>

                  <button
                    className="button button-primary form-submit"
                    type="submit"
                    disabled={isAnalyzing}
                  >
                    {isAnalyzing ? <Spinner label="Analyzing..." /> : 'Run analysis'}
                  </button>
                </form>
              </div>
            </div>

            <div className="workspace-column workspace-column-wide">
              <div className="workspace-card">
                {!result ? (
                  <div className="workspace-empty-state">
                    <h3>No analysis yet.</h3>
                    <p>Run one using the form to see a match score here.</p>
                  </div>
                ) : (
                  <AnalysisResultView result={result} />
                )}
              </div>
            </div>
          </div>
        )}
      </section>
    </main>
  )
}

export default AnalyzePage
