import React, { useState } from 'react';
import { 
  FileText, 
  Edit3, 
  Save, 
  X, 
  CheckCircle, 
  AlertTriangle,
  Copy,
  Download,
  Eye,
  Filter,
  Search
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';

interface ExtractedField {
  key: string;
  value: string;
  confidence: number;
  requires_review: boolean;
  suggestions?: string[];
  extracted_from: 'ocr' | 'manual' | 'ai_suggestion';
}

interface ExtractedData {
  file_name: string;
  file_type: string;
  confidence: number;
  raw_text: string;
  extracted_fields: ExtractedField[];
  processing_time: number;
}

interface TextExtractorProps {
  results: ExtractedData[];
  onDataUpdate?: (updatedData: ExtractedData[]) => void;
}

export const TextExtractor: React.FC<TextExtractorProps> = ({
  results,
  onDataUpdate
}) => {
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [editingField, setEditingField] = useState<string>('');
  const [editValue, setEditValue] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'confidence_high' | 'confidence_medium' | 'confidence_low' | 'requires_review'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'fields' | 'raw'>('fields');

  const selectedData = results.find(r => r.file_name === selectedFile);

  const handleFieldEdit = (fieldKey: string, currentValue: string) => {
    setEditingField(fieldKey);
    setEditValue(currentValue);
  };

  const handleFieldSave = () => {
    if (!selectedData || !editingField) return;

    // Update the field value
    const updatedData = results.map(data => {
      if (data.file_name === selectedFile) {
        return {
          ...data,
          extracted_fields: data.extracted_fields.map(field => 
            field.key === editingField 
              ? { ...field, value: editValue, extracted_from: 'manual' as const }
              : field
          )
        };
      }
      return data;
    });

    onDataUpdate?.(updatedData);
    setEditingField('');
    setEditValue('');
  };

  const handleFieldCancel = () => {
    setEditingField('');
    setEditValue('');
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const exportData = (format: 'json' | 'csv' | 'excel') => {
    if (!selectedData) return;

    let content = '';
    let filename = '';
    let mimeType = '';

    switch (format) {
      case 'json':
        content = JSON.stringify(selectedData, null, 2);
        filename = `${selectedData.file_name.split('.')[0]}_extracted.json`;
        mimeType = 'application/json';
        break;
      
      case 'csv':
        const headers = selectedData.extracted_fields.map(f => f.key);
        const values = selectedData.extracted_fields.map(f => f.value);
        content = [headers.join(','), values.map(v => `"${v}"`).join(',')].join('\n');
        filename = `${selectedData.file_name.split('.')[0]}_extracted.csv`;
        mimeType = 'text/csv';
        break;
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getFilteredFields = () => {
    if (!selectedData) return [];

    let filtered = selectedData.extracted_fields;

    // Apply filter
    switch (filterType) {
      case 'confidence_high':
        filtered = filtered.filter(f => f.confidence >= 90);
        break;
      case 'confidence_medium':
        filtered = filtered.filter(f => f.confidence >= 70 && f.confidence < 90);
        break;
      case 'confidence_low':
        filtered = filtered.filter(f => f.confidence < 70);
        break;
      case 'requires_review':
        filtered = filtered.filter(f => f.requires_review);
        break;
    }

    // Apply search
    if (searchTerm) {
      filtered = filtered.filter(f => 
        f.key.toLowerCase().includes(searchTerm.toLowerCase()) ||
        f.value.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return filtered;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'text-green-600 bg-green-50';
    if (confidence >= 70) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getConfidenceIcon = (confidence: number) => {
    if (confidence >= 90) return CheckCircle;
    if (confidence >= 70) return AlertTriangle;
    return X;
  };

  const copyAllFields = () => {
    if (!selectedData) return;

    const formattedData = selectedData.extracted_fields
      .map(f => `${f.key}: ${f.value}`)
      .join('\n');
    
    copyToClipboard(formattedData);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-neutral-900">Extracted Text & Data</h2>
          <p className="text-neutral-600 mt-1">Review and edit extracted information</p>
        </div>
        
        <div className="flex space-x-3">
          {selectedData && (
            <>
              <button
                onClick={copyAllFields}
                className="flex items-center space-x-2 px-3 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors"
              >
                <Copy className="w-4 h-4" />
                <span>Copy All</span>
              </button>
              <div className="relative group">
                <button className="flex items-center space-x-2 px-3 py-2 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 transition-colors">
                  <Download className="w-4 h-4" />
                  <span>Export</span>
                </button>
                <div className="absolute right-0 top-full mt-1 bg-white border border-neutral-200 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                  <button
                    onClick={() => exportData('json')}
                    className="block w-full text-left px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50"
                  >
                    Export as JSON
                  </button>
                  <button
                    onClick={() => exportData('csv')}
                    className="block w-full text-left px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50"
                  >
                    Export as CSV
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* File Selector */}
      <GlassCard>
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">Select File</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {results.map((result) => (
            <button
              key={result.file_name}
              onClick={() => setSelectedFile(result.file_name)}
              className={`
                p-4 text-left rounded-lg border transition-all
                ${selectedFile === result.file_name 
                  ? 'border-primary-500 bg-primary-50' 
                  : 'border-neutral-200 hover:border-neutral-300 hover:bg-neutral-50'
                }
              `}
            >
              <div className="flex items-center space-x-3">
                <FileText className="w-5 h-5 text-neutral-500" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-neutral-900 truncate">
                    {result.file_name}
                  </p>
                  <p className="text-sm text-neutral-500">
                    {Math.round(result.confidence)}% confidence • {result.extracted_fields.length} fields
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </GlassCard>

      {/* Content */}
      {selectedData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls & Filters */}
          <div className="lg:col-span-1">
            <GlassCard>
              <h4 className="text-lg font-semibold text-neutral-900 mb-4">Controls</h4>
              
              {/* View Mode */}
              <div className="mb-4">
                <label className="text-sm font-medium text-neutral-700 block mb-2">View Mode</label>
                <div className="flex rounded-lg border border-neutral-200 overflow-hidden">
                  <button
                    onClick={() => setViewMode('fields')}
                    className={`flex-1 px-3 py-2 text-sm font-medium ${
                      viewMode === 'fields' 
                        ? 'bg-primary-500 text-white' 
                        : 'bg-white text-neutral-700 hover:bg-neutral-50'
                    }`}
                  >
                    Fields
                  </button>
                  <button
                    onClick={() => setViewMode('raw')}
                    className={`flex-1 px-3 py-2 text-sm font-medium ${
                      viewMode === 'raw' 
                        ? 'bg-primary-500 text-white' 
                        : 'bg-white text-neutral-700 hover:bg-neutral-50'
                    }`}
                  >
                    Raw Text
                  </button>
                </div>
              </div>

              {/* Filters */}
              {viewMode === 'fields' && (
                <>
                  <div className="mb-4">
                    <label className="text-sm font-medium text-neutral-700 block mb-2">Filter</label>
                    <select
                      value={filterType}
                      onChange={(e) => setFilterType(e.target.value as any)}
                      className="w-full px-3 py-2 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                    >
                      <option value="all">All Fields</option>
                      <option value="confidence_high">High Confidence (90%+)</option>
                      <option value="confidence_medium">Medium Confidence (70-89%)</option>
                      <option value="confidence_low">Low Confidence (&lt;70%)</option>
                      <option value="requires_review">Requires Review</option>
                    </select>
                  </div>

                  <div className="mb-4">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400 w-4 h-4" />
                      <input
                        type="text"
                        placeholder="Search fields..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-3 py-2 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* File Info */}
              <div className="border-t border-neutral-200 pt-4">
                <h5 className="font-medium text-neutral-900 mb-2">File Info</h5>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Type:</span>
                    <span className="font-medium">{selectedData.file_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Confidence:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(selectedData.confidence)}`}>
                      {Math.round(selectedData.confidence)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Processing Time:</span>
                    <span className="font-medium">{selectedData.processing_time}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-600">Fields:</span>
                    <span className="font-medium">{selectedData.extracted_fields.length}</span>
                  </div>
                </div>
              </div>
            </GlassCard>
          </div>

          {/* Content Area */}
          <div className="lg:col-span-2">
            <GlassCard>
              {viewMode === 'fields' ? (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-lg font-semibold text-neutral-900">
                      Extracted Fields ({getFilteredFields().length})
                    </h4>
                    <button className="flex items-center space-x-2 px-3 py-1 text-sm text-neutral-600 hover:text-neutral-900">
                      <Eye className="w-4 h-4" />
                      <span>View in Table</span>
                    </button>
                  </div>

                  <div className="space-y-3">
                    {getFilteredFields().map((field) => {
                      const isEditing = editingField === field.key;
                      const ConfidenceIcon = getConfidenceIcon(field.confidence);
                      
                      return (
                        <div key={field.key} className="p-4 bg-neutral-50 rounded-lg">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              <span className="font-medium text-neutral-900">{field.key}</span>
                              <span className={`px-2 py-1 rounded-full text-xs flex items-center space-x-1 ${getConfidenceColor(field.confidence)}`}>
                                <ConfidenceIcon className="w-3 h-3" />
                                <span>{Math.round(field.confidence)}%</span>
                              </span>
                              {field.requires_review && (
                                <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-medium">
                                  Review Required
                                </span>
                              )}
                              <span className="px-2 py-1 bg-neutral-100 text-neutral-600 rounded-full text-xs">
                                {field.extracted_from}
                              </span>
                            </div>
                            
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => copyToClipboard(field.value)}
                                className="p-1 text-neutral-400 hover:text-blue-500 transition-colors"
                              >
                                <Copy className="w-4 h-4" />
                              </button>
                              
                              {isEditing ? (
                                <>
                                  <button
                                    onClick={handleFieldSave}
                                    className="p-1 text-green-600 hover:text-green-700 transition-colors"
                                  >
                                    <Save className="w-4 h-4" />
                                  </button>
                                  <button
                                    onClick={handleFieldCancel}
                                    className="p-1 text-red-600 hover:text-red-700 transition-colors"
                                  >
                                    <X className="w-4 h-4" />
                                  </button>
                                </>
                              ) : (
                                <button
                                  onClick={() => handleFieldEdit(field.key, field.value)}
                                  className="p-1 text-neutral-400 hover:text-blue-500 transition-colors"
                                >
                                  <Edit3 className="w-4 h-4" />
                                </button>
                              )}
                            </div>
                          </div>

                          {isEditing ? (
                            <input
                              type="text"
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                              className="w-full px-3 py-2 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                            />
                          ) : (
                            <p className="text-neutral-900 bg-white px-3 py-2 rounded border">
                              {field.value || 'No value extracted'}
                            </p>
                          )}

                          {field.suggestions && field.suggestions.length > 0 && (
                            <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded">
                              <p className="text-xs text-blue-700 mb-1">Suggestions:</p>
                              {field.suggestions.map((suggestion, index) => (
                                <p key={index} className="text-sm text-blue-800">{suggestion}</p>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {getFilteredFields().length === 0 && (
                    <div className="text-center py-8">
                      <FileText className="w-12 h-12 text-neutral-300 mx-auto mb-3" />
                      <p className="text-neutral-600">No fields match your current filter</p>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-lg font-semibold text-neutral-900">Raw Extracted Text</h4>
                    <button
                      onClick={() => copyToClipboard(selectedData.raw_text)}
                      className="flex items-center space-x-2 px-3 py-1 text-sm text-neutral-600 hover:text-neutral-900"
                    >
                      <Copy className="w-4 h-4" />
                      <span>Copy</span>
                    </button>
                  </div>
                  
                  <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-4">
                    <pre className="text-sm text-neutral-800 whitespace-pre-wrap font-mono">
                      {selectedData.raw_text || 'No text extracted'}
                    </pre>
                  </div>
                </div>
              )}
            </GlassCard>
          </div>
        </div>
      )}

      {!selectedFile && (
        <GlassCard>
          <div className="text-center py-12">
            <FileText className="w-16 h-16 text-neutral-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-neutral-900 mb-2">
              Select a File to Review
            </h3>
            <p className="text-neutral-600">
              Choose a file from the list above to view extracted text and data
            </p>
          </div>
        </GlassCard>
      )}
    </div>
  );
};

export default TextExtractor;