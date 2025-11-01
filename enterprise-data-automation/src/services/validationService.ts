import axios from 'axios';

export interface EmailValidationResult {
  email: string;
  is_valid: boolean;
  deliverability_score: number;
  role: boolean;
  free: boolean;
  disposable: boolean;
  risks: string[];
  server_info: {
    domain: string;
    server: string;
    is_smtp_valid: boolean;
  };
  alternatives?: string[];
}

export interface PhoneValidationResult {
  international_format: string;
  local_format: string;
  country_code: string;
  country_name: string;
  country_prefix: string;
  location: string;
  carrier: string;
  line_type: string;
  is_valid: boolean;
  is_possible: boolean;
}

export interface AddressValidationResult {
  is_valid: boolean;
  address_components: {
    street_number?: string;
    street_name?: string;
    city?: string;
    state?: string;
    zip_code?: string;
    country?: string;
  };
  formatted_address: string;
  location?: {
    latitude: number;
    longitude: number;
  };
}

export interface ValidationResult {
  field: string;
  value: string;
  type: 'email' | 'phone' | 'address';
  is_valid: boolean;
  confidence: number;
  suggestions?: string[];
  details?: any;
}

class ValidationService {
  private hunterApiKey = ''; // Will be set from environment or user input
  private numverifyApiKey = ''; // Will be set from environment or user input

  setApiKeys(hunterKey: string, numverifyKey: string) {
    this.hunterApiKey = hunterKey;
    this.numverifyApiKey = numverifyKey;
  }

  async validateEmail(email: string, useHunter = true): Promise<EmailValidationResult> {
    if (useHunter && this.hunterApiKey) {
      try {
        const response = await axios.get('https://api.hunter.io/v2/email-verifier', {
          params: {
            email: email,
            api_key: this.hunterApiKey
          }
        });
        
        return {
          ...response.data.data,
          risks: this.calculateEmailRisks(response.data.data)
        };
      } catch (error) {
        console.warn('Hunter.io API failed, falling back to basic validation:', error);
      }
    }

    // Fallback to basic email validation
    return this.basicEmailValidation(email);
  }

  async validatePhone(phone: string, useNumverify = true): Promise<PhoneValidationResult> {
    // Clean phone number
    const cleanPhone = phone.replace(/\D/g, '');
    
    if (useNumverify && this.numverifyApiKey) {
      try {
        const response = await axios.get('http://apilayer.net/api/validate', {
          params: {
            access_key: this.numverifyApiKey,
            number: cleanPhone,
            format: 1
          }
        });
        
        return {
          international_format: response.data.international_format,
          local_format: response.data.local_format,
          country_code: response.data.country_code,
          country_name: response.data.country_name,
          country_prefix: response.data.country_prefix,
          location: response.data.location,
          carrier: response.data.carrier,
          line_type: response.data.line_type,
          is_valid: response.data.valid,
          is_possible: response.data.is_possible
        };
      } catch (error) {
        console.warn('Numverify API failed, falling back to basic validation:', error);
      }
    }

    // Fallback to basic phone validation
    return this.basicPhoneValidation(phone);
  }

  async validateAddress(address: string): Promise<AddressValidationResult> {
    // For demo purposes, we'll use a simplified address validation
    // In production, you'd use Google Maps API or similar service
    
    const components = this.parseAddressComponents(address);
    const isValid = this.isValidAddress(components);
    
    return {
      is_valid: isValid,
      address_components: components,
      formatted_address: address,
      location: isValid ? { latitude: 40.7128, longitude: -74.0060 } : undefined // NYC as default for demo
    };
  }

