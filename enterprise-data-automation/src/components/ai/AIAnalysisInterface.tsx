import React, { useState, useEffect } from 'react'
import { Brain, Zap, BarChart3, MessageSquare, FileText, Globe } from 'lucide-react'
import { GlassCard } from '../ui/GlassCard'
import { DataService } from '../../lib/supabase'
import toast from 'react-hot-toast'

export const AIAnalysisInterface: React.FC = () => {
  const [inputText, setInputText] = useState('')
  const [selectedTask, setSelectedTask] = useState('sentiment')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [results, setResults] = useState<any[]>([])
  const [recentJobs, setRecentJobs] = useState<any[]>([])

  const analysisTypes = [
    { id: 'sentiment', name: 'Sentiment Analysis', icon: MessageSquare, description: 'Analyze emotional tone' },
    { id: 'classification', name: 'Text Classification', icon: BarChart3, description: 'Categorize content' },
    { id: 'summarization', name: 'Text Summarization', icon: FileText, description: 'Generate concise summaries' },
    { id: 'entity_extraction', name: 'Entity Extraction', icon: Brain, description: 'Extract names, places, organizations' },
    { id: 'translation', name: 'Translation', icon: Globe, description: 'Translate to different languages' }
  ]

  useEffect(() => {
    loadRecentJobs()
  }, [])

  const loadRecentJobs = async () => {
    try {
      const jobs = await DataService.getAIAnalysisJobs(10)
      setRecentJobs(jobs)
    } catch (error) {
      console.error('Error loading recent jobs:', error)
    }
  }

  const handleAnalysis = async () => {
    if (!inputText.trim()) {
      toast.error('Please enter text to analyze')
      return
    }

    setIsAnalyzing(true)

    try {
      const result = await DataService.runAIAnalysis(inputText, selectedTask)
      
      if (result?.data) {
        setResults(prev => [result.data, ...prev.slice(0, 4)])
        toast.success('Analysis completed successfully!')
        loadRecentJobs() // Refresh recent jobs
      } else {
        toast.error('Analysis failed - no result data')
      }
    } catch (error: any) {
      console.error('Analysis error:', error)
      toast.error(error.message || 'Analysis failed')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const formatAnalysisResult = (result: any) => {
    if (!result?.result) return 'No result available'

    // Handle different analysis types
    switch (result.task) {
      case 'sentiment':
        if (Array.isArray(result.result)) {
          const sentiment = result.result[0]
          return `${sentiment.label} (${(sentiment.score * 100).toFixed(1)}% confidence)`
        }
        break
      case 'classification':
        if (Array.isArray(result.result)) {
          return result.result.map((item: any) => 
            `${item.label}: ${(item.score * 100).toFixed(1)}%`
          ).join(', ')
        }
        break
      case 'summarization':
        if (Array.isArray(result.result)) {
          return result.result[0]?.summary_text || 'No summary available'
        }
        break
      case 'entity_extraction':
        if (Array.isArray(result.result)) {
          return result.result.map((entity: any) => 
            `${entity.word} (${entity.entity_group})`
          ).join(', ')
        }
        break
      default:
        return JSON.stringify(result.result, null, 2)
    }

    return JSON.stringify(result.result, null, 2)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 rounded-xl bg-primary-500/10 backdrop-blur-sm">
          <Brain className="w-8 h-8 text-primary-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">AI Analysis</h1>
          <p className="text-neutral-600">Analyze text using advanced AI models</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Analysis Interface */}
        <div className="lg:col-span-2 space-y-6">
          {/* Analysis Type Selection */}
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Analysis Type</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {analysisTypes.map((type) => {
                const IconComponent = type.icon
                return (
                  <button
                    key={type.id}
                    onClick={() => setSelectedTask(type.id)}
                    className={`p-4 rounded-lg border-2 text-left transition-all duration-200 ${
                      selectedTask === type.id
                        ? 'border-primary-300 bg-primary-50 shadow-md'
                        : 'border-neutral-200 hover:border-neutral-300 hover:bg-neutral-50'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <IconComponent className={`w-5 h-5 mt-0.5 ${
                        selectedTask === type.id ? 'text-primary-600' : 'text-neutral-500'
                      }`} />
                      <div>
                        <h4 className={`font-medium ${
                          selectedTask === type.id ? 'text-primary-900' : 'text-neutral-900'
                        }`}>
                          {type.name}
                        </h4>
                        <p className="text-sm text-neutral-600 mt-1">{type.description}</p>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          </GlassCard>

          {/* Text Input */}
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Input Text</h3>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Enter text to analyze..."
              className="w-full h-32 p-4 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              disabled={isAnalyzing}
            />
            <div className="flex justify-between items-center mt-4">
              <span className="text-sm text-neutral-600">
                {inputText.length} characters
              </span>
              <button
                onClick={handleAnalysis}
                disabled={isAnalyzing || !inputText.trim()}
                className="flex items-center gap-2 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isAnalyzing ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Analyze
                  </>
                )}
              </button>
            </div>
          </GlassCard>

          {/* Results */}
          {results.length > 0 && (
            <GlassCard className="p-6">
              <h3 className="text-lg font-semibold text-neutral-900 mb-4">Results</h3>
              <div className="space-y-4">
                {results.map((result, index) => (
                  <div key={index} className="p-4 bg-neutral-50 rounded-lg border">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-medium text-primary-600 capitalize">
                        {result.task} Analysis
                      </span>
                      <span className="text-xs text-neutral-500">
                        Model: {result.model}
                      </span>
                    </div>
                    <div className="text-sm text-neutral-700 mb-2">
                      <strong>Input:</strong> {result.input.substring(0, 100)}
                      {result.input.length > 100 && '...'}
                    </div>
                    <div className="text-sm text-neutral-900">
                      <strong>Result:</strong> {formatAnalysisResult(result)}
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}
        </div>

        {/* Recent Jobs Sidebar */}
        <div className="space-y-6">
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Recent Analysis</h3>
            <div className="space-y-3">
              {recentJobs.length > 0 ? (
                recentJobs.map((job) => (
                  <div key={job.id} className="p-3 bg-neutral-50 rounded-lg border text-sm">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-medium text-primary-600 capitalize">
                        {job.analysis_type}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        job.status === 'completed' ? 'bg-green-100 text-green-700' :
                        job.status === 'failed' ? 'bg-red-100 text-red-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {job.status}
                      </span>
                    </div>
                    <div className="text-neutral-600">
                      Provider: {job.ai_provider}
                    </div>
                    <div className="text-neutral-500 text-xs mt-1">
                      {new Date(job.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-neutral-500 text-sm">No recent analysis jobs</p>
              )}
            </div>
          </GlassCard>

          {/* Quick Stats */}
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Statistics</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-neutral-600">Total Jobs</span>
                <span className="font-medium">{recentJobs.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-600">Success Rate</span>
                <span className="font-medium text-green-600">
                  {recentJobs.length > 0 
                    ? Math.round((recentJobs.filter(j => j.status === 'completed').length / recentJobs.length) * 100)
                    : 0
                  }%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-600">Most Used</span>
                <span className="font-medium capitalize">
                  {recentJobs.length > 0 
                    ? (() => {
                        const counts = recentJobs.reduce((acc, job) => {
                          acc[job.analysis_type] = (acc[job.analysis_type] || 0) + 1
                          return acc
                        }, {} as Record<string, number>)
                        const entries = Object.entries(counts)
                        if (entries.length === 0) return 'None'
                        const maxEntry = entries.reduce((max, current) => 
                          current[1] > max[1] ? current : max
                        )
                        return maxEntry[0]
                      })()
                    : 'None'
                  }
                </span>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  )
}