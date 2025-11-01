// File Processor - Extracts and processes data from CSV, JSON, TXT files
// Handles structured data parsing and analysis

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Max-Age': '86400',
};

interface ProcessRequest {
  fileId: string;
  fileUrl: string;
  fileType: string;
}

// Parse CSV data
function parseCSV(text: string): any[] {
  const lines = text.trim().split('\n');
  if (lines.length === 0) return [];

  const headers = lines[0].split(',').map(h => h.trim().replace(/['"]/g, ''));
  const data: any[] = [];

  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.trim().replace(/['"]/g, ''));
    const row: any = {};
    headers.forEach((header, index) => {
      row[header] = values[index] || '';
    });
    data.push(row);
  }

  return data;
}

// Generate data summary statistics
function generateDataSummary(data: any[]): any {
  if (data.length === 0) return {};

  const summary: any = {
    totalRows: data.length,
    columns: {},
  };

  const keys = Object.keys(data[0] || {});
  keys.forEach(key => {
    const values = data.map(row => row[key]).filter(v => v !== '');
    const numericValues = values.filter(v => !isNaN(Number(v))).map(Number);

    summary.columns[key] = {
      totalValues: values.length,
      uniqueValues: new Set(values).size,
      dataType: numericValues.length > values.length * 0.8 ? 'numeric' : 'text',
    };

    if (numericValues.length > 0) {
      const sum = numericValues.reduce((a, b) => a + b, 0);
      const avg = sum / numericValues.length;
      const sorted = [...numericValues].sort((a, b) => a - b);
      
      summary.columns[key].statistics = {
        min: Math.min(...numericValues),
        max: Math.max(...numericValues),
        average: avg,
        median: sorted[Math.floor(sorted.length / 2)],
        sum: sum,
      };
    }
  });

  return summary;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
    const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

    const { fileId, fileUrl, fileType } = await req.json() as ProcessRequest;

    // Download file content
    const fileResponse = await fetch(fileUrl);
    if (!fileResponse.ok) {
      throw new Error('Failed to download file');
    }

    const fileContent = await fileResponse.text();
    let extractedData: any[] = [];
    let dataFormat = '';

    // Process based on file type
    if (fileType === 'text/csv' || fileUrl.endsWith('.csv')) {
      extractedData = parseCSV(fileContent);
      dataFormat = 'csv';
    } else if (fileType === 'application/json' || fileUrl.endsWith('.json')) {
      extractedData = JSON.parse(fileContent);
      if (!Array.isArray(extractedData)) {
        extractedData = [extractedData];
      }
      dataFormat = 'json';
    } else if (fileType === 'text/plain' || fileUrl.endsWith('.txt')) {
      // For text files, split into lines
      extractedData = fileContent.split('\n').map((line, idx) => ({
        lineNumber: idx + 1,
        content: line,
      }));
      dataFormat = 'txt';
    }

    // Generate summary
    const dataSummary = generateDataSummary(extractedData);

    // Store full data and sample
    const dataSample = extractedData.slice(0, 100); // First 100 rows

    // Insert extraction results
    const insertResponse = await fetch(`${SUPABASE_URL}/rest/v1/file_data_extraction`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
      },
      body: JSON.stringify({
        file_id: fileId,
        data_format: dataFormat,
        row_count: extractedData.length,
        column_count: Object.keys(extractedData[0] || {}).length,
        data_sample: dataSample,
        full_data: extractedData,
        data_summary: dataSummary,
        schema_info: {
          columns: Object.keys(extractedData[0] || {}),
          dataTypes: dataSummary.columns,
        },
      }),
    });

    if (!insertResponse.ok) {
      const error = await insertResponse.text();
      throw new Error(`Failed to store extraction results: ${error}`);
    }

    // Update file processing status
    await fetch(`${SUPABASE_URL}/rest/v1/file_uploads?id=eq.${fileId}`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        processing_status: 'completed',
      }),
    });

    return new Response(
      JSON.stringify({
        success: true,
        data: {
          fileId,
          dataFormat,
          rowCount: extractedData.length,
          columnCount: Object.keys(extractedData[0] || {}).length,
          dataSample,
          summary: dataSummary,
        },
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  } catch (error) {
    console.error('File processing error:', error);
    return new Response(
      JSON.stringify({
        success: false,
        error: {
          code: 'PROCESSING_FAILED',
          message: error.message || 'File processing failed',
        },
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
