import { createContext, useContext, useState, useEffect } from 'react'
import { login as apiLogin, register as apiRegister } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const isAuthenticated = Boolean(token)

  const login = async (email, password) => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiLogin(email, password)
      const accessToken = res.data.access_token
      localStorage.setItem('token', accessToken)
      setToken(accessToken)
      return { success: true }
    } catch (err) {
      const message =
        err.response?.data?.detail || 'Login failed. Please check your credentials.'
      setError(message)
      return { success: false, error: message }
    } finally {
      setLoading(false)
    }
  }

  const register = async (email, password) => {
    setLoading(true)
    setError(null)
    try {
      await apiRegister(email, password)
      return { success: true }
    } catch (err) {
      const message =
        err.response?.data?.detail || 'Registration failed. Please try again.'
      setError(message)
      return { success: false, error: message }
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
  }

  const clearError = () => setError(null)

  return (
    <AuthContext.Provider
      value={{ token, isAuthenticated, loading, error, login, register, logout, clearError }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
