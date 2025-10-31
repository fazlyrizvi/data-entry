// Edge Function: Webhook Handler for Enterprise Integrations
// Handles incoming webhooks from external systems and processes them

interface WebhookRequest {
  source_system: string;
  event_type: string;
  payload: Record<string, any>;
  headers?: Record<string, string>;
  webhook_id?: string;
  timestamp?: string;
  signature?: string; // For webhook verification
}

interface WebhookResponse {
  success: boolean;
  data?: {
    processed: boolean;
    actions_taken: string[];
    response_data?: any;
    metadata: {
      processing_time: number;
      webhook_id: string;
      source_system: string;
      event_type: string;
      timestamp: string;
    };
  };
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

Deno.serve(async (req: Request) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-webhook-signature',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
    'Access-Control-Max-Age': '86400',
    'Access-Control-Allow-Credentials': 'false'
  };

  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const startTime = Date.now();
  const webhookId = crypto.randomUUID();
  const timestamp = new Date().toISOString();

  try {
    console.log('Webhook received:', {
      method: req.method,
      url: req.url,
      webhook_id: webhookId,
      timestamp
    });

    // Get request headers
    const headers: Record<string, string> = {};
    req.headers.forEach((value, key) => {
      headers[key.toLowerCase()] = value;
    });

    // Parse request body
    const requestData: WebhookRequest = await req.json();
    const { source_system, event_type, payload, webhook_id, timestamp: providedTimestamp, signature } = requestData;

    // Validate required fields
    if (!source_system || !event_type || !payload) {
      const errorResponse: WebhookResponse = {
        success: false,
        error: {
          code: 'INVALID_REQUEST',
          message: 'Missing required fields: source_system, event_type, and payload'
        }
      };
      
      return new Response(JSON.stringify(errorResponse), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Verify webhook signature if provided (mock implementation)
    if (signature) {
      console.log('Webhook signature verification:', { has_signature: true, webhook_id: webhookId });
      // In production, implement actual signature verification using the source system's public key
    }

    const processingTime = Date.now() - startTime;
    const actionsTaken: string[] = [];

    // Process webhook based on source system and event type
    switch (source_system.toLowerCase()) {
      case 'salesforce':
        await handleSalesforceWebhook(event_type, payload, actionsTaken);
        break;
      
      case 'hubspot':
        await handleHubspotWebhook(event_type, payload, actionsTaken);
        break;
      
      case 'slack':
        await handleSlackWebhook(event_type, payload, actionsTaken);
        break;
      
      case 'github':
        await handleGithubWebhook(event_type, payload, actionsTaken);
        break;
      
      case 'stripe':
        await handleStripeWebhook(event_type, payload, actionsTaken);
        break;
      
      default:
        await handleGenericWebhook(event_type, payload, actionsTaken);
        break;
    }

    // Log audit trail
    console.log('Webhook processed successfully:', {
      webhook_id: webhookId,
      source_system,
      event_type,
      actions_count: actionsTaken.length,
      processing_time: processingTime
    });

    const response: WebhookResponse = {
      success: true,
      data: {
        processed: true,
        actions_taken: actionsTaken,
        metadata: {
          processing_time: processingTime,
          webhook_id: webhookId,
          source_system,
          event_type,
          timestamp
        }
      }
    };

    return new Response(JSON.stringify(response), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    const processingTime = Date.now() - startTime;
    console.error('Webhook processing failed:', {
      error: error.message,
      stack: error.stack,
      webhook_id: webhookId,
      processing_time: processingTime
    });

    const errorResponse: WebhookResponse = {
      success: false,
      error: {
        code: 'WEBHOOK_PROCESSING_ERROR',
        message: 'Failed to process webhook',
        details: error.message
      }
    };

    return new Response(JSON.stringify(errorResponse), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});

// Mock webhook handlers for different systems
async function handleSalesWebhook(eventType: string, payload: any, actions: string[]): Promise<void> {
  // Mock Salesforce webhook processing
  switch (eventType.toLowerCase()) {
    case 'lead_created':
      actions.push('Lead created in Salesforce', 'Triggered follow-up automation');
      break;
    case 'opportunity_updated':
      actions.push('Opportunity updated', 'Notified sales team');
      break;
  }
}

async function handleSalesforceWebhook(eventType: string, payload: any, actions: string[]): Promise<void> {
  // Mock Salesforce webhook processing
  switch (eventType.toLowerCase()) {
    case 'lead_created':
      actions.push('Lead created in Salesforce', 'Triggered follow-up automation');
      break;
    case 'opportunity_updated':
      actions.push('Opportunity updated', 'Notified sales team');
      break;
  }
}

async function handleHubspotWebhook(eventType: string, payload: any, actions: string[]): Promise<void> {
  // Mock HubSpot webhook processing
  switch (eventType.toLowerCase()) {
    case 'contact_created':
      actions.push('Contact created in HubSpot', 'Added to email sequence');
      break;
    case 'deal_closed_won':
      actions.push('Deal won in HubSpot', 'Triggered invoicing process');
      break;
  }
}

async function handleSlackWebhook(eventType: string, payload: any, actions: string[]): Promise<void> {
  // Mock Slack webhook processing
  switch (eventType.toLowerCase()) {
    case 'message_posted':
      actions.push('Message processed in Slack', 'Triggered alert if needed');
      break;
    case 'user_joined':
      actions.push('User joined workspace', 'Sent welcome message');
      break;
  }
}

async function handleGithubWebhook(eventType: string, payload: any, actions: string[]): Promise<void> {
  // Mock GitHub webhook processing
  switch (eventType.toLowerCase()) {
    case 'push':
      actions.push('Code pushed to repository', 'Triggered CI/CD pipeline');
      break;
    case 'pull_request':
      actions.push('Pull request created', 'Started code review process');
      break;
  }
}

async function handleStripeWebhook(eventType: string, payload: any, actions: string[]): Promise<void> {
  // Mock Stripe webhook processing
  switch (eventType.toLowerCase()) {
    case 'payment_succeeded':
      actions.push('Payment succeeded', 'Updated order status', 'Sent confirmation email');
      break;
    case 'payment_failed':
      actions.push('Payment failed', 'Notified customer', 'Scheduled retry');
      break;
  }
}

async function handleGenericWebhook(eventType: string, payload: any, actions: string[]): Promise<void> {
  // Mock generic webhook processing
  actions.push('Webhook processed', 'Data integrated into system');
}