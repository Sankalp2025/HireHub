import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, type ApiResponse } from './api'
import { clearAuthTokens, getAccessToken, saveAuthTokens } from './auth'
import { AuthContext, type AuthContextValue, type CurrentUser, type LoginTokens } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [isLoading, setIsLoading] = useState(Boolean(getAccessToken()))

  const loadCurrentUser = useCallback(async () => {
    try {
      const response = await api.get<ApiResponse<CurrentUser>>('/auth/me')
      setUser(response.data.data)
    } catch {
      clearAuthTokens()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (getAccessToken()) {
      // Session check on mount: no UI-driven alternative to fetching here.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      void loadCurrentUser()
    }
  }, [loadCurrentUser])

  const login = useCallback(
    async (tokens: LoginTokens) => {
      saveAuthTokens(tokens)
      setIsLoading(true)
      await loadCurrentUser()
    },
    [loadCurrentUser],
  )

  const logout = useCallback(() => {
    clearAuthTokens()
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      logout,
    }),
    [user, isLoading, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
