import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { 
  Home, 
  Upload, 
  CheckCircle, 
  BarChart3, 
  MessageSquare, 
  Users, 
  Settings,
  Search,
  Bell,
  User,
  Menu,
  X,
  Brain,
  Zap,
  Globe,
  FileText,
  Eye,
  Shield,
  Layers,
  Download,
  LogOut,
  FileStack,
  ClipboardList,
  UserCheck,
  Phone,
  Mail,
  Package
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { cn } from '../lib/utils'

interface NavigationItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  roles: string[]
}

const navigationItems: NavigationItem[] = [
  {
    name: 'Dashboard',
    href: '/',
    icon: Home,
    roles: ['admin', 'manager', 'operator', 'viewer']
  },
  {
    name: 'File Processing',
    href: '/files',
    icon: Upload,
    roles: ['admin', 'manager', 'operator']
  },
  {
    name: 'Data Validation',
    href: '/validation',
    icon: CheckCircle,
    roles: ['admin', 'manager', 'operator']
  },
  {
    name: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
    roles: ['admin', 'manager']
  },
  {
    name: 'AI Commands',
    href: '/commands',
    icon: MessageSquare,
    roles: ['admin', 'manager', 'operator', 'viewer']
  },
  {
    name: 'AI Analysis',
    href: '/ai-analysis',
    icon: Brain,
    roles: ['admin', 'manager']
  },
  {
    name: 'Workflows',
    href: '/workflows',
    icon: Zap,
    roles: ['admin', 'manager', 'operator']
  },
  {
    name: 'Data Feeds',
    href: '/data-feeds',
    icon: Globe,
    roles: ['admin', 'manager']
  },
  {
    name: 'Data Entry',
    href: '/data-entry',
    icon: FileText,
    roles: ['admin', 'manager', 'operator']
  },
  {
    name: 'OCR Processing',
    href: '/ocr',
    icon: Eye,
    roles: ['admin', 'manager', 'operator']
  },
  {
    name: 'Quality Control',
    href: '/quality-control',
    icon: Shield,
    roles: ['admin', 'manager']
  },
  {
    name: 'Batch Processing',
    href: '/batch-processing',
    icon: Layers,
    roles: ['admin', 'manager', 'operator']
  },
  {
    name: 'Data Export',
    href: '/data-export',
    icon: Download,
    roles: ['admin', 'manager', 'operator']
  },
  {
    name: 'Access Control',
    href: '/access',
    icon: Users,
    roles: ['admin']
  },
  // New Enhanced Data Automation Features
  {
    name: 'Document Processing',
    href: '/document-processing',
    icon: FileStack,
    roles: ['admin', 'manager', 'operator']
  },
  {
    name: 'Data Validation Hub',
    href: '/data-validation',
    icon: CheckCircle,
    roles: ['admin', 'manager', 'operator']
  },
  {
    name: 'Templates',
    href: '/templates',
    icon: ClipboardList,
    roles: ['admin', 'manager', 'operator']
  },
  {
    name: 'Medical Records',
    href: '/medical-records',
    icon: UserCheck,
    roles: ['admin', 'manager', 'operator']
  },
  {
    name: 'Batch Upload',
    href: '/batch-upload',
    icon: Package,
    roles: ['admin', 'manager', 'operator']
  }
]

