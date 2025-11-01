import React, { createContext, useContext, useState, useEffect } from 'react'
import { createClient } from '@supabase/supabase-js'
import { User as SupabaseUser } from '@supabase/supabase-js'

// Initialize Supabase client
const supabaseUrl = 'https://cantzkmdnfeikyqyifmk.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNhbnR6a21kbmZlaWt5cXlpZm1rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE5ODYzODksImV4cCI6MjA3NzU2MjM4OX0.66Uir0-ZCVAswYA-4Q91pNowzFluNB5YH2BPQdUSSFQ'

const supabase = createClient(supabaseUrl, supabaseAnonKey)

interface User {
  id: string
  email: string
  full_name?: string
  role: 'admin' | 'manager' | 'operator' | 'viewer'
  avatar_url?: string
}

interface AuthContextType {
  user: User | null
  supabaseUser: SupabaseUser | null
  loading: boolean
  login: (email: string, password: string) => Promise<any>
  signup: (email: string, password: string, fullName: string) => Promise<any>
  logout: () => Promise<void>
  updateProfile: (updates: Partial<User>) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [supabaseUser, setSupabaseUser] = useState<SupabaseUser | null>(null)
  const [loading, setLoading] = useState(true)

  // Function to map Supabase user to our User type
  const mapSupabaseUser = (supabaseUser: SupabaseUser | null): User | null => {
    if (!supabaseUser) return null
    
    // For now, assign default role based on email pattern
    // In production, this would come from user_metadata or a users table
    const defaultRole: 'admin' | 'manager' | 'operator' | 'viewer' = 
      supabaseUser.email?.includes('admin') ? 'admin' : 'manager'
    
    return {
      id: supabaseUser.id,
      email: supabaseUser.email || '',
      full_name: supabaseUser.user_metadata?.full_name || supabaseUser.email?.split('@')[0] || 'User',
      role: supabaseUser.user_metadata?.role || defaultRole,
      avatar_url: supabaseUser.user_metadata?.avatar_url || undefined
    }
  }

  useEffect(() => {
    // Load user on mount (one-time check)
    async function loadUser() {
      setLoading(true)
      try {
        const { data: { user } } = await supabase.auth.getUser()
        setSupabaseUser(user)
        setUser(mapSupabaseUser(user))
      } catch (error) {
        console.error('Error loading user:', error)
      } finally {
        setLoading(false)
      }
    }
    
    loadUser()

    // Set up auth listener - KEEP SIMPLE, avoid any async operations in callback
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        // NEVER use any async operations in callback
        setSupabaseUser(session?.user || null)
        setUser(mapSupabaseUser(session?.user || null))
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  const login = async (email: string, password: string) => {
    setLoading(true)
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      })
      
      if (error) {
        throw error
      }
      
      // User will be set via onAuthStateChange
      return data
    } catch (error: any) {
      console.error('Login error:', error)
      throw new Error(error.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const signup = async (email: string, password: string, fullName: string) => {
    setLoading(true)
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
            role: 'manager' // Default role
          }
        }
      })
      
      if (error) {
        throw error
      }
      
      // User will be set via onAuthStateChange
      return data
    } catch (error: any) {
      console.error('Signup error:', error)
      throw new Error(error.message || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    setLoading(true)
    try {
      const { error } = await supabase.auth.signOut()
      if (error) {
        throw error
      }
      // User will be cleared via onAuthStateChange
    } catch (error: any) {
      console.error('Logout error:', error)
      throw new Error(error.message || 'Logout failed')
    } finally {
      setLoading(false)
    }
  }

  const updateProfile = async (updates: Partial<User>) => {
    if (!supabaseUser) {
      throw new Error('No authenticated user')
    }

    try {
      const { error } = await supabase.auth.updateUser({
        data: updates
      })

      if (error) {
        throw error
      }

      // Update local user state
      setUser(prev => prev ? { ...prev, ...updates } : null)
    } catch (error: any) {
      console.error('Profile update error:', error)
      throw new Error(error.message || 'Profile update failed')
    }
  }

  return (
    <AuthContext.Provider value={{ 
      user, 
      supabaseUser, 
      loading, 
      login, 
      signup, 
      logout, 
      updateProfile 
    }}>
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

// Export Supabase client for use in other components
export { supabase }