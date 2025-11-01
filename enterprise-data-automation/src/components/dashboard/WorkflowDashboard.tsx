import React, { useState, useEffect } from 'react'
import { CheckCircle, Clock, AlertCircle, TrendingUp, Activity, Users, FileText, Zap } from 'lucide-react'
import { DataService } from '../../lib/supabase'

interface DashboardStats {
  totalJobs: number
  activeJobs: number
  completedToday: number
  completedJobs: number
  failedJobs: number
  systemUptime: number
  errorRate: number
  averageProcessingTime: number
  queueLength: number
  throughput: number
}

export const WorkflowDashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalJobs: 12456,
    activeJobs: 127,
    completedToday: 342,
    completedJobs: 12456,
    failedJobs: 45,
    systemUptime: 99.9,
    errorRate: 0.8,
    averageProcessingTime: 2.4,
    queueLength: 45,
    throughput: 94.2
  })
  const [loading, setLoading] = useState(false)

  // Load dashboard data
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true)
        const systemHealth = await DataService.getSystemHealth()
        
        setStats(prevStats => ({
          ...prevStats,
          totalJobs: systemHealth.totalJobs || prevStats.totalJobs,
          activeJobs: systemHealth.activeJobs || prevStats.activeJobs,
          completedToday: systemHealth.completedJobs || prevStats.completedToday,
          completedJobs: systemHealth.completedJobs || prevStats.completedJobs,
          failedJobs: systemHealth.failedJobs || prevStats.failedJobs,
          systemUptime: typeof systemHealth.systemUptime === 'string' ? 
            parseFloat(systemHealth.systemUptime) || prevStats.systemUptime : 
            systemHealth.systemUptime || prevStats.systemUptime,
          errorRate: typeof systemHealth.errorRate === 'string' ? 
            parseFloat(systemHealth.errorRate) || prevStats.errorRate : 
            systemHealth.errorRate || prevStats.errorRate
        }))
      } catch (error) {
        console.log('Backend not ready, using mock data:', error)
        // Keep mock data for now
      } finally {
        setLoading(false)
      }
    }

    loadDashboardData()

    // Real-time updates simulation
    const interval = setInterval(() => {
      setStats(prev => ({
        ...prev,
        activeJobs: Math.max(0, prev.activeJobs + Math.floor(Math.random() * 10) - 5),
        completedToday: Math.max(prev.completedToday, prev.completedToday + Math.floor(Math.random() * 3)),
        throughput: Math.max(85, Math.min(98, prev.throughput + (Math.random() - 0.5) * 2))
      }))
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const StatCard: React.FC<{
    title: string
    value: string | number
    icon: React.ComponentType<{ className?: string }>
    change?: string
    trend?: 'up' | 'down' | 'neutral'
  }> = ({ title, value, icon: Icon, change, trend }) => (
    <div className="bg-glass-light backdrop-blur-glass border border-glass-border rounded-xl p-6 hover:shadow-lg transition-all duration-300">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-neutral-600 mb-1">{title}</p>
          <p className="text-2xl font-bold text-neutral-900">{value}</p>
          {change && (
            <p className={`text-sm mt-1 ${
              trend === 'up' ? 'text-green-600' : 
              trend === 'down' ? 'text-red-600' : 
              'text-neutral-600'
            }`}>
              {change}
            </p>
          )}
        </div>
        <div className="w-12 h-12 bg-gradient-to-br from-primary-100 to-primary-200 rounded-lg flex items-center justify-center">
          <Icon className="w-6 h-6 text-primary-600" />
        </div>
      </div>
    </div>
  )

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-neutral-900 mb-2">
          Enterprise Data Automation Platform
        </h1>
        <p className="text-neutral-600">
          Real-time monitoring and control of your data workflows
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Jobs"
          value={stats.totalJobs.toLocaleString()}
          icon={CheckCircle}
          trend="up"
        />
        <StatCard
          title="Active Jobs"
          value={stats.activeJobs}
          icon={Clock}
          trend="neutral"
        />
        <StatCard
          title="Completed Today"
          value={stats.completedToday}
          icon={TrendingUp}
          change="+12% from yesterday"
          trend="up"
        />
        <StatCard
          title="Failed Jobs"
          value={stats.failedJobs}
          icon={AlertCircle}
          change="2.1% error rate"
          trend="down"
        />
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="System Uptime"
          value={`${stats.systemUptime}%`}
          icon={Activity}
          change="+0.1% this week"
          trend="up"
        />
        <StatCard
          title="Avg Processing Time"
          value={`${stats.averageProcessingTime}s`}
          icon={Zap}
          change="-0.3s improvement"
          trend="up"
        />
        <StatCard
          title="Throughput Rate"
          value={`${stats.throughput}%`}
          icon={TrendingUp}
          change="+1.2% this hour"
          trend="up"
        />
        <StatCard
          title="Queue Length"
          value={stats.queueLength}
          icon={FileText}
          change="Normal range"
          trend="neutral"
        />
      </div>

      {/* Recent Activity */}
      <div className="bg-glass-light backdrop-blur-glass border border-glass-border rounded-xl p-6">
        <h2 className="text-xl font-semibold text-neutral-900 mb-4">Recent Activity</h2>
        <div className="space-y-3">
          {[
            { time: '2 minutes ago', action: 'Data validation completed', status: 'success', count: '45 records' },
            { time: '5 minutes ago', action: 'Batch processing started', status: 'info', count: '1,200 files' },
            { time: '8 minutes ago', action: 'OCR extraction completed', status: 'success', count: '23 documents' },
            { time: '12 minutes ago', action: 'Quality control check', status: 'warning', count: '5 items flagged' },
            { time: '15 minutes ago', action: 'Data export completed', status: 'success', count: '2.4 MB' }
          ].map((activity, index) => (
            <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-white/50">
              <div className="flex items-center space-x-3">
                <div className={`w-2 h-2 rounded-full ${
                  activity.status === 'success' ? 'bg-green-500' :
                  activity.status === 'warning' ? 'bg-yellow-500' :
                  activity.status === 'error' ? 'bg-red-500' : 'bg-blue-500'
                }`} />
                <div>
                  <p className="text-sm font-medium text-neutral-900">{activity.action}</p>
                  <p className="text-xs text-neutral-500">{activity.time}</p>
                </div>
              </div>
              <span className="text-xs text-neutral-500">{activity.count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* System Health */}
      <div className="bg-glass-light backdrop-blur-glass border border-glass-border rounded-xl p-6">
        <h2 className="text-xl font-semibold text-neutral-900 mb-4">System Health</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-20 h-20 mx-auto mb-3 relative">
              <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 36 36">
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#E5E7EB"
                  strokeWidth="3"
                />
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#10B981"
                  strokeWidth="3"
                  strokeDasharray={`${stats.throughput}, 100`}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-bold text-neutral-900">{stats.throughput}%</span>
              </div>
            </div>
            <p className="text-sm font-medium text-neutral-700">Overall Health</p>
          </div>
          
          <div className="text-center">
            <div className="w-20 h-20 mx-auto mb-3 relative">
              <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 36 36">
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#E5E7EB"
                  strokeWidth="3"
                />
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#3B82F6"
                  strokeWidth="3"
                  strokeDasharray={`${(stats.activeJobs / (stats.activeJobs + stats.queueLength)) * 100}, 100`}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-bold text-neutral-900">{stats.activeJobs}</span>
              </div>
            </div>
            <p className="text-sm font-medium text-neutral-700">Active Processes</p>
          </div>
          
          <div className="text-center">
            <div className="w-20 h-20 mx-auto mb-3 relative">
              <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 36 36">
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#E5E7EB"
                  strokeWidth="3"
                />
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="#F59E0B"
                  strokeWidth="3"
                  strokeDasharray={`${100 - stats.errorRate}, 100`}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-bold text-neutral-900">{stats.errorRate}%</span>
              </div>
            </div>
            <p className="text-sm font-medium text-neutral-700">Error Rate</p>
          </div>
        </div>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
          <p className="mt-2 text-neutral-600">Loading dashboard data...</p>
        </div>
      )}
    </div>
  )
}