import { createWorker } from 'tesseract.js';

export interface OCRResult {
  text: string;
  confidence: number;
  words: Array<{
    text: string;
    confidence: number;
    bbox: {
      x0: number;
      y0: number;
      x1: number;
      y1: number;
    };
  }>;
  lines: Array<{
    text: string;
    confidence: number;
    bbox: {
      x0: number;
      y0: number;
      x1: number;
      y1: number;
    };
  }>;
}

export interface ProcessingProgress {
  status: string;
  progress: number;
  message: string;
}

class OCRService {
  private worker: any = null;
  private isInitialized = false;

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      this.worker = await createWorker('eng', undefined, {
        logger: m => {
          if (m.status === 'recognizing text') {
            console.log(`OCR Progress: ${m.progress * 100}%`);
          }
        }
      });
      
      await this.worker.loadLanguage('eng');
      await this.worker.initialize('eng');
      this.isInitialized = true;
    } catch (error) {
      console.error('Failed to initialize OCR worker:', error);
      throw error;
    }
  }

  async processImage(
    imageFile: File | Blob | string,
    onProgress?: (progress: ProcessingProgress) => void
  ): Promise<OCRResult> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    try {
      if (onProgress) {
        onProgress({ status: 'processing', progress: 0, message: 'Starting OCR processing...' });
      }

      const { data } = await this.worker.recognize(imageFile);

      if (onProgress) {
        onProgress({ status: 'complete', progress: 100, message: 'OCR processing complete' });
      }

      return {
        text: data.text,
        confidence: data.confidence,
        words: data.words || [],
        lines: data.lines || []
      };
    } catch (error) {
      console.error('OCR processing failed:', error);
      if (onProgress) {
        onProgress({ status: 'error', progress: 0, message: 'OCR processing failed' });
      }
      throw error;
    }
  }

  async extractStructuredData(
    imageFile: File | Blob | string,
    dataType: 'invoice' | 'receipt' | 'form' | 'document',
    onProgress?: (progress: ProcessingProgress) => void
  ): Promise<any> {
    const ocrResult = await this.processImage(imageFile, onProgress);
    
    // Basic extraction based on data type
    const extractedData: any = {
      raw_text: ocrResult.text,
      confidence: ocrResult.confidence,
      extracted_fields: {},
      suggestions: []
    };

    const text = ocrResult.text.toLowerCase();

    switch (dataType) {
      case 'invoice':
        extractedData.extracted_fields = this.extractInvoiceData(text);
        break;
      case 'receipt':
        extractedData.extracted_fields = this.extractReceiptData(text);
        break;
      case 'form':
        extractedData.extracted_fields = this.extractFormData(text);
        break;
      case 'document':
        extractedData.extracted_fields = this.extractDocumentData(text);
        break;
    }

    return extractedData;
  }

  private extractInvoiceData(text: string): any {
    const lines = text.split('\n').filter(line => line.trim());
    
    return {
      invoice_number: this.extractPattern(lines, /invoice\s*(number|no\.?)?\s*:?\s*([A-Z0-9-]+)/i),
      date: this.extractPattern(lines, /date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})/i),
      vendor: lines[0]?.substring(0, 50) || 'Unknown Vendor',
      amount: this.extractAmount(text),
      currency: this.extractCurrency(text),
      terms: this.extractPattern(lines, /terms\s*:?\s*([0-9]+)\s*days/i)
    };
  }

  private extractReceiptData(text: string): any {
    const lines = text.split('\n').filter(line => line.trim());
    
    return {
      store_name: lines[0]?.substring(0, 50) || 'Unknown Store',
      date: this.extractPattern(lines, /date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})/i),
      total: this.extractAmount(text),
      currency: this.extractCurrency(text),
      items: this.extractItems(text)
    };
  }

  private extractFormData(text: string): any {
    const fields: any = {};
    const lines = text.split('\n').filter(line => line.trim());
    
    lines.forEach(line => {
      const parts = line.split(':');
      if (parts.length === 2) {
        const key = parts[0].trim().toLowerCase().replace(/\s+/g, '_');
        const value = parts[1].trim();
        fields[key] = value;
      }
    });
    
    return fields;
  }

  private extractDocumentData(text: string): any {
    return {
      title: this.extractPattern(text.split('\n'), /^[A-Z][A-Z\s]{5,50}$/),
      sections: this.splitIntoSections(text),
      word_count: text.split(/\s+/).length,
      page_count: 1
    };
  }

  private extractPattern(lines: string[], pattern: RegExp): string | null {
    for (const line of lines) {
      const match = line.match(pattern);
      if (match) {
        return match[match.length - 1] || match[0];
      }
    }
    return null;
  }

  private extractAmount(text: string): number | null {
    const amountMatch = text.match(/\$?\s*([0-9,]+\.[0-9]{2})/);
    return amountMatch ? parseFloat(amountMatch[1].replace(/,/g, '')) : null;
  }

  private extractCurrency(text: string): string {
    if (text.includes('$')) return 'USD';
    if (text.includes('€')) return 'EUR';
    if (text.includes('£')) return 'GBP';
    return 'USD';
  }

  private extractItems(text: string): any[] {
    const items: any[] = [];
    const lines = text.split('\n').filter(line => line.trim());
    
    for (const line of lines) {
      // Look for lines with prices
      if (line.match(/\$?\s*[0-9]+\.[0-9]{2}/)) {
        const parts = line.split(/\$?\s*[0-9]+\.[0-9]{2}/);
        const priceMatch = line.match(/\$?\s*([0-9,]+\.[0-9]{2})/);
        
        if (priceMatch) {
          items.push({
            name: parts[0]?.trim() || 'Unknown Item',
            price: parseFloat(priceMatch[1].replace(/,/g, ''))
          });
        }
      }
    }
    
    return items;
  }

  private splitIntoSections(text: string): string[] {
    const sections = text.split(/\n\s*\n/).filter(section => section.trim().length > 0);
    return sections.map(section => section.trim());
  }

  async terminate(): Promise<void> {
    if (this.worker) {
      await this.worker.terminate();
      this.worker = null;
      this.isInitialized = false;
    }
  }
}

export const ocrService = new OCRService();
export default ocrService;