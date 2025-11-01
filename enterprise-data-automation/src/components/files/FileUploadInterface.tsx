<<<<<<< HEAD
import React, { useState, useCallback, useEffect } from 'react'
=======
import React, { useState, useCallback } from 'react'
>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de
import { useDropzone } from 'react-dropzone'
import { 
  Upload, 
  File, 
<<<<<<< HEAD
=======
  Image, 
>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de
  FileText, 
  X, 
  Check, 
  AlertCircle,
  Clock,
<<<<<<< HEAD
  Download,
  BarChart3,
  Sparkles,
  Eye,
  Loader2
} from 'lucide-react'
import { GlassCard } from '../ui/GlassCard'
import { DataVisualization } from '../visualization/DataVisualization'
import { supabase } from '../../lib/supabase'
import { useAuth } from '../../contexts/AuthContext'
import toast from 'react-hot-toast'
=======
  Play,
  Pause,
  Trash2
} from 'lucide-react'
import { GlassCard } from '../ui/GlassCard'
import { formatFileSize, getStatusColor, getStatusIcon } from '../../lib/utils'
>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de

interface FileUpload {
  id: string
  name: string
  size: number
  type: string
<<<<<<< HEAD
  status: 'uploading' | 'uploaded' | 'processing' | 'completed' | 'failed'
  progress: number
  error?: string
  fileId?: string
  storageUrl?: string
  extractedData?: any
  aiAnalysis?: any
  ocrResult?: any
}

export const FileUploadInterface: React.FC = () => {
  const { user } = useAuth()
  const [uploadedFiles, setUploadedFiles] = useState<FileUpload[]>([])
  const [selectedFile, setSelectedFile] = useState<FileUpload | null>(null)
  const [processing, setProcessing] = useState(false)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      const uploadId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      
      const newFile: FileUpload = {
        id: uploadId,
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'uploading',
        progress: 0
      }

      setUploadedFiles(prev => [...prev, newFile])

      try {
        // Convert file to base64
        const reader = new FileReader()
        reader.onloadend = async () => {
          try {
            const base64Data = reader.result as string

            // Upload to Supabase via edge function
            const { data, error } = await supabase.functions.invoke('file-upload', {
              body: {
                filename: file.name,
                fileData: base64Data,
                fileType: file.type,
                fileSize: file.size,
                userId: user?.id
              }
            })

            if (error) throw error

            // Update file with upload success
            setUploadedFiles(prev => prev.map(f => 
              f.id === uploadId 
                ? { 
                    ...f, 
                    status: 'uploaded', 
                    progress: 100,
                    fileId: data.data.fileId,
                    storageUrl: data.data.storageUrl
                  }
                : f
            ))

            toast.success(`${file.name} uploaded successfully`)

            // Auto-process the file
            await processFile(uploadId, data.data.fileId, data.data.storageUrl, file.type)

          } catch (uploadError: any) {
            console.error('Upload error:', uploadError)
            setUploadedFiles(prev => prev.map(f => 
              f.id === uploadId 
                ? { ...f, status: 'failed', error: uploadError.message }
                : f
            ))
            toast.error(`Upload failed: ${uploadError.message}`)
          }
        }

        reader.onerror = () => {
          setUploadedFiles(prev => prev.map(f => 
            f.id === uploadId 
              ? { ...f, status: 'failed', error: 'File read error' }
              : f
          ))
          toast.error('Failed to read file')
        }

        reader.readAsDataURL(file)

      } catch (error: any) {
        console.error('File processing error:', error)
        setUploadedFiles(prev => prev.map(f => 
          f.id === uploadId 
            ? { ...f, status: 'failed', error: error.message }
            : f
        ))
        toast.error(`Processing failed: ${error.message}`)
      }
    }
  }, [user])

  const processFile = async (uploadId: string, fileId: string, storageUrl: string, fileType: string) => {
    setUploadedFiles(prev => prev.map(f => 
      f.id === uploadId ? { ...f, status: 'processing' } : f
    ))

    try {
      // Process based on file type
      if (fileType === 'application/pdf') {
        // OCR processing for PDFs
        const { data: ocrData, error: ocrError } = await supabase.functions.invoke('file-ocr', {
          body: { fileId, fileUrl: storageUrl }
        })

        if (ocrError) throw ocrError

        setUploadedFiles(prev => prev.map(f => 
          f.id === uploadId ? { ...f, ocrResult: ocrData.data } : f
        ))

        // Run AI analysis on extracted text
        if (ocrData.data.extractedText) {
          await runAIAnalysis(uploadId, fileId, ocrData.data.extractedText)
        }

      } else if (fileType === 'text/csv' || fileType === 'application/json' || fileType === 'text/plain') {
        // Data extraction for structured files
        const { data: processData, error: processError } = await supabase.functions.invoke('file-processor', {
          body: { fileId, fileUrl: storageUrl, fileType }
        })

        if (processError) throw processError

        setUploadedFiles(prev => prev.map(f => 
          f.id === uploadId ? { ...f, extractedData: processData.data } : f
        ))

        // Run AI analysis on text content
        if (processData.data.dataSample && processData.data.dataSample.length > 0) {
          const textContent = JSON.stringify(processData.data.dataSample.slice(0, 5))
          await runAIAnalysis(uploadId, fileId, textContent)
        }
      }

      setUploadedFiles(prev => prev.map(f => 
        f.id === uploadId ? { ...f, status: 'completed' } : f
      ))

      toast.success('File processing completed')

    } catch (error: any) {
      console.error('Processing error:', error)
      setUploadedFiles(prev => prev.map(f => 
        f.id === uploadId ? { ...f, status: 'failed', error: error.message } : f
      ))
      toast.error(`Processing failed: ${error.message}`)
    }
  }

  const runAIAnalysis = async (uploadId: string, fileId: string, text: string) => {
    try {
      const { data, error } = await supabase.functions.invoke('ai-file-analysis', {
        body: {
          fileId,
          text: text.substring(0, 1000), // Limit text length
          analysisType: 'sentiment'
        }
      })

      if (error) throw error

      setUploadedFiles(prev => prev.map(f => 
        f.id === uploadId ? { ...f, aiAnalysis: data.data } : f
      ))
    } catch (error) {
      console.error('AI analysis error:', error)
    }
  }

  const exportFile = async (file: FileUpload, format: 'csv' | 'json' | 'pdf') => {
    if (!file.fileId) return

    setProcessing(true)
    try {
      const { data, error } = await supabase.functions.invoke('file-export', {
        body: {
          fileId: file.fileId,
          exportFormat: format,
          includeAnalysis: true
        }
      })

      if (error) throw error

      // Download the file
      const blob = new Blob([data.data.content], { 
        type: format === 'csv' ? 'text/csv' : format === 'json' ? 'application/json' : 'text/plain'
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = data.data.filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast.success(`Exported as ${format.toUpperCase()}`)
    } catch (error: any) {
      toast.error(`Export failed: ${error.message}`)
    } finally {
      setProcessing(false)
    }
  }
=======
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
>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
<<<<<<< HEAD
      'text/csv': ['.csv'],
      'text/plain': ['.txt'],
      'application/json': ['.json']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: true
  } as any)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-semantic-success'
      case 'processing': case 'uploading': return 'text-semantic-info'
      case 'failed': return 'text-semantic-error'
      default: return 'text-neutral-500'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return Check
      case 'processing': case 'uploading': return Loader2
      case 'failed': return AlertCircle
      default: return Clock
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

