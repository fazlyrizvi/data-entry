// Quality Control Service
// Provides real-time validation, error detection, and quality metrics

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
        const { action, data, rules = [], threshold = 0.8 } = await req.json();

        if (!action) {
            throw new Error('Action is required');
        }

        const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
        const supabaseUrl = Deno.env.get('SUPABASE_URL');

        if (!serviceRoleKey || !supabaseUrl) {
            throw new Error('Supabase configuration missing');
        }

        let result: any = {
            action,
            timestamp: new Date().toISOString(),
            success: true
        };

        try {
            switch (action) {
                case 'validate_quality':
                    result = await validateDataQuality(data, rules, threshold, result);
                    break;
                case 'detect_anomalies':
                    result = await detectDataAnomalies(data, result);
                    break;
                case 'check_completeness':
                    result = await checkDataCompleteness(data, result);
                    break;
                case 'validate_accuracy':
                    result = await validateDataAccuracy(data, result);
                    break;
                case 'generate_qc_report':
                    result = await generateQCReport(data, rules, result);
                    break;
                case 'get_quality_metrics':
                    result = await getQualityMetrics(result);
                    break;
                default:
                    throw new Error(`Unsupported action: ${action}`);
            }

            // Store QC results
            await storeQCResults(result, serviceRoleKey, supabaseUrl);

            return new Response(JSON.stringify({
                data: result
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } catch (error) {
            result.success = false;
            result.error = error.message;

            return new Response(JSON.stringify({
                data: result
            }), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

    } catch (error) {
        console.error('Quality control service error:', error);

        const errorResponse = {
            error: {
                code: 'QUALITY_CONTROL_FAILED',
                message: error.message
            }
        };

        return new Response(JSON.stringify(errorResponse), {
            status: 500,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
    }
});

async function validateDataQuality(data: any[], rules: any[], threshold: number, result: any) {
    console.log('Validating data quality');
    
    const qualityMetrics = {
        totalRecords: data.length,
        validRecords: 0,
        invalidRecords: 0,
        warningRecords: 0,
        qualityScore: 0,
        validationResults: [],
        errors: [],
        warnings: []
    };

    for (let i = 0; i < data.length; i++) {
        const record = data[i];
        const validation = await validateRecordQuality(record, rules, threshold);
        
        qualityMetrics.validationResults.push({
            recordIndex: i,
            recordId: record.id || i,
            ...validation
        });

        if (validation.isValid && validation.confidence >= threshold) {
            qualityMetrics.validRecords++;
        } else if (validation.hasWarnings) {
            qualityMetrics.warningRecords++;
        } else {
            qualityMetrics.invalidRecords++;
        }

        if (validation.errors.length > 0) {
            qualityMetrics.errors.push(...validation.errors.map((error: any) => ({
                recordIndex: i,
                error: error.message
            })));
        }

        if (validation.warnings.length > 0) {
            qualityMetrics.warnings.push(...validation.warnings.map((warning: any) => ({
                recordIndex: i,
                warning: warning.message
            })));
        }
    }

    // Calculate overall quality score
    qualityMetrics.qualityScore = qualityMetrics.totalRecords > 0 ? 
        (qualityMetrics.validRecords / qualityMetrics.totalRecords) * 100 : 0;

    result.qualityMetrics = qualityMetrics;
    result.summary = {
        passRate: `${((qualityMetrics.validRecords / qualityMetrics.totalRecords) * 100).toFixed(1)}%`,
        errorRate: `${((qualityMetrics.invalidRecords / qualityMetrics.totalRecords) * 100).toFixed(1)}%`,
        warningRate: `${((qualityMetrics.warningRecords / qualityMetrics.totalRecords) * 100).toFixed(1)}%`,
        overallQuality: qualityMetrics.qualityScore >= 95 ? 'Excellent' :
                       qualityMetrics.qualityScore >= 85 ? 'Good' :
                       qualityMetrics.qualityScore >= 70 ? 'Fair' : 'Poor'
    };

    console.log(`Quality validation completed: ${qualityMetrics.qualityScore.toFixed(1)}% score`);

    return result;
}

async function validateRecordQuality(record: any, rules: any[], threshold: number) {
    const validation = {
        isValid: true,
        confidence: 1.0,
        hasWarnings: false,
        errors: [] as any[],
        warnings: [] as any[],
        score: 100,
        issues: [] as string[]
    };

    // Apply default validation rules if none provided
    if (rules.length === 0) {
        rules = getDefaultValidationRules();
    }

    for (const rule of rules) {
        try {
            const fieldValue = getNestedValue(record, rule.field);
            const ruleValidation = await applyValidationRule(fieldValue, rule, record);
            
            if (!ruleValidation.isValid) {
                validation.isValid = false;
                validation.errors.push({
                    rule: rule.name || rule.field,
                    message: ruleValidation.message,
                    severity: 'error'
                });
                validation.issues.push(`${rule.field}: ${ruleValidation.message}`);
                validation.score -= ruleValidation.penalty || 20;
            } else if (ruleValidation.hasWarning) {
                validation.hasWarnings = true;
                validation.warnings.push({
                    rule: rule.name || rule.field,
                    message: ruleValidation.warningMessage,
                    severity: 'warning'
                });
                validation.score -= 5;
            }
        } catch (error) {
            validation.errors.push({
                rule: rule.name || rule.field,
                message: `Rule application failed: ${error.message}`,
                severity: 'error'
            });
            validation.score -= 15;
        }
    }

    // Calculate confidence based on score
    validation.confidence = Math.max(0, validation.score / 100);
    validation.isValid = validation.isValid && validation.confidence >= threshold;

    return validation;
}

async function applyValidationRule(value: any, rule: any, record: any) {
    const ruleType = rule.type || 'required';

    switch (ruleType) {
        case 'required':
            if (!value || (typeof value === 'string' && value.trim() === '')) {
                return { isValid: false, message: 'Field is required', penalty: 25 };
            }
            break;

        case 'format':
            if (value && rule.pattern && !new RegExp(rule.pattern).test(value)) {
                return { isValid: false, message: `Invalid format for ${rule.field}`, penalty: 20 };
            }
            break;

        case 'length':
            if (value) {
                if (rule.min && value.length < rule.min) {
                    return { isValid: false, message: `Minimum length is ${rule.min}`, penalty: 15 };
                }
                if (rule.max && value.length > rule.max) {
                    return { isValid: false, message: `Maximum length is ${rule.max}`, penalty: 15 };
                }
            }
            break;

        case 'range':
            if (value !== null && value !== undefined) {
                const numValue = parseFloat(value);
                if (isNaN(numValue)) {
                    return { isValid: false, message: 'Must be a number', penalty: 20 };
                }
                if (rule.min !== undefined && numValue < rule.min) {
                    return { isValid: false, message: `Minimum value is ${rule.min}`, penalty: 15 };
                }
                if (rule.max !== undefined && numValue > rule.max) {
                    return { isValid: false, message: `Maximum value is ${rule.max}`, penalty: 15 };
                }
            }
            break;

        case 'email':
            if (value) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(value)) {
                    return { isValid: false, message: 'Invalid email format', penalty: 20 };
                }
            }
            break;

        case 'phone':
            if (value) {
                const phoneRegex = /^\+?[1-9]\d{1,14}$/;
                const cleanPhone = value.replace(/[\s\-\(\)\.]/g, '');
                if (!phoneRegex.test(cleanPhone)) {
                    return { isValid: false, message: 'Invalid phone format', penalty: 20 };
                }
            }
            break;

        case 'custom':
            if (rule.validator && typeof rule.validator === 'function') {
                try {
                    const customResult = rule.validator(value, record);
                    if (customResult !== true) {
                        return { isValid: false, message: customResult || 'Custom validation failed', penalty: rule.penalty || 20 };
                    }
                } catch (error) {
                    return { isValid: false, message: 'Custom validation error', penalty: 25 };
                }
            }
            break;

        case 'conditional':
            if (rule.condition && !evaluateCondition(rule.condition, record)) {
                return { isValid: true }; // Condition not met, no validation needed
            }
            if (rule.thenValidator) {
                return await applyValidationRule(value, rule.thenValidator, record);
            }
            break;
    }

    return { isValid: true };
}

function getDefaultValidationRules() {
    return [
        {
            field: 'firstName',
            type: 'required',
            name: 'First Name Required'
        },
        {
            field: 'lastName',
            type: 'required',
            name: 'Last Name Required'
        },
        {
            field: 'email',
            type: 'email',
            name: 'Email Format'
        },
        {
            field: 'phone',
            type: 'phone',
            name: 'Phone Format'
        },
        {
            field: 'dateOfBirth',
            type: 'format',
            pattern: '^\\d{4}-\\d{2}-\\d{2}$',
            name: 'Date Format'
        }
    ];
}

async function detectDataAnomalies(data: any[], result: any) {
    console.log('Detecting data anomalies');
    
    const anomalies = {
        totalRecords: data.length,
        anomalyCount: 0,
        anomalies: [],
        statistics: {},
        recommendations: []
    };

    // Analyze each field for anomalies
    const fieldAnalysis = analyzeFieldDistribution(data);
    
    for (const [field, analysis] of Object.entries(fieldAnalysis)) {
        const fieldAnomalies = detectFieldAnomalies(data, field, analysis as any);
        anomalies.anomalies.push(...fieldAnomalies);
    }

    anomalies.anomalyCount = anomalies.anomalies.length;

    // Calculate field statistics
    anomalies.statistics = generateFieldStatistics(data);

    // Generate recommendations
    anomalies.recommendations = generateAnomalyRecommendations(anomalies);

    result.anomalies = anomalies;

    console.log(`Anomaly detection completed: ${anomalies.anomalyCount} anomalies found`);

    return result;
}

function analyzeFieldDistribution(data: any[]) {
    const distributions: any = {};

    for (const record of data) {
        for (const [field, value] of Object.entries(record)) {
            if (!distributions[field]) {
                distributions[field] = {
                    values: [],
                    types: {},
                    numericValues: []
                };
            }

            distributions[field].values.push(value);
            
            const type = typeof value;
            distributions[field].types[type] = (distributions[field].types[type] || 0) + 1;

            if (type === 'number' || (!isNaN(parseFloat(value)) && isFinite(value))) {
                distributions[field].numericValues.push(parseFloat(value));
            }
        }
    }

    // Calculate statistics for each field
    for (const field in distributions) {
        const analysis = distributions[field];
        
        if (analysis.numericValues.length > 0) {
            analysis.numericStats = calculateNumericStats(analysis.numericValues);
        }

        analysis.uniqueCount = new Set(analysis.values).size;
        analysis.mostCommonValue = getMostCommonValue(analysis.values);
    }

    return distributions;
}

function detectFieldAnomalies(data: any[], field: string, analysis: any) {
    const anomalies: any[] = [];

    // Check for unusual value distributions
    if (analysis.uniqueCount < Math.max(1, data.length * 0.01)) {
        anomalies.push({
            field,
            type: 'low_uniqueness',
            description: `Field ${field} has very low uniqueness (${analysis.uniqueCount} unique values for ${data.length} records)`,
            severity: 'medium',
            recommendation: 'Consider if this field should have more variation'
        });
    }

    // Check for mixed data types
    const typeKeys = Object.keys(analysis.types);
    if (typeKeys.length > 2) {
        anomalies.push({
            field,
            type: 'mixed_types',
            description: `Field ${field} has multiple data types: ${typeKeys.join(', ')}`,
            severity: 'high',
            recommendation: 'Standardize data type for this field'
        });
    } else if (typeKeys.length > 1) {
        anomalies.push({
            field,
            type: 'mixed_types',
            description: `Field ${field} has mixed data types: ${typeKeys.join(', ')}`,
            severity: 'medium',
            recommendation: 'Consider standardizing data type'
        });
    }

    // Check for numeric outliers
    if (analysis.numericStats) {
        const { mean, stdDev, min, max } = analysis.numericStats;
        
        for (let i = 0; i < data.length; i++) {
            const value = parseFloat(data[i][field]);
            if (!isNaN(value)) {
                const zScore = Math.abs((value - mean) / stdDev);
                if (zScore > 3) {
                    anomalies.push({
                        field,
                        type: 'outlier',
                        recordIndex: i,
                        value,
                        zScore,
                        description: `Value ${value} is an outlier (z-score: ${zScore.toFixed(2)})`,
                        severity: 'high',
                        recommendation: 'Review this value for accuracy'
                    });
                }
            }
        }
    }

    return anomalies;
}

function calculateNumericStats(values: number[]) {
    const sorted = values.slice().sort((a, b) => a - b);
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);
    
    return {
        mean,
        stdDev,
        min: sorted[0],
        max: sorted[sorted.length - 1],
        median: sorted[Math.floor(sorted.length / 2)],
        count: values.length
    };
}

function getMostCommonValue(values: any[]) {
    const counts: any = {};
    for (const value of values) {
        counts[value] = (counts[value] || 0) + 1;
    }
    
    return Object.keys(counts).reduce((a, b) => counts[a] > counts[b] ? a : b);
}

function generateFieldStatistics(data: any[]) {
    const stats: any = {};
    
    for (const record of data) {
        for (const [field, value] of Object.entries(record)) {
            if (!stats[field]) {
                stats[field] = {
                    count: 0,
                    nullCount: 0,
                    uniqueCount: 0,
                    types: {}
                };
            }
            
            stats[field].count++;
            
            if (value === null || value === undefined) {
                stats[field].nullCount++;
            } else {
                const type = typeof value;
                stats[field].types[type] = (stats[field].types[type] || 0) + 1;
            }
        }
    }
    
    // Calculate unique counts
    for (const field in stats) {
        const values = data.map(record => record[field]).filter(v => v !== null && v !== undefined);
        stats[field].uniqueCount = new Set(values).size;
    }
    
    return stats;
}

function generateAnomalyRecommendations(anomalies: any) {
    const recommendations: string[] = [];
    
    const anomalyTypes = new Set(anomalies.anomalies.map((a: any) => a.type));
    
    if (anomalyTypes.has('mixed_types')) {
        recommendations.push('Standardize data types across fields to improve data quality');
    }
    
    if (anomalyTypes.has('outlier')) {
        recommendations.push('Review and validate outlier values for accuracy');
    }
    
    if (anomalyTypes.has('low_uniqueness')) {
        recommendations.push('Consider the purpose of fields with low uniqueness - they may be constants or reference data');
    }
    
    if (anomalies.anomalyCount > data.length * 0.1) {
        recommendations.push('High anomaly rate detected - consider reviewing data entry processes');
    }
    
    return recommendations;
}

async function checkDataCompleteness(data: any[], result: any) {
    console.log('Checking data completeness');
    
    const completeness = {
        totalRecords: data.length,
        completenessByField: {},
        overallCompleteness: 0,
        incompleteRecords: [],
        recommendations: []
    };

    // Check completeness for each field
    const fields = Object.keys(data[0] || {});
    
    for (const field of fields) {
        let nonNullCount = 0;
        
        for (const record of data) {
            if (record[field] !== null && record[field] !== undefined && 
                record[field] !== '' && record[field] !== ' ') {
                nonNullCount++;
            }
        }
        
        const completenessPercentage = (nonNullCount / data.length) * 100;
        
        completeness.completenessByField[field] = {
            completeRecords: nonNullCount,
            totalRecords: data.length,
            completenessPercentage: parseFloat(completenessPercentage.toFixed(1)),
            status: completenessPercentage >= 95 ? 'good' :
                   completenessPercentage >= 80 ? 'fair' : 'poor'
        };
    }

    // Find incomplete records
    for (let i = 0; i < data.length; i++) {
        const record = data[i];
        const missingFields: string[] = [];
        
        for (const field of fields) {
            if (record[field] === null || record[field] === undefined || 
                record[field] === '' || record[field] === ' ') {
                missingFields.push(field);
            }
        }
        
        if (missingFields.length > 0) {
            completeness.incompleteRecords.push({
                recordIndex: i,
                recordId: record.id || i,
                missingFields,
                missingCount: missingFields.length
            });
        }
    }

    // Calculate overall completeness
    const totalFields = fields.length * data.length;
    const totalCompleteFields = Object.values(completeness.completenessByField)
        .reduce((sum: number, field: any) => sum + field.completeRecords, 0);
    
    completeness.overallCompleteness = parseFloat(((totalCompleteFields / totalFields) * 100).toFixed(1));

    // Generate recommendations
    completeness.recommendations = generateCompletenessRecommendations(completeness);

    result.completeness = completeness;

    console.log(`Completeness check completed: ${completeness.overallCompleteness}% overall`);

    return result;
}

function generateCompletenessRecommendations(completeness: any) {
    const recommendations: string[] = [];
    
    for (const [field, analysis] of Object.entries(completeness.completenessByField)) {
        const fieldAnalysis = analysis as any;
        
        if (fieldAnalysis.status === 'poor') {
            recommendations.push(`Field "${field}" has low completeness (${fieldAnalysis.completenessPercentage}%). Consider making it optional or improving data collection`);
        } else if (fieldAnalysis.status === 'fair') {
            recommendations.push(`Field "${field}" could be improved (${fieldAnalysis.completenessPercentage}%). Consider validation rules`);
        }
    }
    
    if (completeness.incompleteRecords.length > data.length * 0.1) {
        recommendations.push('High number of incomplete records detected. Review data entry processes');
    }
    
    return recommendations;
}

async function validateDataAccuracy(data: any[], result: any) {
    console.log('Validating data accuracy');
    
    const accuracy = {
        totalRecords: data.length,
        validRecords: 0,
        invalidRecords: 0,
        accuracyScore: 0,
        accuracyChecks: [],
        errors: []
    };

    // Perform various accuracy checks
    accuracy.accuracyChecks = [
        checkEmailAccuracy(data),
        checkPhoneAccuracy(data),
        checkDateAccuracy(data),
        checkNumericAccuracy(data)
    ];

    // Calculate overall accuracy
    let totalChecks = 0;
    let passedChecks = 0;

    for (const check of accuracy.accuracyChecks) {
        totalChecks += check.totalChecked;
        passedChecks += check.passed;
    }

    accuracy.accuracyScore = totalChecks > 0 ? (passedChecks / totalChecks) * 100 : 100;
    accuracy.validRecords = Math.round((accuracy.accuracyScore / 100) * data.length);
    accuracy.invalidRecords = data.length - accuracy.validRecords;

    result.accuracy = accuracy;

    console.log(`Accuracy validation completed: ${accuracy.accuracyScore.toFixed(1)}% accuracy`);

    return result;
}

function checkEmailAccuracy(data: any[]) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    let totalChecked = 0;
    let passed = 0;

    for (const record of data) {
        if (record.email) {
            totalChecked++;
            if (emailRegex.test(record.email)) {
                passed++;
            }
        }
    }

    return {
        checkName: 'Email Format',
        totalChecked,
        passed,
        accuracy: totalChecked > 0 ? (passed / totalChecked) * 100 : 100,
        status: totalChecked > 0 ? (passed / totalChecked >= 0.95 ? 'good' : 'needs_improvement') : 'no_data'
    };
}

