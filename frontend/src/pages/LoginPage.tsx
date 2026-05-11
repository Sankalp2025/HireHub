import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { saveAuthTokens } from '../lib/auth'
import { api, getApiErrorMessage, type ApiResponse } from '../lib/api'

type LoginFormState = {
  email: string
  password: string
}

type LoginResponse = {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

const initialFormState: LoginFormState = {
  email: '',
  password: '',
}

function LoginPage() {
  const navigate = useNavigate()
  const [formState, setFormState] = useState<LoginFormState>(initialFormState)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  function updateField(field: keyof LoginFormState, value: string) {
    setFormState((currentState) => ({
      ...currentState,
      [field]: value,
    }))
  }

  function validateForm() {
    if (!formState.email.trim()) {
      return 'Please enter your email address.'
    }

    if (!formState.password.trim()) {
      return 'Please enter your password.'
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
      const response = await api.post<ApiResponse<LoginResponse>>('/auth/login', {
        email: formState.email.trim(),
        password: formState.password,
      })

      if (!response.data.data) {
        setErrorMessage('Login did not return tokens. Please try again.')
        return
      }

      saveAuthTokens({
        accessToken: response.data.data.access_token,
        refreshToken: response.data.data.refresh_token,
      })

      setSuccessMessage('Login successful. Redirecting to your dashboard...')
      setFormState(initialFormState)

      setTimeout(() => {
        navigate('/dashboard')
      }, 700)
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error, 'We could not log you in. Please try again.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="page auth-page">
      <section className="auth-layout">
        <div className="auth-intro">
          <p className="eyebrow">Authentication</p>
          <h1>Sign in and start using the app.</h1>
          <p className="hero-text">
            This page uses the same frontend pattern as registration, but now the backend
            returns tokens that let the app recognize an authenticated user.
          </p>

          <div className="auth-note-card">
            <h2>What this page teaches</h2>
            <ul className="auth-note-list">
              <li>How one API pattern can power multiple forms</li>
              <li>How login tokens are returned from the backend</li>
              <li>How the browser can store session data in local storage</li>
              <li>How navigation can happen after a successful action</li>
            </ul>
          </div>
        </div>

        <div className="auth-form-card">
          <div className="auth-form-header">
            <p className="eyebrow">Welcome back</p>
            <h2>Login</h2>
            <p className="form-supporting-text">
              Sign in with the account you created through the register page.
            </p>
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>
            <label className="form-field" htmlFor="email">
              <span>Email</span>
              <input
                id="email"
                name="email"
                type="email"
                value={formState.email}
                onChange={(event) => updateField('email', event.target.value)}
                placeholder="jane@example.com"
                autoComplete="email"
              />
            </label>

            <label className="form-field" htmlFor="password">
              <span>Password</span>
              <input
                id="password"
                name="password"
                type="password"
                value={formState.password}
                onChange={(event) => updateField('password', event.target.value)}
                placeholder="Your password"
                autoComplete="current-password"
              />
            </label>

            {errorMessage ? (
              <p className="form-message form-message-error" role="alert">
                {errorMessage}
              </p>
            ) : null}

            {successMessage ? (
              <p className="form-message form-message-success" role="status">
                {successMessage}
              </p>
            ) : null}

            <button className="button button-primary form-submit" type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p className="form-footer">
            Need an account? <Link to="/register">Create one here</Link>
          </p>
        </div>
      </section>
    </main>
  )
}

export default LoginPage
