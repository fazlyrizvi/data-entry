import React, { useState } from 'react'
import { 
  Users, 
  Shield, 
  UserPlus, 
  Edit, 
  Trash2, 
  Search, 
  Filter,
  CheckCircle,
  XCircle,
  AlertCircle,
  MoreVertical,
  Eye,
  Settings
} from 'lucide-react'
import { GlassCard } from '../ui/GlassCard'

interface User {
  id: string
  name: string
  email: string
  role: 'admin' | 'manager' | 'operator' | 'viewer'
  status: 'active' | 'inactive' | 'pending'
  lastActive: string
  avatar?: string
}

interface Permission {
  id: string
  feature: string
  view: 'allow' | 'deny' | 'inherit'
  edit: 'allow' | 'deny' | 'inherit'
  delete: 'allow' | 'deny' | 'inherit'
  admin: 'allow' | 'deny' | 'inherit'
}

export const AccessControlInterface: React.FC = () => {
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('all')
  const [activeTab, setActiveTab] = useState<'users' | 'permissions' | 'audit'>('users')

  const mockUsers: User[] = [
    {
      id: '1',
      name: 'John Admin',
      email: 'john.admin@company.com',
      role: 'admin',
      status: 'active',
      lastActive: '2 minutes ago'
    },
    {
      id: '2',
      name: 'Sarah Manager',
      email: 'sarah.manager@company.com',
      role: 'manager',
      status: 'active',
      lastActive: '15 minutes ago'
    },
    {
      id: '3',
      name: 'Mike Operator',
      email: 'mike.operator@company.com',
      role: 'operator',
      status: 'active',
      lastActive: '1 hour ago'
    },
    {
      id: '4',
      name: 'Lisa Viewer',
      email: 'lisa.viewer@company.com',
      role: 'viewer',
      status: 'pending',
      lastActive: '3 days ago'
    },
    {
      id: '5',
      name: 'David Wilson',
      email: 'david.wilson@company.com',
      role: 'operator',
      status: 'inactive',
      lastActive: '2 weeks ago'
    }
  ]

  const permissionMatrix: Permission[] = [
    {
      id: '1',
      feature: 'Workflow Management',
      view: 'allow',
      edit: 'allow',
      delete: 'allow',
      admin: 'allow'
    },
    {
      id: '2',
      feature: 'File Processing',
      view: 'allow',
      edit: 'allow',
      delete: 'deny',
      admin: 'inherit'
    },
    {
      id: '3',
      feature: 'Data Validation',
      view: 'allow',
      edit: 'allow',
      delete: 'deny',
      admin: 'inherit'
    },
    {
      id: '4',
      feature: 'Analytics & Reporting',
      view: 'allow',
      edit: 'deny',
      delete: 'deny',
      admin: 'inherit'
    },
    {
      id: '5',
      feature: 'AI Commands',
      view: 'allow',
      edit: 'deny',
      delete: 'deny',
      admin: 'inherit'
    },
    {
      id: '6',
      feature: 'Access Control',
      view: 'deny',
      edit: 'deny',
      delete: 'deny',
      admin: 'deny'
    },
    {
      id: '7',
      feature: 'System Settings',
      view: 'deny',
      edit: 'deny',
      delete: 'deny',
      admin: 'deny'
    }
  ]

  const auditLogs = [
    {
      id: '1',
      user: 'John Admin',
      action: 'Created new user account',
      resource: 'User Management',
      timestamp: '2025-10-31T16:45:00Z',
      details: 'Added Sarah Manager to the system'
    },
    {
      id: '2',
      user: 'Sarah Manager',
      action: 'Modified workflow settings',
      resource: 'Workflow Management',
      timestamp: '2025-10-31T15:30:00Z',
      details: 'Updated processing timeout from 30s to 45s'
    },
    {
      id: '3',
      user: 'Mike Operator',
      action: 'Processed document batch',
      resource: 'File Processing',
      timestamp: '2025-10-31T14:20:00Z',
      details: 'Processed 150 invoices with 94% accuracy'
    },
    {
      id: '4',
      user: 'System',
      action: 'Permission denied',
      resource: 'Access Control',
      timestamp: '2025-10-31T13:15:00Z',
      details: 'Lisa Viewer attempted to access admin settings'
    },
    {
      id: '5',
      user: 'David Wilson',
      action: 'Downloaded analytics report',
      resource: 'Analytics',
      timestamp: '2025-10-31T12:00:00Z',
      details: 'Exported weekly performance report'
    }
  ]

  const filteredUsers = mockUsers.filter(user => {
    const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRole = roleFilter === 'all' || user.role === roleFilter
    return matchesSearch && matchesRole
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-semantic-success/10 text-semantic-success'
      case 'pending': return 'bg-semantic-warning/10 text-semantic-warning'
      case 'inactive': return 'bg-neutral-500/10 text-neutral-500'
      default: return 'bg-neutral-100 text-neutral-600'
    }
  }

  const getPermissionIcon = (permission: string) => {
    switch (permission) {
      case 'allow': return CheckCircle
      case 'deny': return XCircle
      case 'inherit': return AlertCircle
      default: return AlertCircle
    }
  }

  const getPermissionColor = (permission: string) => {
    switch (permission) {
      case 'allow': return 'text-semantic-success'
      case 'deny': return 'text-semantic-error'
      case 'inherit': return 'text-semantic-warning'
      default: return 'text-neutral-500'
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Access Control</h1>
          <p className="text-neutral-600 mt-1">Manage user permissions and security settings</p>
        </div>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg text-sm font-medium text-neutral-700 hover:bg-glass-lightHover transition-colors">
            Export Audit Log
          </button>
          <button className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors flex items-center space-x-2">
            <UserPlus className="w-4 h-4" />
            <span>Add User</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-neutral-100 rounded-lg p-1">
        {[
          { id: 'users', label: 'User Management', icon: Users },
          { id: 'permissions', label: 'Permission Matrix', icon: Shield },
          { id: 'audit', label: 'Audit Trail', icon: Eye }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-neutral-600 hover:text-neutral-900'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'users' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* User List */}
          <div className="lg:col-span-1">
            <GlassCard>
              <div className="space-y-4">
                {/* Search and Filters */}
                <div className="space-y-3">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400 w-4 h-4" />
                    <input
                      type="text"
                      placeholder="Search users..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                    />
                  </div>
                  <select
                    value={roleFilter}
                    onChange={(e) => setRoleFilter(e.target.value)}
                    className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                  >
                    <option value="all">All Roles</option>
                    <option value="admin">Admin</option>
                    <option value="manager">Manager</option>
                    <option value="operator">Operator</option>
                    <option value="viewer">Viewer</option>
                  </select>
                </div>

                {/* Users */}
                <div className="space-y-2">
                  {filteredUsers.map((user) => (
                    <div
                      key={user.id}
                      onClick={() => setSelectedUser(user)}
                      className={`p-3 rounded-lg cursor-pointer transition-colors ${
                        selectedUser?.id === user.id
                          ? 'bg-primary-50 border border-primary-200'
                          : 'bg-neutral-50/50 hover:bg-neutral-100/50'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-neutral-200 rounded-full flex items-center justify-center">
                          <Users className="w-5 h-5 text-neutral-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-neutral-900 truncate">{user.name}</p>
                          <p className="text-sm text-neutral-500 truncate">{user.email}</p>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className="text-xs bg-neutral-100 text-neutral-600 px-2 py-1 rounded-full capitalize">
                              {user.role}
                            </span>
                            <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(user.status)}`}>
                              {user.status}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </GlassCard>
          </div>

          {/* User Details */}
          <div className="lg:col-span-2">
            {selectedUser ? (
              <GlassCard>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-neutral-900">User Details</h3>
                  <div className="flex space-x-2">
                    <button className="p-2 text-neutral-400 hover:bg-neutral-100 rounded-lg">
                      <Edit className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-neutral-400 hover:bg-neutral-100 rounded-lg">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium text-neutral-700">Full Name</label>
                      <p className="mt-1 text-neutral-900">{selectedUser.name}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-neutral-700">Email</label>
                      <p className="mt-1 text-neutral-900">{selectedUser.email}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-neutral-700">Role</label>
                      <p className="mt-1">
                        <span className="px-3 py-1 bg-neutral-100 text-neutral-700 rounded-full text-sm capitalize">
                          {selectedUser.role}
                        </span>
                      </p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium text-neutral-700">Status</label>
                      <p className="mt-1">
                        <span className={`px-3 py-1 rounded-full text-sm ${getStatusColor(selectedUser.status)}`}>
                          {selectedUser.status}
                        </span>
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-neutral-700">Last Active</label>
                      <p className="mt-1 text-neutral-900">{selectedUser.lastActive}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-neutral-700">Member Since</label>
                      <p className="mt-1 text-neutral-900">January 2024</p>
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-6 border-t border-neutral-200">
                  <h4 className="font-medium text-neutral-900 mb-4">Quick Actions</h4>
                  <div className="flex space-x-3">
                    <button className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600 transition-colors">
                      Edit Permissions
                    </button>
                    <button className="px-4 py-2 bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg text-sm text-neutral-700 hover:bg-glass-lightHover transition-colors">
                      Send Reset Link
                    </button>
                    <button className="px-4 py-2 bg-semantic-error/10 text-semantic-error rounded-lg text-sm hover:bg-semantic-error/20 transition-colors">
                      Deactivate
                    </button>
                  </div>
                </div>
              </GlassCard>
            ) : (
              <GlassCard>
                <div className="text-center py-12">
                  <Users className="w-16 h-16 text-neutral-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                    Select a User
                  </h3>
                  <p className="text-neutral-600">
                    Choose a user from the list to view and manage their details
                  </p>
                </div>
              </GlassCard>
            )}
          </div>
        </div>
      )}

      {activeTab === 'permissions' && (
        <GlassCard>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-neutral-900">Permission Matrix</h3>
            <div className="flex space-x-2">
              <select className="px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-sm">
                <option>All Roles</option>
                <option>Admin</option>
                <option>Manager</option>
                <option>Operator</option>
                <option>Viewer</option>
              </select>
              <button className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600 transition-colors">
                Save Changes
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-200">
                  <th className="text-left py-3 px-4 font-semibold text-neutral-900">Feature</th>
                  <th className="text-center py-3 px-4 font-semibold text-neutral-900">View</th>
                  <th className="text-center py-3 px-4 font-semibold text-neutral-900">Edit</th>
                  <th className="text-center py-3 px-4 font-semibold text-neutral-900">Delete</th>
                  <th className="text-center py-3 px-4 font-semibold text-neutral-900">Admin</th>
                </tr>
              </thead>
              <tbody>
                {permissionMatrix.map((permission) => (
                  <tr key={permission.id} className="border-b border-neutral-100 hover:bg-neutral-50/30">
                    <td className="py-4 px-4 font-medium text-neutral-900">{permission.feature}</td>
                    {(['view', 'edit', 'delete', 'admin'] as const).map((action) => {
                      const IconComponent = getPermissionIcon(permission[action])
                      return (
                        <td key={action} className="py-4 px-4 text-center">
                          <button className={`p-2 rounded-full transition-colors ${getPermissionColor(permission[action])}`}>
                            <IconComponent className="w-5 h-5" />
                          </button>
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      )}

      {activeTab === 'audit' && (
        <GlassCard>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-neutral-900">Audit Trail</h3>
            <div className="flex space-x-2">
              <select className="px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-sm">
                <option>Last 24 hours</option>
                <option>Last 7 days</option>
                <option>Last 30 days</option>
                <option>Custom range</option>
              </select>
              <button className="px-4 py-2 bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg text-sm text-neutral-700 hover:bg-glass-lightHover transition-colors">
                Filter
              </button>
            </div>
          </div>

          <div className="space-y-4">
            {auditLogs.map((log) => (
              <div key={log.id} className="p-4 bg-neutral-50/50 rounded-lg">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-medium text-neutral-900">{log.action}</h4>
                      <span className="px-2 py-1 text-xs bg-neutral-100 text-neutral-600 rounded-full">
                        {log.resource}
                      </span>
                    </div>
                    <p className="text-sm text-neutral-600 mb-2">{log.details}</p>
                    <div className="flex items-center space-x-4 text-xs text-neutral-500">
                      <span>By {log.user}</span>
                      <span>•</span>
                      <span>{new Date(log.timestamp).toLocaleString()}</span>
                    </div>
                  </div>
                  <button className="p-2 text-neutral-400 hover:bg-neutral-100 rounded-lg">
                    <Eye className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}
    </div>
  )
}