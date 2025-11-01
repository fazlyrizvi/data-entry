import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Upload, Download, Settings, FileText, Eye, CheckCircle, AlertCircle, 
  Clock, Play, Pause, BarChart3, Search, Filter 
} from 'lucide-react';

export const OCRDocumentInterface: React.FC = () => {
  const { user } = useAuth();
  const [activeJobs, setActiveJobs] = useState(3);
  const [completedToday, setCompletedToday] = useState(247);
  const [processingAccuracy, setProcessingAccuracy] = useState(94.2);

  const GlassCard: React.FC<{ children: React.ReactNode; className?: string }> = ({ 
    children, 
    className = '' 
  }) => (
    <div className={`bg-glass-light backdrop-blur-glass border border-glass-border rounded-xl p-6 ${className}`}>
      {children}
    </div>
  );

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-neutral-900">OCR Document Processing</h1>
        <p className="text-neutral-600 mt-1">Extract text and data from images and documents using AI</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900">Active Jobs</h3>
              <p className="text-2xl font-bold text-blue-600">{activeJobs}</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900">Completed Today</h3>
              <p className="text-2xl font-bold text-green-600">{completedToday}</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-neutral-900">Accuracy</h3>
              <p className="text-2xl font-bold text-purple-600">{processingAccuracy}%</p>
            </div>
          </div>
        </GlassCard>
      </div>

      <GlassCard>
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">Upload Documents</h3>
        <div className="border-2 border-dashed border-neutral-300 rounded-lg p-8 text-center">
          <Upload className="w-12 h-12 text-neutral-400 mx-auto mb-4" />
          <p className="text-neutral-600 mb-4">Drop documents here or click to browse</p>
          <p className="text-sm text-neutral-500">Supports PDF, JPG, PNG, TIFF files up to 50MB</p>
        </div>
      </GlassCard>
    </div>
  );
};