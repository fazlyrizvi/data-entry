// Enhanced Batch Processing Service
// Handles bulk data entry operations and batch file processing

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
        const { batchType, files, data, processingConfig = {} } = await req.json();

        if (!batchType) {
            throw new Error('Batch type is required');
        }

        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        const supabaseUrl = Deno.env.get('SUPABASE_URL');

        if (!serviceRoleKey || !supabaseUrl) {
            throw new Error('Supabase configuration missing');
        }

        const batchId = generateBatchId();
        const startTime = Date.now();

        console.log(`Starting batch processing: ${batchType} (${batchId})`);

        let batchResult: any = {
            batchId,
            batchType,
            startTime,
            status: 'processing',
            totalItems: 0,
            processedItems: 0,
            successfulItems: 0,
            failedItems: 0,
            results: [],
            errors: []
        };

        try {
            switch (batchType) {
                case 'file_processing':
                    batchResult = await processFileBatch(files, processingConfig, batchResult, serviceRoleKey, supabaseUrl);
                    break;
                case 'data_validation':
                    batchResult = await processDataValidationBatch(data, processingConfig, batchResult, serviceRoleKey, supabaseUrl);
                    break;
                case 'ocr_processing':
                    batchResult = await processOCRBatch(files, processingConfig, batchResult, serviceRoleKey, supabaseUrl);
                    break;
                case 'medical_records':
                    batchResult = await processMedicalRecordsBatch(files, processingConfig, batchResult, serviceRoleKey, supabaseUrl);
                    break;
                case 'customer_import':
                    batchResult = await processCustomerImportBatch(data, processingConfig, batchResult, serviceRoleKey, supabaseUrl);
                    break;
                case 'inventory_update':
                    batchResult = await processInventoryUpdateBatch(data, processingConfig, batchResult, serviceRoleKey, supabaseUrl);
                    break;
                case 'survey_processing':
                    batchResult = await processSurveyBatch(data, processingConfig, batchResult, serviceRoleKey, supabaseUrl);
                    break;
                default:
                    throw new Error(`Unsupported batch type: ${batchType}`);
            }

            batchResult.endTime = Date.now();
            batchResult.totalProcessingTimeMs = batchResult.endTime - startTime;
            batchResult.status = 'completed';

            // Update batch status
            await updateBatchStatus(batchId, batchResult, serviceRoleKey, supabaseUrl);

            console.log(`Batch processing completed: ${batchId}`, {
                totalItems: batchResult.totalItems,
                successfulItems: batchResult.successfulItems,
                failedItems: batchResult.failedItems
            });

            return new Response(JSON.stringify({
                data: batchResult
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } catch (error) {
            batchResult.status = 'failed';
            batchResult.error = error.message;
            batchResult.endTime = Date.now();
            batchResult.totalProcessingTimeMs = batchResult.endTime - startTime;

            // Update batch status with error
            await updateBatchStatus(batchId, batchResult, serviceRoleKey, supabaseUrl);

            console.error(`Batch processing failed: ${batchId}`, error);

            return new Response(JSON.stringify({
                data: batchResult
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

    } catch (error) {
        console.error('Batch processing service error:', error);

        const errorResponse = {
            error: {
                code: 'BATCH_PROCESSING_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

function generateBatchId(): string {
    return `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

async function processFileBatch(files: any[], config: any, batchResult: any, serviceRoleKey: string, supabaseUrl: string) {
    batchResult.totalItems = files.length;

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        try {
            console.log(`Processing file ${i + 1}/${files.length}: ${file.name}`);
            
            // Simulate file processing
            const result = await processFile(file, config);
            
            batchResult.results.push({
                fileName: file.name,
                status: 'success',
                result,
                processingTimeMs: result.processingTimeMs
            });
            
            batchResult.successfulItems++;
        } catch (error) {
            console.error(`Failed to process file ${file.name}:`, error);
            
            batchResult.results.push({
                fileName: file.name,
                status: 'failed',
                error: error.message
            });
            
            batchResult.failedItems++;
            batchResult.errors.push({
                fileName: file.name,
                error: error.message
            });
        }
        
        batchResult.processedItems++;
        
        // Update progress periodically
        if (i % 5 === 0 || i === files.length - 1) {
            await updateBatchProgress(batchResult.batchId, batchResult, serviceRoleKey, supabaseUrl);
        }
    }

    return batchResult;
}

async function processDataValidationBatch(data: any[], config: any, batchResult: any, serviceRoleKey: string, supabaseUrl: string) {
    batchResult.totalItems = data.length;
    const validationType = config.validationType || 'generic';

    for (let i = 0; i < data.length; i++) {
        const item = data[i];
        try {
            console.log(`Validating item ${i + 1}/${data.length}`);
            
            // Call validation service
            const validationResult = await callValidationService(validationType, item, serviceRoleKey, supabaseUrl);
            
            batchResult.results.push({
                item,
                status: 'success',
                validation: validationResult
            });
            
            batchResult.successfulItems++;
        } catch (error) {
            console.error(`Failed to validate item:`, error);
            
            batchResult.results.push({
                item,
                status: 'failed',
                error: error.message
            });
            
            batchResult.failedItems++;
            batchResult.errors.push({
                item,
                error: error.message
            });
        }
        
        batchResult.processedItems++;
        
        if (i % 10 === 0 || i === data.length - 1) {
            await updateBatchProgress(batchResult.batchId, batchResult, serviceRoleKey, supabaseUrl);
        }
    }

    return batchResult;
}

async function processOCRBatch(files: any[], config: any, batchResult: any, serviceRoleKey: string, supabaseUrl: string) {
    batchResult.totalItems = files.length;
    const documentType = config.documentType || 'general_text';

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        try {
            console.log(`OCR processing file ${i + 1}/${files.length}: ${file.name}`);
            
            // Call document processing service
            const ocrResult = await callDocumentProcessingService(file, documentType, serviceRoleKey, supabaseUrl);
            
            batchResult.results.push({
                fileName: file.name,
                status: 'success',
                ocr: ocrResult
            });
            
            batchResult.successfulItems++;
        } catch (error) {
            console.error(`Failed to OCR process file ${file.name}:`, error);
            
            batchResult.results.push({
                fileName: file.name,
                status: 'failed',
                error: error.message
            });
            
            batchResult.failedItems++;
            batchResult.errors.push({
                fileName: file.name,
                error: error.message
            });
        }
        
        batchResult.processedItems++;
        
        if (i % 3 === 0 || i === files.length - 1) {
            await updateBatchProgress(batchResult.batchId, batchResult, serviceRoleKey, supabaseUrl);
        }
    }

    return batchResult;
}

async function processMedicalRecordsBatch(files: any[], config: any, batchResult: any, serviceRoleKey: string, supabaseUrl: string) {
    batchResult.totalItems = files.length;

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        try {
            console.log(`Processing medical record ${i + 1}/${files.length}: ${file.name}`);
            
            // Process as medical form
            const ocrResult = await callDocumentProcessingService(file, 'medical_form', serviceRoleKey, supabaseUrl);
            const validationResult = await callValidationService('medical_record', ocrResult.structuredData, serviceRoleKey, supabaseUrl);
            
            batchResult.results.push({
                fileName: file.name,
                status: 'success',
                medicalRecord: ocrResult.structuredData,
                validation: validationResult
            });
            
            batchResult.successfulItems++;
        } catch (error) {
            console.error(`Failed to process medical record ${file.name}:`, error);
            
            batchResult.results.push({
                fileName: file.name,
                status: 'failed',
                error: error.message
            });
            
            batchResult.failedItems++;
        }
        
        batchResult.processedItems++;
    }

    return batchResult;
}

async function processCustomerImportBatch(data: any[], config: any, batchResult: any, serviceRoleKey: string, supabaseUrl: string) {
    batchResult.totalItems = data.length;

    for (let i = 0; i < data.length; i++) {
        const customer = data[i];
        try {
            console.log(`Processing customer ${i + 1}/${data.length}`);
            
            // Validate customer data
            const validationResult = await callValidationService('customer_data', customer, serviceRoleKey, supabaseUrl);
            
            if (validationResult.success && validationResult.validation?.isValid) {
                // Store in database (simplified)
                const stored = await storeCustomerData(customer, serviceRoleKey, supabaseUrl);
                
                batchResult.results.push({
                    customer,
                    status: 'success',
                    stored,
                    validation: validationResult
                });
                
                batchResult.successfulItems++;
            } else {
                throw new Error('Customer data validation failed');
            }
        } catch (error) {
            console.error(`Failed to process customer:`, error);
            
            batchResult.results.push({
                customer,
                status: 'failed',
                error: error.message
            });
            
            batchResult.failedItems++;
        }
        
        batchResult.processedItems++;
    }

    return batchResult;
}

async function processInventoryUpdateBatch(data: any[], config: any, batchResult: any, serviceRoleKey: string, supabaseUrl: string) {
    batchResult.totalItems = data.length;

    for (let i = 0; i < data.length; i++) {
        const item = data[i];
        try {
            console.log(`Processing inventory item ${i + 1}/${data.length}`);
            
            // Validate inventory data
            const validationResult = await callValidationService('inventory_data', item, serviceRoleKey, supabaseUrl);
            
            if (validationResult.success && validationResult.validation?.isValid) {
                // Update inventory (simplified)
                const updated = await updateInventoryItem(item, serviceRoleKey, supabaseUrl);
                
                batchResult.results.push({
                    item,
                    status: 'success',
                    updated,
                    validation: validationResult
                });
                
                batchResult.successfulItems++;
            } else {
                throw new Error('Inventory data validation failed');
            }
        } catch (error) {
            console.error(`Failed to process inventory item:`, error);
            
            batchResult.results.push({
                item,
                status: 'failed',
                error: error.message
            });
            
            batchResult.failedItems++;
        }
        
        batchResult.processedItems++;
    }

    return batchResult;
}

async function processSurveyBatch(data: any[], config: any, batchResult: any, serviceRoleKey: string, supabaseUrl: string) {
    batchResult.totalItems = data.length;

    for (let i = 0; i < data.length; i++) {
        const response = data[i];
        try {
            console.log(`Processing survey response ${i + 1}/${data.length}`);
            
            // Validate survey data
            const validationResult = await callValidationService('survey_data', response, serviceRoleKey, supabaseUrl);
            
            if (validationResult.success && validationResult.validation?.isValid) {
                // Store survey response (simplified)
                const stored = await storeSurveyResponse(response, serviceRoleKey, supabaseUrl);
                
                batchResult.results.push({
                    response,
                    status: 'success',
                    stored,
                    validation: validationResult
                });
                
                batchResult.successfulItems++;
            } else {
                throw new Error('Survey data validation failed');
            }
        } catch (error) {
            console.error(`Failed to process survey response:`, error);
            
            batchResult.results.push({
                response,
                status: 'failed',
                error: error.message
            });
            
            batchResult.failedItems++;
        }
        
        batchResult.processedItems++;
    }

    return batchResult;
}

async function processFile(file: any, config: any) {
    // Simulate file processing
    await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 500));
    
    return {
        success: true,
        extractedText: `Processed content from ${file.name}`,
        metadata: {
            size: file.size,
            type: file.type,
            lastModified: file.lastModified
        },
        processingTimeMs: Math.random() * 1000 + 500
    };
}

async function callValidationService(validationType: string, data: any, serviceRoleKey: string, supabaseUrl: string) {
    try {
        const response = await fetch(`${supabaseUrl}/functions/v1/data-validation-enhanced`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                validationType,
                data,
                batchMode: true
            })
        });

        if (!response.ok) {
            throw new Error(`Validation service error: ${response.statusText}`);
        }

        const result = await response.json();
        return result.data?.results?.[0] || result.data;
    } catch (error) {
        throw new Error(`Validation service call failed: ${error.message}`);
    }
}

async function callDocumentProcessingService(file: any, documentType: string, serviceRoleKey: string, supabaseUrl: string) {
    try {
        const response = await fetch(`${supabaseUrl}/functions/v1/document-processing-enhanced`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                documentType,
                fileData: file.content || 'base64-encoded-content',
                fileName: file.name,
                processingOptions: {}
            })
        });

        if (!response.ok) {
            throw new Error(`Document processing service error: ${response.statusText}`);
        }

        const result = await response.json();
        return result.data;
    } catch (error) {
        throw new Error(`Document processing service call failed: ${error.message}`);
    }
}

async function storeCustomerData(customer: any, serviceRoleKey: string, supabaseUrl: string) {
    // Simulate storing customer data
    console.log('Storing customer data:', customer);
    return { id: Math.random().toString(36).substr(2, 9), stored: true };
}

async function updateInventoryItem(item: any, serviceRoleKey: string, supabaseUrl: string) {
    // Simulate updating inventory
    console.log('Updating inventory item:', item);
    return { sku: item.sku, updated: true };
}

async function storeSurveyResponse(response: any, serviceRoleKey: string, supabaseUrl: string) {
    // Simulate storing survey response
    console.log('Storing survey response:', response);
    return { id: Math.random().toString(36).substr(2, 9), stored: true };
}

async function updateBatchStatus(batchId: string, batchResult: any, serviceRoleKey: string, supabaseUrl: string) {
    try {
        // In production, would update batch status in database
        console.log(`Batch ${batchId} status updated:`, batchResult.status);
    } catch (error) {
        console.error('Failed to update batch status:', error);
    }
}

async function updateBatchProgress(batchId: string, batchResult: any, serviceRoleKey: string, supabaseUrl: string) {
    try {
        // In production, would update batch progress in database
        const progress = Math.round((batchResult.processedItems / batchResult.totalItems) * 100);
        console.log(`Batch ${batchId} progress: ${progress}%`);
    } catch (error) {
        console.error('Failed to update batch progress:', error);
    }
}
