// Edge Function: Data Extraction (NLP Processing)
// Handles NLP processing for text extraction and analysis

interface NLPRequest {
  text: string;
  extraction_type: 'entities' | 'sentiment' | 'keywords' | 'summary' | 'all';
  options?: {
    language?: string;
    confidence_threshold?: number;
    extract_relationships?: boolean;
    include_metadata?: boolean;
  };
}

interface NLPResponse {
  success: boolean;
  data?: {
    extracted_data: {
      entities?: Array<{
        text: string;
        type: string;
        confidence: number;
        start_position: number;
        end_position: number;
        metadata?: Record<string, any>;
      }>;
      sentiment?: {
        polarity: 'positive' | 'negative' | 'neutral';
        confidence: number;
        score: number;
      };
      keywords?: Array<{
        word: string;
        relevance: number;
        frequency: number;
      }>;
      summary?: string;
      relationships?: Array<{
        source: string;
        target: string;
        relationship: string;
        confidence: number;
      }>;
    };
    metadata: {
      processing_time: number;
      language_detected: string;
      word_count: number;
      extraction_type: string;
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
    console.log('NLP data extraction started:', {
      method: req.method,
      url: req.url,
      timestamp: new Date().toISOString()
    });

    // Parse request body
    const requestData: NLPRequest = await req.json();
    const { text, extraction_type, options = {} } = requestData;

    // Validate required fields
    if (!text || !extraction_type) {
      const errorResponse: NLPResponse = {
        success: false,
        error: {
          code: 'INVALID_REQUEST',
          message: 'Missing required fields: text and extraction_type'
        }
      };
      
      return new Response(JSON.stringify(errorResponse), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Basic text validation
    if (text.trim().length === 0) {
      const errorResponse: NLPResponse = {
        success: false,
        error: {
          code: 'EMPTY_TEXT',
          message: 'Text content is empty'
        }
      };
      
      return new Response(JSON.stringify(errorResponse), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    const wordCount = text.split(/\s+/).length;
    const processingTime = Date.now() - startTime;

    // Mock NLP processing result
    const mockNLPResult = {
      extracted_data: {
        entities: extraction_type === 'entities' || extraction_type === 'all' ? [
          {
            text: "John Smith",
            type: "PERSON",
            confidence: 0.95,
            start_position: 10,
            end_position: 20,
            metadata: { frequency: 1 }
          },
          {
            text: "New York",
            type: "LOCATION",
            confidence: 0.88,
            start_position: 45,
            end_position: 53,
            metadata: { frequency: 1 }
          }
        ] : undefined,
        sentiment: extraction_type === 'sentiment' || extraction_type === 'all' ? {
          polarity: 'positive' as const,
          confidence: 0.82,
          score: 0.65
        } : undefined,
        keywords: extraction_type === 'keywords' || extraction_type === 'all' ? [
          { word: "business", relevance: 0.95, frequency: 3 },
          { word: "strategy", relevance: 0.89, frequency: 2 },
          { word: "growth", relevance: 0.85, frequency: 2 }
        ] : undefined,
        summary: extraction_type === 'summary' || extraction_type === 'all' 
          ? "This is a generated summary of the text. In production, this would use advanced NLP models to generate meaningful summaries." 
          : undefined,
        relationships: extraction_type === 'all' && options.extract_relationships ? [
          {
            source: "John Smith",
            target: "New York",
            relationship: "LOCATED_IN",
            confidence: 0.75
          }
        ] : undefined
      },
      metadata: {
        processing_time: processingTime,
        language_detected: 'en',
        word_count: wordCount,
        extraction_type
      }
    };

    console.log('NLP processing completed successfully:', {
      processing_time: processingTime,
      word_count: wordCount,
      extraction_type,
      confidence: mockNLPResult.extracted_data.sentiment?.confidence || 'N/A'
    });

    const response: NLPResponse = {
      success: true,
      data: mockNLPResult
    };

    return new Response(JSON.stringify(response), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    const processingTime = Date.now() - startTime;
    console.error('NLP processing failed:', {
      error: error.message,
      stack: error.stack,
      processing_time: processingTime
    });

    const errorResponse: NLPResponse = {
      success: false,
      error: {
        code: 'NLP_PROCESSING_ERROR',
        message: 'Failed to process text with NLP',
        details: error.message
      }
    };

    return new Response(JSON.stringify(errorResponse), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});