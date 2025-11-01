import React, { createContext, useContext, useState, useEffect } from 'react'

interface User {
  id: string
  email: string
  full_name: string
  role: 'admin' | 'manager' | 'operator' | 'viewer'
  avatar_url?: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for existing session on mount
    const checkSession = async () => {
      try {
        // Mock user for demo purposes
        const mockUser: User = {
          id: '1',
          email: 'demo@dataflow.com',
          full_name: 'Demo User',
          role: 'admin',
          avatar_url: null
        }
        setUser(mockUser)
      } catch (error) {
        console.log('No existing session')
      } finally {
        setLoading(false)
      }
    }

    checkSession()
  }, [])

  const login = async (email: string, password: string) => {
    setLoading(true)
    try {
      // Mock login for demo purposes
      const mockUser: User = {
        id: '1',
        email: email,
        full_name: 'Demo User',
        role: 'admin',
        avatar_url: null
      }
      setUser(mockUser)
    } catch (error) {
      throw new Error('Login failed')
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    setLoading(true)
    try {
      setUser(null)
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}