import React, { useState } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  BarChart3,
  PieChart,
  Target,
  Award,
  Clock,
  FileText,
  Zap,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';

interface QualityMetric {
  id: string;
  name: string;
  value: number;
  target: number;
  trend: 'up' | 'down' | 'stable';
  change: number;
  color: string;
  description: string;
}

interface QualityIssue {
  id: string;
  type: 'accuracy' | 'completeness' | 'consistency' | 'validation';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  affected_files: number;
  detected_at: string;
  status: 'open' | 'investigating' | 'resolved';
  assigned_to?: string;
}

interface ConfidenceScore {
  range: string;
  count: number;
  percentage: number;
  color: string;
}

export const QualityControlDashboard: React.FC = () => {
  const [selectedTimeRange, setSelectedTimeRange] = useState<'24h' | '7d' | '30d' | '90d'>('7d');
  const [selectedMetric, setSelectedMetric] = useState<string>('overall');

  const qualityMetrics: QualityMetric[] = [
    {
      id: 'accuracy',
      name: 'Overall Accuracy',
      value: 94.2,
      target: 95.0,
      trend: 'up',
      change: 2.1,
      color: 'green',
      description: 'Percentage of correctly processed data'
    },
    {
      id: 'completeness',
      name: 'Data Completeness',
      value: 97.8,
      target: 98.0,
      trend: 'stable',
      change: 0.3,
      color: 'blue',
      description: 'Percentage of fields populated correctly'
    },
    {
      id: 'consistency',
      name: 'Format Consistency',
      value: 89.5,
      target: 92.0,
      trend: 'down',
      change: -1.8,
      color: 'orange',
      description: 'Adherence to data format standards'
    },
    {
      id: 'validation',
      name: 'Validation Pass Rate',
      value: 91.3,
      target: 90.0,
      trend: 'up',
      change: 4.2,
      color: 'purple',
      description: 'Percentage of data passing validation rules'
    },
    {
      id: 'processing_time',
      name: 'Avg Processing Time',
      value: 2.4,
      target: 3.0,
      trend: 'up',
      change: -0.6,
      color: 'indigo',
      description: 'Average time to process single document (seconds)'
    },
    {
      id: 'error_rate',
      name: 'Error Rate',
      value: 2.1,
      target: 1.5,
      trend: 'down',
      change: -0.8,
      color: 'red',
      description: 'Percentage of processing errors'
    }
  ];

  const qualityIssues: QualityIssue[] = [
    {
      id: 'issue_1',
      type: 'accuracy',
      severity: 'high',
      description: 'OCR accuracy below threshold for medical forms',
      affected_files: 23,
      detected_at: '2025-11-01T10:30:00Z',
      status: 'investigating',
      assigned_to: 'Sarah Johnson'
    },
    {
      id: 'issue_2',
      type: 'consistency',
      severity: 'medium',
      description: 'Date format inconsistencies in invoice data',
      affected_files: 45,
      detected_at: '2025-11-01T09:15:00Z',
      status: 'open'
    },
    {
      id: 'issue_3',
      type: 'validation',
      severity: 'critical',
      description: 'Invalid phone number formats detected in batch',
      affected_files: 78,
      detected_at: '2025-11-01T08:45:00Z',
      status: 'resolved',
      assigned_to: 'Mike Chen'
    },
    {
      id: 'issue_4',
      type: 'completeness',
      severity: 'medium',
      description: 'Missing required fields in customer database',
      affected_files: 12,
      detected_at: '2025-11-01T07:20:00Z',
      status: 'open'
    }
  ];

  const confidenceScores: ConfidenceScore[] = [
    { range: '90-100%', count: 1247, percentage: 67.2, color: 'green' },
    { range: '80-89%', count: 398, percentage: 21.5, color: 'blue' },
    { range: '70-79%', count: 156, percentage: 8.4, color: 'yellow' },
    { range: '60-69%', count: 45, percentage: 2.4, color: 'orange' },
    { range: '<60%', count: 9, percentage: 0.5, color: 'red' }
  ];

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-500" />;
      default:
        return <div className="w-4 h-4" />;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-neutral-600';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-700 bg-red-50 border-red-200';
      case 'high':
        return 'text-orange-700 bg-orange-50 border-orange-200';
      case 'medium':
        return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'low':
        return 'text-blue-700 bg-blue-50 border-blue-200';
      default:
        return 'text-neutral-700 bg-neutral-50 border-neutral-200';
    }
  };

  const getIssueIcon = (type: string) => {
    switch (type) {
      case 'accuracy':
        return <Target className="w-4 h-4" />;
      case 'completeness':
        return <FileText className="w-4 h-4" />;
      case 'consistency':
        return <Zap className="w-4 h-4" />;
      case 'validation':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <AlertTriangle className="w-4 h-4" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'resolved':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'investigating':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'open':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default:
        return <XCircle className="w-4 h-4 text-neutral-400" />;
    }
  };

  const criticalIssues = qualityIssues.filter(issue => issue.severity === 'critical').length;
  const openIssues = qualityIssues.filter(issue => issue.status === 'open').length;
  const resolvedIssues = qualityIssues.filter(issue => issue.status === 'resolved').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Quality Control Dashboard</h1>
          <p className="text-neutral-600 mt-1">Monitor data quality metrics and detect issues in real-time</p>
        </div>
        
        <div className="flex space-x-3">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value as any)}
            className="px-3 py-2 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
          
          <button className="flex items-center space-x-2 px-4 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors">
            <Filter className="w-4 h-4" />
            <span>Filters</span>
          </button>
          
          <button className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
            <Download className="w-4 h-4" />
            <span>Export Report</span>
          </button>
          
          <button className="flex items-center space-x-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors">
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <Award className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-neutral-500">Overall Score</p>
              <p className="text-2xl font-bold text-green-600">
                {qualityMetrics.find(m => m.id === 'accuracy')?.value}%
              </p>
            </div>
          </div>
        </GlassCard>
        
        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-neutral-500">Critical Issues</p>
              <p className="text-2xl font-bold text-red-600">{criticalIssues}</p>
            </div>
          </div>
        </GlassCard>
        
        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
              <Clock className="w-5 h-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-neutral-500">Open Issues</p>
              <p className="text-2xl font-bold text-yellow-600">{openIssues}</p>
            </div>
          </div>
        </GlassCard>
        
        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-neutral-500">Resolved Today</p>
              <p className="text-2xl font-bold text-blue-600">{resolvedIssues}</p>
            </div>
          </div>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quality Metrics */}
        <GlassCard>
          <div className="flex items-center space-x-2 mb-4">
            <BarChart3 className="w-5 h-5 text-neutral-500" />
            <h3 className="text-lg font-semibold text-neutral-900">Quality Metrics</h3>
          </div>
          
          <div className="space-y-4">
            {qualityMetrics.map((metric) => (
              <div key={metric.id} className="p-4 bg-neutral-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h4 className="font-medium text-neutral-900">{metric.name}</h4>
                    <p className="text-xs text-neutral-600">{metric.description}</p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center space-x-1">
                      <span className="text-lg font-bold text-neutral-900">
                        {metric.value}{metric.id === 'processing_time' ? 's' : '%'}
                      </span>
                      {getTrendIcon(metric.trend)}
                    </div>
                    <p className={`text-xs ${getTrendColor(metric.trend)}`}>
                      {metric.change > 0 ? '+' : ''}{metric.change}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-neutral-600">Target: {metric.target}{metric.id === 'processing_time' ? 's' : '%'}</span>
                  <span className={`font-medium ${
                    metric.value >= metric.target ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {((metric.value / metric.target) * 100).toFixed(1)}% of target
                  </span>
                </div>
                
                <div className="w-full bg-neutral-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${
                      metric.color === 'green' ? 'bg-green-500' :
                      metric.color === 'blue' ? 'bg-blue-500' :
                      metric.color === 'orange' ? 'bg-orange-500' :
                      metric.color === 'purple' ? 'bg-purple-500' :
                      metric.color === 'indigo' ? 'bg-indigo-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${Math.min((metric.value / metric.target) * 100, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Confidence Scores */}
        <GlassCard>
          <div className="flex items-center space-x-2 mb-4">
            <PieChart className="w-5 h-5 text-neutral-500" />
            <h3 className="text-lg font-semibold text-neutral-900">Confidence Score Distribution</h3>
          </div>
          
          <div className="space-y-3">
            {confidenceScores.map((score) => (
              <div key={score.range} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-4 h-4 rounded-full ${
                    score.color === 'green' ? 'bg-green-500' :
                    score.color === 'blue' ? 'bg-blue-500' :
                    score.color === 'yellow' ? 'bg-yellow-500' :
                    score.color === 'orange' ? 'bg-orange-500' :
                    'bg-red-500'
                  }`} />
                  <span className="text-sm font-medium text-neutral-900">{score.range}</span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-neutral-900">{score.count}</p>
                  <p className="text-xs text-neutral-600">{score.percentage}%</p>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-4 pt-4 border-t border-neutral-200">
            <div className="flex items-center justify-between text-sm">
              <span className="text-neutral-600">High Confidence (90%+)</span>
              <span className="font-medium text-green-600">67.2%</span>
            </div>
            <div className="flex items-center justify-between text-sm mt-1">
              <span className="text-neutral-600">Average Score</span>
              <span className="font-medium text-neutral-900">88.4%</span>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Quality Issues */}
      <GlassCard>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-neutral-500" />
            <h3 className="text-lg font-semibold text-neutral-900">Quality Issues</h3>
          </div>
          <div className="text-sm text-neutral-600">
            {qualityIssues.length} issues detected
          </div>
        </div>
        
        <div className="space-y-3">
          {qualityIssues.map((issue) => (
            <div key={issue.id} className={`p-4 rounded-lg border ${getSeverityColor(issue.severity)}`}>
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  {getIssueIcon(issue.type)}
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-medium text-neutral-900">{issue.description}</h4>
                      <span className={`px-2 py-1 text-xs rounded-full font-medium capitalize ${getSeverityColor(issue.severity)}`}>
                        {issue.severity}
                      </span>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-neutral-600">
                      <span>Type: {issue.type}</span>
                      <span>Affected: {issue.affected_files} files</span>
                      <span>Detected: {new Date(issue.detected_at).toLocaleDateString()}</span>
                      {issue.assigned_to && <span>Assigned to: {issue.assigned_to}</span>}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {getStatusIcon(issue.status)}
                  <span className="text-sm font-medium capitalize">{issue.status}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {qualityIssues.length === 0 && (
          <div className="text-center py-8">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
            <p className="text-neutral-600">No quality issues detected</p>
          </div>
        )}
      </GlassCard>

      {/* Recommendations */}
      <GlassCard>
        <div className="flex items-center space-x-2 mb-4">
          <Target className="w-5 h-5 text-neutral-500" />
          <h3 className="text-lg font-semibold text-neutral-900">Quality Recommendations</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <Zap className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-900 mb-1">Optimize OCR Settings</h4>
                <p className="text-sm text-blue-700">
                  Adjust confidence threshold for medical documents to improve accuracy by 3-5%
                </p>
              </div>
            </div>
          </div>
          
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-green-900 mb-1">Validation Rules</h4>
                <p className="text-sm text-green-700">
                  Implement stricter phone number validation to catch formatting issues early
                </p>
              </div>
            </div>
          </div>
          
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <Clock className="w-5 h-5 text-yellow-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-yellow-900 mb-1">Processing Queue</h4>
                <p className="text-sm text-yellow-700">
                  Consider batching similar document types for improved processing efficiency
                </p>
              </div>
            </div>
          </div>
          
          <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <Award className="w-5 h-5 text-purple-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-purple-900 mb-1">Quality Monitoring</h4>
                <p className="text-sm text-purple-700">
                  Set up automated alerts for quality metrics dropping below thresholds
                </p>
              </div>
            </div>
          </div>
        </div>
      </GlassCard>
    </div>
  );
};

export default QualityControlDashboard;