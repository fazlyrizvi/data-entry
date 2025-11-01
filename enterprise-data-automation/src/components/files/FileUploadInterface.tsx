import React, { useState, useRef } from 'react'
import { Upload, File, CheckCircle, AlertCircle, X, Eye, Download } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  status: 'uploading' | 'processing' | 'completed' | 'error'
  progress: number
  uploadedAt: Date
  result?: any
}

export const FileUploadInterface: React.FC = () => {
  const { user } = useAuth()
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState<UploadedFile | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const droppedFiles = Array.from(e.dataTransfer.files)
    handleFileUpload(droppedFiles)
  }

  const handleFileSelect = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      handleFileUpload(selectedFiles)
    }
  }

  const handleFileUpload = (fileList: File[]) => {
    fileList.forEach(file => {
      const newFile: UploadedFile = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'uploading',
        progress: 0,
        uploadedAt: new Date()
      }

      setFiles(prev => [newFile, ...prev])

      // Simulate upload progress
      simulateUpload(newFile.id)
    })
  }

  const simulateUpload = (fileId: string) => {
    let progress = 0
    const interval = setInterval(() => {
      progress += Math.random() * 30
      if (progress >= 100) {
        progress = 100
        clearInterval(interval)
        
        setFiles(prev => prev.map(file => 
          file.id === fileId 
            ? { ...file, status: 'processing', progress: 100 }
            : file
        ))

        // Simulate processing
        setTimeout(() => {
          setFiles(prev => prev.map(file => 
            file.id === fileId 
              ? { 
                  ...file, 
                  status: 'completed', 
                  result: {
                    extractedData: 'Sample extracted data',
                    confidence: Math.floor(Math.random() * 20) + 80,
                    processingTime: (Math.random() * 10 + 2).toFixed(1)
                  }
                }
              : file
          ))
        }, 2000 + Math.random() * 3000)
      } else {
        setFiles(prev => prev.map(file => 
          file.id === fileId 
            ? { ...file, progress }
            : file
        ))
      }
    }, 200)
  }

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(file => file.id !== fileId))
    if (selectedFile?.id === fileId) {
      setSelectedFile(null)
    }
  }

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      case 'processing':
        return <div className="w-4 h-4 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin" />
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const GlassCard: React.FC<{ children: React.ReactNode; className?: string }> = ({ 
    children, 
    className = '' 
  }) => (
    <div className={`bg-glass-light backdrop-blur-glass border border-glass-border rounded-xl p-6 ${className}`}>
      {children}
    </div>
  )

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-neutral-900">AI-Powered File Processing</h1>
        <p className="text-neutral-600 mt-1">Upload files for instant AI analysis and data extraction</p>
      </div>

      {/* Upload Area */}
      <GlassCard>
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragOver 
              ? 'border-primary-400 bg-primary-50' 
              : 'border-neutral-300 hover:border-primary-300'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.csv,.xlsx"
            onChange={handleFileChange}
            className="hidden"
          />
          
          <div className="flex flex-col items-center space-y-4">
            <div className={`w-16 h-16 rounded-full flex items-center justify-center transition-colors ${
              isDragOver 
                ? 'bg-primary-100' 
                : 'bg-gradient-to-br from-primary-100 to-primary-200'
            }`}>
              <Upload className="w-8 h-8 text-primary-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                {isDragOver ? 'Drop files here' : 'Drag & drop files or click to browse'}
              </h3>
              <p className="text-neutral-600 mb-4">
                Support for PDF, DOC, TXT, images, CSV, and Excel files
              </p>
              <button
                onClick={handleFileSelect}
                className="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
              >
                Select Files
              </button>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* File List */}
      {files.length > 0 && (
        <GlassCard>
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">Processing Queue</h3>
          <div className="space-y-3">
            {files.map(file => (
              <div key={file.id} className="flex items-center justify-between p-4 bg-white/50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <File className="w-5 h-5 text-neutral-500" />
                  <div>
                    <p className="font-medium text-neutral-900">{file.name}</p>
                    <p className="text-sm text-neutral-500">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  {getStatusIcon(file.status)}
                  {file.status === 'uploading' && (
                    <div className="w-24 bg-neutral-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                  )}
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setSelectedFile(file)}
                      className="p-1 text-neutral-500 hover:text-neutral-700"
                      disabled={file.status === 'uploading'}
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => removeFile(file.id)}
                      className="p-1 text-neutral-500 hover:text-red-500"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* File Details Modal */}
      {selectedFile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-neutral-900">File Details</h3>
              <button
                onClick={() => setSelectedFile(null)}
                className="text-neutral-500 hover:text-neutral-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700">File Name</label>
                <p className="text-neutral-900">{selectedFile.name}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-neutral-700">Status</label>
                <p className="text-neutral-900 capitalize">{selectedFile.status}</p>
              </div>
              
              {selectedFile.result && (
                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-2">Extracted Data</label>
                  <div className="bg-neutral-50 rounded-lg p-4">
                    <pre className="text-sm text-neutral-700 whitespace-pre-wrap">
                      {JSON.stringify(selectedFile.result, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
              
              {selectedFile.status === 'completed' && (
                <div className="flex space-x-3">
                  <button className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600">
                    <Download className="w-4 h-4" />
                    <span>Download Result</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}