=======
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

>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
<<<<<<< HEAD
          <h1 className="text-3xl font-bold text-neutral-900">AI-Powered File Processing</h1>
          <p className="text-neutral-600 mt-1">Upload files for instant AI analysis and data extraction</p>
        </div>
        <div className="flex space-x-3">
          <div className="px-4 py-2 bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg">
            <p className="text-xs text-neutral-500">Processed Files</p>
            <p className="text-2xl font-bold text-neutral-900">{uploadedFiles.filter(f => f.status === 'completed').length}</p>
          </div>
=======
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
>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de
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
<<<<<<< HEAD
            <div className="w-16 h-16 bg-gradient-to-br from-primary-100 to-primary-200 rounded-full flex items-center justify-center">
              <Upload className="w-8 h-8 text-primary-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900">
                {isDragActive ? 'Drop files here' : 'Upload files for AI processing'}
              </h3>
              <p className="text-sm text-neutral-500 mt-1">
                Drag and drop or click to browse
              </p>
              <p className="text-xs text-neutral-400 mt-2">
                Supported: PDF, CSV, TXT, JSON (Max 10MB)
=======
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
>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de
              </p>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <GlassCard>
<<<<<<< HEAD
          <h3 className="text-lg font-semibold text-neutral-900 mb-6">Processing Queue</h3>
          <div className="space-y-3">
            {uploadedFiles.map((file) => {
              const StatusIcon = getStatusIcon(file.status)
              return (
                <div 
                  key={file.id} 
                  className="flex items-center space-x-4 p-4 bg-neutral-50/50 rounded-lg hover:bg-neutral-100/50 transition-colors cursor-pointer"
                  onClick={() => setSelectedFile(file)}
                >
                  <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
                    <FileText className="w-5 h-5 text-neutral-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-neutral-900 truncate">{file.name}</p>
                    <p className="text-sm text-neutral-500">{formatFileSize(file.size)}</p>
                    {file.status === 'processing' && (
                      <div className="mt-2">
                        <div className="w-full bg-neutral-200 rounded-full h-2">
                          <div className="bg-semantic-info h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center space-x-3">
                    {file.status === 'completed' && (
                      <>
                        <button
                          onClick={(e) => { e.stopPropagation(); exportFile(file, 'csv') }}
                          className="p-2 text-neutral-400 hover:text-primary-600 transition-colors"
                          title="Export as CSV"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); setSelectedFile(file) }}
                          className="p-2 text-neutral-400 hover:text-primary-600 transition-colors"
                          title="View Details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </>
                    )}
                    <div className={`p-2 rounded-full ${file.status === 'processing' ? 'animate-spin' : ''}`}>
                      <StatusIcon className={`w-4 h-4 ${getStatusColor(file.status)}`} />
                    </div>
                  </div>
=======
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
>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de
                </div>
              )
            })}
          </div>
        </GlassCard>
      )}

