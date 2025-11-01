import React, { useState, useEffect } from 'react';
import { 
  Mail, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Loader2, 
  Settings,
  Info,
  Shield,
  Copy,
  Download
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { validationService, EmailValidationResult } from '../../services/validationService';

interface EmailValidatorProps {
  emails?: string[];
  onValidationComplete?: (results: EmailValidationResult[]) => void;
}

export const EmailValidator: React.FC<EmailValidatorProps> = ({
  emails = [],
  onValidationComplete
}) => {
  const [emailInput, setEmailInput] = useState('');
  const [emailList, setEmailList] = useState<string[]>(emails);
  const [validations, setValidations] = useState<Record<string, EmailValidationResult>>({});
  const [isValidating, setIsValidating] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [useHunter, setUseHunter] = useState(true);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });

  useEffect(() => {
    // Set API key if available
    const savedKey = localStorage.getItem('hunter_api_key');
    if (savedKey) {
      setApiKey(savedKey);
      validationService.setApiKeys(savedKey, '');
    }
  }, []);

  const addEmail = () => {
    if (emailInput.trim() && !emailList.includes(emailInput.trim().toLowerCase())) {
      const newEmail = emailInput.trim().toLowerCase();
      setEmailList([...emailList, newEmail]);
      setEmailInput('');
    }
  };

  const removeEmail = (email: string) => {
    setEmailList(emailList.filter(e => e !== email));
    const { [email]: removed, ...remaining } = validations;
    setValidations(remaining);
  };

  const validateSingleEmail = async (email: string) => {
    try {
      const result = await validationService.validateEmail(email, useHunter);
      setValidations(prev => ({ ...prev, [email]: result }));
      return result;
    } catch (error) {
      console.error(`Failed to validate ${email}:`, error);
      return null;
    }
  };

  const validateAllEmails = async () => {
    if (emailList.length === 0) return;

    setIsValidating(true);
    setBatchProgress({ current: 0, total: emailList.length });

    const results: EmailValidationResult[] = [];

    for (let i = 0; i < emailList.length; i++) {
      const email = emailList[i];
      
      setBatchProgress({ current: i, total: emailList.length });

      try {
        const result = await validateSingleEmail(email);
        if (result) {
          results.push(result);
        }
      } catch (error) {
        console.error(`Validation failed for ${email}:`, error);
      }

      // Small delay to avoid overwhelming the API
      if (useHunter && apiKey) {
        await new Promise(resolve => setTimeout(resolve, 200));
      }
    }

    setBatchProgress({ current: emailList.length, total: emailList.length });
    setIsValidating(false);

    if (onValidationComplete) {
      onValidationComplete(results);
    }
  };

  const exportResults = (format: 'json' | 'csv') => {
    const results = Object.entries(validations).map(([email, result]) => ({
      email,
      ...result
    }));

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'email-validation-results.json';
      a.click();
      URL.revokeObjectURL(url);
    } else if (format === 'csv') {
      const headers = ['Email', 'Valid', 'Deliverability Score', 'Role', 'Free', 'Disposable', 'Risks'];
      const rows = results.map(r => [
        r.email,
        r.is_valid.toString(),
        r.deliverability_score.toString(),
        r.role.toString(),
        r.free.toString(),
        r.disposable.toString(),
        r.risks.join('; ')
      ]);
      
      const csvContent = [headers.join(','), ...rows.map(row => row.map(cell => `"${cell}"`).join(','))].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'email-validation-results.csv';
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const getValidationStatus = (email: string) => {
    const result = validations[email];
    if (!result) return 'pending';

    if (result.is_valid && result.deliverability_score > 70) return 'valid';
    if (!result.is_valid || result.deliverability_score < 30) return 'invalid';
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

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const validCount = Object.values(validations).filter(v => v.is_valid).length;
  const invalidCount = Object.values(validations).filter(v => !v.is_valid).length;
  const highRiskCount = Object.values(validations).filter(v => v.risks.some(risk => risk.includes('Low deliverability'))).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-neutral-900 flex items-center space-x-2">
            <Mail className="w-7 h-7 text-blue-500" />
            <span>Email Validator</span>
          </h2>
          <p className="text-neutral-600 mt-1">Validate email addresses using Hunter.io and custom rules</p>
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
                checked={useHunter}
                onChange={(e) => setUseHunter(e.target.checked)}
                className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
              />
              <span>Use Hunter.io API</span>
            </label>
            <p className="text-xs text-neutral-500 mb-2">Get detailed deliverability scores and domain information</p>
            
            {useHunter && (
              <div>
                <input
                  type="text"
                  placeholder="Hunter.io API Key (optional)"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  onBlur={() => {
                    if (apiKey) {
                      localStorage.setItem('hunter_api_key', apiKey);
                      validationService.setApiKeys(apiKey, '');
                    }
                  }}
                  className="w-full px-3 py-2 border border-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                />
                <p className="text-xs text-neutral-500 mt-1">
                  Get your free API key at hunter.io (50 free verifications/month)
                </p>
              </div>
            )}
          </div>
          
          <div className="flex items-center justify-center">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
                <Shield className="w-6 h-6 text-blue-600" />
              </div>
              <p className="text-sm font-medium text-neutral-900">Advanced Validation</p>
              <p className="text-xs text-neutral-600">SMTP checking + deliverability analysis</p>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Input Area */}
      <GlassCard>
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">Email Input</h3>
        
        <div className="flex space-x-3 mb-4">
          <input
            type="email"
            placeholder="Enter email address..."
            value={emailInput}
            onChange={(e) => setEmailInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addEmail()}
            className="flex-1 px-3 py-2 border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
          />
          <button
            onClick={addEmail}
            disabled={!emailInput.trim()}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg font-medium hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Add Email
          </button>
        </div>

        {/* Email List */}
        {emailList.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium text-neutral-900">Email List ({emailList.length})</h4>
            <div className="max-h-40 overflow-y-auto space-y-1">
              {emailList.map((email) => (
                <div key={email} className="flex items-center justify-between p-2 bg-neutral-50 rounded">
                  <span className="text-sm text-neutral-900">{email}</span>
                  <button
                    onClick={() => removeEmail(email)}
                    className="p-1 text-neutral-400 hover:text-red-500 transition-colors"
                  >
                    <XCircle className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
            
            <div className="flex space-x-3 pt-3 border-t border-neutral-200">
              <button
                onClick={validateAllEmails}
                disabled={isValidating || emailList.length === 0}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isValidating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Validating...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    <span>Validate All ({emailList.length})</span>
                  </>
                )}
              </button>
              
              <button
                onClick={() => setEmailList([])}
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
            <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-3" />
            <p className="text-neutral-900 font-medium">Validating emails...</p>
            <p className="text-neutral-600 text-sm">
              {batchProgress.current} of {batchProgress.total} completed
            </p>
            <div className="mt-3 w-full bg-neutral-200 rounded-full h-2 max-w-md mx-auto">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(batchProgress.current / batchProgress.total) * 100}%` }}
              />
            </div>
          </div>
        </GlassCard>
      )}

      {/* Results Summary */}
      {Object.keys(validations).length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <GlassCard>
            <div className="text-center">
              <div className="text-2xl font-bold text-neutral-900">{emailList.length}</div>
              <div className="text-sm text-neutral-600">Total Emails</div>
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
              <div className="text-2xl font-bold text-red-600">{invalidCount}</div>
              <div className="text-sm text-neutral-600">Invalid</div>
            </div>
          </GlassCard>
          <GlassCard>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{highRiskCount}</div>
              <div className="text-sm text-neutral-600">High Risk</div>
            </div>
          </GlassCard>
        </div>
      )}

      {/* Validation Results */}
      {Object.keys(validations).length > 0 && (
        <GlassCard>
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">Validation Results</h3>
          
          <div className="space-y-3">
            {emailList.map((email) => {
              const result = validations[email];
              const status = getValidationStatus(email);
              const StatusIcon = getStatusIcon(status);
              
              if (!result) return null;
              
              return (
                <div key={email} className={`p-4 rounded-lg border ${getStatusColor(status)}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="font-medium text-neutral-900">{email}</span>
                        <StatusIcon className="w-5 h-5" />
                        <span className="text-sm">
                          {status === 'valid' ? 'Valid' : status === 'invalid' ? 'Invalid' : 'Warning'}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-neutral-600">Deliverability:</span>
                          <div className="flex items-center space-x-1">
                            <span className="font-medium">{result.deliverability_score}%</span>
                            <button
                              onClick={() => copyToClipboard(result.deliverability_score.toString())}
                              className="p-1 hover:bg-white/50 rounded"
                            >
                              <Copy className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                        
                        <div>
                          <span className="text-neutral-600">Role:</span>
                          <span className="font-medium">{result.role ? 'Yes' : 'No'}</span>
                        </div>
                        
                        <div>
                          <span className="text-neutral-600">Free:</span>
                          <span className="font-medium">{result.free ? 'Yes' : 'No'}</span>
                        </div>
                        
                        <div>
                          <span className="text-neutral-600">Disposable:</span>
                          <span className="font-medium">{result.disposable ? 'Yes' : 'No'}</span>
                        </div>
                      </div>
                      
                      {result.risks.length > 0 && (
                        <div className="mt-3">
                          <div className="flex items-center space-x-1 mb-1">
                            <Info className="w-4 h-4 text-orange-600" />
                            <span className="text-sm font-medium text-orange-900">Risks & Warnings:</span>
                          </div>
                          <ul className="text-sm text-orange-800 space-y-1">
                            {result.risks.map((risk, index) => (
                              <li key={index}>• {risk}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {useHunter && result.server_info && (
                        <div className="mt-3">
                          <span className="text-sm font-medium text-neutral-700">Server Info:</span>
                          <p className="text-sm text-neutral-600">
                            {result.server_info.domain} • {result.server_info.is_smtp_valid ? 'SMTP Valid' : 'SMTP Invalid'}
                          </p>
                        </div>
                      )}
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

export default EmailValidator;