import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  Square, 
  Loader2, 
  CheckCircle, 
  AlertCircle, 
  FileText,
  Eye,
  Download,
  Settings
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { ocrService } from '../../services/ocrService';

interface OCRProcessorProps {
  files: File[];
  selectedDataType: 'invoice' | 'receipt' | 'form' | 'document';
  onProcess: (results: any[]) => void;
  onStatusChange?: (status: 'idle' | 'processing' | 'completed' | 'error') => void;
}

interface ProcessingFile {
  file: File;
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  result?: any;
  error?: string;
}

export const OCRProcessor: React.FC<OCRProcessorProps> = ({
  files,
  selectedDataType,
  onProcess,
  onStatusChange
}) => {
  const [processingFiles, setProcessingFiles] = useState<ProcessingFile[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);

  useEffect(() => {
    if (files.length > 0) {
      const newFiles: ProcessingFile[] = files.map(file => ({
        file,
        id: `ocr_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        status: 'pending',
        progress: 0
      }));
      setProcessingFiles(newFiles);
      setCurrentFileIndex(0);
    }
  }, [files]);

  const startProcessing = async () => {
    if (isProcessing || processingFiles.length === 0) return;

    setIsProcessing(true);
    setIsPaused(false);
    onStatusChange?.('processing');

    // Initialize OCR service
    await ocrService.initialize();

    for (let i = currentFileIndex; i < processingFiles.length; i++) {
      if (isPaused) break;

      setCurrentFileIndex(i);
      
      const fileItem = processingFiles[i];
      await processFile(fileItem, i);
    }

    setIsProcessing(false);
    
    // Check if all files are completed
    const allCompleted = processingFiles.every(f => f.status === 'completed');
    const anyError = processingFiles.some(f => f.status === 'error');
    
    onStatusChange?.(anyError ? 'error' : allCompleted ? 'completed' : 'idle');

    // Cleanup
    await ocrService.terminate();

    if (allCompleted) {
      const results = processingFiles
        .filter(f => f.status === 'completed' && f.result)
        .map(f => f.result);
      onProcess(results);
    }
  };

  const processFile = async (fileItem: ProcessingFile, index: number) => {
    try {
      // Update file status to processing
      setProcessingFiles(prev => prev.map(f => 
        f.id === fileItem.id 
          ? { ...f, status: 'processing', progress: 0 }
          : f
      ));

      const result = await ocrService.extractStructuredData(
        fileItem.file,
        selectedDataType,
        (progress) => {
          setProcessingFiles(prev => prev.map(f => 
            f.id === fileItem.id 
              ? { ...f, progress: progress.progress }
              : f
          ));
        }
      );

      // Update file status to completed
      setProcessingFiles(prev => prev.map(f => 
        f.id === fileItem.id 
          ? { ...f, status: 'completed', progress: 100, result }
          : f
      ));

    } catch (error) {
      console.error(`Failed to process ${fileItem.file.name}:`, error);
      
      setProcessingFiles(prev => prev.map(f => 
        f.id === fileItem.id 
          ? { 
              ...f, 
              status: 'error', 
              error: error instanceof Error ? error.message : 'Processing failed'
            }
          : f
      ));
    }
  };

  const pauseProcessing = () => {
    setIsPaused(true);
  };

  const resumeProcessing = () => {
    setIsPaused(false);
    startProcessing();
  };

  const stopProcessing = () => {
    setIsPaused(false);
    setIsProcessing(false);
    onStatusChange?.('idle');
  };

  const clearResults = () => {
    setProcessingFiles([]);
    setCurrentFileIndex(0);
    onStatusChange?.('idle');
  };

  const getStatusColor = (status: ProcessingFile['status']) => {
    switch (status) {
      case 'processing': return 'text-blue-600 bg-blue-50';
      case 'completed': return 'text-green-600 bg-green-50';
      case 'error': return 'text-red-600 bg-red-50';
      default: return 'text-neutral-600 bg-neutral-50';
    }
  };

  const getDataTypeIcon = () => {
    switch (selectedDataType) {
      case 'invoice': return '🧾';
      case 'receipt': return '🧾';
      case 'form': return '📋';
      case 'document': return '📄';
      default: return '📄';
    }
  };

  const completedFiles = processingFiles.filter(f => f.status === 'completed');
  const errorFiles = processingFiles.filter(f => f.status === 'error');
  const processingFiles_count = processingFiles.filter(f => f.status === 'processing').length;

  return (
    <div className="space-y-6">
      {/* Processing Controls */}
      <GlassCard>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-neutral-900 flex items-center space-x-2">
              <span className="text-2xl">{getDataTypeIcon()}</span>
              <span>OCR Processing - {selectedDataType.charAt(0).toUpperCase() + selectedDataType.slice(1)}</span>
            </h3>
            <p className="text-sm text-neutral-600 mt-1">
              Extract structured data from {processingFiles.length} files
            </p>
          </div>
          
          <div className="flex space-x-3">
            {!isProcessing && processingFiles.length > 0 && (
              <button
                onClick={startProcessing}
                className="flex items-center space-x-2 px-4 py-2 bg-primary-500 text-white rounded-lg font-medium hover:bg-primary-600 transition-colors"
              >
                <Play className="w-4 h-4" />
                <span>Start Processing</span>
              </button>
            )}
            
            {isProcessing && !isPaused && (
              <button
                onClick={pauseProcessing}
                className="flex items-center space-x-2 px-4 py-2 bg-yellow-500 text-white rounded-lg font-medium hover:bg-yellow-600 transition-colors"
              >
                <Pause className="w-4 h-4" />
                <span>Pause</span>
              </button>
            )}
            
            {isProcessing && isPaused && (
              <button
                onClick={resumeProcessing}
                className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded-lg font-medium hover:bg-green-600 transition-colors"
              >
                <Play className="w-4 h-4" />
                <span>Resume</span>
              </button>
            )}
            
            {isProcessing && (
              <button
                onClick={stopProcessing}
                className="flex items-center space-x-2 px-4 py-2 bg-red-500 text-white rounded-lg font-medium hover:bg-red-600 transition-colors"
              >
                <Square className="w-4 h-4" />
                <span>Stop</span>
              </button>
            )}
            
            {(completedFiles.length > 0 || errorFiles.length > 0) && (
              <button
                onClick={clearResults}
                className="px-4 py-2 bg-neutral-500 text-white rounded-lg font-medium hover:bg-neutral-600 transition-colors"
              >
                Clear Results
              </button>
            )}
          </div>
        </div>

        {/* Progress Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-neutral-900">{processingFiles.length}</div>
            <div className="text-sm text-neutral-600">Total Files</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{processingFiles_count}</div>
            <div className="text-sm text-neutral-600">Processing</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{completedFiles.length}</div>
            <div className="text-sm text-neutral-600">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{errorFiles.length}</div>
            <div className="text-sm text-neutral-600">Errors</div>
          </div>
        </div>
      </GlassCard>

      {/* File Processing Status */}
      {processingFiles.length > 0 && (
        <GlassCard>
          <h4 className="text-lg font-semibold text-neutral-900 mb-4">Processing Status</h4>
          
          <div className="space-y-3">
            {processingFiles.map((fileItem, index) => (
              <div 
                key={fileItem.id}
                className={`
                  p-4 rounded-lg border transition-all
                  ${fileItem.status === 'processing' ? 'border-blue-200 bg-blue-50' :
                    fileItem.status === 'completed' ? 'border-green-200 bg-green-50' :
                    fileItem.status === 'error' ? 'border-red-200 bg-red-50' :
                    'border-neutral-200 bg-neutral-50'
                  }
                `}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <FileText className="w-5 h-5 text-neutral-500" />
                    <div>
                      <p className="font-medium text-neutral-900">{fileItem.file.name}</p>
                      <p className="text-sm text-neutral-600">
                        {(fileItem.file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    {fileItem.status === 'processing' && (
                      <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                    )}
                    {fileItem.status === 'completed' && (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    )}
                    {fileItem.status === 'error' && (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    )}
                    
                    <span className={`
                      px-2 py-1 text-xs rounded-full font-medium capitalize
                      ${getStatusColor(fileItem.status)}
                    `}>
                      {fileItem.status}
                    </span>
                  </div>
                </div>
                
                {fileItem.status === 'processing' && (
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-neutral-600">Progress</span>
                      <span className="text-neutral-900 font-medium">{Math.round(fileItem.progress)}%</span>
                    </div>
                    <div className="w-full bg-neutral-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${fileItem.progress}%` }}
                      />
                    </div>
                  </div>
                )}
                
                {fileItem.status === 'error' && fileItem.error && (
                  <div className="mt-3 p-2 bg-red-100 border border-red-200 rounded text-sm text-red-700">
                    Error: {fileItem.error}
                  </div>
                )}
                
                {fileItem.status === 'completed' && fileItem.result && (
                  <div className="mt-3 p-2 bg-green-100 border border-green-200 rounded">
                    <p className="text-sm text-green-700">
                      <strong>Confidence:</strong> {Math.round(fileItem.result.confidence)}% • 
                      <strong> Extracted Fields:</strong> {Object.keys(fileItem.result.extracted_fields || {}).length}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Results Summary */}
      {completedFiles.length > 0 && (
        <GlassCard>
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-semibold text-neutral-900">Processing Results</h4>
            <div className="flex space-x-2">
              <button className="flex items-center space-x-2 px-3 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors">
                <Eye className="w-4 h-4" />
                <span>View Details</span>
              </button>
              <button className="flex items-center space-x-2 px-3 py-2 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 transition-colors">
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {Math.round(completedFiles.reduce((sum, f) => sum + (f.result?.confidence || 0), 0) / completedFiles.length)}%
              </div>
              <div className="text-sm text-green-700">Average Confidence</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {completedFiles.reduce((sum, f) => sum + Object.keys(f.result?.extracted_fields || {}).length, 0)}
              </div>
              <div className="text-sm text-blue-700">Total Fields Extracted</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {completedFiles.filter(f => (f.result?.confidence || 0) > 90).length}
              </div>
              <div className="text-sm text-purple-700">High Confidence Results</div>
            </div>
          </div>
        </GlassCard>
      )}
    </div>
  );
};

export default OCRProcessor;