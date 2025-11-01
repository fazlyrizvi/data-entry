// API Configuration for external services
export const API_KEYS = {
  HUNTER_IO: '', // Will be set by user or environment
  NUMVERIFY: '', // Will be set by user or environment
  GOOGLE_MAPS: 'AIzaSyCO0kKndUNlmQi3B5mxy4dblg_8WYcuKuk'
};

// Environment variables that can be set
export const getApiKey = (service: 'HUNTER_IO' | 'NUMVERIFY'): string => {
  // Try environment variable first
  const envKey = process.env[`REACT_APP_${service}_API_KEY`];
  if (envKey) return envKey;
  
  // Fallback to hardcoded for development
  const hardcodedKey = API_KEYS[service];
  if (hardcodedKey) return hardcodedKey;
  
  console.warn(`${service} API key not found. Validation will use basic fallbacks.`);
  return '';
};

export const setApiKey = (service: 'HUNTER_IO' | 'NUMVERIFY', key: string): void => {
  API_KEYS[service] = key;
  
  // Store in localStorage for persistence
  if (typeof window !== 'undefined') {
    localStorage.setItem(`${service.toLowerCase()}_api_key`, key);
  }
};

// Check if API keys are available
export const hasApiKey = (service: 'HUNTER_IO' | 'NUMVERIFY'): boolean => {
  return getApiKey(service).length > 0;
};

export default API_KEYS;