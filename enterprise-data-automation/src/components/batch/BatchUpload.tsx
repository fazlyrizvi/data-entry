import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  File, 
  FileText, 
  Image, 
  AlertCircle, 
  CheckCircle, 
  X,
  Play,
  Pause,
  Square,
  Loader2,
  FolderOpen,
  Trash2,
  Download
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { processingService, ProcessingJob, ProcessingProgress } from '../../services/processingService';

interface BatchFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'uploaded' | 'processing' | 'completed' | 'error';
  progress: number;
  error?: string;
  result?: any;
}

interface BatchJob {
  id: string;
  type: 'ocr' | 'validation' | 'extraction';
  status: 'idle' | 'processing' | 'completed' | 'error';
  files: BatchFile[];
  progress: ProcessingProgress;
}

export const BatchUpload: React.FC = () => {
  const [batchJobs, setBatchJobs] = useState<BatchJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<string>('');
  const [processingType, setProcessingType] = useState<'ocr' | 'validation' | 'extraction'>('ocr');
  const [dataType, setDataType] = useState<'invoice' | 'receipt' | 'form' | 'document'>('invoice');

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    const newFiles: BatchFile[] = acceptedFiles.map(file => ({
      file,
      id: `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      status: 'pending',
      progress: 0
    }));

    createBatchJob(newFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: {
      'image/*': [],
      'application/pdf': []
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    noClick: false,
    noKeyboard: false
  } as any);

  const createBatchJob = (files: BatchFile[]) => {
    const job: BatchJob = {
      id: `job_${Date.now()}`,
      type: processingType,
      status: 'idle',
      files,
      progress: {
        job_id: '',
        progress: 0,
        status: '',
        message: '',
        processed_count: 0,
        total_count: 0
      }
    };

    setBatchJobs(prev => [...prev, job]);
    setSelectedJob(job.id);
  };

  const removeFile = (jobId: string, fileId: string) => {
    setBatchJobs(prev => prev.map(job => 
      job.id === jobId 
        ? { ...job, files: job.files.filter(f => f.id !== fileId) }
        : job
    ));
  };

  const removeJob = (jobId: string) => {
    setBatchJobs(prev => prev.filter(job => job.id !== jobId));
    if (selectedJob === jobId) {
      setSelectedJob('');
    }
  };

  const startBatchProcessing = async (jobId: string) => {
    const job = batchJobs.find(j => j.id === jobId);
    if (!job || job.files.length === 0) return;

    // Update job status
    setBatchJobs(prev => prev.map(j => 
      j.id === jobId 
        ? { ...j, status: 'processing' }
        : j
    ));

    try {
      let serviceJob: ProcessingJob;

      if (job.type === 'ocr') {
        // Create OCR job
        serviceJob = await processingService.createJob('ocr', [], { dataType });
        
        // Process files
        await processingService.processBatchOCR(
          serviceJob.id,
          job.files.map(f => f.file),
          dataType,
          (progress) => {
            setBatchJobs(prev => prev.map(j => 
              j.id === jobId 
                ? { ...j, progress }
                : j
            ));
          }
        );
      } else if (job.type === 'validation') {
        // Create validation job for emails (demo)
        const validationData = job.files.map((file, index) => ({
          id: `field_${index}`,
          field: `email_${index}`,
          value: `test${index}@example.com`,
          type: 'email' as const
        }));

        serviceJob = await processingService.createJob('batch_validation', []);
        
        await processingService.processBatchValidation(
          serviceJob.id,
          { type: 'email', data: validationData },
          (progress) => {
            setBatchJobs(prev => prev.map(j => 
              j.id === jobId 
                ? { ...j, progress }
                : j
            ));
          }
        );
      }

      // Update job status to completed
      setBatchJobs(prev => prev.map(j => 
        j.id === jobId 
          ? { ...j, status: 'completed' }
          : j
      ));

    } catch (error) {
      console.error('Batch processing failed:', error);
      setBatchJobs(prev => prev.map(j => 
        j.id === jobId 
          ? { ...j, status: 'error' }
          : j
      ));
    }
  };

  const stopBatchProcessing = (jobId: string) => {
    setBatchJobs(prev => prev.map(j => 
      j.id === jobId 
        ? { ...j, status: 'idle' }
        : j
    ));
  };

  const getStatusIcon = (status: BatchFile['status']) => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'uploaded':
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <File className="w-4 h-4 text-neutral-400" />;
    }
  };

  const getStatusColor = (status: BatchFile['status']) => {
    switch (status) {
      case 'processing': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'completed': return 'text-green-600 bg-green-50 border-green-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-neutral-600 bg-neutral-50 border-neutral-200';
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return Image;
    if (file.type === 'application/pdf') return FileText;
    return File;
  };

  const exportResults = (jobId: string) => {
    const job = batchJobs.find(j => j.id === jobId);
    if (!job || job.status !== 'completed') return;

    const results = job.files
      .filter(f => f.status === 'completed' && f.result)
      .map(f => ({
        filename: f.file.name,
        result: f.result
      }));

    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `batch-results-${jobId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const selectedJobData = batchJobs.find(j => j.id === selectedJob);
  const totalFiles = batchJobs.reduce((sum, job) => sum + job.files.length, 0);
  const completedFiles = batchJobs.reduce((sum, job) => sum + job.files.filter(f => f.status === 'completed').length, 0);
  const processingFiles = batchJobs.reduce((sum, job) => sum + job.files.filter(f => f.status === 'processing').length, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Batch Processing</h1>
          <p className="text-neutral-600 mt-1">Process multiple files simultaneously with OCR and validation</p>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <GlassCard>
          <div className="text-center">
            <div className="text-2xl font-bold text-neutral-900">{batchJobs.length}</div>
            <div className="text-sm text-neutral-600">Active Jobs</div>
          </div>
        </GlassCard>
        <GlassCard>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{totalFiles}</div>
            <div className="text-sm text-neutral-600">Total Files</div>
          </div>
        </GlassCard>
        <GlassCard>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{completedFiles}</div>
            <div className="text-sm text-neutral-600">Completed</div>
          </div>
        </GlassCard>
        <GlassCard>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{processingFiles}</div>
            <div className="text-sm text-neutral-600">Processing</div>
          </div>
        </GlassCard>
      </div>

      {/* Processing Type Selection */}
      <GlassCard>
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">Processing Type</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => setProcessingType('ocr')}
            className={`p-4 border-2 rounded-lg text-left transition-all ${
              processingType === 'ocr' 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-neutral-200 hover:border-neutral-300'
            }`}
          >
            <div className="flex items-center space-x-3">
              <FileText className={`w-6 h-6 ${processingType === 'ocr' ? 'text-blue-600' : 'text-neutral-500'}`} />
              <div>
                <h4 className="font-medium text-neutral-900">OCR Processing</h4>
                <p className="text-sm text-neutral-600">Extract text and data from documents</p>
              </div>
            </div>
          </button>

          <button
            onClick={() => setProcessingType('validation')}
            className={`p-4 border-2 rounded-lg text-left transition-all ${
              processingType === 'validation' 
                ? 'border-green-500 bg-green-50' 
                : 'border-neutral-200 hover:border-neutral-300'
            }`}
          >
            <div className="flex items-center space-x-3">
              <CheckCircle className={`w-6 h-6 ${processingType === 'validation' ? 'text-green-600' : 'text-neutral-500'}`} />
              <div>
                <h4 className="font-medium text-neutral-900">Data Validation</h4>
                <p className="text-sm text-neutral-600">Validate emails, phones, addresses</p>
              </div>
            </div>
          </button>

          <button
            onClick={() => setProcessingType('extraction')}
            className={`p-4 border-2 rounded-lg text-left transition-all ${
              processingType === 'extraction' 
                ? 'border-purple-500 bg-purple-50' 
                : 'border-neutral-200 hover:border-neutral-300'
            }`}
          >
            <div className="flex items-center space-x-3">
              <AlertCircle className={`w-6 h-6 ${processingType === 'extraction' ? 'text-purple-600' : 'text-neutral-500'}`} />
              <div>
                <h4 className="font-medium text-neutral-900">Data Extraction</h4>
                <p className="text-sm text-neutral-600">Extract structured data from forms</p>
              </div>
            </div>
          </button>
        </div>

        {processingType === 'ocr' && (
          <div className="mt-4 pt-4 border-t border-neutral-200">
            <label className="block text-sm font-medium text-neutral-700 mb-2">Document Type</label>
            <select
              value={dataType}
              onChange={(e) => setDataType(e.target.value as any)}
              className="w-full max-w-xs px-3 py-2 border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
            >
              <option value="invoice">Invoice</option>
              <option value="receipt">Receipt</option>
              <option value="form">Form</option>
              <option value="document">Document</option>
            </select>
          </div>
        )}
      </GlassCard>

      {/* Upload Area */}
      <GlassCard>
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer
            ${isDragActive 
              ? 'border-primary-500 bg-primary-50' 
              : 'border-neutral-300 hover:border-primary-400 hover:bg-neutral-50'
            }
          `}
        >
          <input {...(getInputProps() as any)} />
          
          <div className="flex flex-col items-center space-y-4">
            <div className={`
              w-16 h-16 rounded-full flex items-center justify-center transition-colors
              ${isDragActive ? 'bg-primary-100' : 'bg-neutral-100'}
            `}>
              <Upload className={`
                w-8 h-8 transition-colors
                ${isDragActive ? 'text-primary-600' : 'text-neutral-500'}
              `} />
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                {isDragActive ? 'Drop files here' : 'Batch Upload Files'}
              </h3>
              <p className="text-neutral-600 mb-4">
                Drag and drop files here, or click to select multiple files
              </p>
              <div className="text-sm text-neutral-500">
                <p>Supported formats: PDF, JPG, PNG, TIFF</p>
                <p>Maximum file size: 50MB per file</p>
                <p>Processing type: {processingType.toUpperCase()}</p>
              </div>
            </div>
          </div>
        </div>

        {/* File Rejections */}
        {fileRejections.length > 0 && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <h4 className="font-medium text-red-900 mb-2">File Upload Errors:</h4>
            {fileRejections.map(({ file, errors }, index) => (
              <div key={index} className="text-sm text-red-700 mb-1">
                <span className="font-medium">{file.name}</span>:
                <ul className="ml-4 mt-1">
                  {errors.map(error => (
                    <li key={error.code}>• {error.message}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Batch Jobs */}
      {batchJobs.length > 0 && (
        <GlassCard>
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">Batch Jobs</h3>
          
          <div className="space-y-4">
            {batchJobs.map((job) => (
              <div key={job.id} className="border border-neutral-200 rounded-lg">
                <div className="p-4 bg-neutral-50 border-b border-neutral-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <FolderOpen className="w-5 h-5 text-neutral-500" />
                      <div>
                        <h4 className="font-medium text-neutral-900">
                          {job.type.toUpperCase()} Job - {job.files.length} files
                        </h4>
                        <p className="text-sm text-neutral-600">
                          Status: <span className="capitalize">{job.status}</span>
                          {job.type === 'ocr' && ` • ${dataType} documents`}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {job.status === 'idle' && job.files.length > 0 && (
                        <button
                          onClick={() => startBatchProcessing(job.id)}
                          className="flex items-center space-x-2 px-3 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors"
                        >
                          <Play className="w-4 h-4" />
                          <span>Start</span>
                        </button>
                      )}
                      
                      {job.status === 'processing' && (
                        <button
                          onClick={() => stopBatchProcessing(job.id)}
                          className="flex items-center space-x-2 px-3 py-2 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 transition-colors"
                        >
                          <Square className="w-4 h-4" />
                          <span>Stop</span>
                        </button>
                      )}
                      
                      {job.status === 'completed' && (
                        <button
                          onClick={() => exportResults(job.id)}
                          className="flex items-center space-x-2 px-3 py-2 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 transition-colors"
                        >
                          <Download className="w-4 h-4" />
                          <span>Export</span>
                        </button>
                      )}
                      
                      <button
                        onClick={() => removeJob(job.id)}
                        className="p-2 text-neutral-400 hover:text-red-500 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Progress */}
                  {job.progress.total_count > 0 && (
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="text-neutral-600">
                          {job.progress.message}
                        </span>
                        <span className="font-medium text-neutral-900">
                          {Math.round(job.progress.progress)}%
                        </span>
                      </div>
                      <div className="w-full bg-neutral-200 rounded-full h-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${job.progress.progress}%` }}
                        />
                      </div>
                      <div className="text-xs text-neutral-500 mt-1">
                        {job.progress.processed_count} of {job.progress.total_count} files processed
                      </div>
                    </div>
                  )}
                </div>

                {/* Files */}
                <div className="p-4">
                  <div className="space-y-2">
                    {job.files.map((file) => {
                      const FileIcon = getFileIcon(file.file);
                      
                      return (
                        <div key={file.id} className={`p-3 rounded-lg border ${getStatusColor(file.status)}`}>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <FileIcon className="w-5 h-5 text-neutral-500" />
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-neutral-900 truncate">
                                  {file.file.name}
                                </p>
                                <p className="text-sm text-neutral-600">
                                  {formatFileSize(file.file.size)}
                                </p>
                              </div>
                            </div>
                            
                            <div className="flex items-center space-x-3">
                              {getStatusIcon(file.status)}
                              {file.status === 'processing' && (
                                <div className="w-16 bg-neutral-200 rounded-full h-2">
                                  <div 
                                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                                    style={{ width: `${file.progress}%` }}
                                  />
                                </div>
                              )}
                              <button
                                onClick={() => removeFile(job.id, file.id)}
                                className="p-1 text-neutral-400 hover:text-red-500 transition-colors"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                          
                          {file.error && (
                            <div className="mt-2 p-2 bg-red-100 border border-red-200 rounded text-sm text-red-700">
                              {file.error}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {batchJobs.length === 0 && (
        <GlassCard>
          <div className="text-center py-12">
            <FolderOpen className="w-16 h-16 text-neutral-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-neutral-900 mb-2">
              No Batch Jobs Created
            </h3>
            <p className="text-neutral-600">
              Upload files to create your first batch processing job
            </p>
          </div>
        </GlassCard>
      )}
    </div>
  );
};

export default BatchUpload;