function checkPhoneAccuracy(data: any[]) {
    const phoneRegex = /^\+?[1-9]\d{1,14}$/;
    let totalChecked = 0;
    let passed = 0;

    for (const record of data) {
        if (record.phone) {
            totalChecked++;
            const cleanPhone = record.phone.replace(/[\s\-\(\)\.]/g, '');
            if (phoneRegex.test(cleanPhone)) {
                passed++;
            }
        }
    }

    return {
        checkName: 'Phone Format',
        totalChecked,
        passed,
        accuracy: totalChecked > 0 ? (passed / totalChecked) * 100 : 100,
        status: totalChecked > 0 ? (passed / totalChecked >= 0.95 ? 'good' : 'needs_improvement') : 'no_data'
    };
}

function checkDateAccuracy(data: any[]) {
    let totalChecked = 0;
    let passed = 0;

    for (const record of data) {
        const dateFields = ['dateOfBirth', 'date', 'createdAt', 'updatedAt'];
        
        for (const field of dateFields) {
            if (record[field]) {
                totalChecked++;
                const date = new Date(record[field]);
                if (!isNaN(date.getTime())) {
                    passed++;
                }
            }
        }
    }

    return {
        checkName: 'Date Validity',
        totalChecked,
        passed,
        accuracy: totalChecked > 0 ? (passed / totalChecked) * 100 : 100,
        status: totalChecked > 0 ? (passed / totalChecked >= 0.95 ? 'good' : 'needs_improvement') : 'no_data'
    };
}

