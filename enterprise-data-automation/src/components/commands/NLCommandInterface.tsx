import React, { useState, useRef, useEffect } from 'react'
import { 
  Send, 
  Mic, 
  MicOff, 
  Bot, 
  User, 
  Clock, 
  FileText,
  BarChart3,
  Settings,
  Zap,
  Command
} from 'lucide-react'
import { GlassCard } from '../ui/GlassCard'

interface Message {
  id: string
  type: 'user' | 'bot'
  content: string
  timestamp: Date
  suggestions?: string[]
}

export const NLCommandInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      content: 'Hello! I\'m your AI assistant for the data automation system. I can help you with processing workflows, viewing analytics, managing files, and more. What would you like to do?',
      timestamp: new Date(),
      suggestions: [
        'Show processing queue status',
        'Display today\'s analytics',
        'Start batch processing',
        'Check system health'
      ]
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const quickActions = [
    { icon: FileText, label: 'Process Files', command: 'process 100 documents' },
    { icon: BarChart3, label: 'View Analytics', command: 'show performance metrics' },
    { icon: Settings, label: 'System Status', command: 'check system health' },
    { icon: Zap, label: 'Queue Status', command: 'display processing queue' }
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (content: string = inputValue) => {
    if (!content.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const botResponse = generateBotResponse(content)
      setMessages(prev => [...prev, botResponse])
      setIsTyping(false)
    }, 1500)
  }

  const generateBotResponse = (userInput: string): Message => {
    const input = userInput.toLowerCase()
    
    if (input.includes('process') || input.includes('files') || input.includes('documents')) {
      return {
        id: Date.now().toString(),
        type: 'bot',
        content: 'I can help you process files. Currently there are 127 active jobs in the queue with an average processing time of 2.4 seconds per document. Would you like me to start a new batch or show you the current queue status?',
        timestamp: new Date(),
        suggestions: [
          'Show processing queue',
          'Start new batch',
          'Check processing speed'
        ]
      }
    }
    
    if (input.includes('analytics') || input.includes('metrics') || input.includes('performance')) {
      return {
        id: Date.now().toString(),
        type: 'bot',
        content: 'Here are today\'s key metrics: 127,453 documents processed (12.5% increase), 94.2% accuracy rate, and $0.12 cost per document. The system uptime is 99.9%. What specific metrics would you like to explore?',
        timestamp: new Date(),
        suggestions: [
          'Show error analysis',
          'Display department performance',
          'Export compliance report'
        ]
      }
    }
    
    if (input.includes('queue') || input.includes('status') || input.includes('health')) {
      return {
        id: Date.now().toString(),
        type: 'bot',
        content: 'System status: All systems operational. Queue has 45 pending jobs. Processing throughput is at 94.2% capacity. The last error rate was 0.8% in the last 24 hours.',
        timestamp: new Date(),
        suggestions: [
          'View detailed health metrics',
          'Show processing trends',
          'Check error logs'
        ]
      }
    }

    if (input.includes('help') || input.includes('what can you do')) {
      return {
        id: Date.now().toString(),
        type: 'bot',
        content: 'I can assist you with: processing files, viewing analytics, checking system status, managing workflows, and generating reports. Try commands like "process 100 documents" or "show today\'s performance".',
        timestamp: new Date(),
        suggestions: [
          'Process files',
          'Show analytics',
          'Check system status',
          'View workflows'
        ]
      }
    }

    return {
      id: Date.now().toString(),
      type: 'bot',
      content: 'I understand you\'re asking about that. While I can help with data processing, analytics, and system management, I might need more specific information. Try asking about processing, analytics, or system status.',
      timestamp: new Date(),
      suggestions: [
        'Show processing status',
        'Display analytics',
        'Check system health',
        'Process files'
      ]
    }
  }

  const handleVoiceToggle = () => {
    setIsListening(!isListening)
    // In a real implementation, this would start/stop speech recognition
  }

  const handleSuggestionClick = (suggestion: string) => {
    handleSendMessage(suggestion)
  }

  const handleQuickAction = (action: any) => {
    handleSendMessage(action.command)
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">AI Command Interface</h1>
          <p className="text-neutral-600 mt-1">Natural language control for your automation workflows</p>
        </div>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg text-sm font-medium text-neutral-700 hover:bg-glass-lightHover transition-colors flex items-center space-x-2">
            <Command className="w-4 h-4" />
            <span>Command History</span>
          </button>
          <button className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors">
            Voice Commands
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Chat Interface */}
        <div className="lg:col-span-2">
          <GlassCard className="h-[600px] flex flex-col">
            {/* Chat Header */}
            <div className="flex items-center space-x-3 p-6 border-b border-neutral-200">
              <div className="w-10 h-10 bg-primary-500 rounded-full flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-neutral-900">AI Assistant</h3>
                <p className="text-sm text-neutral-500">Always ready to help</p>
              </div>
              <div className="ml-auto">
                <span className="w-2 h-2 bg-semantic-success rounded-full"></span>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`flex space-x-3 max-w-[80%] ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.type === 'user' ? 'bg-primary-500' : 'bg-neutral-200'
                    }`}>
                      {message.type === 'user' ? (
                        <User className="w-4 h-4 text-white" />
                      ) : (
                        <Bot className="w-4 h-4 text-neutral-600" />
                      )}
                    </div>
                    <div className={`rounded-lg p-4 ${
                      message.type === 'user' 
                        ? 'bg-primary-500 text-white' 
                        : 'bg-glass-light backdrop-blur-glass border border-glass-border'
                    }`}>
                      <p className={message.type === 'user' ? 'text-white' : 'text-neutral-900'}>{message.content}</p>
                      <p className={`text-xs mt-2 ${
                        message.type === 'user' ? 'text-primary-100' : 'text-neutral-500'
                      }`}>
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                      
                      {message.suggestions && (
                        <div className="mt-3 space-y-2">
                          <p className="text-xs opacity-75">Quick suggestions:</p>
                          {message.suggestions.map((suggestion, index) => (
                            <button
                              key={index}
                              onClick={() => handleSuggestionClick(suggestion)}
                              className={`block w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                                message.type === 'user'
                                  ? 'bg-primary-600 hover:bg-primary-700 text-white'
                                  : 'bg-neutral-100 hover:bg-neutral-200 text-neutral-700'
                              }`}
                            >
                              {suggestion}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {isTyping && (
                <div className="flex justify-start">
                  <div className="flex space-x-3 max-w-[80%]">
                    <div className="w-8 h-8 bg-neutral-200 rounded-full flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-neutral-600" />
                    </div>
                    <div className="bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg p-4">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-6 border-t border-neutral-200">
              <div className="flex space-x-3">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Ask me anything about your data processing system..."
                    className="w-full pl-4 pr-12 py-3 bg-glass-light backdrop-blur-glass border border-glass-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                  />
                  <button
                    onClick={handleVoiceToggle}
                    className={`absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded-full transition-colors ${
                      isListening 
                        ? 'text-semantic-error hover:bg-semantic-error/10' 
                        : 'text-neutral-400 hover:bg-neutral-100'
                    }`}
                  >
                    {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                  </button>
                </div>
                <button
                  onClick={() => handleSendMessage()}
                  disabled={!inputValue.trim()}
                  className="px-4 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
              {isListening && (
                <div className="mt-3 p-3 bg-semantic-error/10 border border-semantic-error/20 rounded-lg">
                  <p className="text-sm text-semantic-error flex items-center">
                    <Mic className="w-4 h-4 mr-2 animate-pulse" />
                    Listening... Speak now
                  </p>
                </div>
              )}
            </div>
          </GlassCard>
        </div>

        {/* Quick Actions */}
        <div className="lg:col-span-1 space-y-6">
          <GlassCard>
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickAction(action)}
                  className="w-full flex items-center space-x-3 p-3 rounded-lg bg-neutral-50/50 hover:bg-neutral-100/50 transition-colors text-left"
                >
                  <action.icon className="w-5 h-5 text-primary-500" />
                  <div>
                    <p className="font-medium text-neutral-900">{action.label}</p>
                    <p className="text-xs text-neutral-500">{action.command}</p>
                  </div>
                </button>
              ))}
            </div>
          </GlassCard>

          {/* Recent Commands */}
          <GlassCard>
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Recent Commands</h3>
            <div className="space-y-3">
              {[
                { command: 'Show processing queue status', time: '2 min ago' },
                { command: 'Display today\'s analytics', time: '5 min ago' },
                { command: 'Process 100 invoices', time: '12 min ago' },
                { command: 'Check system health', time: '18 min ago' }
              ].map((cmd, index) => (
                <div
                  key={index}
                  className="p-3 bg-neutral-50/50 rounded-lg cursor-pointer hover:bg-neutral-100/50 transition-colors"
                  onClick={() => handleSuggestionClick(cmd.command)}
                >
                  <p className="font-medium text-neutral-900 text-sm">{cmd.command}</p>
                  <p className="text-xs text-neutral-500 mt-1 flex items-center">
                    <Clock className="w-3 h-3 mr-1" />
                    {cmd.time}
                  </p>
                </div>
              ))}
            </div>
          </GlassCard>

          {/* Command Examples */}
          <GlassCard>
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Command Examples</h3>
            <div className="space-y-2 text-sm">
              <div className="p-2 bg-neutral-50/50 rounded">
                <p className="text-neutral-700">"Process 500 invoices"</p>
              </div>
              <div className="p-2 bg-neutral-50/50 rounded">
                <p className="text-neutral-700">"Show weekly analytics"</p>
              </div>
              <div className="p-2 bg-neutral-50/50 rounded">
                <p className="text-neutral-700">"Check error rate"</p>
              </div>
              <div className="p-2 bg-neutral-50/50 rounded">
                <p className="text-neutral-700">"Export compliance report"</p>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  )
}