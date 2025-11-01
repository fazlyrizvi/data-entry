import React, { useState, useEffect, useRef } from 'react'
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
  Package,
  ChevronDown
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { cn } from '../lib/utils'

interface NavigationItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  roles: string[]
}

interface NavigationGroup {
  name: string
  items: NavigationItem[]
}

// Organize navigation into logical groups
const navigationGroups: NavigationGroup[] = [
  {
    name: 'Main',
    items: [
      {
        name: 'Dashboard',
        href: '/',
        icon: Home,
        roles: ['admin', 'manager', 'operator', 'viewer']
      }
    ]
  },
  {
    name: 'Data Processing',
    items: [
      {
        name: 'File Processing',
        href: '/files',
        icon: Upload,
        roles: ['admin', 'manager', 'operator']
      },
      {
        name: 'Document Processing',
        href: '/document-processing',
        icon: FileStack,
        roles: ['admin', 'manager', 'operator']
      },
      {
        name: 'OCR Processing',
        href: '/ocr',
        icon: Eye,
        roles: ['admin', 'manager', 'operator']
      },
      {
        name: 'Batch Processing',
        href: '/batch-processing',
        icon: Layers,
        roles: ['admin', 'manager', 'operator']
      },
      {
        name: 'Batch Upload',
        href: '/batch-upload',
        icon: Package,
        roles: ['admin', 'manager', 'operator']
      }
    ]
  },
  {
    name: 'Data Entry',
    items: [
      {
        name: 'Data Entry',
        href: '/data-entry',
        icon: FileText,
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
      }
    ]
  },
  {
    name: 'Quality & Validation',
    items: [
      {
        name: 'Data Validation',
        href: '/validation',
        icon: CheckCircle,
        roles: ['admin', 'manager', 'operator']
      },
      {
        name: 'Data Validation Hub',
        href: '/data-validation',
        icon: CheckCircle,
        roles: ['admin', 'manager', 'operator']
      },
      {
        name: 'Quality Control',
        href: '/quality-control',
        icon: Shield,
        roles: ['admin', 'manager']
      }
    ]
  },
  {
    name: 'Analytics & AI',
    items: [
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
      }
    ]
  },
  {
    name: 'Automation',
    items: [
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
      }
    ]
  },
  {
    name: 'Export & Admin',
    items: [
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
      }
    ]
  }
]

