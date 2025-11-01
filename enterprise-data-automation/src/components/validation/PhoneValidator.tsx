import React, { useState, useEffect } from 'react';
import { 
  Phone, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Loader2, 
  Settings,
  Info,
  Smartphone,
  Copy,
  Download,
  MapPin
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { validationService, PhoneValidationResult } from '../../services/validationService';

interface PhoneValidatorProps {
  phones?: string[];
  onValidationComplete?: (results: PhoneValidationResult[]) => void;
}

export const PhoneValidator: React.FC<PhoneValidatorProps> = ({
  phones = [],
  onValidationComplete
}) => {
  const [phoneInput, setPhoneInput] = useState('');
  const [phoneList, setPhoneList] = useState<string[]>(phones);
  const [validations, setValidations] = useState<Record<string, PhoneValidationResult>>({});
  const [isValidating, setIsValidating] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [useNumverify, setUseNumverify] = useState(true);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });

  useEffect(() => {
    // Set API key if available
    const savedKey = localStorage.getItem('numverify_api_key');
    if (savedKey) {
      setApiKey(savedKey);
      validationService.setApiKeys('', savedKey);
    }
  }, []);

  const addPhone = () => {
    if (phoneInput.trim() && !phoneList.includes(phoneInput.trim())) {
      const newPhone = phoneInput.trim();
      setPhoneList([...phoneList, newPhone]);
      setPhoneInput('');
    }
  };

  const removePhone = (phone: string) => {
    setPhoneList(phoneList.filter(p => p !== phone));
    const { [phone]: removed, ...remaining } = validations;
    setValidations(remaining);
  };

  const validateSinglePhone = async (phone: string) => {
    try {
      const result = await validationService.validatePhone(phone, useNumverify);
      setValidations(prev => ({ ...prev, [phone]: result }));
      return result;
    } catch (error) {
      console.error(`Failed to validate ${phone}:`, error);
      return null;
    }
  };

  const validateAllPhones = async () => {
    if (phoneList.length === 0) return;

    setIsValidating(true);
    setBatchProgress({ current: 0, total: phoneList.length });

    const results: PhoneValidationResult[] = [];

    for (let i = 0; i < phoneList.length; i++) {
      const phone = phoneList[i];
      
      setBatchProgress({ current: i, total: phoneList.length });

      try {
        const result = await validateSinglePhone(phone);
        if (result) {
          results.push(result);
        }
      } catch (error) {
        console.error(`Validation failed for ${phone}:`, error);
      }

      // Small delay to avoid overwhelming the API
      if (useNumverify && apiKey) {
        await new Promise(resolve => setTimeout(resolve, 300));
      }
    }

    setBatchProgress({ current: phoneList.length, total: phoneList.length });
    setIsValidating(false);

    if (onValidationComplete) {
      onValidationComplete(results);
    }
  };

  const exportResults = (format: 'json' | 'csv') => {
    const results = Object.entries(validations).map(([phone, result]) => ({
      phone,
      ...result
    }));

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'phone-validation-results.json';
      a.click();
      URL.revokeObjectURL(url);
    } else if (format === 'csv') {
      const headers = ['Phone', 'Valid', 'International Format', 'Country', 'Carrier', 'Line Type', 'Location'];
      const rows = results.map(r => [
        r.international_format,
        r.is_valid.toString(),
        r.international_format,
        r.country_name,
        r.carrier,
        r.line_type,
        r.location
      ]);
      
      const csvContent = [headers.join(','), ...rows.map(row => row.map(cell => `"${cell}"`).join(','))].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'phone-validation-results.csv';
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const getValidationStatus = (phone: string) => {
    const result = validations[phone];
    if (!result) return 'pending';

    if (result.is_valid && result.is_possible) return 'valid';
    if (!result.is_valid && !result.is_possible) return 'invalid';
    return 'warning';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'valid': return CheckCircle;
      case 'invalid': return XCircle;
      case 'warning': return AlertTriangle;
      default: return Loader2;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'valid': return 'text-green-600 bg-green-50 border-green-200';
      case 'invalid': return 'text-red-600 bg-red-50 border-red-200';
      case 'warning': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-neutral-600 bg-neutral-50 border-neutral-200';
    }
  };

  const getLineTypeIcon = (lineType: string) => {
    switch (lineType.toLowerCase()) {
      case 'mobile': return '📱';
      case 'landline': return '☎️';
      case 'toll-free': return '🆓';
      default: return '📞';
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const validCount = Object.values(validations).filter(v => v.is_valid && v.is_possible).length;
  const invalidCount = Object.values(validations).filter(v => !v.is_valid || !v.is_possible).length;
  const mobileCount = Object.values(validations).filter(v => v.line_type?.toLowerCase() === 'mobile').length;
  const landlineCount = Object.values(validations).filter(v => v.line_type?.toLowerCase() === 'landline').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-neutral-900 flex items-center space-x-2">
            <Phone className="w-7 h-7 text-green-500" />
            <span>Phone Validator</span>
          </h2>
          <p className="text-neutral-600 mt-1">Validate phone numbers using Numverify API and format checking</p>
        </div>
        
        <div className="flex space-x-3">
          {Object.keys(validations).length > 0 && (
            <>
              <button
                onClick={() => exportResults('json')}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors"
              >
                Export JSON
              </button>
              <button
                onClick={() => exportResults('csv')}
                className="px-4 py-2 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 transition-colors"
              >
                Export CSV
              </button>
            </>
          )}
        </div>
      </div>

      {/* Settings */}
      <GlassCard>
        <div className="flex items-center space-x-2 mb-4">
          <Settings className="w-5 h-5 text-neutral-500" />
          <h3 className="text-lg font-semibold text-neutral-900">Validation Settings</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="flex items-center space-x-2 text-sm font-medium text-neutral-700 mb-2">
              <input
                type="checkbox"
                checked={useNumverify}
                onChange={(e) => setUseNumverify(e.target.checked)}
                className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
              />
              <span>Use Numverify API</span>
            </label>
            <p className="text-xs text-neutral-500 mb-2">Get detailed carrier and location information</p>
            
            {useNumverify && (
              <div>
                <input
                  type="text"
                  placeholder="Numverify API Key (optional)"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  onBlur={() => {
                    if (apiKey) {
                      localStorage.setItem('numverify_api_key', apiKey);
                      validationService.setApiKeys('', apiKey);
                    }
                  }}
                  className="w-full px-3 py-2 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                />
                <p className="text-xs text-neutral-500 mt-1">
                  Get your free API key at numverify.com (100 free validations/month)
                </p>
              </div>
            )}
          </div>
          
          <div className="flex items-center justify-center">
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
                <Smartphone className="w-6 h-6 text-green-600" />
              </div>
              <p className="text-sm font-medium text-neutral-900">Advanced Validation</p>
              <p className="text-xs text-neutral-600">Carrier detection + format validation</p>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Input Area */}
      <GlassCard>
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">Phone Number Input</h3>
        
        <div className="flex space-x-3 mb-4">
          <input
            type="tel"
            placeholder="Enter phone number (e.g., +1234567890)..."
            value={phoneInput}
            onChange={(e) => setPhoneInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addPhone()}
            className="flex-1 px-3 py-2 border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
          />
          <button
            onClick={addPhone}
            disabled={!phoneInput.trim()}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg font-medium hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Add Phone
          </button>
        </div>

        {/* Phone List */}
        {phoneList.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium text-neutral-900">Phone List ({phoneList.length})</h4>
            <div className="max-h-40 overflow-y-auto space-y-1">
              {phoneList.map((phone) => (
                <div key={phone} className="flex items-center justify-between p-2 bg-neutral-50 rounded">
                  <span className="text-sm text-neutral-900">{phone}</span>
                  <button
                    onClick={() => removePhone(phone)}
                    className="p-1 text-neutral-400 hover:text-red-500 transition-colors"
                  >
                    <XCircle className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
            
            <div className="flex space-x-3 pt-3 border-t border-neutral-200">
              <button
                onClick={validateAllPhones}
                disabled={isValidating || phoneList.length === 0}
                className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded-lg font-medium hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isValidating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Validating...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    <span>Validate All ({phoneList.length})</span>
                  </>
                )}
              </button>
              
              <button
                onClick={() => setPhoneList([])}
                className="px-4 py-2 bg-neutral-500 text-white rounded-lg font-medium hover:bg-neutral-600 transition-colors"
              >
                Clear List
              </button>
            </div>
          </div>
        )}
      </GlassCard>

      {/* Progress */}
      {isValidating && (
        <GlassCard>
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin text-green-500 mx-auto mb-3" />
            <p className="text-neutral-900 font-medium">Validating phone numbers...</p>
            <p className="text-neutral-600 text-sm">
              {batchProgress.current} of {batchProgress.total} completed
            </p>
            <div className="mt-3 w-full bg-neutral-200 rounded-full h-2 max-w-md mx-auto">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(batchProgress.current / batchProgress.total) * 100}%` }}
              />
            </div>
          </div>
        </GlassCard>
      )}

      {/* Results Summary */}
      {Object.keys(validations).length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <GlassCard>
            <div className="text-center">
              <div className="text-2xl font-bold text-neutral-900">{phoneList.length}</div>
              <div className="text-sm text-neutral-600">Total Numbers</div>
            </div>
          </GlassCard>
          <GlassCard>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{validCount}</div>
              <div className="text-sm text-neutral-600">Valid</div>
            </div>
          </GlassCard>
          <GlassCard>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{mobileCount}</div>
              <div className="text-sm text-neutral-600">Mobile</div>
            </div>
          </GlassCard>
          <GlassCard>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{landlineCount}</div>
              <div className="text-sm text-neutral-600">Landline</div>
            </div>
          </GlassCard>
        </div>
      )}

      {/* Validation Results */}
      {Object.keys(validations).length > 0 && (
        <GlassCard>
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">Validation Results</h3>
          
          <div className="space-y-3">
            {phoneList.map((phone) => {
              const result = validations[phone];
              const status = getValidationStatus(phone);
              const StatusIcon = getStatusIcon(status);
              
              if (!result) return null;
              
              return (
                <div key={phone} className={`p-4 rounded-lg border ${getStatusColor(status)}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-2xl">{getLineTypeIcon(result.line_type || '')}</span>
                        <div>
                          <span className="font-medium text-neutral-900">{phone}</span>
                          <div className="flex items-center space-x-2">
                            <StatusIcon className="w-5 h-5" />
                            <span className="text-sm">
                              {status === 'valid' ? 'Valid' : status === 'invalid' ? 'Invalid' : 'Warning'}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-neutral-600">International:</span>
                          <div className="flex items-center space-x-1">
                            <span className="font-medium">{result.international_format}</span>
                            <button
                              onClick={() => copyToClipboard(result.international_format)}
                              className="p-1 hover:bg-white/50 rounded"
                            >
                              <Copy className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                        
                        <div>
                          <span className="text-neutral-600">Country:</span>
                          <div className="flex items-center space-x-1">
                            <span className="font-medium">{result.country_name}</span>
                            <span className="text-xs text-neutral-500">({result.country_code})</span>
                          </div>
                        </div>
                        
                        <div>
                          <span className="text-neutral-600">Carrier:</span>
                          <span className="font-medium">{result.carrier || 'Unknown'}</span>
                        </div>
                        
                        <div>
                          <span className="text-neutral-600">Type:</span>
                          <span className="font-medium capitalize">{result.line_type || 'Unknown'}</span>
                        </div>
                        
                        <div>
                          <span className="text-neutral-600">Local Format:</span>
                          <div className="flex items-center space-x-1">
                            <span className="font-medium">{result.local_format}</span>
                            <button
                              onClick={() => copyToClipboard(result.local_format)}
                              className="p-1 hover:bg-white/50 rounded"
                            >
                              <Copy className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                        
                        <div>
                          <span className="text-neutral-600">Prefix:</span>
                          <span className="font-medium">{result.country_prefix}</span>
                        </div>
                      </div>
                      
                      {result.location && (
                        <div className="mt-3 flex items-center space-x-1">
                          <MapPin className="w-4 h-4 text-neutral-500" />
                          <span className="text-sm text-neutral-600">Location: </span>
                          <span className="text-sm font-medium text-neutral-900">{result.location}</span>
                        </div>
                      )}
                      
                      <div className="mt-3 flex items-center space-x-4 text-xs">
                        <span className={`px-2 py-1 rounded-full ${
                          result.is_valid ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                        }`}>
                          {result.is_valid ? 'Valid Number' : 'Invalid Number'}
                        </span>
                        <span className={`px-2 py-1 rounded-full ${
                          result.is_possible ? 'bg-blue-100 text-blue-700' : 'bg-orange-100 text-orange-700'
                        }`}>
                          {result.is_possible ? 'Possible Format' : 'Format Issue'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </GlassCard>
      )}
    </div>
  );
};

export default PhoneValidator;