// Enhanced Document Processing Service
// Handles OCR, text extraction, and document analysis for data entry automation

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
        const { documentType, fileData, fileName, processingOptions = {} } = await req.json();

        if (!documentType || !fileData || !fileName) {
            throw new Error('Document type, file data, and filename are required');
        }

        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        const supabaseUrl = Deno.env.get('SUPABASE_URL');

        if (!serviceRoleKey || !supabaseUrl) {
            throw new Error('Supabase configuration missing');
        }

        const startTime = Date.now();
        let result: any = {
            fileName,
            documentType,
            timestamp: new Date().toISOString()
        };

        try {
            // Process based on document type
            switch (documentType) {
                case 'invoice':
                    result = await processInvoice(fileData, processingOptions, result);
                    break;
                case 'medical_form':
                    result = await processMedicalForm(fileData, processingOptions, result);
                    break;
                case 'customer_form':
                    result = await processCustomerForm(fileData, processingOptions, result);
                    break;
                case 'inventory_sheet':
                    result = await processInventorySheet(fileData, processingOptions, result);
                    break;
                case 'survey_form':
                    result = await processSurveyForm(fileData, processingOptions, result);
                    break;
                case 'general_text':
                    result = await processGeneralText(fileData, processingOptions, result);
                    break;
                default:
                    result = await processGenericDocument(fileData, processingOptions, result);
            }

            result.processingTimeMs = Date.now() - startTime;
            
            // Store extraction results
            await storeExtractionResults(result, serviceRoleKey, supabaseUrl);

            return new Response(JSON.stringify({
                data: result
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } catch (error) {
            result.error = error.message;
            result.success = false;
            result.processingTimeMs = Date.now() - startTime;

            return new Response(JSON.stringify({
                data: result
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

    } catch (error) {
        console.error('Document processing error:', error);

        const errorResponse = {
            error: {
                code: 'DOCUMENT_PROCESSING_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

async function processInvoice(fileData: string, options: any, result: any) {
    // Simulate OCR text extraction (in production, would use actual OCR service)
    const extractedText = await simulateOCR(fileData);
    
    // Parse invoice-specific data
    const invoiceData = parseInvoiceText(extractedText);
    
    return {
        ...result,
        success: true,
        extractedText,
        structuredData: invoiceData,
        confidence: 0.85,
        confidenceScore: 0.85,
        extractionMethod: 'enhanced_pattern_matching',
        metadata: {
            documentType: 'invoice',
            fieldsFound: Object.keys(invoiceData).length,
            language: 'en'
        }
    };
}

async function processMedicalForm(fileData: string, options: any, result: any) {
    const extractedText = await simulateOCR(fileData);
    const medicalData = parseMedicalFormText(extractedText);
    
    return {
        ...result,
        success: true,
        extractedText,
        structuredData: medicalData,
        confidence: 0.90,
        confidenceScore: 0.90,
        extractionMethod: 'medical_form_parsing',
        metadata: {
            documentType: 'medical',
            fieldsFound: Object.keys(medicalData).length,
            sensitiveData: true
        }
    };
}

async function processCustomerForm(fileData: string, options: any, result: any) {
    const extractedText = await simulateOCR(fileData);
    const customerData = parseCustomerFormText(extractedText);
    
    return {
        ...result,
        success: true,
        extractedText,
        structuredData: customerData,
        confidence: 0.88,
        confidenceScore: 0.88,
        extractionMethod: 'customer_form_parsing',
        metadata: {
            documentType: 'customer',
            fieldsFound: Object.keys(customerData).length
        }
    };
}

async function processInventorySheet(fileData: string, options: any, result: any) {
    const extractedText = await simulateOCR(fileData);
    const inventoryData = parseInventorySheetText(extractedText);
    
    return {
        ...result,
        success: true,
        extractedText,
        structuredData: inventoryData,
        confidence: 0.82,
        confidenceScore: 0.82,
        extractionMethod: 'inventory_sheet_parsing',
        metadata: {
            documentType: 'inventory',
            fieldsFound: Object.keys(inventoryData).length,
            rowCount: inventoryData.items?.length || 0
        }
    };
}

async function processSurveyForm(fileData: string, options: any, result: any) {
    const extractedText = await simulateOCR(fileData);
    const surveyData = parseSurveyFormText(extractedText);
    
    return {
        ...result,
        success: true,
        extractedText,
        structuredData: surveyData,
        confidence: 0.87,
        confidenceScore: 0.87,
        extractionMethod: 'survey_form_parsing',
        metadata: {
            documentType: 'survey',
            fieldsFound: Object.keys(surveyData).length,
            questionCount: surveyData.responses?.length || 0
        }
    };
}

async function processGeneralText(fileData: string, options: any, result: any) {
    const extractedText = await simulateOCR(fileData);
    const generalData = parseGeneralText(extractedText);
    
    return {
        ...result,
        success: true,
        extractedText,
        structuredData: generalData,
        confidence: 0.75,
        confidenceScore: 0.75,
        extractionMethod: 'general_text_parsing',
        metadata: {
            documentType: 'general',
            textLength: extractedText.length
        }
    };
}

async function processGenericDocument(fileData: string, options: any, result: any) {
    const extractedText = await simulateOCR(fileData);
    const genericData = extractKeyEntities(extractedText);
    
    return {
        ...result,
        success: true,
        extractedText,
        structuredData: genericData,
        confidence: 0.70,
        confidenceScore: 0.70,
        extractionMethod: 'generic_entity_extraction',
        metadata: {
            documentType: 'generic',
            entitiesFound: Object.keys(genericData).length
        }
    };
}

async function simulateOCR(fileData: string): Promise<string> {
    // In production, this would call actual OCR services
    // For now, simulate OCR output based on file type
    return `
        Sample Document Content
        =======================
        
        Date: 2025-11-01
        Invoice #: INV-2025-001
        Amount: $1,299.50
        
        Items:
        1. Product A - $450.00
        2. Product B - $849.50
        
        Total: $1,299.50
        
        Contact: John Doe
        Email: john@example.com
        Phone: +1-555-0123
        
        Thank you for your business!
    `;
}

function parseInvoiceText(text: string) {
    const lines = text.split('\n').map(line => line.trim()).filter(line => line);
    
    const invoiceData: any = {
        invoiceNumber: null,
        date: null,
        amount: null,
        items: [],
        vendor: null,
        customer: null
    };

    // Parse invoice number
    const invoiceMatch = text.match(/Invoice\s*#?:\s*([A-Z0-9\-]+)/i);
    if (invoiceMatch) {
        invoiceData.invoiceNumber = invoiceMatch[1];
    }

    // Parse date
    const dateMatch = text.match(/Date:\s*([0-9\-]+)/);
    if (dateMatch) {
        invoiceData.date = dateMatch[1];
    }

    // Parse amount
    const amountMatch = text.match(/Total:\s*\$([0-9,]+\.[0-9]+)/);
    if (amountMatch) {
        invoiceData.amount = parseFloat(amountMatch[1].replace(',', ''));
    }

    // Parse customer
    const customerMatch = text.match(/Contact:\s*(.+)/);
    if (customerMatch) {
        invoiceData.customer = {
            name: customerMatch[1].trim(),
            email: null,
            phone: null
        };
    }

    // Parse email
    const emailMatch = text.match(/Email:\s*([\w\.-]+@[\w\.-]+)/);
    if (emailMatch) {
        if (!invoiceData.customer) invoiceData.customer = {};
        invoiceData.customer.email = emailMatch[1];
    }

    // Parse phone
    const phoneMatch = text.match(/Phone:\s*([\+\d\-\s\(\)]+)/);
    if (phoneMatch) {
        if (!invoiceData.customer) invoiceData.customer = {};
        invoiceData.customer.phone = phoneMatch[1].trim();
    }

    // Parse items (simplified)
    const itemMatches = [...text.matchAll(/(\d+)\.\s*(.+?)\s*-\s*\$([0-9,]+\.[0-9]+)/g)];
    if (itemMatches.length > 0) {
        invoiceData.items = itemMatches.map(match => ({
            number: parseInt(match[1]),
            description: match[2].trim(),
            amount: parseFloat(match[3].replace(',', ''))
        }));
    }

    return invoiceData;
}

function parseMedicalFormText(text: string) {
    const medicalData: any = {
        patientId: null,
        firstName: null,
        lastName: null,
        dateOfBirth: null,
        address: null,
        phone: null,
        insuranceInfo: null,
        diagnosis: null,
        symptoms: []
    };

    // Parse patient ID
    const patientIdMatch = text.match(/Patient\s*ID:\s*([A-Z0-9\-]+)/i);
    if (patientIdMatch) {
        medicalData.patientId = patientIdMatch[1];
    }

    // Parse name
    const nameMatch = text.match(/Name:\s*(.+)/);
    if (nameMatch) {
        const parts = nameMatch[1].trim().split(' ');
        if (parts.length >= 2) {
            medicalData.firstName = parts[0];
            medicalData.lastName = parts[parts.length - 1];
        }
    }

    // Parse date of birth
    const dobMatch = text.match(/DOB:\s*([0-9\-]+)/);
    if (dobMatch) {
        medicalData.dateOfBirth = dobMatch[1];
    }

    // Parse address
    const addressMatch = text.match(/Address:\s*(.+?)(?:\n|$)/);
    if (addressMatch) {
        medicalData.address = addressMatch[1].trim();
    }

    // Parse phone
    const phoneMatch = text.match(/Phone:\s*([\+\d\-\s\(\)]+)/);
    if (phoneMatch) {
        medicalData.phone = phoneMatch[1].trim();
    }

    // Parse diagnosis
    const diagnosisMatch = text.match(/Diagnosis:\s*(.+)/);
    if (diagnosisMatch) {
        medicalData.diagnosis = diagnosisMatch[1].trim();
    }

    return medicalData;
}

function parseCustomerFormText(text: string) {
    const customerData: any = {
        firstName: null,
        lastName: null,
        email: null,
        phone: null,
        address: null,
        company: null,
        title: null
    };

    // Parse first name
    const firstNameMatch = text.match(/First\s*Name:\s*(.+)/);
    if (firstNameMatch) {
        customerData.firstName = firstNameMatch[1].trim();
    }

    // Parse last name
    const lastNameMatch = text.match(/Last\s*Name:\s*(.+)/);
    if (lastNameMatch) {
        customerData.lastName = lastNameMatch[1].trim();
    }

    // Parse email
    const emailMatch = text.match(/Email:\s*([\w\.-]+@[\w\.-]+)/);
    if (emailMatch) {
        customerData.email = emailMatch[1];
    }

    // Parse phone
    const phoneMatch = text.match(/Phone:\s*([\+\d\-\s\(\)]+)/);
    if (phoneMatch) {
        customerData.phone = phoneMatch[1].trim();
    }

    // Parse address
    const addressMatch = text.match(/Address:\s*(.+?)(?:\n|$)/);
    if (addressMatch) {
        customerData.address = addressMatch[1].trim();
    }

    // Parse company
    const companyMatch = text.match(/Company:\s*(.+)/);
    if (companyMatch) {
        customerData.company = companyMatch[1].trim();
    }

    // Parse title
    const titleMatch = text.match(/Title:\s*(.+)/);
    if (titleMatch) {
        customerData.title = titleMatch[1].trim();
    }

    return customerData;
}

function parseInventorySheetText(text: string) {
    const inventoryData: any = {
        warehouse: null,
        date: null,
        items: []
    };

    // Parse warehouse
    const warehouseMatch = text.match(/Warehouse:\s*(.+)/);
    if (warehouseMatch) {
        inventoryData.warehouse = warehouseMatch[1].trim();
    }

    // Parse date
    const dateMatch = text.match(/Date:\s*([0-9\-]+)/);
    if (dateMatch) {
        inventoryData.date = dateMatch[1];
    }

    // Parse inventory items
    const itemMatches = [...text.matchAll(/(\d+)\.\s*(.+?)\s+SKU:\s*([A-Z0-9\-]+)\s+Qty:\s*(\d+)/g)];
    if (itemMatches.length > 0) {
        inventoryData.items = itemMatches.map(match => ({
            number: parseInt(match[1]),
            description: match[2].trim(),
            sku: match[3],
            quantity: parseInt(match[4])
        }));
    }

    return inventoryData;
}

function parseSurveyFormText(text: string) {
    const surveyData: any = {
        surveyId: null,
        respondentId: null,
        date: null,
        responses: []
    };

    // Parse survey ID
    const surveyIdMatch = text.match(/Survey\s*ID:\s*([A-Z0-9\-]+)/);
    if (surveyIdMatch) {
        surveyData.surveyId = surveyIdMatch[1];
    }

    // Parse respondent ID
    const respondentMatch = text.match(/Respondent\s*ID:\s*([A-Z0-9\-]+)/);
    if (respondentMatch) {
        surveyData.respondentId = respondentMatch[1];
    }

    // Parse date
    const dateMatch = text.match(/Date:\s*([0-9\-]+)/);
    if (dateMatch) {
        surveyData.date = dateMatch[1];
    }

    // Parse responses
    const responseMatches = [...text.matchAll(/Q(\d+):\s*(.+?)\s*A:\s*(.+)/g)];
    if (responseMatches.length > 0) {
        surveyData.responses = responseMatches.map(match => ({
            questionNumber: parseInt(match[1]),
            question: match[2].trim(),
            answer: match[3].trim()
        }));
    }

    return surveyData;
}

function parseGeneralText(text: string) {
    return {
        textLength: text.length,
        wordCount: text.split(/\s+/).length,
        lineCount: text.split('\n').length,
        hasDates: /\d{4}-\d{2}-\d{2}/.test(text),
        hasEmails: /[\w\.-]+@[\w\.-]+/.test(text),
        hasPhoneNumbers: /[\+\d\-\s\(\)]{10,}/.test(text),
        hasCurrency: /\$[\d,]+\.?\d*/.test(text)
    };
}

function extractKeyEntities(text: string) {
    const entities: any = {
        emails: [],
        phoneNumbers: [],
        dates: [],
        currency: [],
        urls: [],
        addresses: []
    };

    // Extract emails
    const emailMatches = [...text.matchAll(/[\w\.-]+@[\w\.-]+/g)];
    entities.emails = emailMatches.map(match => match[0]);

    // Extract phone numbers
    const phoneMatches = [...text.matchAll(/[\+\d\-\s\(\)]{10,}/g)];
    entities.phoneNumbers = phoneMatches.map(match => match[0].trim());

    // Extract dates
    const dateMatches = [...text.matchAll(/\d{4}-\d{2}-\d{2}/g)];
    entities.dates = dateMatches.map(match => match[0]);

    // Extract currency
    const currencyMatches = [...text.matchAll(/\$[\d,]+\.?\d*/g)];
    entities.currency = currencyMatches.map(match => match[0]);

    // Extract URLs
    const urlMatches = [...text.matchAll(/https?:\/\/[^\s]+/g)];
    entities.urls = urlMatches.map(match => match[0]);

    return entities;
}

async function storeExtractionResults(result: any, serviceRoleKey: string, supabaseUrl: string) {
    try {
        const extractionRecord = {
            extraction_method: result.extractionMethod,
            raw_data: JSON.stringify({ extractedText: result.extractedText }),
            structured_data: JSON.stringify(result.structuredData),
            confidence_score: result.confidenceScore,
            extraction_config: JSON.stringify({
                documentType: result.documentType,
                processingTimeMs: result.processingTimeMs,
                metadata: result.metadata
            }),
            created_at: new Date().toISOString()
        };

        await fetch(`${supabaseUrl}/rest/v1/extracted_data`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(extractionRecord)
        });
    } catch (error) {
        console.error('Failed to store extraction results:', error);
        // Don't fail the extraction if storage fails
    }
}
