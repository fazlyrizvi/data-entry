// Enhanced Data Export Service
// Handles exporting processed data to multiple formats (CSV, Excel, JSON)

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
        const { data, exportFormat, exportOptions = {}, batchMode = false } = await req.json();

        if (!data || !exportFormat) {
            throw new Error('Data and export format are required');
        }

        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        const supabaseUrl = Deno.env.get('SUPABASE_URL');

        if (!serviceRoleKey || !supabaseUrl) {
            throw new Error('Supabase configuration missing');
        }

        const startTime = Date.now();
        const exportId = generateExportId();

        console.log(`Starting data export: ${exportFormat} (${exportId})`);

        let result: any = {
            exportId,
            exportFormat,
            status: 'processing',
            startTime,
            data: null,
            fileName: null,
            content: null,
            downloadUrl: null
        };

        try {
            // Generate export based on format
            switch (exportFormat.toLowerCase()) {
                case 'csv':
                    result = await exportToCSV(data, exportOptions, result);
                    break;
                case 'excel':
                    result = await exportToExcel(data, exportOptions, result);
                    break;
                case 'json':
                    result = await exportToJSON(data, exportOptions, result);
                    break;
                case 'pdf':
                    result = await exportToPDF(data, exportOptions, result);
                    break;
                case 'xml':
                    result = await exportToXML(data, exportOptions, result);
                    break;
                default:
                    throw new Error(`Unsupported export format: ${exportFormat}`);
            }

            result.endTime = Date.now();
            result.processingTimeMs = result.endTime - startTime;
            result.status = 'completed';

            // Store export job and upload file
            const uploadResult = await storeAndUploadExport(result, serviceRoleKey, supabaseUrl);
            result.downloadUrl = uploadResult.downloadUrl;

            console.log(`Data export completed: ${exportId}`);

            return new Response(JSON.stringify({
                data: result
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } catch (error) {
            result.status = 'failed';
            result.error = error.message;
            result.endTime = Date.now();
            result.processingTimeMs = result.endTime - startTime;

            console.error(`Data export failed: ${exportId}`, error);

            return new Response(JSON.stringify({
                data: result
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

    } catch (error) {
        console.error('Data export service error:', error);

        const errorResponse = {
            error: {
                code: 'DATA_EXPORT_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

function generateExportId(): string {
    return `export_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

async function exportToCSV(data: any[], options: any, result: any) {
    console.log('Exporting to CSV format');
    
    // Flatten data objects for CSV
    const flattenedData = data.map(item => flattenObject(item));
    
    // Get headers from first row or options
    const headers = options.headers || Object.keys(flattenedData[0] || {});
    
    // Generate CSV content
    const csvLines = [];
    
    // Add headers
    csvLines.push(headers.join(','));
    
    // Add data rows
    for (const row of flattenedData) {
        const values = headers.map(header => {
            let value = row[header] || '';
            // Escape commas and quotes in CSV
            if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
                value = '"' + value.replace(/"/g, '""') + '"';
            }
            return value;
        });
        csvLines.push(values.join(','));
    }
    
    const csvContent = csvLines.join('\n');
    
    result.fileName = `data_export_${Date.now()}.csv`;
    result.content = csvContent;
    result.headers = headers;
    result.recordCount = data.length;
    result.size = csvContent.length;
    
    console.log(`CSV export completed: ${data.length} records, ${csvContent.length} characters`);
    
    return result;
}

async function exportToExcel(data: any[], options: any, result: any) {
    console.log('Exporting to Excel format');
    
    // For Excel, we'll create a simple XML-based format that Excel can read
    // In production, would use a proper Excel library
    
    const flattenedData = data.map(item => flattenObject(item));
    const headers = options.headers || Object.keys(flattenedData[0] || {});
    
    // Create basic Excel XML format
    const excelXml = generateExcelXML(flattenedData, headers, options);
    
    result.fileName = `data_export_${Date.now()}.xlsx`;
    result.content = excelXml;
    result.headers = headers;
    result.recordCount = data.length;
    result.size = excelXml.length;
    
    console.log(`Excel export completed: ${data.length} records`);
    
    return result;
}

async function exportToJSON(data: any[], options: any, result: any) {
    console.log('Exporting to JSON format');
    
    let jsonContent: string;
    
    if (options.format === 'pretty') {
        jsonContent = JSON.stringify(data, null, 2);
    } else {
        jsonContent = JSON.stringify(data);
    }
    
    // Add metadata if requested
    if (options.includeMetadata) {
        const metadata = {
            exportDate: new Date().toISOString(),
            recordCount: data.length,
            exportFormat: 'JSON',
            ...options.metadata
        };
        
        const jsonWithMetadata = {
            metadata,
            data: data
        };
        
        jsonContent = options.format === 'pretty' ? 
            JSON.stringify(jsonWithMetadata, null, 2) : 
            JSON.stringify(jsonWithMetadata);
    }
    
    result.fileName = `data_export_${Date.now()}.json`;
    result.content = jsonContent;
    result.recordCount = data.length;
    result.size = jsonContent.length;
    
    console.log(`JSON export completed: ${data.length} records`);
    
    return result;
}

async function exportToPDF(data: any[], options: any, result: any) {
    console.log('Exporting to PDF format');
    
    // For PDF, we'll create a basic formatted text that can be converted
    // In production, would use a proper PDF library
    
    const flattenedData = data.map(item => flattenObject(item));
    const headers = options.headers || Object.keys(flattenedData[0] || {});
    
    const pdfContent = generatePDFContent(flattenedData, headers, options);
    
    result.fileName = `data_export_${Date.now()}.pdf`;
    result.content = pdfContent;
    result.headers = headers;
    result.recordCount = data.length;
    result.size = pdfContent.length;
    
    console.log(`PDF export completed: ${data.length} records`);
    
    return result;
}

async function exportToXML(data: any[], options: any, result: any) {
    console.log('Exporting to XML format');
    
    const rootElement = options.rootElement || 'data';
    const itemElement = options.itemElement || 'record';
    
    let xmlContent = `<?xml version="1.0" encoding="UTF-8"?>\n`;
    xmlContent += `<${rootElement}>\n`;
    
    for (const item of data) {
        const flattened = flattenObject(item);
        xmlContent += `  <${itemElement}>\n`;
        
        for (const [key, value] of Object.entries(flattened)) {
            const xmlKey = key.replace(/[^a-zA-Z0-9]/g, '_'); // Sanitize for XML
            xmlContent += `    <${xmlKey}>${escapeXML(value)}</${xmlKey}>\n`;
        }
        
        xmlContent += `  </${itemElement}>\n`;
    }
    
    xmlContent += `</${rootElement}>`;
    
    result.fileName = `data_export_${Date.now()}.xml`;
    result.content = xmlContent;
    result.recordCount = data.length;
    result.size = xmlContent.length;
    
    console.log(`XML export completed: ${data.length} records`);
    
    return result;
}

function flattenObject(obj: any, prefix = ''): any {
    const flattened: any = {};
    
    for (const [key, value] of Object.entries(obj)) {
        const newKey = prefix ? `${prefix}.${key}` : key;
        
        if (value && typeof value === 'object' && !Array.isArray(value) && !(value instanceof Date)) {
            Object.assign(flattened, flattenObject(value, newKey));
        } else if (Array.isArray(value)) {
            flattened[newKey] = JSON.stringify(value);
        } else {
            flattened[newKey] = value;
        }
    }
    
    return flattened;
}

function generateExcelXML(data: any[], headers: string[], options: any): string {
    // Simple Excel XML format
    let xml = `<?xml version="1.0"?>\n`;
    xml += `<?mso-application progid="Excel.Sheet"?>\n`;
    xml += `<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"\n`;
    xml += ` xmlns:o="urn:schemas-microsoft-com:office:office"\n`;
    xml += ` xmlns:x="urn:schemas-microsoft-com:office:excel"\n`;
    xml += ` xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">\n`;
    xml += `<Worksheet ss:Name="Export">\n`;
    xml += `<Table>\n`;
    
    // Headers
    xml += `<Row>\n`;
    for (const header of headers) {
        xml += `<Cell><Data ss:Type="String">${escapeXML(header)}</Data></Cell>\n`;
    }
    xml += `</Row>\n`;
    
    // Data rows
    for (const row of data) {
        xml += `<Row>\n`;
        for (const header of headers) {
            const value = row[header] || '';
            const dataType = typeof value === 'number' ? 'Number' : 'String';
            xml += `<Cell><Data ss:Type="${dataType}">${escapeXML(value)}</Data></Cell>\n`;
        }
        xml += `</Row>\n`;
    }
    
    xml += `</Table>\n`;
    xml += `</Worksheet>\n`;
    xml += `</Workbook>`;
    
    return xml;
}

function generatePDFContent(data: any[], headers: string[], options: any): string {
    let content = 'Data Export Report\n';
    content += '==================\n\n';
    content += `Generated: ${new Date().toISOString()}\n`;
    content += `Record Count: ${data.length}\n\n`;
    
    // Table format
    content += 'Data Records:\n';
    content += '-'.repeat(80) + '\n';
    
    // Headers
    content += headers.map(h => h.padEnd(20)).join(' | ') + '\n';
    content += '-'.repeat(80) + '\n';
    
    // Data rows
    for (const row of data) {
        const values = headers.map(header => {
            const value = row[header] || '';
            return String(value).padEnd(20);
        });
        content += values.join(' | ') + '\n';
    }
    
    return content;
}

function escapeXML(value: any): string {
    if (value === null || value === undefined) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&apos;');
}

async function storeAndUploadExport(result: any, serviceRoleKey: string, supabaseUrl: string) {
    try {
        // Create export job record
        const exportRecord = {
            export_format: result.exportFormat,
            export_status: result.status,
            export_config: JSON.stringify({
                fileName: result.fileName,
                recordCount: result.recordCount,
                size: result.size,
                processingTimeMs: result.processingTimeMs
            }),
            created_at: new Date().toISOString()
        };

        const insertResponse = await fetch(`${supabaseUrl}/rest/v1/file_export_jobs`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            },
            body: JSON.stringify(exportRecord)
        });

        if (!insertResponse.ok) {
            console.error('Failed to create export job record');
        }

        // Convert content to base64 for storage
        const content = typeof result.content === 'string' ? 
            btoa(result.content) : 
            btoa(JSON.stringify(result.content));

        // Generate storage path
        const timestamp = Date.now();
        const storagePath = `exports/${result.exportFormat}/${timestamp}-${result.fileName}`;

        // Upload to Supabase Storage
        const uploadResponse = await fetch(`${supabaseUrl}/storage/v1/object/uploaded-files/${storagePath}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'Content-Type': 'application/octet-stream',
                'x-upsert': 'true'
            },
            body: content
        });

        if (!uploadResponse.ok) {
            const errorText = await uploadResponse.text();
            throw new Error(`Upload failed: ${errorText}`);
        }

        // Get public URL
        const downloadUrl = `${supabaseUrl}/storage/v1/object/public/uploaded-files/${storagePath}`;

        console.log(`Export file uploaded: ${downloadUrl}`);

        return {
            downloadUrl,
            storagePath,
            uploadSuccess: true
        };

    } catch (error) {
        console.error('Failed to store and upload export:', error);
        return {
            downloadUrl: null,
            storagePath: null,
            uploadSuccess: false,
            error: error.message
        };
    }
}
