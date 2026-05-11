import { useEffect, useState } from 'react'
import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import './App.css'
import { clearAuthTokens, isLoggedIn } from './lib/auth'
import { api, getApiErrorMessage, type ApiResponse } from './lib/api'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ResumesPage from './pages/ResumesPage'

type CurrentUser = {
  id: string
  email: string
  full_name: string
  created_at: string
}

function HomePage() {
  const features = [
    {
      title: 'Track resume versions',
      description:
        'Save tailored resume drafts for different roles and keep the editing process organized.',
    },
    {
      title: 'Compare against real job descriptions',
      description:
        'Paste a listing or select a saved job description to see how closely your resume matches.',
    },
    {
      title: 'Review skill gaps fast',
      description:
        'Surface missing skills, match scoring, and action-oriented suggestions in one place.',
    },
  ]

  const workflowSteps = [
    'Create an account and sign in.',
    'Save one or more resumes.',
    'Save job descriptions you want to target.',
    'Run analyses and review the score breakdown.',
  ]

  return (
    <main className="page">
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Resume analysis workspace</p>
          <h1>Make resume tailoring feel structured instead of overwhelming.</h1>
          <p className="hero-text">
            HireHub helps job seekers save resume versions, compare them to target roles,
            and turn vague feedback into practical next edits.
          </p>
          <div className="hero-actions">
            <NavLink className="button button-primary" to="/register">
              Create account
            </NavLink>
            <NavLink className="button button-secondary" to="/login">
              Sign in
            </NavLink>
          </div>
        </div>

        <aside className="hero-card" aria-label="Product summary">
          <p className="hero-card-label">Core flow</p>
          <ul className="checklist">
            {workflowSteps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </aside>
      </section>

      <section className="section">
        <div className="section-heading">
          <p className="eyebrow">What the frontend will cover</p>
          <h2>We’re building the complete user-facing side of the project.</h2>
        </div>

        <div className="feature-grid">
          {features.map((feature) => (
            <article key={feature.title} className="feature-card">
              <div className="feature-accent" aria-hidden="true" />
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}

function DashboardPage() {
  const loggedIn = isLoggedIn()
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [isLoading, setIsLoading] = useState(loggedIn)

  useEffect(() => {
    if (!loggedIn) {
      setIsLoading(false)
      setUser(null)
      return
    }

    let isMounted = true

    async function loadCurrentUser() {
      try {
        setIsLoading(true)
        setErrorMessage('')

        const response = await api.get<ApiResponse<CurrentUser>>('/auth/me')

        if (!isMounted) {
          return
        }

        if (!response.data.data) {
          setErrorMessage('We could not load your account details.')
          setUser(null)
          return
        }

        setUser(response.data.data)
      } catch (error) {
        if (!isMounted) {
          return
        }

        clearAuthTokens()
        setUser(null)
        setErrorMessage(
          getApiErrorMessage(
            error,
            'Your session could not be verified. Please log in again.',
          ),
        )
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    void loadCurrentUser()

    return () => {
      isMounted = false
    }
  }, [loggedIn])

  return (
    <main className="page">
      <section className="dashboard-panel">
        <p className="eyebrow">Workspace</p>
        <h1>
          {!loggedIn
            ? 'Please log in to access your dashboard.'
            : isLoading
              ? 'Checking your session...'
              : user
                ? `Welcome back, ${user.full_name}.`
                : 'Your session needs attention.'}
        </h1>
        <p className="hero-text">
          {!loggedIn
            ? 'The dashboard is a private area. Once you log in, we can fetch your real account data and later show resumes, job descriptions, and analysis history here.'
            : isLoading
              ? 'The frontend is using your saved access token to ask the backend who the current user is.'
              : user
                ? 'Your session is now being validated with the backend, not just the browser. This is the foundation for protected pages and authenticated data fetching.'
                : 'The frontend could not confirm your account with the backend. Logging in again should restore access.'}
        </p>

        {errorMessage ? (
          <p className="form-message form-message-error dashboard-message" role="alert">
            {errorMessage}
          </p>
        ) : null}

        {user ? (
          <div className="dashboard-grid">
            <article className="dashboard-card">
              <p className="dashboard-card-label">Authenticated user</p>
              <h2>{user.full_name}</h2>
              <p className="dashboard-card-value">{user.email}</p>
            </article>

            <article className="dashboard-card">
              <p className="dashboard-card-label">Account status</p>
              <h2>Active session</h2>
              <p className="dashboard-card-value">Access token accepted by backend</p>
            </article>

            <article className="dashboard-card">
              <p className="dashboard-card-label">Next frontend step</p>
              <h2>Protected workspace</h2>
              <p className="dashboard-card-value">
                Next we’ll turn this area into resume, job description, and analysis pages.
              </p>
            </article>
          </div>
        ) : null}
      </section>
    </main>
  )
}

function AppShell() {
  return (
    <div className="app-shell">
      <header className="site-header">
        <NavLink className="brand-mark" to="/">
          <span className="brand-badge">H</span>
          <div>
            <strong>HireHub</strong>
            <p>Resume matching studio</p>
          </div>
        </NavLink>

        <nav className="site-nav" aria-label="Primary">
          <NavLink to="/">Home</NavLink>
          <NavLink to="/login">Login</NavLink>
          <NavLink to="/register">Register</NavLink>
          <NavLink to="/dashboard">Dashboard</NavLink>
          <NavLink to="/resumes">Resumes</NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route
          path="/login"
          element={<LoginPage />}
        />
        <Route
          path="/register"
          element={<RegisterPage />}
        />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/resumes" element={<ResumesPage />} />
      </Routes>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  )
}

export default App
