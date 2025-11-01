// Edge Function: Audit Logger for Compliance Logging
// Handles comprehensive audit logging for compliance and security monitoring

interface AuditLogEntry {
  event_type: string;
  user_id?: string;
  session_id?: string;
  source_ip?: string;
  user_agent?: string;
  resource?: string;
  action: string;
  outcome: 'success' | 'failure' | 'warning';
  details?: Record<string, any>;
  compliance_tags?: string[];
  timestamp?: string;
  request_id?: string;
  risk_level?: 'low' | 'medium' | 'high' | 'critical';
}

interface AuditLogRequest {
  logs: AuditLogEntry[];
  retention_period_days?: number;
  export_format?: 'json' | 'csv' | 'xml';
  filters?: {
    start_date?: string;
    end_date?: string;
    user_id?: string;
    event_type?: string;
    risk_level?: string;
    outcome?: string;
  };
}

interface AuditLogResponse {
  success: boolean;
  data?: {
    logged: number;
    failed: number;
    log_ids: string[];
    summary: {
      total_logs: number;
      successful_logs: number;
      failed_logs: number;
      retention_period: number;
      compliance_status: 'compliant' | 'partial' | 'non_compliant';
    };
    metadata: {
      processing_time: number;
      batch_id: string;
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
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
    'Access-Control-Max-Age': '86400',
    'Access-Control-Allow-Credentials': 'false'
  };

  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  const startTime = Date.now();
  const batchId = crypto.randomUUID();
  const timestamp = new Date().toISOString();

  try {
    console.log('Audit logging started:', {
      method: req.method,
      url: req.url,
      batch_id: batchId,
      timestamp
    });

    // Parse request body
    const requestData: AuditLogRequest = await req.json();
    const { logs, retention_period_days = 90, export_format = 'json', filters } = requestData;

    // Validate required fields
    if (!logs || !Array.isArray(logs) || logs.length === 0) {
      const errorResponse: AuditLogResponse = {
        success: false,
        error: {
          code: 'INVALID_REQUEST',
          message: 'Missing or invalid logs array'
        }
      };
      
      return new Response(JSON.stringify(errorResponse), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    const processingTime = Date.now() - startTime;
    const logIds: string[] = [];
    let successfulLogs = 0;
    let failedLogs = 0;
    const complianceIssues: string[] = [];

    // Process each audit log entry
    for (const logEntry of logs) {
      try {
        const logId = crypto.randomUUID();
        
        // Validate required audit log fields
        if (!logEntry.event_type || !logEntry.action) {
          throw new Error('Missing required fields: event_type and action');
        }

        // Add metadata
        const enrichedLog = {
          ...logEntry,
          log_id: logId,
          batch_id: batchId,
          timestamp: logEntry.timestamp || new Date().toISOString(),
          retention_period_days,
          compliance_checks: performComplianceChecks(logEntry),
          processing_info: {
            processed_at: timestamp,
            processing_time_ms: processingTime,
            system_version: '1.0.0'
          }
        };

        // Mock logging to different systems (in production, this would log to actual systems)
        await logToAuditSystems(enrichedLog, logIds);
        
        successfulLogs++;
        
        // Check for compliance issues
        const issues = enrichedLog.compliance_checks;
        if (issues.length > 0) {
          complianceIssues.push(...issues);
        }

        console.log('Audit log processed successfully:', {
          log_id: logId,
          event_type: logEntry.event_type,
          outcome: logEntry.outcome,
          risk_level: logEntry.risk_level || 'low'
        });

      } catch (error) {
        failedLogs++;
        console.error('Failed to process audit log:', {
          error: error.message,
          log_entry: logEntry,
          batch_id: batchId
        });
      }
    }

    const totalLogs = logs.length;
    const complianceStatus = determineComplianceStatus(complianceIssues, totalLogs);

    // Generate audit summary
    const summary = {
      total_logs: totalLogs,
      successful_logs: successfulLogs,
      failed_logs: failedLogs,
      retention_period: retention_period_days,
      compliance_status: complianceStatus
    };

    console.log('Audit logging completed:', {
      batch_id: batchId,
      total_logs: totalLogs,
      successful_logs: successfulLogs,
      failed_logs: failedLogs,
      compliance_status: complianceStatus,
      processing_time: processingTime
    });

    const response: AuditLogResponse = {
      success: true,
      data: {
        logged: successfulLogs,
        failed: failedLogs,
        log_ids: logIds,
        summary,
        metadata: {
          processing_time: processingTime,
          batch_id: batchId,
          timestamp
        }
      }
    };

    return new Response(JSON.stringify(response), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    const processingTime = Date.now() - startTime;
    console.error('Audit logging failed:', {
      error: error.message,
      stack: error.stack,
      batch_id: batchId,
      processing_time: processingTime
    });

    const errorResponse: AuditLogResponse = {
      success: false,
      error: {
        code: 'AUDIT_LOGGING_ERROR',
        message: 'Failed to process audit logs',
        details: error.message
      }
    };

    return new Response(JSON.stringify(errorResponse), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});

// Compliance checking function
function performComplianceChecks(logEntry: AuditLogEntry): string[] {
  const issues: string[] = [];
  
  // SOX compliance checks
  if (logEntry.action.includes('delete') || logEntry.action.includes('remove')) {
    if (!logEntry.user_id) {
      issues.push('SOX: User ID missing for critical action');
    }
    if (!logEntry.source_ip) {
      issues.push('SOX: Source IP missing for critical action');
    }
  }

  // GDPR compliance checks
  if (logEntry.event_type.includes('personal_data') || logEntry.action.includes('pii')) {
    if (!logEntry.compliance_tags?.includes('gdpr_logged')) {
      issues.push('GDPR: Personal data access not properly logged');
    }
  }

  // HIPAA compliance checks
  if (logEntry.event_type.includes('health') || logEntry.action.includes('medical')) {
    if (logEntry.risk_level === 'high' && !logEntry.approval_trail) {
      issues.push('HIPAA: High-risk health data access lacks approval trail');
    }
  }

  // PCI DSS compliance checks
  if (logEntry.event_type.includes('payment') || logEntry.event_type.includes('card')) {
    if (!logEntry.compliance_tags?.includes('encrypted')) {
      issues.push('PCI DSS: Payment data not flagged as encrypted');
    }
  }

  return issues;
}

// Compliance status determination
function determineComplianceStatus(issues: string[], totalLogs: number): 'compliant' | 'partial' | 'non_compliant' {
  if (issues.length === 0) {
    return 'compliant';
  } else if (issues.length < totalLogs * 0.1) {
    return 'partial';
  } else {
    return 'non_compliant';
  }
}

// Mock logging to various audit systems
async function logToAuditSystems(logEntry: any, logIds: string[]): Promise<void> {
  // Mock logging to different systems
  const systems = ['primary_audit', 'compliance_audit', 'security_audit', 'backup_audit'];
  
  for (const system of systems) {
    try {
      // Mock system-specific logging
      console.log(`Logged to ${system}:`, {
        log_id: logEntry.log_id,
        system,
        timestamp: logEntry.timestamp
      });
    } catch (error) {
      console.error(`Failed to log to ${system}:`, error);
      throw error;
    }
  }
  
  logIds.push(logEntry.log_id);
}