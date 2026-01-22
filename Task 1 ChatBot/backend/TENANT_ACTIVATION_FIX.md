# API Gateway Tenant Activation Error Fix

## Error Message

```
SOAP Fault: Error while getting tenant activation status.
```

## What This Means

This error indicates that the API Gateway tenant/service is not properly activated. This is a **configuration issue**, not a code problem.

## Solutions

### 1. Verify API Gateway Configuration

Check with your API Gateway administrator:
- Is the tenant properly activated?
- Is the service subscription active?
- Are the authentication credentials correct?

### 2. Verify Credentials

Check your `.env` file:
```env
API_GATEWAY_AUTH_HEADER=Basic cFFjZTVKk0kFRcFY0Q1lh
API_GATEWAY_TOKEN_URL=https://api.apigate.com/token
API_GATEWAY_CHAT_URL=https://api.apigate.com/t/com.my/Inventory-AI-LLM/1.0.0/api/chat
```

### 3. Test Token Endpoint Manually

```bash
curl -X POST "https://api.apigate.com/token?grant_type=client_credentials&scope=chat" \
  -H "Authorization: Basic cFFjZTVKk0kFRcFY0Q1lh" \
  -H "Cookie: visid_incap_2987376=mDFwBkeLRNOhB/BKqta1eNwKu2gAAAAAQUIPAAAAAAAYa6w/RznO64PTVP3jVW0q"
```

If this returns a token successfully, the issue is with the chat endpoint.

### 4. Test Chat Endpoint Manually

After getting a token:
```bash
TOKEN="your_token_here"

curl -X POST "https://api.apigate.com/t/com.my/Inventory-AI-LLM/1.0.0/api/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Cookie: visid_incap_2987376=mDFwBkeLRNOhB/BKqta1eNwKu2gAAAAAQUIPAAAAAAAYa6w/RznO64PTVP3jVW0q" \
  -d '{
    "model": "phi4:14b",
    "messages": [{"role": "user", "content": "test"}],
    "stream": false
  }'
```

### 5. Contact API Gateway Administrator

If the tenant activation error persists:
- Contact your API Gateway administrator
- Verify the service is properly subscribed
- Check if there are any pending activations
- Ensure the service endpoint is correctly configured

## Temporary Workaround

If you need to test the system while resolving the tenant activation issue, you can:

1. **Switch to OpenAI** (if you have an API key):
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-key-here
   ```

2. **Use a different API Gateway endpoint** (if available):
   Update the `API_GATEWAY_CHAT_URL` in `.env` to a working endpoint

## Notes

- This error is **NOT retryable** - it's a configuration issue
- The code will not automatically retry on tenant activation errors
- You must resolve the API Gateway configuration before the system will work
