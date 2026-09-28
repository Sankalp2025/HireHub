import { BrowserRouter, NavLink, Route, Routes, useNavigate } from 'react-router-dom'
import './App.css'
import { AuthProvider } from './lib/AuthContext'
import { useAuth } from './lib/useAuth'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ResumesPage from './pages/ResumesPage'

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
          <p className="hero-card-label">How it works</p>
          <ul className="checklist">
            {workflowSteps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </aside>
      </section>

      <section className="section">
        <div className="section-heading">
          <p className="eyebrow">What you get</p>
          <h2>Everything you need to tailor a resume to a specific role.</h2>
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
  const { user } = useAuth()

  return (
    <main className="page">
      <section className="dashboard-panel">
        <p className="eyebrow">Workspace</p>
        <h1>Welcome back{user ? `, ${user.full_name}` : ''}.</h1>
        <p className="hero-text">
          Manage your saved resumes, job descriptions, and analysis history from here.
        </p>

        {user ? (
          <div className="dashboard-grid">
            <article className="dashboard-card">
              <p className="dashboard-card-label">Account</p>
              <h2>{user.full_name}</h2>
              <p className="dashboard-card-value">{user.email}</p>
            </article>

            <article className="dashboard-card">
              <p className="dashboard-card-label">Resumes</p>
              <h2>Manage versions</h2>
              <p className="dashboard-card-value">
                <NavLink to="/resumes">Open resumes workspace</NavLink>
              </p>
            </article>

            <article className="dashboard-card">
              <p className="dashboard-card-label">Coming next</p>
              <h2>Job descriptions & analysis</h2>
              <p className="dashboard-card-value">
                Save target roles and run match analyses against your resumes.
              </p>
            </article>
          </div>
        ) : null}
      </section>
    </main>
  )
}

function AppShell() {
  const { isAuthenticated, isLoading, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/')
  }

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
          {!isLoading && isAuthenticated ? (
            <>
              <NavLink to="/dashboard">Dashboard</NavLink>
              <NavLink to="/resumes">Resumes</NavLink>
              <button type="button" className="nav-logout" onClick={handleLogout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login">Login</NavLink>
              <NavLink to="/register">Register</NavLink>
            </>
          )}
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/resumes"
          element={
            <ProtectedRoute>
              <ResumesPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
