import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import './App.css'

type PlaceholderPageProps = {
  eyebrow: string
  title: string
  description: string
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

function PlaceholderPage({ eyebrow, title, description }: PlaceholderPageProps) {
  return (
    <main className="page">
      <section className="placeholder-panel">
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="hero-text">{description}</p>
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
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route
          path="/login"
          element={
            <PlaceholderPage
              eyebrow="Authentication"
              title="Login page coming next."
              description="This route is ready. Our next step will be turning it into a real form connected to the FastAPI auth endpoints."
            />
          }
        />
        <Route
          path="/register"
          element={
            <PlaceholderPage
              eyebrow="Authentication"
              title="Register page coming next."
              description="We’ll build this with validation, API calls, and clean error states so you can understand the full auth flow."
            />
          }
        />
        <Route
          path="/dashboard"
          element={
            <PlaceholderPage
              eyebrow="Workspace"
              title="Dashboard page coming next."
              description="This is where your saved resumes, job descriptions, and recent analyses will eventually live."
            />
          }
        />
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
