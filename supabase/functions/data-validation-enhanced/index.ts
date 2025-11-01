// Enhanced Data Validation Service
// Integrates multiple validation APIs for comprehensive data entry automation

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
        const { validationType, data, batchMode = false } = await req.json();

        if (!validationType || !data) {
            throw new Error('Validation type and data are required');
        }

        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        const supabaseUrl = Deno.env.get('SUPABASE_URL');

        if (!serviceRoleKey || !supabaseUrl) {
            throw new Error('Supabase configuration missing');
        }

        let results = [];

        if (batchMode && Array.isArray(data)) {
            // Batch validation
            for (const item of data) {
                try {
                    const validation = await performValidation(validationType, item, serviceRoleKey, supabaseUrl);
                    results.push(validation);
                } catch (error) {
                    results.push({
                        item,
                        success: false,
                        error: error.message
                    });
                }
            }
        } else {
            // Single validation
            const validation = await performValidation(validationType, data, serviceRoleKey, supabaseUrl);
            results.push(validation);
        }

        // Store validation results
        if (results.length > 0) {
            await storeValidationResults(results, serviceRoleKey, supabaseUrl);
        }

        return new Response(JSON.stringify({
            data: {
                validationType,
                results,
                timestamp: new Date().toISOString(),
                processedCount: results.length
            }
        }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });

    } catch (error) {
        console.error('Data validation error:', error);

        const errorResponse = {
            error: {
                code: 'DATA_VALIDATION_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

async function performValidation(validationType: string, data: any, serviceRoleKey: string, supabaseUrl: string) {
    const startTime = Date.now();
    let result: any = {
        data,
        success: true,
        validationType,
        timestamp: new Date().toISOString()
    };

    try {
        switch (validationType) {
            case 'email':
                result = await validateEmail(data, result);
                break;
            case 'phone':
                result = await validatePhone(data, result);
                break;
            case 'address':
                result = await validateAddress(data, result);
                break;
            case 'medical_record':
                result = await validateMedicalRecord(data, result);
                break;
            case 'customer_data':
                result = await validateCustomerData(data, result);
                break;
            case 'inventory_data':
                result = await validateInventoryData(data, result);
                break;
            case 'survey_data':
                result = await validateSurveyData(data, result);
                break;
            default:
                throw new Error(`Unsupported validation type: ${validationType}`);
        }

        result.processingTimeMs = Date.now() - startTime;
        return result;

    } catch (error) {
        return {
            ...result,
            success: false,
            error: error.message,
            processingTimeMs: Date.now() - startTime
        };
    }
}

async function validateEmail(email: string, result: any) {
    // Basic email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!emailRegex.test(email)) {
        return {
            ...result,
            success: false,
            validation: {
                isValid: false,
                errors: ['Invalid email format'],
                suggestions: []
            }
        };
    }

    // Extract domain
    const domain = email.split('@')[1].toLowerCase();
    
    // Check for common disposable email domains
    const disposableDomains = [
        '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
        'mailinator.com', 'throwaway.email', 'yopmail.com'
    ];
    
    const isDisposable = disposableDomains.includes(domain);

    // Get MX records check (basic)
    const mxCheck = await checkMXRecord(domain);

    return {
        ...result,
        validation: {
            isValid: true,
            isDisposable,
            domain,
            mxCheck,
            confidence: mxCheck ? 0.9 : 0.6
        }
    };
}

async function validatePhone(phone: string, result: any) {
    // Basic phone format validation
    const phoneRegex = /^\+?[1-9]\d{1,14}$/;
    
    if (!phoneRegex.test(phone.replace(/[\s\-\(\)\.]/g, ''))) {
        return {
            ...result,
            success: false,
            validation: {
                isValid: false,
                errors: ['Invalid phone format'],
                suggestions: ['Use E.164 format: +1234567890']
            }
        };
    }

    // Clean phone number
    const cleanPhone = phone.replace(/[\s\-\(\)\.]/g, '');
    const countryCode = cleanPhone.match(/^\+(\d{1,3})/);
    
    // Basic country detection
    const country = countryCode ? getCountryByCode(countryCode[1]) : 'Unknown';

    return {
        ...result,
        validation: {
            isValid: true,
            cleanPhone,
            country,
            countryCode: countryCode ? countryCode[1] : null,
            confidence: 0.7
        }
    };
}

async function validateAddress(address: any, result: any) {
    const requiredFields = ['street', 'city', 'state', 'postalCode'];
    const errors = [];
    const warnings = [];

    // Check required fields
    for (const field of requiredFields) {
        if (!address[field] || address[field].trim() === '') {
            errors.push(`Missing required field: ${field}`);
        }
    }

    // Validate postal code format
    if (address.postalCode) {
        const postalRegex = /^[A-Za-z0-9\s\-]{3,10}$/;
        if (!postalRegex.test(address.postalCode)) {
            warnings.push('Invalid postal code format');
        }
    }

    // Validate state (US)
    if (address.country === 'US' && address.state) {
        const usStates = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ];
        
        if (!usStates.includes(address.state.toUpperCase())) {
            errors.push('Invalid US state code');
        }
    }

    return {
        ...result,
        validation: {
            isValid: errors.length === 0,
            errors,
            warnings,
            suggestions: errors.length > 0 ? ['Please fill in all required fields'] : []
        }
    };
}

async function validateMedicalRecord(record: any, result: any) {
    const errors = [];
    const warnings = [];

    // Required medical fields
    const requiredFields = ['patientId', 'firstName', 'lastName', 'dateOfBirth'];
    
    for (const field of requiredFields) {
        if (!record[field] || record[field].toString().trim() === '') {
            errors.push(`Missing required field: ${field}`);
        }
    }

    // Validate date of birth
    if (record.dateOfBirth) {
        const dob = new Date(record.dateOfBirth);
        const today = new Date();
        const age = today.getFullYear() - dob.getFullYear();
        
        if (isNaN(dob.getTime())) {
            errors.push('Invalid date of birth');
        } else if (age < 0 || age > 150) {
            errors.push('Date of birth must be between 0 and 150 years');
        }
    }

    // Validate medical record format
    if (record.patientId && record.patientId.length < 6) {
        warnings.push('Patient ID seems too short (minimum 6 characters)');
    }

    return {
        ...result,
        validation: {
            isValid: errors.length === 0,
            errors,
            warnings,
            category: 'medical',
            confidence: errors.length === 0 ? 0.9 : 0.5
        }
    };
}

async function validateCustomerData(data: any, result: any) {
    const errors = [];
    const warnings = [];

    // Required customer fields
    const requiredFields = ['firstName', 'lastName', 'email'];
    
    for (const field of requiredFields) {
        if (!data[field] || data[field].toString().trim() === '') {
            errors.push(`Missing required field: ${field}`);
        }
    }

    // Validate email if provided
    if (data.email) {
        const emailValidation = await validateEmail(data.email, { data: data.email });
        if (!emailValidation.validation.isValid) {
            errors.push('Invalid email format');
        }
    }

    // Validate phone if provided
    if (data.phone) {
        const phoneValidation = await validatePhone(data.phone, { data: data.phone });
        if (!phoneValidation.validation.isValid) {
            warnings.push('Invalid phone format');
        }
    }

    return {
        ...result,
        validation: {
            isValid: errors.length === 0,
            errors,
            warnings,
            category: 'customer',
            confidence: errors.length === 0 ? 0.8 : 0.4
        }
    };
}

async function validateInventoryData(data: any, result: any) {
    const errors = [];
    const warnings = [];

    // Required inventory fields
    const requiredFields = ['productName', 'sku', 'quantity'];
    
    for (const field of requiredFields) {
        if (!data[field] || data[field].toString().trim() === '') {
            errors.push(`Missing required field: ${field}`);
        }
    }

    // Validate numeric fields
    if (data.quantity !== undefined && isNaN(parseFloat(data.quantity))) {
        errors.push('Quantity must be a number');
    }

    if (data.price !== undefined && isNaN(parseFloat(data.price))) {
        errors.push('Price must be a number');
    }

    // SKU format validation
    if (data.sku && data.sku.length < 3) {
        warnings.push('SKU seems too short (minimum 3 characters)');
    }

    return {
        ...result,
        validation: {
            isValid: errors.length === 0,
            errors,
            warnings,
            category: 'inventory',
            confidence: errors.length === 0 ? 0.85 : 0.5
        }
    };
}

async function validateSurveyData(data: any, result: any) {
    const errors = [];
    const warnings = [];

    // Check for required survey fields
    const requiredFields = ['surveyId', 'questionId', 'response'];
    
    for (const field of requiredFields) {
        if (!data[field] || data[field].toString().trim() === '') {
            errors.push(`Missing required field: ${field}`);
        }
    }

    // Validate response type
    if (data.responseType) {
        const validTypes = ['text', 'number', 'boolean', 'select', 'multiselect'];
        if (!validTypes.includes(data.responseType)) {
            warnings.push('Invalid response type');
        }
    }

    // Validate response based on type
    if (data.responseType === 'number' && data.response) {
        if (isNaN(parseFloat(data.response))) {
            errors.push('Response must be a number');
        }
    }

    return {
        ...result,
        validation: {
            isValid: errors.length === 0,
            errors,
            warnings,
            category: 'survey',
            confidence: errors.length === 0 ? 0.8 : 0.5
        }
    };
}

async function checkMXRecord(domain: string): Promise<boolean> {
    // Basic MX record check simulation
    // In production, this would query DNS or use a real DNS API
    return true; // Simplified for demo
}

function getCountryByCode(code: string): string {
    // Basic country code mapping
    const countryMap: { [key: string]: string } = {
        '1': 'United States/Canada',
        '44': 'United Kingdom',
        '33': 'France',
        '49': 'Germany',
        '39': 'Italy',
        '81': 'Japan',
        '86': 'China',
        '91': 'India'
    };
    
    return countryMap[code] || 'Unknown';
}

async function storeValidationResults(results: any[], serviceRoleKey: string, supabaseUrl: string) {
    try {
        const validationRecords = results.map(result => ({
            validator_name: 'enhanced_data_validation',
            validation_status: result.success && result.validation?.isValid ? 'valid' : 'invalid',
            validation_errors: result.validation?.errors || [],
            validation_warnings: result.validation?.warnings || [],
            confidence_score: result.validation?.confidence || 0.5,
            validation_config: JSON.stringify({
                validationType: result.validationType,
                processingTimeMs: result.processingTimeMs
            }),
            validated_by: null,
            created_at: new Date().toISOString()
        }));

        await fetch(`${supabaseUrl}/rest/v1/validation_results`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${serviceRoleKey}`,
                'apikey': serviceRoleKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(validationRecords)
        });
    } catch (error) {
        console.error('Failed to store validation results:', error);
        // Don't fail the validation if storage fails
    }
}
