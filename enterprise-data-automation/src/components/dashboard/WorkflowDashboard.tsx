import React, { useState, useEffect } from 'react'
import { 
  Activity, 
  FileText, 
  CheckCircle, 
  Clock, 
  Users, 
  TrendingUp,
  AlertTriangle,
  Zap
} from 'lucide-react'
import { GlassCard, MetricCard, StatusCard } from '../ui/GlassCard'
import { ProcessingChart } from '../charts/ProcessingChart'
import { ErrorRateChart } from '../charts/ErrorRateChart'
import { DataService } from '../../lib/supabase'

interface DashboardStats {
  totalJobs: number
  activeJobs: number
  completedToday: number
<<<<<<< HEAD
  completedJobs: number
  failedJobs: number
  systemUptime: number
  errorRate: number
  averageProcessingTime: number
=======
  averageProcessingTime: number
  errorRate: number
  systemUptime: number
>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de
  queueLength: number
  throughput: number
}

export const WorkflowDashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
<<<<<<< HEAD
    totalJobs: 0,
    activeJobs: 0,
    completedToday: 0,
    completedJobs: 0,
    failedJobs: 0,
    systemUptime: 0,
    errorRate: 0,
    averageProcessingTime: 0,
    queueLength: 0,
    throughput: 0
  })
  const [loading, setLoading] = useState(true)

  // Load dashboard data
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true)
        const systemHealth = await DataService.getSystemHealth()
        const today = new Date().toISOString().split('T')[0]
        
        // Calculate completed today from metrics
        const completedToday = systemHealth.completedJobs || 0
        
        setStats({
          totalJobs: systemHealth.totalJobs || 0,
          activeJobs: systemHealth.activeJobs || 0,
          completedToday,
          completedJobs: systemHealth.completedJobs || 0,
          failedJobs: systemHealth.failedJobs || 0,
          systemUptime: typeof systemHealth.systemUptime === 'string' ? 
            parseFloat(systemHealth.systemUptime) || 99.9 : 
            systemHealth.systemUptime || 99.9,
          errorRate: parseFloat(systemHealth.errorRate) || 0,
          averageProcessingTime: 2.4, // Default, can be calculated from actual data
          queueLength: 0, // Default, can be enhanced with queue-specific logic
          throughput: systemHealth.totalJobs > 0 ? 
            ((systemHealth.completedJobs / systemHealth.totalJobs) * 100) : 0
        })
      } catch (error) {
        console.error('Error loading dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    loadDashboardData()
    
    // Refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000)
    return () => clearInterval(interval)
  }, [])
=======
    totalJobs: 12456,
    activeJobs: 127,
    completedToday: 342,
    averageProcessingTime: 2.4,
    errorRate: 0.8,
    systemUptime: 99.9,
    queueLength: 45,
    throughput: 94.2
  })
