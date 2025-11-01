import React, { useState, useEffect } from 'react'
import { Activity, Database, RefreshCw, Plus, Settings, Eye, EyeOff } from 'lucide-react'
import { GlassCard } from '../ui/GlassCard'
import { DataService, RealTimeDataFeed } from '../../lib/supabase'
import toast from 'react-hot-toast'

export const DataFeedsInterface: React.FC = () => {
  const [feeds, setFeeds] = useState<any[]>([])
  const [selectedFeed, setSelectedFeed] = useState<any>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResults, setTestResults] = useState<any>(null)

  // New feed form
  const [newFeed, setNewFeed] = useState<Partial<RealTimeDataFeed>>({
    name: '',
    data_source: 'weather_api',
    source_config: {},
    refresh_interval_seconds: 300,
    is_active: true
  })

  const dataSources = [
    { 
      id: 'github', 
      name: 'GitHub API', 
      description: 'Repository data, commits, issues',
      configFields: ['owner', 'repo', 'endpoint']
    },
    { 
      id: 'alpha_vantage', 
      name: 'Alpha Vantage', 
      description: 'Stock market and financial data',
      configFields: ['symbol', 'function', 'interval', 'apikey']
    },
    { 
      id: 'weather_api', 
      name: 'Weather API', 
      description: 'Current weather and forecasts',
      configFields: ['city', 'appid']
    },
    { 
      id: 'news_api', 
      name: 'News API', 
      description: 'Latest news articles',
      configFields: ['q', 'category', 'country', 'apiKey']
    },
    { 
      id: 'guardian_api', 
      name: 'Guardian API', 
      description: 'The Guardian news articles',
      configFields: ['q', 'section', 'apiKey']
    }
  ]

  useEffect(() => {
    loadFeeds()
  }, [])

  const loadFeeds = async () => {
    try {
      const data = await DataService.getDataFeeds()
      setFeeds(data)
    } catch (error) {
      console.error('Error loading feeds:', error)
    }
  }

  const handleCreateFeed = async () => {
    if (!newFeed.name.trim()) {
      toast.error('Please enter a feed name')
      return
    }

    setIsCreating(true)

    try {
      await DataService.createDataFeed(newFeed)
      toast.success('Data feed created successfully!')
      
      // Reset form
      setNewFeed({
        name: '',
        data_source: 'weather_api' as RealTimeDataFeed['data_source'],
        source_config: {},
        refresh_interval_seconds: 300,
        is_active: true
      })
      
      loadFeeds()
    } catch (error: any) {
      console.error('Error creating feed:', error)
      toast.error(error.message || 'Failed to create data feed')
    } finally {
      setIsCreating(false)
    }
  }

  const handleTestFeed = async (feed?: any) => {
    const feedToTest = feed || selectedFeed
    if (!feedToTest) return

    setIsTesting(true)

    try {
      const result = await DataService.fetchDataFeed(
        feedToTest.data_source,
        feedToTest.source_config,
        feedToTest.id
      )
      
      setTestResults(result)
      toast.success('Feed test completed!')
    } catch (error: any) {
      console.error('Error testing feed:', error)
      toast.error(error.message || 'Feed test failed')
      setTestResults({ error: error.message })
    } finally {
      setIsTesting(false)
    }
  }

  const updateSourceConfig = (field: string, value: string) => {
    setNewFeed(prev => ({
      ...prev,
      source_config: {
        ...prev.source_config,
        [field]: value
      }
    }))
  }

  const getDefaultConfig = (sourceId: string) => {
    const defaults: Record<string, any> = {
      github: { owner: 'facebook', repo: 'react', endpoint: 'repos' },
      alpha_vantage: { symbol: 'IBM', function: 'TIME_SERIES_INTRADAY', interval: '5min', apikey: 'demo' },
      weather_api: { city: 'London', appid: 'demo' },
      news_api: { q: 'technology', category: 'technology', country: 'us', apiKey: 'demo' },
      guardian_api: { q: 'technology', section: 'technology', apiKey: 'demo' }
    }
    return defaults[sourceId] || {}
  }

  const handleSourceChange = (sourceId: string) => {
    const typedSourceId = sourceId as RealTimeDataFeed['data_source']
    setNewFeed(prev => ({
      ...prev,
      data_source: typedSourceId,
      source_config: getDefaultConfig(sourceId)
    }))
  }

  const formatFeedData = (data: any) => {
    if (!data) return 'No data'
    
    if (typeof data === 'object') {
      // Show a summary for different data sources
      if (data.weather) {
        return `Weather: ${data.weather[0]?.description}, ${data.main?.temp}°C`
      } else if (data.articles) {
        return `${data.articles.length} news articles`
      } else if (data.response?.results) {
        return `${data.response.results.length} Guardian articles`
      } else if (data.name && data.full_name) {
        return `Repository: ${data.full_name}, ${data.stargazers_count} stars`
      } else if (Array.isArray(data)) {
        return `${data.length} items`
      }
    }
    
    return JSON.stringify(data).substring(0, 100) + '...'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 rounded-xl bg-primary-500/10 backdrop-blur-sm">
          <Activity className="w-8 h-8 text-primary-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Real-time Data Feeds</h1>
          <p className="text-neutral-600">Monitor and manage live data sources</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Data Feeds List */}
        <div className="lg:col-span-1 space-y-6">
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Active Feeds</h3>
            <div className="space-y-3">
              {feeds.length > 0 ? (
                feeds.map((feed) => (
                  <div 
                    key={feed.id} 
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedFeed?.id === feed.id
                        ? 'border-primary-300 bg-primary-50'
                        : 'border-neutral-200 hover:border-neutral-300 hover:bg-neutral-50'
                    }`}
                    onClick={() => setSelectedFeed(feed)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium text-neutral-900">{feed.name}</h4>
                      <div className="flex items-center gap-2">
                        {feed.is_active ? (
                          <Eye className="w-4 h-4 text-green-600" />
                        ) : (
                          <EyeOff className="w-4 h-4 text-gray-400" />
                        )}
                        <span className={`w-2 h-2 rounded-full ${
                          feed.error_count === 0 ? 'bg-green-500' : 'bg-red-500'
                        }`} />
                      </div>
                    </div>
                    <p className="text-sm text-neutral-600 mb-2 capitalize">
                      {feed.data_source.replace('_', ' ')}
                    </p>
                    <div className="text-xs text-neutral-500">
                      <div>Interval: {feed.refresh_interval_seconds}s</div>
                      <div>
                        Last fetch: {feed.last_fetch_at 
                          ? new Date(feed.last_fetch_at).toLocaleString()
                          : 'Never'
                        }
                      </div>
                      {feed.error_count > 0 && (
                        <div className="text-red-600">
                          Errors: {feed.error_count}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-neutral-500 text-sm">No data feeds configured</p>
              )}
            </div>
          </GlassCard>

          {/* Selected Feed Actions */}
          {selectedFeed && (
            <GlassCard className="p-6">
              <h4 className="font-semibold text-neutral-900 mb-4">Feed Actions</h4>
              <div className="space-y-2">
                <button
                  onClick={() => handleTestFeed()}
                  disabled={isTesting}
                  className="w-full flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
                >
                  <RefreshCw className={`w-4 h-4 ${isTesting ? 'animate-spin' : ''}`} />
                  {isTesting ? 'Testing...' : 'Test Feed'}
                </button>
                <button className="w-full flex items-center gap-2 px-4 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors">
                  <Settings className="w-4 h-4" />
                  Configure
                </button>
              </div>
            </GlassCard>
          )}
        </div>

        {/* Feed Configuration */}
        <div className="lg:col-span-2 space-y-6">
          {/* Create New Feed */}
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Create New Feed</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Feed Name
                </label>
                <input
                  type="text"
                  value={newFeed.name}
                  onChange={(e) => setNewFeed(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter feed name"
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Data Source
                </label>
                <select
                  value={newFeed.data_source}
                  onChange={(e) => handleSourceChange(e.target.value)}
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {dataSources.map((source) => (
                    <option key={source.id} value={source.id}>
                      {source.name} - {source.description}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Refresh Interval (seconds)
                </label>
                <input
                  type="number"
                  value={newFeed.refresh_interval_seconds}
                  onChange={(e) => setNewFeed(prev => ({ 
                    ...prev, 
                    refresh_interval_seconds: parseInt(e.target.value) || 300 
                  }))}
                  min="60"
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              {/* Source-specific configuration */}
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Source Configuration
                </label>
                <div className="space-y-3">
                  {dataSources
                    .find(s => s.id === newFeed.data_source)
                    ?.configFields.map((field) => (
                      <div key={field}>
                        <label className="block text-xs font-medium text-neutral-600 mb-1">
                          {field}
                        </label>
                        <input
                          type="text"
                          value={(newFeed.source_config as any)[field] || ''}
                          onChange={(e) => updateSourceConfig(field, e.target.value)}
                          placeholder={`Enter ${field}`}
                          className="w-full p-2 border border-neutral-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-transparent text-sm"
                        />
                      </div>
                    ))
                  }
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={newFeed.is_active}
                  onChange={(e) => setNewFeed(prev => ({ ...prev, is_active: e.target.checked }))}
                  className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                />
                <label htmlFor="is_active" className="text-sm text-neutral-700">
                  Active (start fetching immediately)
                </label>
              </div>

              <button
                onClick={handleCreateFeed}
                disabled={isCreating}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
              >
                {isCreating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    Create Feed
                  </>
                )}
              </button>
            </div>
          </GlassCard>

          {/* Feed Details */}
          {selectedFeed && (
            <GlassCard className="p-6">
              <h3 className="text-lg font-semibold text-neutral-900 mb-4">Feed Details</h3>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-1">Name</label>
                    <div className="p-2 bg-neutral-50 rounded">{selectedFeed.name}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-1">Source</label>
                    <div className="p-2 bg-neutral-50 rounded capitalize">
                      {selectedFeed.data_source.replace('_', ' ')}
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-1">Configuration</label>
                  <pre className="p-3 bg-neutral-50 rounded text-xs overflow-x-auto">
                    {JSON.stringify(selectedFeed.source_config, null, 2)}
                  </pre>
                </div>

                {selectedFeed.latest_data && (
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-1">Latest Data</label>
                    <div className="p-3 bg-neutral-50 rounded text-sm">
                      {formatFeedData(selectedFeed.latest_data)}
                    </div>
                  </div>
                )}
              </div>
            </GlassCard>
          )}

          {/* Test Results */}
          {testResults && (
            <GlassCard className="p-6">
              <h3 className="text-lg font-semibold text-neutral-900 mb-4">Test Results</h3>
              {testResults.error ? (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="text-red-700 font-medium">Error</div>
                  <div className="text-red-600 text-sm">{testResults.error}</div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-neutral-700">Response Time</span>
                    <span className="text-sm text-neutral-900">{testResults.data?.response_time_ms}ms</span>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-2">Data Preview</label>
                    <div className="p-3 bg-neutral-50 rounded text-sm max-h-64 overflow-y-auto">
                      {formatFeedData(testResults.data?.data)}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-2">Full Response</label>
                    <pre className="p-3 bg-neutral-50 rounded text-xs overflow-x-auto max-h-64 overflow-y-auto">
                      {JSON.stringify(testResults.data, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  )
}