import React, { useState } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  BarChart3, 
  PieChart, 
  Download, 
  Calendar,
  Filter,
  Target,
  Clock,
  CheckCircle,
  AlertTriangle,
  XCircle
} from 'lucide-react'
import { GlassCard, MetricCard } from '../ui/GlassCard'
import { PerformanceChart } from '../charts/PerformanceChart'
import { ComplianceChart } from '../charts/ComplianceChart'

export const AnalyticsDashboard: React.FC = () => {
  const [dateRange, setDateRange] = useState('7d')
  const [selectedMetric, setSelectedMetric] = useState('throughput')

  // Analytics data
  const kpiMetrics = {
    totalProcessed: {
      value: '127,453',
      change: 12.5,
      trend: 'up'
    },
    avgProcessingTime: {
      value: '2.4s',
      change: -15.3,
      trend: 'down'
    },
    accuracyRate: {
      value: '94.2%',
      change: 2.1,
      trend: 'up'
    },
    costPerDocument: {
      value: '$0.12',
      change: -8.7,
      trend: 'down'
    }
  }

  const performanceData = {
    dailyStats: [
      { date: '2025-10-25', processed: 12450, errors: 89, avgTime: 2.3 },
      { date: '2025-10-26', processed: 13200, errors: 76, avgTime: 2.1 },
      { date: '2025-10-27', processed: 11890, errors: 92, avgTime: 2.5 },
      { date: '2025-10-28', processed: 14120, errors: 68, avgTime: 2.0 },
      { date: '2025-10-29', processed: 15670, errors: 54, avgTime: 1.9 },
      { date: '2025-10-30', processed: 14930, errors: 61, avgTime: 2.2 },
      { date: '2025-10-31', processed: 16200, errors: 45, avgTime: 1.8 }
    ],
    topErrors: [
      { type: 'OCR Timeout', count: 234, percentage: 32.1 },
      { type: 'Invalid Format', count: 156, percentage: 21.4 },
      { type: 'Data Validation', count: 128, percentage: 17.6 },
      { type: 'Network Error', count: 89, percentage: 12.2 },
      { type: 'Permission Denied', count: 67, percentage: 9.2 },
      { type: 'Other', count: 53, percentage: 7.3 }
    ],
    departmentPerformance: [
      { department: 'Finance', documents: 12450, accuracy: 96.2, avgTime: 2.1 },
      { department: 'HR', documents: 8930, accuracy: 94.8, avgTime: 2.6 },
      { department: 'Operations', documents: 15670, accuracy: 92.1, avgTime: 2.8 },
      { department: 'Sales', documents: 11200, accuracy: 95.7, avgTime: 2.3 },
      { department: 'Marketing', documents: 6780, accuracy: 97.1, avgTime: 1.9 }
    ]
  }

  const complianceMetrics = {
    gdpr: { score: 98.5, status: 'compliant' },
    sox: { score: 94.2, status: 'compliant' },
    hipaa: { score: 89.1, status: 'partial' },
    pci: { score: 97.3, status: 'compliant' }
  }

  const getComplianceStatus = (score: number) => {
    if (score >= 95) return { icon: CheckCircle, color: 'text-semantic-success', bg: 'bg-semantic-success/10' }
    if (score >= 85) return { icon: AlertTriangle, color: 'text-semantic-warning', bg: 'bg-semantic-warning/10' }
    return { icon: XCircle, color: 'text-semantic-error', bg: 'bg-semantic-error/10' }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Analytics & Reporting</h1>
          <p className="text-neutral-600 mt-1">Performance insights and compliance monitoring</p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="px-4 py-2 bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
          <button className="px-4 py-2 bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg text-sm font-medium text-neutral-700 hover:bg-glass-lightHover transition-colors flex items-center space-x-2">
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* KPI Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Processed"
          value={kpiMetrics.totalProcessed.value}
          change={{ 
            value: Math.abs(kpiMetrics.totalProcessed.change), 
            type: kpiMetrics.totalProcessed.trend as 'increase' | 'decrease'
          }}
          icon={BarChart3}
        />
        <MetricCard
          title="Avg Processing Time"
          value={kpiMetrics.avgProcessingTime.value}
          change={{ 
            value: Math.abs(kpiMetrics.avgProcessingTime.change), 
            type: kpiMetrics.avgProcessingTime.trend as 'increase' | 'decrease'
          }}
          icon={Clock}
        />
        <MetricCard
          title="Accuracy Rate"
          value={kpiMetrics.accuracyRate.value}
          change={{ 
            value: Math.abs(kpiMetrics.accuracyRate.change), 
            type: kpiMetrics.accuracyRate.trend as 'increase' | 'decrease'
          }}
          icon={Target}
        />
        <MetricCard
          title="Cost per Document"
          value={kpiMetrics.costPerDocument.value}
          change={{ 
            value: Math.abs(kpiMetrics.costPerDocument.change), 
            type: kpiMetrics.costPerDocument.trend as 'increase' | 'decrease'
          }}
          icon={TrendingDown}
        />
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard>
          <PerformanceChart />
        </GlassCard>
        <GlassCard>
          <ComplianceChart />
        </GlassCard>
      </div>

      {/* Error Analysis and Department Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Errors */}
        <GlassCard>
          <h3 className="text-lg font-semibold text-neutral-900 mb-6">Error Analysis</h3>
          <div className="space-y-4">
            {performanceData.topErrors.map((error, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-semantic-error/10 rounded-lg flex items-center justify-center">
                    <XCircle className="w-4 h-4 text-semantic-error" />
                  </div>
                  <div>
                    <p className="font-medium text-neutral-900">{error.type}</p>
                    <p className="text-sm text-neutral-500">{error.count} occurrences</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-neutral-900">{error.percentage}%</p>
                  <div className="w-20 bg-neutral-200 rounded-full h-2 mt-1">
                    <div 
                      className="bg-semantic-error h-2 rounded-full"
                      style={{ width: `${error.percentage}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Department Performance */}
        <GlassCard>
          <h3 className="text-lg font-semibold text-neutral-900 mb-6">Department Performance</h3>
          <div className="space-y-4">
            {performanceData.departmentPerformance.map((dept, index) => (
              <div key={index} className="p-4 bg-neutral-50/50 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-neutral-900">{dept.department}</h4>
                  <div className="flex space-x-2">
                    <span className="px-2 py-1 text-xs bg-semantic-info/10 text-semantic-info rounded-full">
                      {dept.documents.toLocaleString()} docs
                    </span>
                    <span className="px-2 py-1 text-xs bg-semantic-success/10 text-semantic-success rounded-full">
                      {dept.accuracy}% accurate
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-neutral-500">Documents Processed</p>
                    <p className="font-semibold text-neutral-900">{dept.documents.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-neutral-500">Avg Processing Time</p>
                    <p className="font-semibold text-neutral-900">{dept.avgTime}s</p>
                  </div>
                </div>
                <div className="mt-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-neutral-500">Accuracy</span>
                    <span className="text-xs text-neutral-500">{dept.accuracy}%</span>
                  </div>
                  <div className="w-full bg-neutral-200 rounded-full h-2">
                    <div 
                      className="bg-semantic-success h-2 rounded-full"
                      style={{ width: `${dept.accuracy}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Compliance Dashboard */}
      <GlassCard>
        <h3 className="text-lg font-semibold text-neutral-900 mb-6">Compliance Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Object.entries(complianceMetrics).map(([regulation, metric]) => {
            const { icon: Icon, color, bg } = getComplianceStatus(metric.score)
            return (
              <div key={regulation} className="text-center">
                <div className={`w-16 h-16 ${bg} rounded-full flex items-center justify-center mx-auto mb-3`}>
                  <Icon className={`w-8 h-8 ${color}`} />
                </div>
                <h4 className="font-semibold text-neutral-900 mb-1">{regulation.toUpperCase()}</h4>
                <p className={`text-2xl font-bold ${color} mb-2`}>{metric.score}%</p>
                <p className={`text-sm capitalize ${metric.score >= 95 ? 'text-semantic-success' : metric.score >= 85 ? 'text-semantic-warning' : 'text-semantic-error'}`}>
                  {metric.status}
                </p>
              </div>
            )
          })}
        </div>
      </GlassCard>

      {/* Detailed Metrics Table */}
      <GlassCard>
        <h3 className="text-lg font-semibold text-neutral-900 mb-6">Performance Trends</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-200">
                <th className="text-left py-3 px-4 font-semibold text-neutral-900">Date</th>
                <th className="text-right py-3 px-4 font-semibold text-neutral-900">Documents</th>
                <th className="text-right py-3 px-4 font-semibold text-neutral-900">Errors</th>
                <th className="text-right py-3 px-4 font-semibold text-neutral-900">Error Rate</th>
                <th className="text-right py-3 px-4 font-semibold text-neutral-900">Avg Time</th>
                <th className="text-right py-3 px-4 font-semibold text-neutral-900">Throughput</th>
              </tr>
            </thead>
            <tbody>
              {performanceData.dailyStats.map((day, index) => (
                <tr key={index} className="border-b border-neutral-100 hover:bg-neutral-50/30">
                  <td className="py-3 px-4 text-neutral-900">
                    {new Date(day.date).toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric' 
                    })}
                  </td>
                  <td className="py-3 px-4 text-right font-medium text-neutral-900">
                    {day.processed.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right text-semantic-error">
                    {day.errors}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      (day.errors / day.processed) > 0.01 
                        ? 'bg-semantic-error/10 text-semantic-error' 
                        : 'bg-semantic-success/10 text-semantic-success'
                    }`}>
                      {((day.errors / day.processed) * 100).toFixed(2)}%
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right text-neutral-700">
                    {day.avgTime}s
                  </td>
                  <td className="py-3 px-4 text-right text-neutral-700">
                    {(day.processed / 24).toFixed(0)}/hr
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  )
}