  async validateMultipleFields(fields: Array<{
    field: string;
    value: string;
    type: 'email' | 'phone' | 'address';
  }>): Promise<ValidationResult[]> {
    const results: ValidationResult[] = [];

    for (const fieldData of fields) {
      try {
        let result: ValidationResult;

        switch (fieldData.type) {
          case 'email':
            const emailResult = await this.validateEmail(fieldData.value);
            result = {
              field: fieldData.field,
              value: fieldData.value,
              type: 'email',
              is_valid: emailResult.is_valid,
              confidence: emailResult.deliverability_score,
              suggestions: this.getEmailSuggestions(emailResult),
              details: emailResult
            };
            break;

          case 'phone':
            const phoneResult = await this.validatePhone(fieldData.value);
            result = {
              field: fieldData.field,
              value: fieldData.value,
              type: 'phone',
              is_valid: phoneResult.is_valid,
              confidence: phoneResult.is_possible ? 95 : 20,
              suggestions: this.getPhoneSuggestions(phoneResult),
              details: phoneResult
            };
            break;

          case 'address':
            const addressResult = await this.validateAddress(fieldData.value);
            result = {
              field: fieldData.field,
              value: fieldData.value,
              type: 'address',
              is_valid: addressResult.is_valid,
              confidence: addressResult.is_valid ? 90 : 30,
              suggestions: this.getAddressSuggestions(addressResult),
              details: addressResult
            };
            break;
        }

        results.push(result);
      } catch (error) {
        console.error(`Validation failed for ${fieldData.field}:`, error);
        results.push({
          field: fieldData.field,
          value: fieldData.value,
          type: fieldData.type,
          is_valid: false,
          confidence: 0,
          suggestions: [`Validation failed for ${fieldData.type}`]
        });
      }
    }

    return results;
  }

  private basicEmailValidation(email: string): EmailValidationResult {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(email);
    
    return {
      email,
      is_valid: isValid,
      deliverability_score: isValid ? 85 : 0,
      role: false,
      free: false,
      disposable: false,
      risks: isValid ? [] : ['Invalid email format'],
      server_info: {
        domain: email.split('@')[1] || '',
        server: 'unknown',
        is_smtp_valid: false
      }
    };
  }

  private basicPhoneValidation(phone: string): PhoneValidationResult {
    const cleanPhone = phone.replace(/\D/g, '');
    const isValid = cleanPhone.length >= 10 && cleanPhone.length <= 15;
    
    return {
      international_format: phone,
      local_format: phone,
      country_code: 'US',
      country_name: 'United States',
      country_prefix: '+1',
      location: 'Unknown',
      carrier: 'Unknown',
      line_type: 'Unknown',
      is_valid: isValid,
      is_possible: isValid
    };
  }

  private parseAddressComponents(address: string): any {
    const parts = address.split(',').map(part => part.trim());
    
    return {
      street_number: parts[0]?.match(/^\d+/)?.[0] || '',
      street_name: parts[0]?.replace(/^\d+\s*/, '') || '',
      city: parts[1] || '',
      state: parts[2]?.match(/[A-Z]{2}/)?.[0] || '',
      zip_code: parts[2]?.match(/\d{5}(-\d{4})?/)?.[0] || '',
      country: parts[3] || 'United States'
    };
  }

  private isValidAddress(components: any): boolean {
    return Boolean(
      components.street_name && 
      components.city && 
      components.state &&
      components.zip_code
    );
  }

  private calculateEmailRisks(data: any): string[] {
    const risks: string[] = [];
    
    if (data.free) risks.push('Free email provider');
    if (data.disposable) risks.push('Disposable email');
    if (data.role) risks.push('Role-based email');
    if (data.deliverability_score < 60) risks.push('Low deliverability score');
    if (!data.server_info?.is_smtp_valid) risks.push('SMTP server validation failed');
    
    return risks;
  }

  private getEmailSuggestions(result: any): string[] {
    const suggestions: string[] = [];
    
    if (result.alternatives && result.alternatives.length > 0) {
      suggestions.push(`Suggested alternative: ${result.alternatives[0]}`);
    }
    
    if (result.risks.includes('Low deliverability score')) {
      suggestions.push('Consider using a more reliable email provider');
    }
    
    return suggestions;
  }

  private getPhoneSuggestions(result: any): string[] {
    const suggestions: string[] = [];
    
    if (!result.is_valid) {
      suggestions.push('Check phone number format');
    }
    
    if (result.line_type === 'mobile') {
      suggestions.push('This is a mobile number');
    } else if (result.line_type === 'landline') {
      suggestions.push('This is a landline number');
    }
    
    return suggestions;
  }

  private getAddressSuggestions(result: any): string[] {
    const suggestions: string[] = [];
    
    if (!result.is_valid) {
      suggestions.push('Address format appears incomplete');
    }
    
    if (!result.address_components.street_number) {
      suggestions.push('Missing street number');
    }
    
    if (!result.address_components.city) {
      suggestions.push('Missing city');
    }
    
    return suggestions;
  }

  // Real-time validation helper for forms
  async validateFieldRealTime(field: string, value: string, type: 'email' | 'phone' | 'address'): Promise<ValidationResult> {
    const results = await this.validateMultipleFields([{ field, value, type }]);
    return results[0];
  }
}

export const validationService = new ValidationService();
export default validationService;