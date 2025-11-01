import React, { useState } from 'react';
import { 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Mail, 
  Phone, 
  MapPin, 
  BarChart3,
  FileText,
  Download,
  RefreshCw,
  Settings,
  Filter,
  Eye
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import EmailValidator from './EmailValidator';
import PhoneValidator from './PhoneValidator';

interface ValidationJob {
  id: string;
  type: 'email' | 'phone' | 'address' | 'mixed';
  status: 'pending' | 'processing' | 'completed' | 'error';
  total_items: number;
  valid_items: number;
  invalid_items: number;
  created_at: string;
  completed_at?: string;
  results_summary?: any;
}

export const ValidationDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'email' | 'phone' | 'address' | 'dashboard'>('dashboard');
  const [validationJobs, setValidationJobs] = useState<ValidationJob[]>([
    {
      id: 'job_1',
      type: 'email',
      status: 'completed',
      total_items: 1250,
      valid_items: 1180,
      invalid_items: 70,
      created_at: '2025-11-01T10:30:00Z',
      completed_at: '2025-11-01T10:45:00Z',
      results_summary: {
        deliverability_average: 87.5,
        high_risk_count: 25,
        role_accounts: 45
      }
    },
    {
      id: 'job_2',
      type: 'phone',
      status: 'completed',
      total_items: 890,
      valid_items: 856,
      invalid_items: 34,
      created_at: '2025-11-01T09:15:00Z',
      completed_at: '2025-11-01T09:28:00Z',
      results_summary: {
        mobile_percentage: 78,
        landline_percentage: 22,
        carrier_coverage: 95
      }
    },
    {
      id: 'job_3',
      type: 'mixed',
      status: 'processing',
      total_items: 500,
      valid_items: 320,
      invalid_items: 180,
      created_at: '2025-11-01T11:00:00Z'
    }
  ]);

  const totalProcessed = validationJobs.reduce((sum, job) => sum + job.total_items, 0);
  const totalValid = validationJobs.reduce((sum, job) => sum + job.valid_items, 0);
  const totalInvalid = validationJobs.reduce((sum, job) => sum + job.invalid_items, 0);
  const overallAccuracy = totalProcessed > 0 ? (totalValid / totalProcessed) * 100 : 0;

  const getJobIcon = (type: ValidationJob['type']) => {
    switch (type) {
      case 'email': return Mail;
      case 'phone': return Phone;
      case 'address': return MapPin;
      default: return FileText;
    }
  };

  const getJobColor = (type: ValidationJob['type']) => {
    switch (type) {
      case 'email': return 'text-blue-600 bg-blue-50';
      case 'phone': return 'text-green-600 bg-green-50';
      case 'address': return 'text-purple-600 bg-purple-50';
      default: return 'text-neutral-600 bg-neutral-50';
    }
  };

  const getStatusColor = (status: ValidationJob['status']) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50';
      case 'processing': return 'text-blue-600 bg-blue-50';
      case 'error': return 'text-red-600 bg-red-50';
      default: return 'text-yellow-600 bg-yellow-50';
    }
  };

  const getStatusIcon = (status: ValidationJob['status']) => {
    switch (status) {
      case 'completed': return CheckCircle;
      case 'processing': return RefreshCw;
      case 'error': return XCircle;
      default: return AlertTriangle;
    }
  };

  const exportJobResults = (job: ValidationJob) => {
    // This would typically export the actual results
    const data = {
      job_id: job.id,
      type: job.type,
      summary: job.results_summary,
      total_items: job.total_items,
      valid_items: job.valid_items,
      invalid_items: job.invalid_items,
      accuracy: ((job.valid_items / job.total_items) * 100).toFixed(2) + '%'
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `validation-results-${job.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Data Validation Hub</h1>
          <p className="text-neutral-600 mt-1">Comprehensive data validation with real-time API integrations</p>
        </div>
        
        <div className="flex space-x-3">
          <button className="flex items-center space-x-2 px-4 py-2 bg-neutral-500 text-white rounded-lg text-sm hover:bg-neutral-600 transition-colors">
            <Settings className="w-4 h-4" />
            <span>Settings</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600 transition-colors">
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-neutral-500">Total Processed</p>
              <p className="text-2xl font-bold text-neutral-900">{totalProcessed.toLocaleString()}</p>
            </div>
          </div>
        </GlassCard>
        
        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-neutral-500">Valid Items</p>
              <p className="text-2xl font-bold text-green-600">{totalValid.toLocaleString()}</p>
            </div>
          </div>
        </GlassCard>
        
        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <XCircle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-neutral-500">Invalid Items</p>
              <p className="text-2xl font-bold text-red-600">{totalInvalid.toLocaleString()}</p>
            </div>
          </div>
        </GlassCard>
        
        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-neutral-500">Accuracy Rate</p>
              <p className="text-2xl font-bold text-purple-600">{overallAccuracy.toFixed(1)}%</p>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Navigation Tabs */}
      <GlassCard>
        <div className="flex space-x-1">
          {[
            { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
            { id: 'email', label: 'Email Validation', icon: Mail },
            { id: 'phone', label: 'Phone Validation', icon: Phone },
            { id: 'address', label: 'Address Validation', icon: MapPin }
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`
                  flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors
                  ${activeTab === tab.id 
                    ? 'bg-primary-500 text-white' 
                    : 'text-neutral-600 hover:bg-neutral-100'
                  }
                `}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </GlassCard>

      {/* Content */}
      {activeTab === 'dashboard' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Jobs */}
          <GlassCard>
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Recent Validation Jobs</h3>
            
            <div className="space-y-3">
              {validationJobs.map((job) => {
                const JobIcon = getJobIcon(job.type);
                const StatusIcon = getStatusIcon(job.status);
                
                return (
                  <div key={job.id} className="p-4 bg-neutral-50 rounded-lg">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-lg ${getJobColor(job.type)}`}>
                          <JobIcon className="w-5 h-5" />
                        </div>
                        <div>
                          <h4 className="font-medium text-neutral-900 capitalize">
                            {job.type} Validation
                          </h4>
                          <p className="text-sm text-neutral-600">
                            {job.total_items} items • {new Date(job.created_at).toLocaleDateString()}
                          </p>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className={`px-2 py-1 rounded-full text-xs flex items-center space-x-1 ${getStatusColor(job.status)}`}>
                              <StatusIcon className="w-3 h-3" />
                              <span className="capitalize">{job.status}</span>
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <p className="font-semibold text-neutral-900">
                          {((job.valid_items / job.total_items) * 100).toFixed(1)}%
                        </p>
                        <p className="text-sm text-neutral-600">accuracy</p>
                      </div>
                    </div>
                    
                    {job.status === 'completed' && (
                      <div className="flex justify-end mt-3">
                        <button
                          onClick={() => exportJobResults(job)}
                          className="flex items-center space-x-1 px-3 py-1 text-sm text-blue-600 hover:text-blue-700"
                        >
                          <Download className="w-3 h-3" />
                          <span>Export</span>
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </GlassCard>

          {/* Validation Metrics */}
          <GlassCard>
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Validation Metrics</h3>
            
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-neutral-600">Email Validation</span>
                  <span className="font-medium">87.2%</span>
                </div>
                <div className="w-full bg-neutral-200 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: '87.2%' }} />
                </div>
              </div>
              
              <div>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-neutral-600">Phone Validation</span>
                  <span className="font-medium">94.8%</span>
                </div>
                <div className="w-full bg-neutral-200 rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{ width: '94.8%' }} />
                </div>
              </div>
              
              <div>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-neutral-600">Address Validation</span>
                  <span className="font-medium">76.5%</span>
                </div>
                <div className="w-full bg-neutral-200 rounded-full h-2">
                  <div className="bg-purple-500 h-2 rounded-full" style={{ width: '76.5%' }} />
                </div>
              </div>
              
              <div className="pt-4 border-t border-neutral-200">
                <h4 className="font-medium text-neutral-900 mb-3">API Usage Today</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <p className="text-xl font-bold text-blue-600">1,245</p>
                    <p className="text-xs text-neutral-600">Hunter.io requests</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xl font-bold text-green-600">890</p>
                    <p className="text-xs text-neutral-600">Numverify requests</p>
                  </div>
                </div>
              </div>
            </div>
          </GlassCard>
        </div>
      )}

      {activeTab === 'email' && <EmailValidator />}

      {activeTab === 'phone' && <PhoneValidator />}

      {activeTab === 'address' && (
        <GlassCard>
          <div className="text-center py-12">
            <MapPin className="w-16 h-16 text-neutral-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-neutral-900 mb-2">
              Address Validation
            </h3>
            <p className="text-neutral-600 mb-6">
              Address validation using Google Maps API and custom formatting rules
            </p>
            <div className="text-sm text-neutral-500">
              <p>Features:</p>
              <ul className="mt-2 space-y-1">
                <li>• Real-time address format validation</li>
                <li>• Geographic location verification</li>
                <li>• USPS address standardization</li>
                <li>• Bulk address processing</li>
              </ul>
            </div>
          </div>
        </GlassCard>
      )}
    </div>
  );
};

export default ValidationDashboard;