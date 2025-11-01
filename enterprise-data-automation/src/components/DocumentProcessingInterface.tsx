import React, { useState } from 'react';
import { 
  FileText, 
  Upload, 
  Brain, 
  BarChart3,
  ArrowRight,
  Settings,
  Play,
  Eye,
  Download
} from 'lucide-react';
import { GlassCard } from './ui/GlassCard';
import DocumentUpload from './document-processing/DocumentUpload';
import OCRProcessor from './document-processing/OCRProcessor';
import TextExtractor from './document-processing/TextExtractor';
import { useAuth } from '../contexts/AuthContext';

interface ProcessingStep {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<any>;
  completed: boolean;
}

export const DocumentProcessingInterface: React.FC = () => {
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState<'upload' | 'process' | 'extract' | 'results'>('upload');
  const [files, setFiles] = useState<File[]>([]);
  const [processingResults, setProcessingResults] = useState<any[]>([]);
  const [selectedDataType, setSelectedDataType] = useState<'invoice' | 'receipt' | 'form' | 'document'>('invoice');
  const [processingStatus, setProcessingStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('idle');

  const steps: ProcessingStep[] = [
    {
      id: 'upload',
      name: 'Upload Documents',
      description: 'Select and upload documents for processing',
      icon: Upload,
      completed: files.length > 0
    },
    {
      id: 'process',
      name: 'OCR Processing',
      description: 'Extract text and data using OCR technology',
      icon: Brain,
      completed: processingResults.length > 0
    },
    {
      id: 'extract',
      name: 'Data Extraction',
      description: 'Review and edit extracted information',
      icon: BarChart3,
      completed: currentStep === 'results'
    },
    {
      id: 'results',
      name: 'Results & Export',
      description: 'Review results and export to your systems',
      icon: FileText,
      completed: false
    }
  ];

  const handleFileSelect = (selectedFiles: File[]) => {
    setFiles(selectedFiles);
    if (selectedFiles.length > 0 && currentStep === 'upload') {
      setCurrentStep('process');
    }
  };

  const handleProcessingComplete = (results: any[]) => {
    setProcessingResults(results);
    setProcessingStatus('completed');
    setCurrentStep('extract');
  };

  const handleDataUpdate = (updatedData: any[]) => {
    setProcessingResults(updatedData);
  };

  const handleProcessingStatusChange = (status: 'idle' | 'processing' | 'completed' | 'error') => {
    setProcessingStatus(status);
  };

  const getStepStatus = (stepId: string) => {
    const stepIndex = steps.findIndex(s => s.id === stepId);
    const currentIndex = steps.findIndex(s => s.id === currentStep);
    
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'current';
    return 'pending';
  };

  const getStepIcon = (step: ProcessingStep, status: string) => {
    const Icon = step.icon;
    
    if (status === 'completed') {
      return <Icon className="w-5 h-5 text-green-600" />;
    } else if (status === 'current') {
      return <Icon className="w-5 h-5 text-primary-600" />;
    } else {
      return <Icon className="w-5 h-5 text-neutral-400" />;
    }
  };

  const currentStepIndex = steps.findIndex(s => s.id === currentStep);
  const currentStepData = steps[currentStepIndex];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900 flex items-center space-x-2">
            <FileText className="w-8 h-8 text-blue-600" />
            <span>Document Processing</span>
          </h1>
          <p className="text-neutral-600 mt-1">AI-powered document analysis and data extraction</p>
        </div>
        
        <div className="flex space-x-3">
          <button className="flex items-center space-x-2 px-4 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors">
            <Settings className="w-4 h-4" />
            <span>Settings</span>
          </button>
          
          {currentStep !== 'upload' && (
            <button
              onClick={() => setCurrentStep('upload')}
              className="flex items-center space-x-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
            >
              <Upload className="w-4 h-4" />
              <span>New Batch</span>
            </button>
          )}
        </div>
      </div>

      {/* Progress Steps */}
      <GlassCard>
        <div className="flex items-center justify-between">
          {steps.map((step, index) => {
            const status = getStepStatus(step.id);
            
            return (
              <div key={step.id} className="flex items-center">
                <div className={`
                  flex items-center justify-center w-12 h-12 rounded-full border-2 transition-colors
                  ${status === 'completed' ? 'border-green-500 bg-green-50' :
                    status === 'current' ? 'border-primary-500 bg-primary-50' : 'border-neutral-300 bg-neutral-50'}
                `}>
                  {getStepIcon(step, status)}
                </div>
                <div className="ml-3">
                  <p className={`text-sm font-medium ${
                    status === 'current' ? 'text-primary-600' :
                    status === 'completed' ? 'text-green-600' : 'text-neutral-600'
                  }`}>
                    {step.name}
                  </p>
                  <p className="text-xs text-neutral-500">{step.description}</p>
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-16 h-px mx-4 ${
                    status === 'completed' ? 'bg-green-300' : 'bg-neutral-300'
                  }`} />
                )}
              </div>
            );
          })}
        </div>
      </GlassCard>

      {/* Current Step Content */}
      <div className="min-h-96">
        {currentStep === 'upload' && (
          <div className="space-y-6">
            {/* Document Type Selection */}
            <GlassCard>
              <h3 className="text-lg font-semibold text-neutral-900 mb-4">Document Type</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { id: 'invoice', name: 'Invoice', icon: '🧾', description: 'Bills and invoices' },
                  { id: 'receipt', name: 'Receipt', icon: '🧾', description: 'Purchase receipts' },
                  { id: 'form', name: 'Form', icon: '📋', description: 'Structured forms' },
                  { id: 'document', name: 'Document', icon: '📄', description: 'General documents' }
                ].map((type) => (
                  <button
                    key={type.id}
                    onClick={() => setSelectedDataType(type.id as any)}
                    className={`
                      p-4 border-2 rounded-lg text-left transition-all
                      ${selectedDataType === type.id 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-neutral-200 hover:border-neutral-300'
                      }
                    `}
                  >
                    <div className="text-2xl mb-2">{type.icon}</div>
                    <h4 className="font-medium text-neutral-900">{type.name}</h4>
                    <p className="text-sm text-neutral-600">{type.description}</p>
                  </button>
                ))}
              </div>
            </GlassCard>

            {/* Upload Component */}
            <DocumentUpload
              onFileSelect={handleFileSelect}
              acceptedFileTypes={['image/*', 'application/pdf']}
              maxFileSize={25 * 1024 * 1024} // 25MB
              maxFiles={50}
              isProcessing={false}
            />

            {/* Next Step Button */}
            {files.length > 0 && (
              <div className="flex justify-center">
                <button
                  onClick={() => setCurrentStep('process')}
                  className="flex items-center space-x-2 px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                >
                  <span>Continue to OCR Processing</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        )}

        {currentStep === 'process' && (
          <div className="space-y-6">
            <OCRProcessor
              files={files}
              selectedDataType={selectedDataType}
              onProcess={handleProcessingComplete}
              onStatusChange={handleProcessingStatusChange}
            />
          </div>
        )}

        {currentStep === 'extract' && (
          <div className="space-y-6">
            <TextExtractor
              results={processingResults}
              onDataUpdate={handleDataUpdate}
            />
          </div>
        )}

        {currentStep === 'results' && (
          <div className="space-y-6">
            <GlassCard>
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <FileText className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-2xl font-bold text-neutral-900 mb-2">Processing Complete!</h3>
                <p className="text-neutral-600 mb-6">
                  Successfully processed {files.length} documents with {processingResults.length} results
                </p>
                
                <div className="flex space-x-4 justify-center">
                  <button className="flex items-center space-x-2 px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors">
                    <Eye className="w-4 h-4" />
                    <span>View Detailed Results</span>
                  </button>
                  <button className="flex items-center space-x-2 px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors">
                    <Download className="w-4 h-4" />
                    <span>Export Results</span>
                  </button>
                  <button
                    onClick={() => setCurrentStep('upload')}
                    className="flex items-center space-x-2 px-6 py-3 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors"
                  >
                    <Play className="w-4 h-4" />
                    <span>Process More</span>
                  </button>
                </div>
              </div>
            </GlassCard>
          </div>
        )}
      </div>

      {/* Step Navigation */}
      {currentStep !== 'results' && (
        <div className="flex justify-between">
          <button
            onClick={() => {
              const currentIndex = steps.findIndex(s => s.id === currentStep);
              if (currentIndex > 0) {
                setCurrentStep(steps[currentIndex - 1].id as any);
              }
            }}
            disabled={currentStepIndex === 0}
            className="px-6 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Previous Step
          </button>

          <button
            onClick={() => {
              const currentIndex = steps.findIndex(s => s.id === currentStep);
              if (currentIndex < steps.length - 1) {
                setCurrentStep(steps[currentIndex + 1].id as any);
              }
            }}
            disabled={
              (currentStep === 'upload' && files.length === 0) ||
              (currentStep === 'process' && processingStatus === 'idle') ||
              (currentStep === 'extract' && processingResults.length === 0)
            }
            className="flex items-center space-x-2 px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <span>Next Step</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};

export default DocumentProcessingInterface;