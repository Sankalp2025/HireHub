import { Link } from 'react-router-dom'
import { useAuth } from '../lib/useAuth'

function NotFoundPage() {
  const { isAuthenticated } = useAuth()

  return (
    <main className="page">
      <section className="hero-panel not-found-panel">
        <div className="hero-copy">
          <p className="eyebrow">404</p>
          <h1>This page doesn't exist.</h1>
          <p className="hero-text">
            The link may be out of date, or the page may have moved.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" to="/">
              Go home
            </Link>
            {isAuthenticated ? (
              <Link className="button button-secondary" to="/dashboard">
                Go to dashboard
              </Link>
            ) : (
              <Link className="button button-secondary" to="/login">
                Sign in
              </Link>
            )}
          </div>
        </div>
      </section>
    </main>
  )
}

export default NotFoundPage