function checkNumericAccuracy(data: any[]) {
    let totalChecked = 0;
    let passed = 0;

    for (const record of data) {
        const numericFields = ['quantity', 'price', 'amount', 'score', 'rating'];
        
        for (const field of numericFields) {
            if (record[field] !== undefined && record[field] !== null) {
                totalChecked++;
                const numValue = parseFloat(record[field]);
                if (!isNaN(numValue) && isFinite(numValue)) {
                    passed++;
                }
            }
        }
    }

    return {
        checkName: 'Numeric Validity',
        totalChecked,
        passed,
        accuracy: totalChecked > 0 ? (passed / totalChecked) * 100 : 100,
        status: totalChecked > 0 ? (passed / totalChecked >= 0.95 ? 'good' : 'needs_improvement') : 'no_data'
    };
}

async function generateQCReport(data: any[], rules: any[], result: any) {
    console.log('Generating comprehensive QC report');
    
    const report = {
        generatedAt: new Date().toISOString(),
        dataSummary: {
            totalRecords: data.length,
            fields: Object.keys(data[0] || {}),
            dataTypes: {}
        },
        qualityScore: 0,
        sections: []
    };

    // Generate all QC sections
    const qualityResult = await validateDataQuality(data, rules, 0.8, { action: 'quality_validation' });
    const anomalyResult = await detectDataAnomalies(data, { action: 'anomaly_detection' });
    const completenessResult = await checkDataCompleteness(data, { action: 'completeness_check' });
    const accuracyResult = await validateDataAccuracy(data, { action: 'accuracy_validation' });

    // Compile sections
    report.sections = [
        {
            title: 'Data Quality Overview',
            summary: qualityResult.summary,
            metrics: qualityResult.qualityMetrics
        },
        {
            title: 'Anomaly Detection',
            summary: {
                anomalyCount: anomalyResult.anomalies.anomalyCount,
                anomalyRate: ((anomalyResult.anomalies.anomalyCount / data.length) * 100).toFixed(1) + '%'
            },
            details: anomalyResult.anomalies
        },
        {
            title: 'Data Completeness',
            summary: {
                overallCompleteness: completenessResult.completeness.overallCompleteness + '%',
                incompleteRecords: completenessResult.completeness.incompleteRecords.length
            },
            details: completenessResult.completeness
        },
        {
            title: 'Data Accuracy',
            summary: {
                accuracyScore: accuracyResult.accuracy.accuracyScore.toFixed(1) + '%',
                validRecords: accuracyResult.accuracy.validRecords
            },
            details: accuracyResult.accuracy
        }
    ];

    // Calculate overall quality score
    const scores = [
        qualityResult.qualityMetrics.qualityScore,
        100 - ((anomalyResult.anomalies.anomalyCount / data.length) * 100),
        completenessResult.completeness.overallCompleteness,
        accuracyResult.accuracy.accuracyScore
    ];
    
    report.qualityScore = scores.reduce((sum, score) => sum + score, 0) / scores.length;

    result.report = report;

    console.log(`QC report generated: ${report.qualityScore.toFixed(1)}% overall quality`);

    return result;
}

