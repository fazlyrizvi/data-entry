// File Export Generator
// Creates PDF reports, CSV exports, and JSON data exports

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Max-Age': '86400',
};

interface ExportRequest {
  fileId: string;
  exportFormat: 'pdf' | 'csv' | 'json';
  includeAnalysis?: boolean;
  includeCharts?: boolean;
}

// Generate CSV export
function generateCSV(data: any[]): string {
  if (data.length === 0) return '';

  const headers = Object.keys(data[0]);
  const csvRows = [headers.join(',')];

  for (const row of data) {
    const values = headers.map(header => {
      const value = row[header]?.toString() || '';
      // Escape quotes and wrap in quotes if contains comma
      return value.includes(',') ? `"${value.replace(/"/g, '""')}"` : value;
    });
    csvRows.push(values.join(','));
  }

  return csvRows.join('\n');
}

// Generate JSON export
function generateJSON(data: any, metadata: any): string {
  return JSON.stringify({
    metadata: {
      exportedAt: new Date().toISOString(),
      fileId: metadata.fileId,
      fileName: metadata.fileName,
      recordCount: Array.isArray(data) ? data.length : 1,
    },
    data: data,
  }, null, 2);
}

// Generate simple text-based PDF report
function generatePDFReport(fileInfo: any, analysis: any, extraction: any): string {
  const report = `
FILE ANALYSIS REPORT
Generated: ${new Date().toISOString()}

===================================
FILE INFORMATION
===================================
Filename: ${fileInfo.original_filename}
File Type: ${fileInfo.file_type}
File Size: ${(fileInfo.file_size / 1024).toFixed(2)} KB
Uploaded: ${new Date(fileInfo.created_at).toLocaleString()}

===================================
DATA EXTRACTION SUMMARY
===================================
${extraction ? `
Format: ${extraction.data_format || 'N/A'}
Total Rows: ${extraction.row_count || 0}
Total Columns: ${extraction.column_count || 0}

Column Summary:
${JSON.stringify(extraction.data_summary?.columns || {}, null, 2)}
` : 'No extraction data available'}

===================================
AI ANALYSIS RESULTS
===================================
${analysis?.map((a: any, idx: number) => `
Analysis ${idx + 1}: ${a.analysis_type}
Model: ${a.ai_model}
Confidence: ${(a.confidence_score * 100).toFixed(2)}%
Processing Time: ${a.processing_time_ms}ms

Result:
${JSON.stringify(a.result, null, 2)}
`).join('\n') || 'No AI analysis available'}

===================================
END OF REPORT
===================================
`;

  return report;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
    const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

    const { fileId, exportFormat, includeAnalysis, includeCharts } = await req.json() as ExportRequest;

    // Fetch file information
    const fileResponse = await fetch(
      `${SUPABASE_URL}/rest/v1/file_uploads?id=eq.${fileId}&select=*`,
      {
        headers: {
          'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
          'apikey': SUPABASE_SERVICE_ROLE_KEY,
        },
      }
    );

    if (!fileResponse.ok) {
      throw new Error('Failed to fetch file information');
    }

    const files = await fileResponse.json();
    const fileInfo = files[0];

    if (!fileInfo) {
      throw new Error('File not found');
    }

    // Fetch extraction data
    const extractionResponse = await fetch(
      `${SUPABASE_URL}/rest/v1/file_data_extraction?file_id=eq.${fileId}&select=*`,
      {
        headers: {
          'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
          'apikey': SUPABASE_SERVICE_ROLE_KEY,
        },
      }
    );

    const extractions = await extractionResponse.json();
    const extraction = extractions[0];

    // Fetch AI analysis if requested
    let analysis = null;
    if (includeAnalysis) {
      const analysisResponse = await fetch(
        `${SUPABASE_URL}/rest/v1/ai_file_analysis?file_id=eq.${fileId}&select=*`,
        {
          headers: {
            'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
            'apikey': SUPABASE_SERVICE_ROLE_KEY,
          },
        }
      );
      analysis = await analysisResponse.json();
    }

    // Generate export based on format
    let exportData: string;
    let contentType: string;
    let filename: string;

    switch (exportFormat) {
      case 'csv':
        if (!extraction?.full_data) {
          throw new Error('No data available for CSV export');
        }
        exportData = generateCSV(extraction.full_data);
        contentType = 'text/csv';
        filename = `export-${fileId}.csv`;
        break;

      case 'json':
        exportData = generateJSON(extraction?.full_data || {}, {
          fileId,
          fileName: fileInfo.original_filename,
        });
        contentType = 'application/json';
        filename = `export-${fileId}.json`;
        break;

      case 'pdf':
        exportData = generatePDFReport(fileInfo, analysis, extraction);
        contentType = 'text/plain'; // Simple text report (full PDF generation requires library)
        filename = `report-${fileId}.txt`;
        break;

      default:
        throw new Error('Unsupported export format');
    }

    // Create export job record
    await fetch(`${SUPABASE_URL}/rest/v1/file_export_jobs`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        file_id: fileId,
        export_format: exportFormat,
        export_status: 'completed',
        export_config: {
          includeAnalysis,
          includeCharts,
        },
        completed_at: new Date().toISOString(),
      }),
    });

    return new Response(
      JSON.stringify({
        success: true,
        data: {
          fileId,
          exportFormat,
          filename,
          content: exportData,
          size: exportData.length,
        },
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  } catch (error) {
    console.error('Export error:', error);
    return new Response(
      JSON.stringify({
        success: false,
        error: {
          code: 'EXPORT_FAILED',
          message: error.message || 'Export generation failed',
        },
      }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
