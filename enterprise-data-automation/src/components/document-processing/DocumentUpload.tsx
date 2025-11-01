import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  File, 
  Image, 
  FileText, 
  AlertCircle, 
  CheckCircle, 
  X,
  Loader2
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';

interface DocumentUploadProps {
  onFileSelect: (files: File[]) => void;
  acceptedFileTypes?: string[];
  maxFileSize?: number;
  maxFiles?: number;
  isProcessing?: boolean;
}

interface FilePreview {
  file: File;
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  error?: string;
  preview?: string;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onFileSelect,
  acceptedFileTypes = ['image/*', 'application/pdf'],
  maxFileSize = 10 * 1024 * 1024, // 10MB
  maxFiles = 10,
  isProcessing = false
}) => {
  const [files, setFiles] = useState<FilePreview[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    const newFiles: FilePreview[] = acceptedFiles.map(file => ({
      file,
      id: `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      status: 'pending',
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined
    }));

    const updatedFiles = [...files, ...newFiles];
    setFiles(updatedFiles);
    onFileSelect(acceptedFiles);

    // Clean up object URLs when component unmounts
    return () => {
      newFiles.forEach(file => {
        if (file.preview) {
          URL.revokeObjectURL(file.preview);
        }
      });
    };
  }, [files, onFileSelect]);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: acceptedFileTypes.reduce((acc, type) => {
      acc[type] = [];
      return acc;
    }, {} as Record<string, string[]>),
    maxSize: maxFileSize,
    maxFiles,
    disabled: isProcessing,
    noClick: false,
    noKeyboard: false
  } as any);

  const removeFile = (fileId: string) => {
    setFiles(prev => {
      const fileToRemove = prev.find(f => f.id === fileId);
      if (fileToRemove?.preview) {
        URL.revokeObjectURL(fileToRemove.preview);
      }
      return prev.filter(f => f.id !== fileId);
    });
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

  const getStatusIcon = (status: FilePreview['status']) => {
    switch (status) {
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
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
            ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
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
                {isDragActive ? 'Drop files here' : 'Upload Documents'}
              </h3>
              <p className="text-neutral-600 mb-4">
                Drag and drop files here, or click to select
              </p>
              <div className="text-sm text-neutral-500">
                <p>Supported formats: PDF, JPG, PNG, TIFF</p>
                <p>Maximum file size: {formatFileSize(maxFileSize)}</p>
                <p>Maximum files: {maxFiles}</p>
              </div>
            </div>
            
            <button 
              className="px-6 py-3 bg-primary-500 text-white rounded-lg font-medium hover:bg-primary-600 transition-colors disabled:opacity-50"
              disabled={isProcessing}
            >
              {isProcessing ? 'Processing...' : 'Select Files'}
            </button>
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

      {/* File Preview */}
      {files.length > 0 && (
        <GlassCard>
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">
            Selected Files ({files.length})
          </h3>
          
          <div className="space-y-3">
            {files.map((filePreview) => {
              const FileIcon = getFileIcon(filePreview.file);
              
              return (
                <div 
                  key={filePreview.id}
                  className="flex items-center space-x-4 p-4 bg-neutral-50 rounded-lg"
                >
                  {/* File Preview/Icon */}
                  <div className="flex-shrink-0">
                    {filePreview.preview ? (
                      <img 
                        src={filePreview.preview} 
                        alt={filePreview.file.name}
                        className="w-12 h-12 object-cover rounded-lg"
                      />
                    ) : (
                      <div className="w-12 h-12 bg-neutral-200 rounded-lg flex items-center justify-center">
                        <FileIcon className="w-6 h-6 text-neutral-500" />
                      </div>
                    )}
                  </div>

                  {/* File Info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-neutral-900 truncate">
                      {filePreview.file.name}
                    </p>
                    <p className="text-sm text-neutral-500">
                      {formatFileSize(filePreview.file.size)}
                    </p>
                  </div>

                  {/* Status */}
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(filePreview.status)}
                    {filePreview.status === 'error' && filePreview.error && (
                      <span className="text-xs text-red-600">{filePreview.error}</span>
                    )}
                  </div>

                  {/* Remove Button */}
                  <button
                    onClick={() => removeFile(filePreview.id)}
                    className="p-1 text-neutral-400 hover:text-red-500 transition-colors"
                    disabled={isProcessing}
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              );
            })}
          </div>

          {/* Progress Summary */}
          {Object.keys(uploadProgress).length > 0 && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <div className="flex items-center justify-between text-sm">
                <span className="text-blue-900">Upload Progress</span>
                <span className="text-blue-700">
                  {Object.values(uploadProgress).reduce((sum, val) => sum + val, 0)}% complete
                </span>
              </div>
              <div className="mt-2 w-full bg-blue-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ 
                    width: `${Object.values(uploadProgress).reduce((sum, val) => sum + val, 0) / files.length}%` 
                  }}
                />
              </div>
            </div>
          )}
        </GlassCard>
      )}
    </div>
  );
};

export default DocumentUpload;