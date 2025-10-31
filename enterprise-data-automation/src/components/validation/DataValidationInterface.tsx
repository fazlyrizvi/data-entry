import React, { useState } from 'react'
import { 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Edit3, 
  Save, 
  X, 
  Eye, 
  Download,
  Filter,
  Search
} from 'lucide-react'
import { GlassCard } from '../ui/GlassCard'
import { formatFileSize } from '../../lib/utils'

interface ValidationIssue {
  id: string
  field_name: string
  detected_value: string
  suggested_value?: string
  confidence: number
  severity: 'success' | 'warning' | 'error'
  requires_manual_review: boolean
  job_id: string
  file_name: string
}

interface ValidationResult {
  id: string
  job_id: string
  file_name: string
  total_fields: number
  valid_fields: number
  warnings: number
  errors: number
  confidence_score: number
  processed_at: string
  issues: ValidationIssue[]
}

export const DataValidationInterface: React.FC = () => {
  const [selectedJob, setSelectedJob] = useState<string | null>(null)
  const [editingField, setEditingField] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const [filterSeverity, setFilterSeverity] = useState<'all' | 'error' | 'warning'>('all')
  const [searchTerm, setSearchTerm] = useState('')

  const [validationResults] = useState<ValidationResult[]>([
    {
      id: '1',
      job_id: 'job_123',
      file_name: 'Q4_Invoice_Batch_001.pdf',
      total_fields: 145,
      valid_fields: 138,
      warnings: 4,
      errors: 3,
      confidence_score: 95.2,
      processed_at: '2025-10-31T15:30:00Z',
      issues: [
        {
          id: 'issue_1',
          field_name: 'Invoice Number',
          detected_value: 'INV-2024-Q4-00',
          suggested_value: 'INV-2024-Q4-001',
          confidence: 87.5,
          severity: 'warning',
          requires_manual_review: false,
          job_id: 'job_123',
          file_name: 'Q4_Invoice_Batch_001.pdf'
        },
        {
          id: 'issue_2',
          field_name: 'Total Amount',
          detected_value: '$1,234.567',
          suggested_value: '$1,234.56',
          confidence: 92.1,
          severity: 'warning',
          requires_manual_review: false,
          job_id: 'job_123',
          file_name: 'Q4_Invoice_Batch_001.pdf'
        },
        {
          id: 'issue_3',
          field_name: 'Customer Email',
          detected_value: 'invalid-email',
          confidence: 45.2,
          severity: 'error',
          requires_manual_review: true,
          job_id: 'job_123',
          file_name: 'Q4_Invoice_Batch_001.pdf'
        }
      ]
    },
    {
      id: '2',
      job_id: 'job_124',
      file_name: 'Employee_Records_2024.csv',
      total_fields: 2847,
      valid_fields: 2839,
      warnings: 6,
      errors: 2,
      confidence_score: 97.8,
      processed_at: '2025-10-31T14:45:00Z',
      issues: [
        {
          id: 'issue_4',
          field_name: 'Employee ID',
          detected_value: 'EMP00123',
          suggested_value: 'EMP-00123',
          confidence: 89.3,
          severity: 'warning',
          requires_manual_review: false,
          job_id: 'job_124',
          file_name: 'Employee_Records_2024.csv'
        },
        {
          id: 'issue_5',
          field_name: 'Phone Number',
          detected_value: '+1234567890',
          confidence: 78.9,
          severity: 'warning',
          requires_manual_review: false,
          job_id: 'job_124',
          file_name: 'Employee_Records_2024.csv'
        }
      ]
    }
  ])

  const filteredIssues = validationResults
    .find(result => result.id === selectedJob)?.issues
    ?.filter(issue => {
      if (filterSeverity !== 'all' && issue.severity !== filterSeverity) return false
      if (searchTerm && !issue.field_name.toLowerCase().includes(searchTerm.toLowerCase())) return false
      return true
    }) || []

  const handleEditStart = (issue: ValidationIssue) => {
    setEditingField(issue.id)
    setEditValue(issue.detected_value)
  }

  const handleEditSave = (issueId: string) => {
    // Here you would typically update the validation result
    console.log('Saving edit:', issueId, editValue)
    setEditingField(null)
    setEditValue('')
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'success': return CheckCircle
      case 'warning': return AlertTriangle
      case 'error': return XCircle
      default: return CheckCircle
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'success': return 'text-semantic-success bg-semantic-success/10'
      case 'warning': return 'text-semantic-warning bg-semantic-warning/10'
      case 'error': return 'text-semantic-error bg-semantic-error/10'
      default: return 'text-neutral-500 bg-neutral-100'
    }
  }

  const selectedResult = validationResults.find(r => r.id === selectedJob)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Data Validation</h1>
          <p className="text-neutral-600 mt-1">Review and correct automated data extraction results</p>
        </div>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg text-sm font-medium text-neutral-700 hover:bg-glass-lightHover transition-colors">
            Batch Review
          </button>
          <button className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors">
            Export Results
          </button>
        </div>
      </div>

      {/* Validation Results Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-semantic-info/10 rounded-lg flex items-center justify-center">
              <Eye className="w-5 h-5 text-semantic-info" />
            </div>
            <div>
              <p className="text-sm text-neutral-500">Total Files</p>
              <p className="text-2xl font-bold text-neutral-900">247</p>
            </div>
          </div>
        </GlassCard>
        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-semantic-success/10 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-semantic-success" />
            </div>
            <div>
              <p className="text-sm text-neutral-500">Validation Rate</p>
              <p className="text-2xl font-bold text-neutral-900">94.2%</p>
            </div>
          </div>
        </GlassCard>
        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-semantic-warning/10 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-semantic-warning" />
            </div>
            <div>
              <p className="text-sm text-neutral-500">Pending Review</p>
              <p className="text-2xl font-bold text-neutral-900">18</p>
            </div>
          </div>
        </GlassCard>
        <GlassCard>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-semantic-error/10 rounded-lg flex items-center justify-center">
              <XCircle className="w-5 h-5 text-semantic-error" />
            </div>
            <div>
              <p className="text-sm text-neutral-500">Critical Issues</p>
              <p className="text-2xl font-bold text-neutral-900">5</p>
            </div>
          </div>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* File List */}
        <div className="lg:col-span-1">
          <GlassCard>
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Validation Results</h3>
            <div className="space-y-3">
              {validationResults.map((result) => (
                <div
                  key={result.id}
                  className={`p-4 rounded-lg cursor-pointer transition-colors ${
                    selectedJob === result.id 
                      ? 'bg-primary-50 border border-primary-200' 
                      : 'bg-neutral-50/50 hover:bg-neutral-100/50'
                  }`}
                  onClick={() => setSelectedJob(result.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-neutral-900 truncate text-sm">
                        {result.file_name}
                      </p>
                      <p className="text-xs text-neutral-500 mt-1">
                        {new Date(result.processed_at).toLocaleString()}
                      </p>
                      <div className="flex items-center space-x-2 mt-2">
                        <span className="text-xs bg-semantic-success/10 text-semantic-success px-2 py-1 rounded-full">
                          {result.valid_fields}/{result.total_fields} valid
                        </span>
                        {result.errors > 0 && (
                          <span className="text-xs bg-semantic-error/10 text-semantic-error px-2 py-1 rounded-full">
                            {result.errors} errors
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-neutral-900">
                        {result.confidence_score}%
                      </p>
                      <p className="text-xs text-neutral-500">confidence</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>

        {/* Validation Details */}
        <div className="lg:col-span-2">
          {selectedResult ? (
            <GlassCard>
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-neutral-900">
                  Validation Details - {selectedResult.file_name}
                </h3>
                <div className="flex items-center space-x-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400 w-4 h-4" />
                    <input
                      type="text"
                      placeholder="Search fields..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 pr-4 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                    />
                  </div>
                  <select
                    value={filterSeverity}
                    onChange={(e) => setFilterSeverity(e.target.value as any)}
                    className="px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                  >
                    <option value="all">All Issues</option>
                    <option value="error">Errors Only</option>
                    <option value="warning">Warnings Only</option>
                  </select>
                </div>
              </div>

              <div className="space-y-4">
                {filteredIssues.map((issue) => {
                  const SeverityIcon = getSeverityIcon(issue.severity)
                  const isEditing = editingField === issue.id

                  return (
                    <div key={issue.id} className="p-4 bg-neutral-50/50 rounded-lg">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="font-medium text-neutral-900">{issue.field_name}</span>
                            <span className={`px-2 py-1 text-xs rounded-full flex items-center space-x-1 ${getSeverityColor(issue.severity)}`}>
                              <SeverityIcon className="w-3 h-3" />
                              <span className="capitalize">{issue.severity}</span>
                            </span>
                            <span className="px-2 py-1 text-xs bg-neutral-100 text-neutral-600 rounded-full">
                              {issue.confidence}% confidence
                            </span>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <label className="text-sm text-neutral-500 block mb-1">Detected Value</label>
                              {isEditing ? (
                                <input
                                  type="text"
                                  value={editValue}
                                  onChange={(e) => setEditValue(e.target.value)}
                                  className="w-full px-3 py-2 bg-white border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                                />
                              ) : (
                                <p className="text-sm text-neutral-900 bg-white px-3 py-2 rounded-lg border">
                                  {issue.detected_value}
                                </p>
                              )}
                            </div>

                            <div>
                              <label className="text-sm text-neutral-500 block mb-1">Suggested Value</label>
                              <p className="text-sm text-neutral-900 bg-white px-3 py-2 rounded-lg border">
                                {issue.suggested_value || 'No suggestion available'}
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 ml-4">
                          {isEditing ? (
                            <>
                              <button
                                onClick={() => handleEditSave(issue.id)}
                                className="p-2 text-semantic-success hover:bg-semantic-success/10 rounded-lg transition-colors"
                              >
                                <Save className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => setEditingField(null)}
                                className="p-2 text-neutral-400 hover:bg-neutral-100 rounded-lg transition-colors"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={() => handleEditStart(issue)}
                              className="p-2 text-neutral-400 hover:bg-neutral-100 rounded-lg transition-colors"
                            >
                              <Edit3 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </div>

                      {issue.requires_manual_review && (
                        <div className="mt-3 p-3 bg-semantic-warning/10 border border-semantic-warning/20 rounded-lg">
                          <p className="text-sm text-semantic-warning">
                            ⚠️ This field requires manual review
                          </p>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {filteredIssues.length === 0 && (
                <div className="text-center py-8">
                  <CheckCircle className="w-12 h-12 text-semantic-success mx-auto mb-3" />
                  <p className="text-neutral-600">No issues found matching your filters</p>
                </div>
              )}
            </GlassCard>
          ) : (
            <GlassCard>
              <div className="text-center py-12">
                <Eye className="w-16 h-16 text-neutral-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                  Select a File to Review
                </h3>
                <p className="text-neutral-600">
                  Choose a file from the list to view validation results and make corrections
                </p>
              </div>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  )
}