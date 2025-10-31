import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { 
  Upload, 
  File, 
  Image, 
  FileText, 
  X, 
  Check, 
  AlertCircle,
  Clock,
  Play,
  Pause,
  Trash2
} from 'lucide-react'
import { GlassCard } from '../ui/GlassCard'
import { formatFileSize, getStatusColor, getStatusIcon } from '../../lib/utils'

interface FileUpload {
  id: string
  name: string
  size: number
  type: string
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'paused' | 'uploading'
  progress: number
  error?: string
  confidence?: number
}

interface UploadedFile extends FileUpload {
  file: File
}

export const FileUploadInterface: React.FC = () => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'completed'>('all')
  const [processingJobs, setProcessingJobs] = useState<FileUpload[]>([
    {
      id: '1',
      name: 'Q4_Financial_Report.pdf',
      size: 2456789,
      type: 'PDF',
      status: 'processing',
      progress: 67,
      confidence: 92.5
    },
    {
      id: '2',
      name: 'Employee_Records.xlsx',
      size: 456723,
      type: 'Excel',
      status: 'completed',
      progress: 100,
      confidence: 98.2
    },
    {
      id: '3',
      name: 'Invoice_Batch_003.zip',
      size: 15678934,
      type: 'Archive',
      status: 'failed',
      progress: 23,
      error: 'OCR processing timeout'
    },
    {
      id: '4',
      name: 'Customer_Data.csv',
      size: 789456,
      type: 'CSV',
      status: 'queued',
      progress: 0
    }
  ])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map((file, index) => ({
      id: `${Date.now()}-${index}`,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading',
      progress: 0,
      file
    }))

    setUploadedFiles(prev => [...prev, ...newFiles])

    // Simulate upload progress
    newFiles.forEach(uploadFile => {
      let progress = 0
      const interval = setInterval(() => {
        progress += Math.random() * 20
        if (progress >= 100) {
          progress = 100
          clearInterval(interval)
          setUploadedFiles(prev => prev.map(f => 
            f.id === uploadFile.id 
              ? { ...f, status: 'queued', progress: 100 }
              : f
          ))
        } else {
          setUploadedFiles(prev => prev.map(f => 
            f.id === uploadFile.id 
              ? { ...f, progress }
              : f
          ))
        }
      }, 200)
    })
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg'],
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/zip': ['.zip']
    },
    maxSize: 100 * 1024 * 1024 // 100MB
  } as any)

  const getFileIcon = (type: string) => {
    if (type.includes('image')) return Image
    if (type.includes('pdf')) return FileText
    return File
  }

  const removeFile = (id: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== id))
  }

  const getStatusIconComponent = (status: string) => {
    switch (status) {
      case 'completed': return Check
      case 'processing': return Play
      case 'failed': return AlertCircle
      case 'queued': return Clock
      default: return Upload
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">File Processing</h1>
          <p className="text-neutral-600 mt-1">Upload and manage your document processing workflows</p>
        </div>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg text-sm font-medium text-neutral-700 hover:bg-glass-lightHover transition-colors">
            Batch Operations
          </button>
          <button className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors">
            Queue Settings
          </button>
        </div>
      </div>

      {/* Upload Zone */}
      <GlassCard>
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all duration-300
            ${isDragActive 
              ? 'border-primary-500 bg-primary-50' 
              : 'border-neutral-300 hover:border-primary-400 hover:bg-neutral-50'
            }
          `}
        >
          <input {...(getInputProps() as any)} />
          <div className="flex flex-col items-center space-y-4">
            <div className="w-16 h-16 bg-neutral-100 rounded-full flex items-center justify-center">
              <Upload className="w-8 h-8 text-neutral-500" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900">
                {isDragActive ? 'Drop files here' : 'Drag files here or click to browse'}
              </h3>
              <p className="text-sm text-neutral-500 mt-1">
                Supports PDF, images, spreadsheets, and archives up to 100MB
              </p>
              <p className="text-xs text-neutral-400 mt-2">
                Supported formats: .pdf, .png, .jpg, .csv, .xlsx, .zip
              </p>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <GlassCard>
          <h3 className="text-lg font-semibold text-neutral-900 mb-6">Uploaded Files</h3>
          <div className="space-y-4">
            {uploadedFiles.map((file) => {
              const IconComponent = getFileIcon(file.type)
              return (
                <div key={file.id} className="flex items-center space-x-4 p-4 bg-neutral-50/50 rounded-lg">
                  <IconComponent className="w-8 h-8 text-neutral-500" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-neutral-900 truncate">{file.name}</p>
                    <p className="text-sm text-neutral-500">{formatFileSize(file.size)}</p>
                    <div className="mt-2">
                      <div className="w-full bg-neutral-200 rounded-full h-2">
                        <div 
                          className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${file.progress}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(file.status)}`}>
                      {file.status}
                    </span>
                    <button
                      onClick={() => removeFile(file.id)}
                      className="p-1 text-neutral-400 hover:text-neutral-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </GlassCard>
      )}

      {/* Processing Queue */}
      <GlassCard>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-neutral-900">Processing Queue</h3>
          <div className="flex space-x-2">
            <button 
              onClick={() => setFilterStatus('active')}
              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                filterStatus === 'active' 
                  ? 'bg-semantic-warning text-white' 
                  : 'bg-semantic-warning/10 text-semantic-warning hover:bg-semantic-warning/20'
              }`}
            >
              4 Active
            </button>
            <button 
              onClick={() => setFilterStatus('completed')}
              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                filterStatus === 'completed' 
                  ? 'bg-semantic-success text-white' 
                  : 'bg-semantic-success/10 text-semantic-success hover:bg-semantic-success/20'
              }`}
            >
              142 Completed
            </button>
          </div>
        </div>

        <div className="space-y-3">
          {processingJobs
            .filter(job => {
              if (filterStatus === 'all') return true
              if (filterStatus === 'active') return ['processing', 'queued'].includes(job.status)
              if (filterStatus === 'completed') return job.status === 'completed'
              return true
            })
            .map((job) => {
            const StatusIcon = getStatusIconComponent(job.status)
            return (
              <div key={job.id} className="flex items-center space-x-4 p-4 bg-neutral-50/50 rounded-lg hover:bg-neutral-100/50 transition-colors">
                <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
                  <FileText className="w-5 h-5 text-neutral-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <p className="font-medium text-neutral-900 truncate">{job.name}</p>
                    <span className="px-2 py-1 text-xs bg-neutral-100 text-neutral-600 rounded-full">
                      {job.type}
                    </span>
                  </div>
                  <p className="text-sm text-neutral-500 mt-1">{formatFileSize(job.size)}</p>
                  
                  {job.status === 'processing' && job.progress > 0 && (
                    <div className="mt-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-neutral-500">Processing...</span>
                        <span className="text-xs text-neutral-500">{Math.round(job.progress)}%</span>
                      </div>
                      <div className="w-full bg-neutral-200 rounded-full h-2">
                        <div 
                          className="bg-semantic-info h-2 rounded-full transition-all duration-300"
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {job.status === 'completed' && job.confidence && (
                    <p className="text-xs text-semantic-success mt-2">
                      Confidence: {job.confidence}%
                    </p>
                  )}

                  {job.error && (
                    <p className="text-xs text-semantic-error mt-2">
                      Error: {job.error}
                    </p>
                  )}
                </div>

                <div className="flex items-center space-x-2">
                  <div className={`p-2 rounded-full ${getStatusColor(job.status).replace('text-', 'bg-').replace('-500', '-100')}`}>
                    <StatusIcon className={`w-4 h-4 ${getStatusColor(job.status)}`} />
                  </div>
                  
                  <div className="flex space-x-1">
                    {job.status === 'processing' && (
                      <button className="p-1 text-neutral-400 hover:text-neutral-600">
                        <Pause className="w-4 h-4" />
                      </button>
                    )}
                    {job.status === 'paused' && (
                      <button className="p-1 text-neutral-400 hover:text-neutral-600">
                        <Play className="w-4 h-4" />
                      </button>
                    )}
                    <button className="p-1 text-neutral-400 hover:text-neutral-600">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </GlassCard>
    </div>
  )
}