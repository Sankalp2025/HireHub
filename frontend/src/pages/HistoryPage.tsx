import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
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

function HistoryPage() {
  const [analyses, setAnalyses] = useState<AnalysisResult[]>([])
  const [resumesById, setResumesById] = useState<Record<string, Resume>>({})
  const [jobDescriptionsById, setJobDescriptionsById] = useState<
    Record<string, JobDescription>
  >({})
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    let isMounted = true

    async function loadHistory() {
      try {
        setIsLoading(true)
        setErrorMessage('')

        const [analysesResponse, resumesResponse, jobDescriptionsResponse] = await Promise.all([
          api.get<ApiResponse<PaginatedResponse<AnalysisResult>>>('/analyses'),
          api.get<ApiResponse<PaginatedResponse<Resume>>>('/resumes'),
          api.get<ApiResponse<PaginatedResponse<JobDescription>>>('/job-descriptions'),
        ])

        if (!isMounted) {
          return
        }

        const loadedAnalyses = analysesResponse.data.data?.items ?? []
        const loadedResumes = resumesResponse.data.data?.items ?? []
        const loadedJobDescriptions = jobDescriptionsResponse.data.data?.items ?? []

        setAnalyses(loadedAnalyses)
        setResumesById(Object.fromEntries(loadedResumes.map((resume) => [resume.id, resume])))
        setJobDescriptionsById(
          Object.fromEntries(loadedJobDescriptions.map((jd) => [jd.id, jd])),
        )

        if (loadedAnalyses.length > 0) {
          setSelectedId((current) => current ?? loadedAnalyses[0].id)
        }
      } catch (error) {
        if (!isMounted) {
          return
        }

        setErrorMessage(getApiErrorMessage(error, 'We could not load your analysis history.'))
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    void loadHistory()

    return () => {
      isMounted = false
    }
  }, [])

  const selectedAnalysis = analyses.find((analysis) => analysis.id === selectedId) ?? null

  function describeAnalysis(analysis: AnalysisResult) {
    const resumeTitle = analysis.resume_id ? resumesById[analysis.resume_id]?.title : null
    const jd = analysis.jd_id ? jobDescriptionsById[analysis.jd_id] : null
    const jdLabel = jd ? [jd.title, jd.company].filter(Boolean).join(' · ') : null

    return {
      resumeLabel: resumeTitle ?? 'Deleted resume',
      jdLabel: jdLabel ?? 'Deleted job description',
    }
  }

  return (
    <main className="page workspace-page">
      <section className="workspace-panel">
        <div className="workspace-header">
          <div>
            <p className="eyebrow">History</p>
            <h1>Past analyses.</h1>
            <p className="hero-text">Every analysis you have run, with the full result saved.</p>
          </div>
        </div>

        {errorMessage ? (
          <p className="form-message form-message-error workspace-message" role="alert">
            {errorMessage}
          </p>
        ) : null}

        {isLoading ? (
          <div className="workspace-empty-state">
            <Spinner label="Loading your analysis history..." />
          </div>
        ) : analyses.length === 0 ? (
          <div className="workspace-empty-state">
            <h3>No analyses yet.</h3>
            <p>Run one from the Analyze page and it will show up here.</p>
            <div className="hero-actions">
              <Link className="button button-primary" to="/analyze">
                Go to Analyze
              </Link>
            </div>
          </div>
        ) : (
          <div className="workspace-layout">
            <div className="workspace-column">
              <div className="workspace-card">
                <div className="workspace-card-header">
                  <h2>Runs</h2>
                  <p className="workspace-card-copy">Select one to see the full breakdown.</p>
                </div>

                <div className="resume-list">
                  {analyses.map((analysis) => {
                    const { resumeLabel, jdLabel } = describeAnalysis(analysis)
                    const scorePercent = Math.round(Number(analysis.match_score))

                    return (
                      <button
                        key={analysis.id}
                        type="button"
                        className={`resume-list-item history-list-item ${
                          selectedId === analysis.id ? 'is-selected' : ''
                        }`}
                        onClick={() => setSelectedId(analysis.id)}
                      >
                        <span className="history-list-item-top">
                          <strong>{jdLabel}</strong>
                          <span className="history-score-pill">{scorePercent}%</span>
                        </span>
                        <span>
                          {resumeLabel} ·{' '}
                          {new Date(analysis.analyzed_at).toLocaleDateString()}
                        </span>
                      </button>
                    )
                  })}
                </div>
              </div>
            </div>

            <div className="workspace-column workspace-column-wide">
              <div className="workspace-card">
                {selectedAnalysis ? (
                  <AnalysisResultView result={selectedAnalysis} />
                ) : (
                  <div className="workspace-empty-state">
                    <h3>Select a run to see its details.</h3>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </section>
    </main>
  )
}

export default HistoryPage
