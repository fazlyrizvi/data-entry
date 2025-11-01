import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
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
<<<<<<< HEAD
  X,
  Brain,
  Zap,
  Globe
=======
  X
>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de
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
<<<<<<< HEAD
    name: 'AI Analysis',
    href: '/ai-analysis',
    icon: Brain,
    roles: ['admin', 'manager', 'analyst']
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
    roles: ['admin', 'manager', 'analyst']
  },
  {
=======
>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de
    name: 'Access Control',
    href: '/access',
    icon: Users,
    roles: ['admin']
  }
]

export const Navigation: React.FC = () => {
  const { user } = useAuth()
  const location = useLocation()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

<<<<<<< HEAD
  // Show all navigation items for public access
  const filteredNavItems = navigationItems
=======
  const filteredNavItems = navigationItems.filter(item => 
    user && item.roles.includes(user.role)
  )
>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de

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
            {/* Notifications */}
            <button className="relative p-2 text-neutral-500 hover:text-neutral-700 transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-semantic-error rounded-full"></span>
            </button>

            {/* User info */}
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-neutral-200 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-neutral-600" />
              </div>
              <div className="hidden sm:block text-sm">
                <div className="font-medium text-neutral-900">{user?.full_name}</div>
                <div className="text-neutral-500 capitalize">{user?.role}</div>
              </div>
            </div>

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
          </div>
        </div>
      )}
    </nav>
  )
}