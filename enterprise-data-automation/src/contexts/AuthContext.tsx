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
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => void
  switchRole: (role: User['role']) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Public user for anonymous access
const publicUser: User = {
  id: 'public-user',
  email: 'public@enterprise.com',
  full_name: 'Public User',
  role: 'admin',
  avatar_url: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face'
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(publicUser) // Default to public user
  const [loading, setLoading] = useState(false)

  const signIn = async (email: string, password: string) => {
    setLoading(true)
    // For public access, just simulate login
    setTimeout(() => {
      setUser(publicUser)
      setLoading(false)
    }, 500)
  }

  const signOut = () => {
    // Keep public user for seamless access
    setUser(publicUser)
  }

  const switchRole = (role: User['role']) => {
    if (user) {
      setUser({ ...user, role })
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut, switchRole }}>
      {children}
    </AuthContext.Provider>
  )
}