import React, { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Upload, Download, Play, Pause, FileText, Users, Package, Stethoscope, 
  BarChart3, Clock, CheckCircle, AlertCircle, Loader2, Settings, Trash2, Eye 
} from 'lucide-react';

interface BatchJob {
  id: string;
  batchId: string;
  batchType: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  totalItems: number;
  processedItems: number;
  startTime: string;
  estimatedCompletion?: string;
  priority: 'low' | 'normal' | 'high';
  userId: string;
  userName: string;
}

interface BatchProcess {
  id: string;
  name: string;
  description: string;
  type: string;
  estimatedDuration: string;
  maxBatchSize: number;
  active: boolean;
}

export const BatchProcessingInterface: React.FC = () => {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<BatchJob[]>([]);
  const [processes, setProcesses] = useState<BatchProcess[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedJob, setSelectedJob] = useState<BatchJob | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newProcessName, setNewProcessName] = useState('');
  const [selectedProcessType, setSelectedProcessType] = useState('');

  const processTypes = [
    { value: 'data-validation', label: 'Data Validation', icon: CheckCircle },
    { value: 'ocr-processing', label: 'OCR Document Processing', icon: FileText },
    { value: 'batch-export', label: 'Data Export', icon: Download },
    { value: 'quality-control', label: 'Quality Control', icon: Stethoscope }
  ];

  useEffect(() => {
    loadBatchJobs();
    loadBatchProcesses();
  }, []);

  const loadBatchJobs = async () => {
    setLoading(true);
    try {
      // Mock data for demonstration
      const mockJobs: BatchJob[] = [
        {
          id: '1',
          batchId: 'BATCH-2024-001',
          batchType: 'data-validation',
          status: 'processing',
          totalItems: 1500,
          processedItems: 847,
          startTime: new Date(Date.now() - 3600000).toISOString(),
          estimatedCompletion: new Date(Date.now() + 1800000).toISOString(),
          priority: 'normal',
          userId: user?.id || '1',
          userName: user?.full_name || 'Demo User'
        },
        {
          id: '2',
          batchId: 'BATCH-2024-002',
          batchType: 'ocr-processing',
          status: 'completed',
          totalItems: 500,
          processedItems: 500,
          startTime: new Date(Date.now() - 7200000).toISOString(),
          priority: 'high',
          userId: user?.id || '1',
          userName: user?.full_name || 'Demo User'
        },
        {
          id: '3',
          batchId: 'BATCH-2024-003',
          batchType: 'quality-control',
          status: 'failed',
          totalItems: 100,
          processedItems: 23,
          startTime: new Date(Date.now() - 5400000).toISOString(),
          priority: 'low',
          userId: user?.id || '1',
          userName: user?.full_name || 'Demo User'
        }
      ];
      setJobs(mockJobs);
    } catch (error) {
      console.error('Error loading batch jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadBatchProcesses = async () => {
    try {
      const mockProcesses: BatchProcess[] = [
        {
          id: '1',
          name: 'Daily Data Validation',
          description: 'Validates all customer data entries for completeness and accuracy',
          type: 'data-validation',
          estimatedDuration: '2-4 hours',
          maxBatchSize: 5000,
          active: true
        },
        {
          id: '2',
          name: 'Document OCR Processing',
          description: 'Extracts text and metadata from uploaded documents',
          type: 'ocr-processing',
          estimatedDuration: '30-60 minutes',
          maxBatchSize: 1000,
          active: true
        },
        {
          id: '3',
          name: 'Weekly Export',
          description: 'Exports validated data to external systems',
          type: 'batch-export',
          estimatedDuration: '1-2 hours',
          maxBatchSize: 10000,
          active: false
        }
      ];
      setProcesses(mockProcesses);
    } catch (error) {
      console.error('Error loading batch processes:', error);
    }
  };

  const createBatchJob = async () => {
    if (!newProcessName || !selectedProcessType) return;
    
    setLoading(true);
    try {
      const newJob: BatchJob = {
        id: Date.now().toString(),
        batchId: `BATCH-2024-${String(jobs.length + 1).padStart(3, '0')}`,
        batchType: selectedProcessType,
        status: 'pending',
        totalItems: Math.floor(Math.random() * 1000) + 100,
        processedItems: 0,
        startTime: new Date().toISOString(),
        priority: 'normal',
        userId: user?.id || '1',
        userName: user?.full_name || 'Demo User'
      };

      setJobs(prev => [newJob, ...prev]);
      setNewProcessName('');
      setSelectedProcessType('');
      setShowCreateForm(false);
      
      // Simulate job processing
      setTimeout(() => {
        setJobs(prev => prev.map(job => 
          job.id === newJob.id 
            ? { ...job, status: 'processing' as const }
            : job
        ));
      }, 2000);
    } catch (error) {
      console.error('Error creating batch job:', error);
    } finally {
      setLoading(false);
    }
  };

  const pauseJob = async (jobId: string) => {
    setJobs(prev => prev.map(job => 
      job.id === jobId && job.status === 'processing'
        ? { ...job, status: 'pending' as const }
        : job
    ));
  };

  const resumeJob = async (jobId: string) => {
    setJobs(prev => prev.map(job => 
      job.id === jobId && job.status === 'pending'
        ? { ...job, status: 'processing' as const }
        : job
    ));
  };

  const deleteJob = async (jobId: string) => {
    setJobs(prev => prev.filter(job => job.id !== jobId));
    if (selectedJob?.id === jobId) {
      setSelectedJob(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50';
      case 'processing': return 'text-blue-600 bg-blue-50';
      case 'failed': return 'text-red-600 bg-red-50';
      case 'pending': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-neutral-600 bg-neutral-50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'processing': return <Loader2 className="w-4 h-4 animate-spin" />;
      case 'failed': return <AlertCircle className="w-4 h-4" />;
      case 'pending': return <Clock className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const formatDuration = (startTime: string) => {
    const start = new Date(startTime);
    const now = new Date();
    const diff = Math.floor((now.getTime() - start.getTime()) / 1000);
    const hours = Math.floor(diff / 3600);
    const minutes = Math.floor((diff % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const formatEstimatedCompletion = (estimated?: string) => {
    if (!estimated) return 'Calculating...';
    const time = new Date(estimated);
    return time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const GlassCard: React.FC<{ children: React.ReactNode; className?: string }> = ({ 
    children, 
    className = '' 
  }) => (
    <div className={`bg-glass-light backdrop-blur-glass border border-glass-border rounded-xl p-6 ${className}`}>
      {children}
    </div>
  );

  const GlassButton: React.FC<{ 
    children: React.ReactNode; 
    onClick?: () => void; 
    variant?: 'primary' | 'secondary' | 'danger';
    disabled?: boolean;
    className?: string;
  }> = ({ children, onClick, variant = 'primary', disabled = false, className = '' }) => {
    const baseClasses = 'px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2';
    const variantClasses = {
      primary: 'bg-primary-500 text-white hover:bg-primary-600 disabled:bg-neutral-300',
      secondary: 'bg-white text-neutral-700 border border-neutral-300 hover:bg-neutral-50 disabled:bg-neutral-100',
      danger: 'bg-red-500 text-white hover:bg-red-600 disabled:bg-neutral-300'
    };

    return (
      <button
        onClick={onClick}
        disabled={disabled}
        className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      >
        {children}
      </button>
    );
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Batch Processing</h1>
          <p className="text-neutral-600 mt-1">Manage and monitor large-scale data processing jobs</p>
        </div>
        <GlassButton onClick={() => setShowCreateForm(true)}>
          <Upload className="w-4 h-4" />
          <span>New Batch Job</span>
        </GlassButton>
      </div>

      {/* Create Job Form */}
      {showCreateForm && (
        <GlassCard>
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">Create New Batch Job</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">Job Name</label>
              <input
                type="text"
                value={newProcessName}
                onChange={(e) => setNewProcessName(e.target.value)}
                placeholder="Enter job name..."
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">Process Type</label>
              <select
                value={selectedProcessType}
                onChange={(e) => setSelectedProcessType(e.target.value)}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Select process type...</option>
                {processTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex space-x-3">
              <GlassButton onClick={createBatchJob} disabled={!newProcessName || !selectedProcessType}>
                <Play className="w-4 h-4" />
                <span>Create & Start</span>
              </GlassButton>
              <GlassButton onClick={() => setShowCreateForm(false)} variant="secondary">
                Cancel
              </GlassButton>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Active Jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <GlassCard>
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900">Processing</h3>
              <p className="text-2xl font-bold text-blue-600">
                {jobs.filter(j => j.status === 'processing').length}
              </p>
            </div>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900">Completed</h3>
              <p className="text-2xl font-bold text-green-600">
                {jobs.filter(j => j.status === 'completed').length}
              </p>
            </div>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <AlertCircle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900">Failed</h3>
              <p className="text-2xl font-bold text-red-600">
                {jobs.filter(j => j.status === 'failed').length}
              </p>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Jobs List */}
      <GlassCard>
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">Recent Batch Jobs</h3>
        <div className="space-y-3">
          {jobs.map(job => (
            <div key={job.id} className="border border-neutral-200 rounded-lg p-4 hover:bg-neutral-50 transition-colors">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-neutral-100 rounded-lg flex items-center justify-center">
                    <Package className="w-5 h-5 text-neutral-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-neutral-900">{job.batchId}</h4>
                    <p className="text-sm text-neutral-600">{job.batchType}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${getStatusColor(job.status)}`}>
                    {getStatusIcon(job.status)}
                    <span>{job.status}</span>
                  </span>
                  <div className="flex space-x-1">
                    <button
                      onClick={() => setSelectedJob(job)}
                      className="p-1 text-neutral-500 hover:text-neutral-700"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    {job.status === 'processing' ? (
                      <button
                        onClick={() => pauseJob(job.id)}
                        className="p-1 text-neutral-500 hover:text-yellow-600"
                      >
                        <Pause className="w-4 h-4" />
                      </button>
                    ) : job.status === 'pending' ? (
                      <button
                        onClick={() => resumeJob(job.id)}
                        className="p-1 text-neutral-500 hover:text-green-600"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    ) : null}
                    <button
                      onClick={() => deleteJob(job.id)}
                      className="p-1 text-neutral-500 hover:text-red-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-neutral-500">Progress</p>
                  <p className="font-medium">{job.processedItems}/{job.totalItems}</p>
                </div>
                <div>
                  <p className="text-neutral-500">Duration</p>
                  <p className="font-medium">{formatDuration(job.startTime)}</p>
                </div>
                <div>
                  <p className="text-neutral-500">Priority</p>
                  <p className="font-medium capitalize">{job.priority}</p>
                </div>
                <div>
                  <p className="text-neutral-500">User</p>
                  <p className="font-medium">{job.userName}</p>
                </div>
              </div>
              
              {job.status === 'processing' && (
                <div className="mt-3">
                  <div className="w-full bg-neutral-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${(job.processedItems / job.totalItems) * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Job Details Modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-neutral-900">Job Details</h3>
              <button
                onClick={() => setSelectedJob(null)}
                className="text-neutral-500 hover:text-neutral-700"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-700">Batch ID</label>
                  <p className="text-neutral-900">{selectedJob.batchId}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700">Status</label>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(selectedJob.status)}`}>
                    {selectedJob.status}
                  </span>
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700">Type</label>
                  <p className="text-neutral-900">{selectedJob.batchType}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700">Priority</label>
                  <p className="text-neutral-900 capitalize">{selectedJob.priority}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700">Start Time</label>
                  <p className="text-neutral-900">{new Date(selectedJob.startTime).toLocaleString()}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700">Duration</label>
                  <p className="text-neutral-900">{formatDuration(selectedJob.startTime)}</p>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-neutral-700">Progress</label>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 bg-neutral-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${(selectedJob.processedItems / selectedJob.totalItems) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm text-neutral-600">
                    {selectedJob.processedItems}/{selectedJob.totalItems}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};