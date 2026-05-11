import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api, getApiErrorMessage, type ApiResponse } from '../lib/api'

type RegisterFormState = {
  fullName: string
  email: string
  password: string
}

type RegisterResponse = {
  id: string
  email: string
  full_name: string
  created_at: string
}

const initialFormState: RegisterFormState = {
  fullName: '',
  email: '',
  password: '',
}

function RegisterPage() {
  const [formState, setFormState] = useState<RegisterFormState>(initialFormState)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  function updateField(field: keyof RegisterFormState, value: string) {
    setFormState((currentState) => ({
      ...currentState,
      [field]: value,
    }))
  }

  function validateForm() {
    if (!formState.fullName.trim()) {
      return 'Please enter your full name.'
    }

    if (!formState.email.trim()) {
      return 'Please enter your email address.'
    }

    if (formState.password.length < 8) {
      return 'Password must be at least 8 characters.'
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
      const response = await api.post<ApiResponse<RegisterResponse>>('/auth/register', {
        email: formState.email.trim(),
        password: formState.password,
        full_name: formState.fullName.trim(),
      })

      if (!response.data.data) {
        setErrorMessage('Registration did not return a user. Please try again.')
        return
      }

      setSuccessMessage(
        `Account created for ${response.data.data.full_name}. Next we’ll connect this to login.`,
      )
      setFormState(initialFormState)
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, 'We could not create your account. Please try again.'),
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="page auth-page">
      <section className="auth-layout">
        <div className="auth-intro">
          <p className="eyebrow">Authentication</p>
          <h1>Create your HireHub account.</h1>
          <p className="hero-text">
            This form sends a real request to the FastAPI backend. That means you are now
            building actual frontend behavior, not just static screens.
          </p>

          <div className="auth-note-card">
            <h2>What this page teaches</h2>
            <ul className="auth-note-list">
              <li>How React stores form values in state</li>
              <li>How a submit handler prevents the browser refresh</li>
              <li>How the frontend sends JSON to the backend</li>
              <li>How success and error messages are shown to the user</li>
            </ul>
          </div>
        </div>

        <div className="auth-form-card">
          <div className="auth-form-header">
            <p className="eyebrow">New account</p>
            <h2>Register</h2>
            <p className="form-supporting-text">
              Use a real email and a password with at least 8 characters.
            </p>
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>
            <label className="form-field" htmlFor="fullName">
              <span>Full name</span>
              <input
                id="fullName"
                name="fullName"
                type="text"
                value={formState.fullName}
                onChange={(event) => updateField('fullName', event.target.value)}
                placeholder="Jane Doe"
                autoComplete="name"
              />
            </label>

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
                placeholder="At least 8 characters"
                autoComplete="new-password"
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
              {isSubmitting ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          <p className="form-footer">
            Already have an account? <Link to="/login">Go to login</Link>
          </p>
        </div>
      </section>
    </main>
  )
}

export default RegisterPage