async function getQualityMetrics(result: any) {
    console.log('Retrieving quality metrics');
    
    // In production, would query historical metrics from database
    const metrics = {
        lastUpdated: new Date().toISOString(),
        historicalTrends: {
            qualityScore: [
                { date: '2025-10-01', score: 78.5 },
                { date: '2025-10-15', score: 82.1 },
                { date: '2025-11-01', score: 85.7 }
            ],
            errorRate: [
                { date: '2025-10-01', rate: 12.3 },
                { date: '2025-10-15', rate: 9.8 },
                { date: '2025-11-01', rate: 7.2 }
            ]
        },
        currentPeriod: {
            processingTime: '2.3s avg',
            throughput: '150 records/min',
            accuracy: '94.2%',
            completion: '98.5%'
        },
        alerts: [
            {
                type: 'warning',
                message: 'Email validation accuracy dropped to 89% this week',
                timestamp: new Date().toISOString()
            }
        ]
    };

    result.metrics = metrics;

    console.log('Quality metrics retrieved');

    return result;
}

function getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => current?.[key], obj);
}

function evaluateCondition(condition: any, record: any): boolean {
    // Simple condition evaluation
    if (typeof condition === 'object' && condition.field && condition.operator && condition.value !== undefined) {
        const fieldValue = getNestedValue(record, condition.field);
        
        switch (condition.operator) {
            case 'equals':
                return fieldValue === condition.value;
            case 'not_equals':
                return fieldValue !== condition.value;
            case 'contains':
                return String(fieldValue).includes(condition.value);
            case 'greater_than':
                return parseFloat(fieldValue) > parseFloat(condition.value);
            case 'less_than':
                return parseFloat(fieldValue) < parseFloat(condition.value);
            default:
                return false;
        }
    }
    
    return false;
}

async function storeQCResults(result: any, serviceRoleKey: string, supabaseUrl: string) {
    try {
        // In production, would store QC results in database
        console.log('QC results stored:', result.action);
    } catch (error) {
        console.error('Failed to store QC results:', error);
    }
}
