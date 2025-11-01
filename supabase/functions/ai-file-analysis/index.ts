// AI File Analysis using Hugging Face API
// Provides sentiment analysis, text classification, and summarization

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Max-Age': '86400',
};

interface AnalysisRequest {
  fileId: string;
  text: string;
  analysisType: 'sentiment' | 'classification' | 'summarization' | 'ner';
}

// Demo mode - generates mock analysis results
function generateDemoAnalysis(text: string, analysisType: string) {
  const wordCount = text.split(/\s+/).length;
  
  switch (analysisType) {
    case 'sentiment':
      return {
        label: 'POSITIVE',
        score: 0.85 + Math.random() * 0.1,
        details: {
          positive: 0.85,
          negative: 0.10,
          neutral: 0.05,
        },
      };
    
    case 'classification':
      const categories = ['Business', 'Technology', 'Finance', 'Marketing', 'Operations'];
      return {
        label: categories[Math.floor(Math.random() * categories.length)],
        score: 0.75 + Math.random() * 0.2,
        topCategories: categories.slice(0, 3).map((cat, idx) => ({
          category: cat,
          score: 0.8 - (idx * 0.15),
        })),
      };
    
    case 'summarization':
      const sentences = text.split(/[.!?]+/).filter(s => s.trim());
      const summary = sentences.slice(0, Math.min(3, sentences.length)).join('. ') + '.';
      return {
        summary: summary.length > 200 ? summary.substring(0, 197) + '...' : summary,
        originalLength: text.length,
        summaryLength: summary.length,
        compressionRatio: (summary.length / text.length * 100).toFixed(2) + '%',
      };
    
    case 'ner':
      return {
        entities: [
          { text: 'Q4', label: 'DATE', score: 0.95 },
          { text: '2024', label: 'DATE', score: 0.98 },
          { text: 'Revenue', label: 'METRIC', score: 0.89 },
        ],
        entityCount: 3,
      };
    
    default:
      return { result: 'Analysis completed', confidence: 0.85 };
  }
}

// Call Hugging Face API
async function callHuggingFace(text: string, analysisType: string, apiKey: string) {
  const modelMap: Record<string, string> = {
    'sentiment': 'distilbert-base-uncased-finetuned-sst-2-english',
    'classification': 'facebook/bart-large-mnli',
    'summarization': 'facebook/bart-large-cnn',
    'ner': 'dbmdz/bert-large-cased-finetuned-conll03-english',
  };

  const model = modelMap[analysisType] || modelMap['sentiment'];

  const response = await fetch(
    `https://api-inference.huggingface.co/models/${model}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ inputs: text }),
    }
  );

  if (!response.ok) {
    throw new Error(`Hugging Face API error: ${response.statusText}`);
  }

  return await response.json();
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
    const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const HUGGINGFACE_API_KEY = Deno.env.get('HUGGINGFACE_API_KEY');

    const { fileId, text, analysisType } = await req.json() as AnalysisRequest;

    const startTime = Date.now();
    let result: any;
    let isDemo = false;

    // Trim text to avoid API limits
    const trimmedText = text.substring(0, 5000);

    if (!HUGGINGFACE_API_KEY) {
      // Demo mode
      result = generateDemoAnalysis(trimmedText, analysisType);
      isDemo = true;
    } else {
      // Real API call
      try {
        result = await callHuggingFace(trimmedText, analysisType, HUGGINGFACE_API_KEY);
      } catch (apiError) {
        console.error('HuggingFace API error, falling back to demo mode:', apiError);
        result = generateDemoAnalysis(trimmedText, analysisType);
        isDemo = true;
      }
    }

    const processingTime = Date.now() - startTime;

    // Store analysis result
    const insertResponse = await fetch(`${SUPABASE_URL}/rest/v1/ai_file_analysis`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
      },
      body: JSON.stringify({
        file_id: fileId,
        analysis_type: analysisType,
        input_text: trimmedText,
        result: result,
        confidence_score: result.score || result.topCategories?.[0]?.score || 0.85,
        processing_time_ms: processingTime,
        ai_model: isDemo ? 'demo-mode' : `huggingface-${analysisType}`,
      }),
    });

    if (!insertResponse.ok) {
      const error = await insertResponse.text();
      throw new Error(`Failed to store analysis: ${error}`);
    }

    return new Response(
      JSON.stringify({
        success: true,
        data: {
          fileId,
          analysisType,
          result,
          processingTime,
          isDemo,
          message: isDemo ? 'Demo mode - using simulated AI analysis' : 'Analysis completed',
        },
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  } catch (error) {
    console.error('AI analysis error:', error);
    return new Response(
      JSON.stringify({
        success: false,
        error: {
          code: 'ANALYSIS_FAILED',
          message: error.message || 'AI analysis failed',
        },
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
