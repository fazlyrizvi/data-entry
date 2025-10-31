// Edge Function: Data Validation Engine
// Handles data validation, schema checking, and quality assurance

interface ValidationRequest {
  data: any;
  validation_type: 'schema' | 'business_rules' | 'data_quality' | 'compliance' | 'all';
  schema?: Record<string, any>;
  rules?: Array<{
    field: string;
    rule: string;
    parameters?: Record<string, any>;
    error_message?: string;
  }>;
  options?: {
    strict_mode?: boolean;
    partial_validation?: boolean;
    include_suggestions?: boolean;
  };
}

interface ValidationResult {
  field: string;
  is_valid: boolean;
  error_message?: string;
  suggestions?: string[];
  confidence?: number;
}

interface ValidationResponse {
  success: boolean;
  data?: {
    validation_results: {
      overall_valid: boolean;
      results: ValidationResult[];
      summary: {
        total_fields: number;
        valid_fields: number;
        invalid_fields: number;
        confidence_score: number;
      };
      suggestions?: string[];
      metadata: {
        processing_time: number;
        validation_type: string;
        strict_mode: boolean;
      };
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

  try {
    console.log('Data validation started:', {
      method: req.method,
      url: req.url,
      timestamp: new Date().toISOString()
    });

    // Parse request body
    const requestData: ValidationRequest = await req.json();
    const { data, validation_type, schema, rules = [], options = {} } = requestData;

    // Validate required fields
    if (!data || !validation_type) {
      const errorResponse: ValidationResponse = {
        success: false,
        error: {
          code: 'INVALID_REQUEST',
          message: 'Missing required fields: data and validation_type'
        }
      };
      
      return new Response(JSON.stringify(errorResponse), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    const processingTime = Date.now() - startTime;
    const validationResults: ValidationResult[] = [];
    let overallValid = true;
    let confidenceScore = 0;
    const suggestions: string[] = [];

    // Mock validation logic - in production, this would implement actual validation rules
    const dataKeys = Object.keys(data);
    
    for (const key of dataKeys) {
      const value = data[key];
      const result: ValidationResult = {
        field: key,
        is_valid: true,
        suggestions: []
      };

      // Schema validation (mock)
      if (validation_type === 'schema' || validation_type === 'all') {
        if (value === null || value === undefined) {
          result.is_valid = false;
          result.error_message = `Field '${key}' cannot be null or undefined`;
          overallValid = false;
        } else if (typeof value === 'string' && value.trim() === '') {
          result.is_valid = false;
          result.error_message = `Field '${key}' cannot be empty`;
          overallValid = false;
        }
      }

      // Business rules validation (mock)
      if (validation_type === 'business_rules' || validation_type === 'all') {
        if (typeof value === 'string') {
          // Check for suspicious patterns
          if (value.length > 1000) {
            result.suggestions?.push(`Consider splitting '${key}' into smaller fields`);
          }
        }
      }

      // Data quality validation (mock)
      if (validation_type === 'data_quality' || validation_type === 'all') {
        if (typeof value === 'string') {
          // Mock data quality checks
          const hasSpecialChars = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(value);
          const hasNumbers = /\d/.test(value);
          
          if (hasSpecialChars && hasNumbers) {
            result.confidence = 0.85;
          } else {
            result.confidence = 0.95;
          }
        }
      }

      // Compliance validation (mock)
      if (validation_type === 'compliance' || validation_type === 'all') {
        // Mock compliance checks (GDPR, SOX, etc.)
        if (typeof value === 'string') {
          const containsPII = /\b\d{3}-\d{2}-\d{4}\b|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/.test(value);
          if (containsPII) {
            result.suggestions?.push(`Field '${key}' may contain PII - ensure compliance with privacy regulations`);
          }
        }
      }

      // Apply custom rules if provided
      for (const rule of rules) {
        if (rule.field === key) {
          switch (rule.rule) {
            case 'required':
              if (!value) {
                result.is_valid = false;
                result.error_message = rule.error_message || `Field '${key}' is required`;
                overallValid = false;
              }
              break;
            case 'email':
              if (typeof value === 'string' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                result.is_valid = false;
                result.error_message = rule.error_message || `Field '${key}' must be a valid email`;
                overallValid = false;
              }
              break;
            case 'numeric':
              if (typeof value !== 'number' && isNaN(Number(value))) {
                result.is_valid = false;
                result.error_message = rule.error_message || `Field '${key}' must be numeric`;
                overallValid = false;
              }
              break;
          }
        }
      }

      validationResults.push(result);
    }

    const summary = {
      total_fields: dataKeys.length,
      valid_fields: validationResults.filter(r => r.is_valid).length,
      invalid_fields: validationResults.filter(r => !r.is_valid).length,
      confidence_score: validationResults.length > 0 
        ? validationResults.reduce((sum, r) => sum + (r.confidence || 0.9), 0) / validationResults.length 
        : 1
    };

    console.log('Data validation completed:', {
      processing_time: processingTime,
      overall_valid: overallValid,
      total_fields: summary.total_fields,
      valid_fields: summary.valid_fields,
      invalid_fields: summary.invalid_fields,
      confidence_score: summary.confidence_score
    });

    const response: ValidationResponse = {
      success: true,
      data: {
        validation_results: {
          overall_valid: overallValid,
          results: validationResults,
          summary,
          suggestions: options.include_suggestions ? suggestions : undefined,
          metadata: {
            processing_time: processingTime,
            validation_type,
            strict_mode: options.strict_mode || false
          }
        }
      }
    };

    return new Response(JSON.stringify(response), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    const processingTime = Date.now() - startTime;
    console.error('Data validation failed:', {
      error: error.message,
      stack: error.stack,
      processing_time: processingTime
    });

    const errorResponse: ValidationResponse = {
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Failed to validate data',
        details: error.message
      }
    };

    return new Response(JSON.stringify(errorResponse), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});