const ACCESS_TOKEN_KEY = 'hirehub_access_token'
const REFRESH_TOKEN_KEY = 'hirehub_refresh_token'

type AuthTokens = {
  accessToken: string
  refreshToken: string
}

export function saveAuthTokens(tokens: AuthTokens) {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.accessToken)
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken)
}

export function clearAuthTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function isLoggedIn() {
  return Boolean(getAccessToken())
}