export const Navigation: React.FC = () => {
  const { user, logout, loading } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)

  const filteredNavItems = navigationItems.filter(item => 
    user && item.roles.includes(user.role)
  )

  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  return (
    <nav className="sticky top-0 z-50 border-b border-neutral-200 bg-glass-light backdrop-blur-glass supports-[backdrop-filter]:bg-glass-light/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-18">
          {/* Logo and brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-semibold text-neutral-900 hidden sm:block">
                DataFlow Enterprise
              </span>
            </Link>
          </div>

          {/* Desktop navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {filteredNavItems.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center space-x-2 px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'text-primary-500 border-b-2 border-primary-500'
                      : 'text-neutral-700 hover:text-primary-500'
                  )}
                >
                  <item.icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </div>

          {/* Search bar */}
          <div className="hidden lg:block flex-1 max-w-md mx-8">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-500 w-4 h-4" />
              <input
                type="text"
                placeholder="Search files, workflows..."
                className="w-full pl-10 pr-4 py-2 bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
              />
            </div>
          </div>

          {/* User controls */}
          <div className="flex items-center space-x-4">
            {/* Notifications - Only show for authenticated users */}
            {user && (
              <button className="relative p-2 text-neutral-500 hover:text-neutral-700 transition-colors">
                <Bell className="w-5 h-5" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-semantic-error rounded-full"></span>
              </button>
            )}

            {/* Authentication Status */}
            {!user && !loading ? (
              // Show login/signup buttons for non-authenticated users
              <div className="flex items-center space-x-2">
                <Link
                  to="/login"
                  className="px-3 py-2 text-sm font-medium text-neutral-700 hover:text-primary-600 transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/signup"
                  className="px-4 py-2 bg-primary-500 text-white text-sm font-medium rounded-lg hover:bg-primary-600 transition-colors"
                >
                  Sign Up
                </Link>
              </div>
            ) : user ? (
              // Show user dropdown for authenticated users
              <div className="relative">
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className="flex items-center space-x-2 p-2 rounded-lg hover:bg-white/50 transition-colors"
                >
                  <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-primary-600" />
                  </div>
                  <div className="hidden sm:block text-sm text-left">
                    <div className="font-medium text-neutral-900">{user.full_name}</div>
                    <div className="text-neutral-500 capitalize">{user.role}</div>
                  </div>
                </button>

                {/* User Dropdown Menu */}
                {isUserMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-neutral-200 py-2 z-50">
                    <div className="px-4 py-2 border-b border-neutral-200">
                      <p className="text-sm font-medium text-neutral-900">{user.full_name}</p>
                      <p className="text-xs text-neutral-500">{user.email}</p>
                    </div>
                    <button
                      onClick={() => {
                        setIsUserMenuOpen(false)
                        navigate('/profile')
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50 flex items-center space-x-2"
                    >
                      <User className="w-4 h-4" />
                      <span>Profile</span>
                    </button>
                    <button
                      onClick={() => {
                        setIsUserMenuOpen(false)
                        handleLogout()
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center space-x-2"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Logout</span>
                    </button>
                  </div>
                )}
              </div>
            ) : null}

            {/* Mobile menu button */}
            <button
              className="md:hidden p-2 text-neutral-500 hover:text-neutral-700"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-neutral-200 bg-glass-light backdrop-blur-glass">
          <div className="px-4 py-2 space-y-1">
            {/* Auth Menu Items */}
            {!user && !loading && (
              <>
                <Link
                  to="/login"
                  className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-neutral-700 hover:bg-neutral-50"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <User className="w-4 h-4" />
                  <span>Login</span>
                </Link>
                <Link
                  to="/signup"
                  className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium bg-primary-500 text-white hover:bg-primary-600"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>Sign Up</span>
                </Link>
                <hr className="my-2 border-neutral-200" />
              </>
            )}
            
            {/* Navigation Items */}
            {filteredNavItems.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium',
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-neutral-700 hover:bg-neutral-50'
                  )}
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <item.icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
            
            {/* User Menu Items (Mobile) */}
            {user && (
              <>
                <hr className="my-2 border-neutral-200" />
                <div className="px-3 py-2">
                  <p className="text-sm font-medium text-neutral-900">{user.full_name}</p>
                  <p className="text-xs text-neutral-500 capitalize">{user.role}</p>
                </div>
                <button
                  onClick={() => {
                    setIsMobileMenuOpen(false)
                    navigate('/profile')
                  }}
                  className="w-full text-left flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-neutral-700 hover:bg-neutral-50"
                >
                  <User className="w-4 h-4" />
                  <span>Profile</span>
                </button>
                <button
                  onClick={() => {
                    setIsMobileMenuOpen(false)
                    handleLogout()
                  }}
                  className="w-full text-left flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-red-600 hover:bg-red-50"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}