<<<<<<< HEAD
      {/* File Details Modal */}
      {selectedFile && (
        <GlassCard>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-neutral-900">File Analysis Results</h3>
            <button
              onClick={() => setSelectedFile(null)}
              className="p-1 text-neutral-400 hover:text-neutral-600"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-6">
            {/* File Info */}
            <div>
              <h4 className="font-medium text-neutral-700 mb-2">File Information</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-neutral-500">Filename</p>
                  <p className="font-medium text-neutral-900">{selectedFile.name}</p>
                </div>
                <div>
                  <p className="text-neutral-500">Size</p>
                  <p className="font-medium text-neutral-900">{formatFileSize(selectedFile.size)}</p>
                </div>
                <div>
                  <p className="text-neutral-500">Type</p>
                  <p className="font-medium text-neutral-900">{selectedFile.type}</p>
                </div>
                <div>
                  <p className="text-neutral-500">Status</p>
                  <p className={`font-medium ${getStatusColor(selectedFile.status)}`}>
                    {selectedFile.status}
                  </p>
                </div>
              </div>
            </div>

            {/* AI Analysis */}
            {selectedFile.aiAnalysis && (
              <div>
                <h4 className="font-medium text-neutral-700 mb-2 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary-500" />
                  AI Analysis
                </h4>
                <div className="p-4 bg-primary-50/50 rounded-lg">
                  <pre className="text-sm text-neutral-700 whitespace-pre-wrap">
                    {JSON.stringify(selectedFile.aiAnalysis.result, null, 2)}
                  </pre>
                  {selectedFile.aiAnalysis.isDemo && (
                    <p className="text-xs text-semantic-warning mt-2">
                      Demo mode - Add Hugging Face API key for real AI analysis
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Data Visualizations */}
            {selectedFile.extractedData && selectedFile.extractedData.dataSample && (
              <DataVisualization 
                data={selectedFile.extractedData.dataSample}
                dataSummary={selectedFile.extractedData.summary}
              />
            )}

            {/* Extracted Data */}
            {selectedFile.extractedData && (
              <div>
                <h4 className="font-medium text-neutral-700 mb-2 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-semantic-success" />
                  Extracted Data ({selectedFile.extractedData.rowCount} rows)
                </h4>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="border-b border-neutral-200">
                        {selectedFile.extractedData.dataSample && 
                         Object.keys(selectedFile.extractedData.dataSample[0] || {}).map((key) => (
                          <th key={key} className="px-4 py-2 text-left font-medium text-neutral-700">
                            {key}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {selectedFile.extractedData.dataSample?.slice(0, 10).map((row: any, idx: number) => (
                        <tr key={idx} className="border-b border-neutral-100">
                          {Object.values(row).map((value: any, vidx: number) => (
                            <td key={vidx} className="px-4 py-2 text-neutral-600">
                              {String(value)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* OCR Result */}
            {selectedFile.ocrResult && (
              <div>
                <h4 className="font-medium text-neutral-700 mb-2">OCR Extracted Text</h4>
                <div className="p-4 bg-neutral-50 rounded-lg max-h-96 overflow-y-auto">
                  <p className="text-sm text-neutral-700 whitespace-pre-wrap">
                    {selectedFile.ocrResult.extractedText}
                  </p>
                  {selectedFile.ocrResult.isDemo && (
                    <p className="text-xs text-semantic-warning mt-2">
                      Demo mode - Add Azure Computer Vision key for real OCR
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Export Options */}
            <div className="flex gap-2 pt-4 border-t border-neutral-200">
              <button
                onClick={() => exportFile(selectedFile, 'csv')}
                disabled={processing}
                className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors disabled:opacity-50"
              >
                Export CSV
              </button>
              <button
                onClick={() => exportFile(selectedFile, 'json')}
                disabled={processing}
                className="px-4 py-2 bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg text-sm font-medium text-neutral-700 hover:bg-glass-lightHover transition-colors disabled:opacity-50"
              >
                Export JSON
              </button>
              <button
                onClick={() => exportFile(selectedFile, 'pdf')}
                disabled={processing}
                className="px-4 py-2 bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg text-sm font-medium text-neutral-700 hover:bg-glass-lightHover transition-colors disabled:opacity-50"
              >
                Export Report
              </button>
            </div>
          </div>
        </GlassCard>
      )}
    </div>
  )
}
=======
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
>>>>>>> 2a7bfaf2bdc4a4cb016cc420a3663eea37ba32de