export const Navigation: React.FC = () => {
  const { user, logout, loading } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null)
  
  const userMenuRef = useRef<HTMLDivElement>(null)
  const dropdownRefs = useRef<{ [key: string]: HTMLDivElement | null }>({})

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false)
      }
      
      if (activeDropdown) {
        const dropdownRef = dropdownRefs.current[activeDropdown]
        if (dropdownRef && !dropdownRef.contains(event.target as Node)) {
          setActiveDropdown(null)
        }
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [activeDropdown])

  // Filter navigation groups based on user role
  const filteredGroups = navigationGroups.map(group => ({
    ...group,
    items: group.items.filter(item => user && item.roles.includes(user.role))
  })).filter(group => group.items.length > 0)

  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  return (
    <nav className="sticky top-0 z-[100] border-b border-neutral-200 bg-white/90 backdrop-blur-md shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center shadow-md">
                <CheckCircle className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-semibold text-neutral-900 hidden sm:block">
                DataFlow Enterprise
              </span>
            </Link>
          </div>

          {/* Desktop navigation with dropdown groups */}
          <div className="hidden lg:flex items-center space-x-1">
            {filteredGroups.map((group) => {
              if (group.items.length === 1) {
                // Single item - render as direct link
                const item = group.items[0]
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    className={cn(
                      'flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200',
                      isActive
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-neutral-700 hover:bg-neutral-50 hover:text-blue-600'
                    )}
                  >
                    <item.icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                )
              }

              // Multiple items - render as dropdown
              const isGroupActive = group.items.some(item => location.pathname === item.href)
              const isDropdownOpen = activeDropdown === group.name

              return (
                <div
                  key={group.name}
                  className="relative"
                  ref={(el) => { dropdownRefs.current[group.name] = el }}
                >
                  <button
                    onClick={() => setActiveDropdown(isDropdownOpen ? null : group.name)}
                    className={cn(
                      'flex items-center space-x-1 px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200',
                      isGroupActive
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-neutral-700 hover:bg-neutral-50 hover:text-blue-600'
                    )}
                  >
                    <span>{group.name}</span>
                    <ChevronDown className={cn(
                      'w-4 h-4 transition-transform duration-200',
                      isDropdownOpen && 'rotate-180'
                    )} />
                  </button>

                  {isDropdownOpen && (
                    <div className="absolute top-full left-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-neutral-200 py-2 z-[110] animate-in fade-in slide-in-from-top-2 duration-200">
                      {group.items.map((item) => {
                        const isActive = location.pathname === item.href
                        return (
                          <Link
                            key={item.href}
                            to={item.href}
                            onClick={() => setActiveDropdown(null)}
                            className={cn(
                              'flex items-center space-x-3 px-4 py-2.5 text-sm transition-colors',
                              isActive
                                ? 'bg-blue-50 text-blue-600 font-medium'
                                : 'text-neutral-700 hover:bg-neutral-50'
                            )}
                          >
                            <item.icon className="w-4 h-4" />
                            <span>{item.name}</span>
                          </Link>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* User controls */}
          <div className="flex items-center space-x-4">
            {/* Notifications - Only show for authenticated users */}
            {user && (
              <button className="relative p-2 text-neutral-500 hover:text-neutral-700 hover:bg-neutral-50 rounded-lg transition-colors">
                <Bell className="w-5 h-5" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
            )}

            {/* Authentication Status */}
            {!user && !loading ? (
              // Show login/signup buttons for non-authenticated users
              <div className="flex items-center space-x-2">
                <Link
                  to="/login"
                  className="px-3 py-2 text-sm font-medium text-neutral-700 hover:text-blue-600 transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/signup"
                  className="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white text-sm font-medium rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all shadow-sm"
                >
                  Sign Up
                </Link>
              </div>
            ) : user ? (
              // Show user dropdown for authenticated users
              <div className="relative" ref={userMenuRef}>
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className="flex items-center space-x-2 p-2 rounded-lg hover:bg-neutral-50 transition-colors"
                >
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-blue-700" />
                  </div>
                  <div className="hidden sm:block text-sm text-left">
                    <div className="font-medium text-neutral-900">{user.full_name}</div>
                    <div className="text-neutral-500 capitalize text-xs">{user.role}</div>
                  </div>
                  <ChevronDown className={cn(
                    'w-4 h-4 text-neutral-500 transition-transform duration-200 hidden sm:block',
                    isUserMenuOpen && 'rotate-180'
                  )} />
                </button>

                {/* User Dropdown Menu */}
                {isUserMenuOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-neutral-200 py-2 z-[110] animate-in fade-in slide-in-from-top-2 duration-200">
                    <div className="px-4 py-3 border-b border-neutral-200">
                      <p className="text-sm font-medium text-neutral-900">{user.full_name}</p>
                      <p className="text-xs text-neutral-500 mt-1">{user.email}</p>
                      <p className="text-xs text-blue-600 capitalize mt-1 font-medium">{user.role}</p>
                    </div>
                    <button
                      onClick={() => {
                        setIsUserMenuOpen(false)
                        navigate('/profile')
                      }}
                      className="w-full text-left px-4 py-2.5 text-sm text-neutral-700 hover:bg-neutral-50 flex items-center space-x-3 transition-colors"
                    >
                      <User className="w-4 h-4" />
                      <span>Profile</span>
                    </button>
                    <div className="border-t border-neutral-200 my-1"></div>
                    <button
                      onClick={() => {
                        setIsUserMenuOpen(false)
                        handleLogout()
                      }}
                      className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 flex items-center space-x-3 transition-colors"
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
              className="lg:hidden p-2 text-neutral-500 hover:text-neutral-700 hover:bg-neutral-50 rounded-lg transition-colors"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isMobileMenuOpen && (
        <div className="lg:hidden border-t border-neutral-200 bg-white shadow-lg max-h-[calc(100vh-4rem)] overflow-y-auto scrollbar-thin">
          <div className="px-4 py-4 space-y-1">
            {/* Auth Menu Items */}
            {!user && !loading && (
              <>
                <Link
                  to="/login"
                  className="flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium text-neutral-700 hover:bg-neutral-50 transition-colors"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <User className="w-5 h-5" />
                  <span>Login</span>
                </Link>
                <Link
                  to="/signup"
                  className="flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 transition-all shadow-sm"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <CheckCircle className="w-5 h-5" />
                  <span>Sign Up</span>
                </Link>
                <hr className="my-3 border-neutral-200" />
              </>
            )}
            
            {/* Navigation Groups */}
            {filteredGroups.map((group) => (
              <div key={group.name} className="space-y-1">
                <div className="px-4 py-2 text-xs font-semibold text-neutral-500 uppercase tracking-wider">
                  {group.name}
                </div>
                {group.items.map((item) => {
                  const isActive = location.pathname === item.href
                  return (
                    <Link
                      key={item.href}
                      to={item.href}
                      className={cn(
                        'flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-all',
                        isActive
                          ? 'bg-blue-50 text-blue-600'
                          : 'text-neutral-700 hover:bg-neutral-50'
                      )}
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      <item.icon className="w-5 h-5" />
                      <span>{item.name}</span>
                    </Link>
                  )
                })}
              </div>
            ))}
            
            {/* User Menu Items (Mobile) */}
            {user && (
              <>
                <hr className="my-3 border-neutral-200" />
                <div className="px-4 py-3 bg-neutral-50 rounded-lg">
                  <p className="text-sm font-medium text-neutral-900">{user.full_name}</p>
                  <p className="text-xs text-neutral-500 mt-1">{user.email}</p>
                  <p className="text-xs text-blue-600 capitalize mt-1 font-medium">{user.role}</p>
                </div>
                <button
                  onClick={() => {
                    setIsMobileMenuOpen(false)
                    navigate('/profile')
                  }}
                  className="w-full text-left flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium text-neutral-700 hover:bg-neutral-50 transition-colors"
                >
                  <User className="w-5 h-5" />
                  <span>Profile</span>
                </button>
                <button
                  onClick={() => {
                    setIsMobileMenuOpen(false)
                    handleLogout()
                  }}
                  className="w-full text-left flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="w-5 h-5" />
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
