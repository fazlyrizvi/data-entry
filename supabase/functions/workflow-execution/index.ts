Deno.serve(async (req) => {
    const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
        'Access-Control-Max-Age': '86400',
        'Access-Control-Allow-Credentials': 'false'
    };

    if (req.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers: corsHeaders });
    }

    try {
        const requestData = await req.json();
        const { workflowId, triggerData, inputData } = requestData;

        if (!workflowId) {
            throw new Error('Workflow ID is required');
        }

        // Get workflow details from database
        const workflow = await getWorkflow(workflowId);
        if (!workflow) {
            throw new Error('Workflow not found');
        }

        // Create workflow execution record
        const execution = await createWorkflowExecution(workflowId, triggerData, inputData, workflow.steps.length);
        
        const executionId = execution.id;
        const startTime = Date.now();

        try {
            // Execute workflow steps
            const results = await executeWorkflowSteps(workflow.steps, inputData, executionId);
            
            const duration = Date.now() - startTime;

            // Update execution as completed
            await updateWorkflowExecution(executionId, 'completed', results, workflow.steps.length, null, duration);
            
            // Update workflow statistics
            await updateWorkflowStats(workflowId, true, duration);

            return new Response(JSON.stringify({
                data: {
                    executionId,
                    workflowId,
                    status: 'completed',
                    duration_ms: duration,
                    results
                }
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } catch (stepError) {
            const duration = Date.now() - startTime;
            
            // Update execution as failed
            await updateWorkflowExecution(executionId, 'failed', [], 0, stepError.message, duration);
            
            // Update workflow statistics
            await updateWorkflowStats(workflowId, false, duration);

            throw stepError;
        }

    } catch (error) {
        console.error('Workflow execution error:', error);

        const errorResponse = {
            error: {
                code: 'WORKFLOW_EXECUTION_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

async function getWorkflow(workflowId) {
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    const response = await fetch(`${supabaseUrl}/rest/v1/workflows?id=eq.${workflowId}`, {
        headers: {
            'Authorization': `Bearer ${serviceRoleKey}`,
            'apikey': serviceRoleKey
        }
    });

    if (!response.ok) {
        throw new Error('Failed to fetch workflow');
    }

    const workflows = await response.json();
    return workflows[0] || null;
}

async function createWorkflowExecution(workflowId, triggerData, inputData, totalSteps) {
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    const executionData = {
        workflow_id: workflowId,
        execution_status: 'processing',
        trigger_source: 'manual',
        trigger_data: triggerData || {},
        input_data: inputData || {},
        total_steps: totalSteps,
        started_at: new Date().toISOString()
    };

    const response = await fetch(`${supabaseUrl}/rest/v1/workflow_executions`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${serviceRoleKey}`,
            'apikey': serviceRoleKey,
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        },
        body: JSON.stringify(executionData)
    });

    if (!response.ok) {
        throw new Error('Failed to create workflow execution');
    }

    const executions = await response.json();
    return executions[0];
}

async function executeWorkflowSteps(steps, inputData, executionId) {
    const results = [];
    let currentData = inputData;

    for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        
        try {
            // Update current step
            await updateCurrentStep(executionId, i + 1);
            
            // Execute step based on type
            const stepResult = await executeStep(step, currentData);
            
            results.push({
                step: i + 1,
                type: step.type,
                status: 'completed',
                result: stepResult,
                timestamp: new Date().toISOString()
            });

            // Use step result as input for next step
            currentData = { ...currentData, [`step_${i + 1}_result`]: stepResult };

        } catch (stepError) {
            results.push({
                step: i + 1,
                type: step.type,
                status: 'failed',
                error: stepError.message,
                timestamp: new Date().toISOString()
            });
            
            // Update step results in database
            await updateStepResults(executionId, results);
            
            throw new Error(`Step ${i + 1} failed: ${stepError.message}`);
        }
    }

    // Update final step results
    await updateStepResults(executionId, results);
    
    return results;
}

async function executeStep(step, data) {
    const { type, config } = step;

    switch (type) {
        case 'ai_analysis':
            return await executeAIAnalysisStep(config, data);
        case 'data_fetch':
            return await executeDataFetchStep(config, data);
        case 'notification':
            return await executeNotificationStep(config, data);
        case 'data_transform':
            return await executeDataTransformStep(config, data);
        case 'condition':
            return await executeConditionStep(config, data);
        case 'delay':
            return await executeDelayStep(config, data);
        default:
            throw new Error(`Unsupported step type: ${type}`);
    }
}

async function executeAIAnalysisStep(config, data) {
    const { text, task, model } = config;
    const inputText = text || data.text || JSON.stringify(data);

    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    const response = await fetch(`${supabaseUrl}/functions/v1/ai-analysis`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${serviceRoleKey}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: inputText, task, model })
    });

    if (!response.ok) {
        throw new Error('AI analysis step failed');
    }

    const result = await response.json();
    return result.data;
}

async function executeDataFetchStep(config, data) {
    const { source, sourceConfig } = config;

    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    const response = await fetch(`${supabaseUrl}/functions/v1/data-feed`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${serviceRoleKey}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ source, config: sourceConfig })
    });

    if (!response.ok) {
        throw new Error('Data fetch step failed');
    }

    const result = await response.json();
    return result.data;
}

async function executeNotificationStep(config, data) {
    const { channel, recipient, message, subject } = config;
    
    // Replace placeholders in message with data
    const processedMessage = message.replace(/\{\{(\w+)\}\}/g, (match, key) => {
        return data[key] || match;
    });

    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    const response = await fetch(`${supabaseUrl}/functions/v1/send-notification`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${serviceRoleKey}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            channel, 
            recipient, 
            message: processedMessage, 
            subject,
            config: config.channelConfig || {}
        })
    });

    if (!response.ok) {
        throw new Error('Notification step failed');
    }

    const result = await response.json();
    return result.data;
}

async function executeDataTransformStep(config, data) {
    const { transformation } = config;
    
    switch (transformation) {
        case 'json_extract':
            const { path } = config;
            return extractFromPath(data, path);
        case 'filter':
            const { condition } = config;
            return applyFilter(data, condition);
        case 'map':
            const { mapping } = config;
            return applyMapping(data, mapping);
        default:
            return data;
    }
}

async function executeConditionStep(config, data) {
    const { condition, operator, value } = config;
    const dataValue = data[condition];
    
    let result;
    switch (operator) {
        case 'equals':
            result = dataValue == value;
            break;
        case 'not_equals':
            result = dataValue != value;
            break;
        case 'greater_than':
            result = dataValue > value;
            break;
        case 'less_than':
            result = dataValue < value;
            break;
        case 'contains':
            result = String(dataValue).includes(value);
            break;
        default:
            result = false;
    }
    
    return { condition_met: result, checked_value: dataValue };
}

async function executeDelayStep(config, data) {
    const { duration } = config; // duration in milliseconds
    
    await new Promise(resolve => setTimeout(resolve, duration));
    
    return { delayed_for_ms: duration };
}

function extractFromPath(data, path) {
    return path.split('.').reduce((obj, key) => obj?.[key], data);
}

function applyFilter(data, condition) {
    if (Array.isArray(data)) {
        return data.filter(item => evaluateCondition(item, condition));
    }
    return data;
}

function applyMapping(data, mapping) {
    const result = {};
    for (const [newKey, oldKey] of Object.entries(mapping)) {
        result[newKey] = data[oldKey];
    }
    return result;
}

function evaluateCondition(item, condition) {
    // Simple condition evaluation (can be expanded)
    const { field, operator, value } = condition;
    const itemValue = item[field];
    
    switch (operator) {
        case 'equals': return itemValue == value;
        case 'contains': return String(itemValue).includes(value);
        default: return true;
    }
}

async function updateWorkflowExecution(executionId, status, stepResults, currentStep, errorMessage, duration) {
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    const updateData = {
        execution_status: status,
        step_results: stepResults,
        current_step: currentStep,
        error_message: errorMessage,
        duration_ms: duration,
        completed_at: new Date().toISOString()
    };

    await fetch(`${supabaseUrl}/rest/v1/workflow_executions?id=eq.${executionId}`, {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${serviceRoleKey}`,
            'apikey': serviceRoleKey,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
    });
}

async function updateCurrentStep(executionId, stepNumber) {
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    await fetch(`${supabaseUrl}/rest/v1/workflow_executions?id=eq.${executionId}`, {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${serviceRoleKey}`,
            'apikey': serviceRoleKey,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ current_step: stepNumber })
    });
}

async function updateStepResults(executionId, results) {
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    await fetch(`${supabaseUrl}/rest/v1/workflow_executions?id=eq.${executionId}`, {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${serviceRoleKey}`,
            'apikey': serviceRoleKey,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ step_results: results })
    });
}

async function updateWorkflowStats(workflowId, success, duration) {
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    await fetch(`${supabaseUrl}/rpc/update_workflow_stats`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${serviceRoleKey}`,
            'apikey': serviceRoleKey,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            workflow_uuid: workflowId,
            success,
            duration
        })
    });
}