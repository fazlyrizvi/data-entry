import { ocrService } from './ocrService';
import { validationService, ValidationResult } from './validationService';

export interface ProcessingJob {
  id: string;
  type: 'ocr' | 'validation' | 'extraction' | 'batch_validation';
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  input_files: string[];
  results?: any;
  error_message?: string;
  created_at: string;
  updated_at: string;
  metadata?: any;
}

export interface BatchValidationRequest {
  type: 'email' | 'phone' | 'address' | 'mixed';
  data: Array<{
    id: string;
    field: string;
    value: string;
    type: 'email' | 'phone' | 'address';
  }>;
}

export interface ProcessingProgress {
  job_id: string;
  progress: number;
  status: string;
  message: string;
  processed_count: number;
  total_count: number;
  results?: any[];
}

class ProcessingService {
  private jobs = new Map<string, ProcessingJob>();
  private progressCallbacks = new Map<string, (progress: ProcessingProgress) => void>();

  // Create a new processing job
  async createJob(
    type: ProcessingJob['type'],
    input_files: string[],
    metadata?: any
  ): Promise<ProcessingJob> {
    const job: ProcessingJob = {
      id: `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      status: 'pending',
      progress: 0,
      input_files,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      metadata
    };

    this.jobs.set(job.id, job);
    return job;
  }

  // Process a single OCR job
  async processOCRJob(
    job_id: string,
    file: File,
    dataType: 'invoice' | 'receipt' | 'form' | 'document',
    onProgress?: (progress: ProcessingProgress) => void
  ): Promise<void> {
    const job = this.jobs.get(job_id);
    if (!job) throw new Error('Job not found');

    try {
      job.status = 'processing';
      job.updated_at = new Date().toISOString();
      
      if (onProgress) {
        this.progressCallbacks.set(job_id, onProgress);
        onProgress({
          job_id,
          progress: 10,
          status: 'processing',
          message: 'Initializing OCR...',
          processed_count: 0,
          total_count: 1
        });
      }

      const result = await ocrService.extractStructuredData(
        file,
        dataType,
        (ocrProgress) => {
          if (onProgress) {
            onProgress({
              job_id,
              progress: 10 + (ocrProgress.progress * 0.8),
              status: 'processing',
              message: ocrProgress.message,
              processed_count: 0,
              total_count: 1
            });
          }
        }
      );

      job.results = result;
      job.progress = 100;
      job.status = 'completed';
      job.updated_at = new Date().toISOString();

      if (onProgress) {
        onProgress({
          job_id,
          progress: 100,
          status: 'completed',
          message: 'OCR processing completed successfully',
          processed_count: 1,
          total_count: 1,
          results: [result]
        });
      }
    } catch (error) {
      job.status = 'error';
      job.error_message = error instanceof Error ? error.message : 'Unknown error';
      job.updated_at = new Date().toISOString();

      if (onProgress) {
        onProgress({
          job_id,
          progress: 0,
          status: 'error',
          message: `Processing failed: ${job.error_message}`,
          processed_count: 0,
          total_count: 1
        });
      }
    }
  }

  // Process batch validation
  async processBatchValidation(
    job_id: string,
    request: BatchValidationRequest,
    onProgress?: (progress: ProcessingProgress) => void
  ): Promise<void> {
    const job = this.jobs.get(job_id);
    if (!job) throw new Error('Job not found');

    try {
      job.status = 'processing';
      job.updated_at = new Date().toISOString();

      if (onProgress) {
        onProgress({
          job_id,
          progress: 5,
          status: 'processing',
          message: 'Starting batch validation...',
          processed_count: 0,
          total_count: request.data.length
        });
      }

      const results: ValidationResult[] = [];
      const chunkSize = 10; // Process in chunks to avoid overwhelming APIs

      for (let i = 0; i < request.data.length; i += chunkSize) {
        const chunk = request.data.slice(i, i + chunkSize);
        
        if (onProgress) {
          onProgress({
            job_id,
            progress: 5 + (i / request.data.length * 90),
            status: 'processing',
            message: `Validating ${i + 1} to ${Math.min(i + chunkSize, request.data.length)} of ${request.data.length}`,
            processed_count: i,
            total_count: request.data.length
          });
        }

        const chunkResults = await validationService.validateMultipleFields(chunk);
        results.push(...chunkResults);

        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      job.results = {
        summary: this.generateValidationSummary(results),
        results
      };
      job.progress = 100;
      job.status = 'completed';
      job.updated_at = new Date().toISOString();

      if (onProgress) {
        onProgress({
          job_id,
          progress: 100,
          status: 'completed',
          message: 'Batch validation completed successfully',
          processed_count: request.data.length,
          total_count: request.data.length,
          results: results
        });
      }
    } catch (error) {
      job.status = 'error';
      job.error_message = error instanceof Error ? error.message : 'Unknown error';
      job.updated_at = new Date().toISOString();

      if (onProgress) {
        onProgress({
          job_id,
          progress: 0,
          status: 'error',
          message: `Batch validation failed: ${job.error_message}`,
          processed_count: 0,
          total_count: request.data.length
        });
      }
    }
  }

  // Process multiple files for OCR
  async processBatchOCR(
    job_id: string,
    files: File[],
    dataType: 'invoice' | 'receipt' | 'form' | 'document',
    onProgress?: (progress: ProcessingProgress) => void
  ): Promise<void> {
    const job = this.jobs.get(job_id);
    if (!job) throw new Error('Job not found');

    try {
      job.status = 'processing';
      job.updated_at = new Date().toISOString();

      if (onProgress) {
        onProgress({
          job_id,
          progress: 0,
          status: 'processing',
          message: 'Starting batch OCR processing...',
          processed_count: 0,
          total_count: files.length
        });
      }

      const results = [];

      for (let i = 0; i < files.length; i++) {
        const file = files[i];

        if (onProgress) {
          onProgress({
            job_id,
            progress: (i / files.length) * 95,
            status: 'processing',
            message: `Processing file ${i + 1} of ${files.length}: ${file.name}`,
            processed_count: i,
            total_count: files.length
          });
        }

        const result = await ocrService.extractStructuredData(file, dataType);
        results.push({
          filename: file.name,
          file_id: `file_${i}`,
          ...result
        });

        // Small delay to prevent overwhelming the system
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      job.results = {
        files_processed: results.length,
        summary: this.generateOCRSummary(results),
        results
      };
      job.progress = 100;
      job.status = 'completed';
      job.updated_at = new Date().toISOString();

      if (onProgress) {
        onProgress({
          job_id,
          progress: 100,
          status: 'completed',
          message: 'Batch OCR processing completed successfully',
          processed_count: files.length,
          total_count: files.length,
          results
        });
      }
    } catch (error) {
      job.status = 'error';
      job.error_message = error instanceof Error ? error.message : 'Unknown error';
      job.updated_at = new Date().toISOString();

      if (onProgress) {
        onProgress({
          job_id,
          progress: 0,
          status: 'error',
          message: `Batch OCR processing failed: ${job.error_message}`,
          processed_count: 0,
          total_count: files.length
        });
      }
    }
  }

  // Get job status
  getJob(job_id: string): ProcessingJob | undefined {
    return this.jobs.get(job_id);
  }

  // Get all jobs
  getAllJobs(): ProcessingJob[] {
    return Array.from(this.jobs.values()).sort((a, b) => 
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    );
  }

  // Remove completed job
  removeJob(job_id: string): boolean {
    this.progressCallbacks.delete(job_id);
    return this.jobs.delete(job_id);
  }

  private generateValidationSummary(results: ValidationResult[]): any {
    const validCount = results.filter(r => r.is_valid).length;
    const invalidCount = results.length - validCount;
    
    const typeStats = results.reduce((acc, result) => {
      acc[result.type] = acc[result.type] || { valid: 0, invalid: 0 };
      if (result.is_valid) acc[result.type].valid++;
      else acc[result.type].invalid++;
      return acc;
    }, {} as Record<string, { valid: number; invalid: number }>);

    return {
      total: results.length,
      valid: validCount,
      invalid: invalidCount,
      accuracy: (validCount / results.length * 100).toFixed(1) + '%',
      by_type: typeStats
    };
  }

  private generateOCRSummary(results: any[]): any {
    const totalConfidence = results.reduce((sum, result) => sum + (result.confidence || 0), 0);
    const avgConfidence = results.length > 0 ? totalConfidence / results.length : 0;
    
    return {
      files_processed: results.length,
      average_confidence: Math.round(avgConfidence),
      high_confidence_files: results.filter(r => r.confidence > 90).length,
      medium_confidence_files: results.filter(r => r.confidence >= 70 && r.confidence <= 90).length,
      low_confidence_files: results.filter(r => r.confidence < 70).length
    };
  }

  // Clean up old jobs
  cleanupOldJobs(maxAgeHours = 24): void {
    const cutoffTime = new Date(Date.now() - (maxAgeHours * 60 * 60 * 1000));
    
    for (const [job_id, job] of this.jobs.entries()) {
      if (new Date(job.updated_at) < cutoffTime) {
        this.removeJob(job_id);
      }
    }
  }
}

export const processingService = new ProcessingService();
export default processingService;