import React, { useState, useEffect } from 'react'
import { Workflow, Play, Plus, Settings, Trash2, Copy, Edit3 } from 'lucide-react'
import { GlassCard } from '../ui/GlassCard'
import { DataService } from '../../lib/supabase'
import toast from 'react-hot-toast'

interface WorkflowStep {
  type: string
  config: any
  name?: string
}

export const WorkflowBuilderInterface: React.FC = () => {
  const [workflows, setWorkflows] = useState<any[]>([])
  const [selectedWorkflow, setSelectedWorkflow] = useState<any>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [executions, setExecutions] = useState<any[]>([])

  // New workflow form
  const [newWorkflow, setNewWorkflow] = useState({
    name: '',
    description: '',
    trigger_type: 'manual',
    steps: [] as WorkflowStep[]
  })

  const stepTypes = [
    { id: 'ai_analysis', name: 'AI Analysis', description: 'Analyze text with AI models' },
    { id: 'data_fetch', name: 'Data Fetch', description: 'Fetch data from external APIs' },
    { id: 'notification', name: 'Send Notification', description: 'Send notifications via various channels' },
    { id: 'data_transform', name: 'Data Transform', description: 'Transform and process data' },
    { id: 'condition', name: 'Condition Check', description: 'Conditional logic and branching' },
    { id: 'delay', name: 'Delay', description: 'Wait for specified time' }
  ]

  useEffect(() => {
    loadWorkflows()
    loadExecutions()
  }, [])

  const loadWorkflows = async () => {
    try {
      const data = await DataService.getWorkflows()
      setWorkflows(data)
    } catch (error) {
      console.error('Error loading workflows:', error)
    }
  }

  const loadExecutions = async () => {
    try {
      const data = await DataService.getWorkflowExecutions()
      setExecutions(data)
    } catch (error) {
      console.error('Error loading executions:', error)
    }
  }

  const handleCreateWorkflow = async () => {
    if (!newWorkflow.name.trim()) {
      toast.error('Please enter a workflow name')
      return
    }

    if (newWorkflow.steps.length === 0) {
      toast.error('Please add at least one step')
      return
    }

    setIsCreating(true)

    try {
      const workflowData = {
        name: newWorkflow.name,
        description: newWorkflow.description,
        trigger_type: newWorkflow.trigger_type as any,
        steps: newWorkflow.steps,
        status: 'draft' as any
      }

      await DataService.createWorkflow(workflowData)
      toast.success('Workflow created successfully!')
      
      // Reset form
      setNewWorkflow({
        name: '',
        description: '',
        trigger_type: 'manual',
        steps: []
      })
      
      loadWorkflows()
    } catch (error: any) {
      console.error('Error creating workflow:', error)
      toast.error(error.message || 'Failed to create workflow')
    } finally {
      setIsCreating(false)
    }
  }

  const handleExecuteWorkflow = async (workflowId: string) => {
    setIsExecuting(true)

    try {
      const result = await DataService.executeWorkflow(workflowId, {
        input_text: 'Sample automation test'
      })
      
      if (result?.data) {
        toast.success('Workflow executed successfully!')
        loadExecutions()
      } else {
        toast.error('Workflow execution failed')
      }
    } catch (error: any) {
      console.error('Error executing workflow:', error)
      toast.error(error.message || 'Failed to execute workflow')
    } finally {
      setIsExecuting(false)
    }
  }

  const addStep = (stepType: string) => {
    const defaultConfigs = {
      ai_analysis: { task: 'sentiment', text: '{{input_text}}' },
      data_fetch: { source: 'weather_api', sourceConfig: { city: 'London', appid: 'demo' } },
      notification: { 
        channel: 'telegram', 
        recipient: 'demo_chat', 
        message: 'Workflow notification: {{result}}',
        channelConfig: { botToken: 'demo' }
      },
      data_transform: { transformation: 'json_extract', path: 'data.result' },
      condition: { condition: 'status', operator: 'equals', value: 'success' },
      delay: { duration: 5000 }
    }

    const newStep: WorkflowStep = {
      type: stepType,
      config: defaultConfigs[stepType as keyof typeof defaultConfigs] || {},
      name: `${stepTypes.find(t => t.id === stepType)?.name} ${newWorkflow.steps.length + 1}`
    }

    setNewWorkflow(prev => ({
      ...prev,
      steps: [...prev.steps, newStep]
    }))
  }

  const removeStep = (index: number) => {
    setNewWorkflow(prev => ({
      ...prev,
      steps: prev.steps.filter((_, i) => i !== index)
    }))
  }

  const updateStepConfig = (index: number, config: any) => {
    setNewWorkflow(prev => ({
      ...prev,
      steps: prev.steps.map((step, i) => 
        i === index ? { ...step, config } : step
      )
    }))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 rounded-xl bg-primary-500/10 backdrop-blur-sm">
          <Workflow className="w-8 h-8 text-primary-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Workflow Builder</h1>
          <p className="text-neutral-600">Create and manage automation workflows</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Workflow List */}
        <div className="lg:col-span-1 space-y-6">
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Existing Workflows</h3>
            <div className="space-y-3">
              {workflows.length > 0 ? (
                workflows.map((workflow) => (
                  <div 
                    key={workflow.id} 
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedWorkflow?.id === workflow.id
                        ? 'border-primary-300 bg-primary-50'
                        : 'border-neutral-200 hover:border-neutral-300 hover:bg-neutral-50'
                    }`}
                    onClick={() => setSelectedWorkflow(workflow)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium text-neutral-900">{workflow.name}</h4>
                      <span className={`px-2 py-1 text-xs rounded ${
                        workflow.status === 'active' ? 'bg-green-100 text-green-700' :
                        workflow.status === 'draft' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {workflow.status}
                      </span>
                    </div>
                    <p className="text-sm text-neutral-600 mb-2">{workflow.description}</p>
                    <div className="flex justify-between items-center text-xs text-neutral-500">
                      <span>{workflow.steps?.length || 0} steps</span>
                      <span>Runs: {workflow.run_count}</span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-neutral-500 text-sm">No workflows created yet</p>
              )}
            </div>
          </GlassCard>

          {/* Selected Workflow Actions */}
          {selectedWorkflow && (
            <GlassCard className="p-6">
              <h4 className="font-semibold text-neutral-900 mb-4">Actions</h4>
              <div className="space-y-2">
                <button
                  onClick={() => handleExecuteWorkflow(selectedWorkflow.id)}
                  disabled={isExecuting}
                  className="w-full flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
                >
                  <Play className="w-4 h-4" />
                  {isExecuting ? 'Executing...' : 'Execute'}
                </button>
                <button className="w-full flex items-center gap-2 px-4 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors">
                  <Edit3 className="w-4 h-4" />
                  Edit
                </button>
                <button className="w-full flex items-center gap-2 px-4 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors">
                  <Copy className="w-4 h-4" />
                  Duplicate
                </button>
              </div>
            </GlassCard>
          )}
        </div>

        {/* Workflow Builder */}
        <div className="lg:col-span-2 space-y-6">
          {/* New Workflow Form */}
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Create New Workflow</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Workflow Name
                </label>
                <input
                  type="text"
                  value={newWorkflow.name}
                  onChange={(e) => setNewWorkflow(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter workflow name"
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Description
                </label>
                <textarea
                  value={newWorkflow.description}
                  onChange={(e) => setNewWorkflow(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe what this workflow does"
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent h-20 resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Trigger Type
                </label>
                <select
                  value={newWorkflow.trigger_type}
                  onChange={(e) => setNewWorkflow(prev => ({ ...prev, trigger_type: e.target.value }))}
                  className="w-full p-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="manual">Manual</option>
                  <option value="schedule">Scheduled</option>
                  <option value="webhook">Webhook</option>
                  <option value="event">Event</option>
                </select>
              </div>
            </div>
          </GlassCard>

          {/* Step Builder */}
          <GlassCard className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-neutral-900">Workflow Steps</h3>
              <div className="flex gap-2">
                {stepTypes.map((stepType) => (
                  <button
                    key={stepType.id}
                    onClick={() => addStep(stepType.id)}
                    title={stepType.description}
                    className="px-3 py-1 text-sm bg-primary-100 text-primary-700 rounded-lg hover:bg-primary-200 transition-colors"
                  >
                    <Plus className="w-3 h-3 inline mr-1" />
                    {stepType.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              {newWorkflow.steps.length > 0 ? (
                newWorkflow.steps.map((step, index) => (
                  <div key={index} className="p-4 border border-neutral-200 rounded-lg">
                    <div className="flex justify-between items-center mb-3">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 bg-primary-600 text-white text-xs rounded-full flex items-center justify-center">
                          {index + 1}
                        </span>
                        <span className="font-medium text-neutral-900">
                          {step.name || stepTypes.find(t => t.id === step.type)?.name}
                        </span>
                      </div>
                      <button
                        onClick={() => removeStep(index)}
                        className="text-red-600 hover:text-red-700 p-1"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                    
                    <div className="text-sm text-neutral-600 mb-2">
                      Type: {stepTypes.find(t => t.id === step.type)?.description}
                    </div>
                    
                    <div className="bg-neutral-50 p-3 rounded border">
                      <pre className="text-xs text-neutral-700 overflow-x-auto">
                        {JSON.stringify(step.config, null, 2)}
                      </pre>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-neutral-500 text-center py-8">
                  No steps added yet. Click the buttons above to add workflow steps.
                </p>
              )}
            </div>

            {newWorkflow.steps.length > 0 && (
              <div className="mt-6 pt-4 border-t border-neutral-200">
                <button
                  onClick={handleCreateWorkflow}
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
                      Create Workflow
                    </>
                  )}
                </button>
              </div>
            )}
          </GlassCard>

          {/* Recent Executions */}
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Recent Executions</h3>
            <div className="space-y-3">
              {executions.length > 0 ? (
                executions.slice(0, 5).map((execution) => (
                  <div key={execution.id} className="p-3 border border-neutral-200 rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium text-neutral-900">
                        {execution.workflows?.name || 'Unknown Workflow'}
                      </span>
                      <span className={`px-2 py-1 text-xs rounded ${
                        execution.execution_status === 'completed' ? 'bg-green-100 text-green-700' :
                        execution.execution_status === 'failed' ? 'bg-red-100 text-red-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {execution.execution_status}
                      </span>
                    </div>
                    <div className="text-sm text-neutral-600">
                      Steps: {execution.current_step}/{execution.total_steps}
                    </div>
                    {execution.duration_ms && (
                      <div className="text-sm text-neutral-500">
                        Duration: {execution.duration_ms}ms
                      </div>
                    )}
                    <div className="text-xs text-neutral-500 mt-1">
                      {new Date(execution.created_at).toLocaleString()}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-neutral-500 text-sm">No executions yet</p>
              )}
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  )
}