>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de

  // Handler functions for action buttons
  const handleExportReport = () => {
    // TODO: Implement report export functionality
    console.log('Exporting dashboard report...')
    alert('Report export functionality will be implemented with real backend integration')
  }

  const handleNewWorkflow = () => {
    // TODO: Implement new workflow creation
    console.log('Creating new workflow...')
    alert('New workflow creation will be implemented with real backend integration')
  }

  const [recentJobs, setRecentJobs] = useState([
    {
      id: '1',
      file_name: 'Q4_Invoice_Batch_001.pdf',
      status: 'processing',
      progress: 67,
      user: 'Sarah Johnson',
      timestamp: '2 minutes ago'
    },
    {
      id: '2',
      file_name: 'Employee_Records_2024.csv',
      status: 'completed',
      progress: 100,
      user: 'Mike Chen',
      timestamp: '5 minutes ago'
    },
    {
      id: '3',
      file_name: 'Customer_Data_Export.xlsx',
      status: 'failed',
      progress: 0,
      user: 'Lisa Park',
      timestamp: '12 minutes ago'
    },
    {
      id: '4',
      file_name: 'Product_Catalog_Images.zip',
      status: 'queued',
      progress: 0,
      user: 'David Wilson',
      timestamp: '15 minutes ago'
    }
  ])

  // Load dashboard metrics from backend
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        // Try to load real data, fallback to mock data if backend not ready
        const metrics = await DataService.getDashboardMetrics()
        const systemHealth = await DataService.getSystemHealth()
        
        if (metrics && systemHealth) {
          // Transform backend data to component format
          setStats({
<<<<<<< HEAD
            totalJobs: systemHealth.totalJobs || 0,
            activeJobs: systemHealth.activeJobs || 0,
            completedToday: systemHealth.completedJobs || 0,
            completedJobs: systemHealth.completedJobs || 0,
            failedJobs: systemHealth.failedJobs || 0,
            averageProcessingTime: 2.4, // Not available in current backend schema
            errorRate: typeof systemHealth.errorRate === 'string' ? 
              parseFloat(systemHealth.errorRate) || 0 : 
              systemHealth.errorRate || 0,
            systemUptime: typeof systemHealth.systemUptime === 'string' ? 
              parseFloat(systemHealth.systemUptime) || 99.9 : 
              systemHealth.systemUptime || 99.9,
            queueLength: 0, // Not available in current backend schema
            throughput: systemHealth.totalJobs > 0 ? 
              ((systemHealth.completedJobs / systemHealth.totalJobs) * 100) : 0
=======
            totalJobs: systemHealth.totalJobs || 12456,
            activeJobs: systemHealth.activeJobs || 127,
            completedToday: systemHealth.completedJobs || 342,
            averageProcessingTime: 2.4, // Not available in current backend schema
            errorRate: parseFloat(systemHealth.errorRate) || 0.8,
            systemUptime: systemHealth.systemUptime || 99.9,
            queueLength: 45, // Not available in current backend schema
            throughput: 94.2 // Not available in current backend schema
>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de
          })
        }
      } catch (error) {
        console.log('Backend not ready, using mock data:', error)
        // Keep mock data for now
      }
    }

    loadDashboardData()

    // Real-time updates simulation
    const interval = setInterval(() => {
      setStats(prev => ({
        ...prev,
        activeJobs: Math.floor(Math.random() * 20) + 120,
        completedToday: prev.completedToday + Math.floor(Math.random() * 3),
        queueLength: Math.floor(Math.random() * 20) + 40
      }))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Workflow Orchestration</h1>
          <p className="text-neutral-600 mt-1">Monitor and control your data processing workflows</p>
        </div>
        <div className="flex space-x-3">
          <button 
            onClick={handleExportReport}
            className="px-4 py-2 bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg text-sm font-medium text-neutral-700 hover:bg-glass-lightHover transition-colors hover:shadow-md"
          >
            Export Report
          </button>
          <button 
            onClick={handleNewWorkflow}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors hover:shadow-md"
          >
            New Workflow
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Jobs"
          value={stats.totalJobs.toLocaleString()}
          change={{ value: 12.5, type: 'increase' }}
          icon={FileText}
        />
        <MetricCard
          title="Active Jobs"
          value={stats.activeJobs}
          icon={Activity}
        />
        <MetricCard
          title="Completed Today"
          value={stats.completedToday}
          change={{ value: 8.2, type: 'increase' }}
          icon={CheckCircle}
        />
        <MetricCard
          title="Avg Processing Time"
          value={`${stats.averageProcessingTime}s`}
          change={{ value: 15.3, type: 'decrease' }}
          icon={Zap}
        />
      </div>

      {/* System Health and Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Health */}
        <div className="lg:col-span-1 space-y-4">
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">System Health</h3>
          <StatusCard
            title="System Status"
            description="All systems operational"
            status="success"
            icon={CheckCircle}
          />
          <StatusCard
            title="Queue Status"
            description={`${stats.queueLength} jobs in queue`}
            status={stats.queueLength > 100 ? 'warning' : 'info'}
            progress={Math.min((stats.queueLength / 200) * 100, 100)}
            icon={Clock}
          />
          <StatusCard
            title="Error Rate"
            description={`${stats.errorRate}% in last 24h`}
            status={stats.errorRate > 2 ? 'error' : 'success'}
            icon={AlertTriangle}
          />
        </div>

        {/* Processing Chart */}
        <div className="lg:col-span-2">
          <ProcessingChart />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Jobs */}
        <GlassCard>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-neutral-900">Recent Jobs</h3>
            <button className="text-sm text-primary-500 hover:text-primary-600">View All</button>
          </div>
          <div className="space-y-4">
            {recentJobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between p-3 rounded-lg bg-neutral-50/50">
                <div className="flex-1">
                  <p className="font-medium text-neutral-900 text-sm">{job.file_name}</p>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="text-xs text-neutral-500">{job.user}</span>
                    <span className="text-xs text-neutral-400">•</span>
                    <span className="text-xs text-neutral-500">{job.timestamp}</span>
                  </div>
                  {job.status === 'processing' && job.progress > 0 && (
                    <div className="mt-2">
                      <div className="w-full bg-neutral-200 rounded-full h-1.5">
                        <div 
                          className="bg-primary-500 h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`
                    px-2 py-1 text-xs rounded-full
                    ${job.status === 'completed' ? 'bg-semantic-success/10 text-semantic-success' : ''}
                    ${job.status === 'processing' ? 'bg-semantic-info/10 text-semantic-info' : ''}
                    ${job.status === 'failed' ? 'bg-semantic-error/10 text-semantic-error' : ''}
                    ${job.status === 'queued' ? 'bg-neutral-500/10 text-neutral-500' : ''}
                  `}>
                    {job.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Performance Chart */}
        <GlassCard>
          <ErrorRateChart />
        </GlassCard>
      </div>
    </div>
  )
}