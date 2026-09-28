import { createContext } from 'react'

export type CurrentUser = {
  id: string
  email: string
  full_name: string
  created_at: string
}

export type LoginTokens = {
  accessToken: string
  refreshToken: string
}

export type AuthContextValue = {
  user: CurrentUser | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (tokens: LoginTokens) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)
