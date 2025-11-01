# API Keys Required for Full Functionality

To enable the full data validation features, you need to obtain API keys from the following services:

## 1. Hunter.io API Key (for Email Validation)
- **Purpose**: Advanced email validation with deliverability scores
- **Free Tier**: 50 verifications/month
- **Sign up**: https://hunter.io/api
- **Steps**: 
  1. Create account at hunter.io
  2. Go to API section
  3. Copy your API key

## 2. Numverify API Key (for Phone Validation)  
- **Purpose**: Phone number validation with carrier and location detection
- **Free Tier**: 100 validations/month
- **Sign up**: https://numverify.com
- **Steps**:
  1. Create account at numverify.com
  2. Register for API access
  3. Copy your API key

## How to Set Up API Keys

Once you have the keys, you can set them in the application by:

1. **Direct Input**: The validation services have settings panels where you can enter your API keys
2. **Environment Variables**: Set `REACT_APP_HUNTER_IO_API_KEY` and `REACT_APP_NUMVERIFY_API_KEY`
3. **Local Storage**: Keys will be saved in browser localStorage after first use

## Fallback Behavior

Without API keys, the validation services will use basic fallbacks:
- **Email**: Format validation only
- **Phone**: Basic number format checking
- **Address**: Simple format validation

This will still work but without the advanced features like deliverability scores and carrier detection.