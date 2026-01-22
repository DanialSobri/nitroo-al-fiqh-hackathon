# Troubleshooting Guide

## Common Issues and Solutions

### 1. API Gateway 500 Internal Server Error

**Symptoms:**
- Error message: "API Gateway returned error: HTTP 500"
- Answer shows server error message

**Possible Causes & Solutions:**

#### A. Request Payload Too Large
- **Issue**: The prompt/context is too long for the API
- **Solution**: The code now automatically truncates prompts over 8000 characters
- **Manual Fix**: Reduce `max_results` in your request to get fewer context chunks

#### B. Model Not Available
- **Issue**: The specified model (e.g., `phi4:14b`) may not be available
- **Solution**: Check available models and update `API_GATEWAY_MODEL` in `.env`
- **Example**: Try `llama2:13b` or `mistral:7b`

#### C. API Gateway Service Issue
- **Issue**: The API Gateway or Ollama service may be down
- **Solution**: 
  - Check if Ollama is running locally
  - Verify API Gateway endpoints are accessible
  - Check network connectivity

#### D. Token Expired or Invalid
- **Issue**: Token may have expired or be invalid
- **Solution**: The code automatically refreshes tokens, but you can:
  - Check token endpoint is accessible
  - Verify `API_GATEWAY_AUTH_HEADER` is correct
  - Check cookie value is still valid

### 2. Token Authentication Errors

**Symptoms:**
- "Failed to get API Gateway token"
- 401 Unauthorized errors

**Solutions:**
1. Verify `API_GATEWAY_AUTH_HEADER` in `.env` matches your credentials
2. Check `API_GATEWAY_TOKEN_URL` is correct
3. Ensure cookie value is current (may expire)
4. Test token endpoint manually:
   ```bash
   curl -X POST "https://api.apigate.com/token?grant_type=client_credentials&scope=chat" \
     -H "Authorization: Basic cFFjZTVKk0kFRcFY0Q1lh"
   ```

### 3. Empty or Invalid Responses

**Symptoms:**
- Answer is empty or shows raw JSON
- Response format not recognized

**Solutions:**
1. Check API Gateway response format - may have changed
2. Review logs to see actual response structure
3. Update response parsing in `api_gateway_llm.py` if needed

### 4. Qdrant Connection Issues

**Symptoms:**
- "Failed to connect to Qdrant server"
- Collections not found

**Solutions:**
1. **Using Qdrant Server**:
   - Ensure Qdrant is running: `docker ps` or check service
   - Verify URL: `http://localhost:6333`
   - Test connection: `curl http://localhost:6333/collections`

2. **Using Local Database**:
   - Check path exists: `../Web-Scraper/qdrant_db`
   - Verify collections exist: Run `python verify_db.py` in Web-Scraper folder
   - Ensure you've run the scraper first

### 5. Long Response Times

**Symptoms:**
- Requests take very long
- Timeout errors

**Solutions:**
1. Reduce `max_results` in request (fewer documents to process)
2. Increase timeout in `api_gateway_llm.py` (currently 120s)
3. Use a faster/smaller model
4. Check Ollama performance locally

## Debugging Steps

### 1. Enable Verbose Logging

The code now includes detailed logging. Check console output for:
- Token fetch status
- Request details (without sensitive data)
- Response structure
- Error details

### 2. Test Token Endpoint Manually

```bash
curl -X POST "https://api.apigate.com/token?grant_type=client_credentials&scope=chat" \
  -H "Authorization: Basic cFFjZTVKk0kFRcFY0Q1lh" \
  -H "Cookie: visid_incap_2987376=mDFwBkeLRNOhB/BKqta1eNwKu2gAAAAAQUIPAAAAAAAYa6w/RznO64PTVP3jVW0q"
```

### 3. Test Chat API Manually

```bash
# First get token (from step 2)
TOKEN="your_token_here"

curl -X POST "https://api.apigate.com/t/com.my/Inventory-AI-LLM/1.0.0/api/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi4:14b",
    "messages": [{"role": "user", "content": "test"}],
    "stream": false
  }'
```

### 4. Check Environment Variables

```bash
# In backend directory
python -c "from config import settings; print(settings.dict())"
```

### 5. Test RAG Service Directly

```python
from rag_service import RAGService
from models import CollectionType

rag = RAGService()
result = rag.ask_question(
    question="What is Islamic banking?",
    collections=[CollectionType.ALL],
    max_results=3,
    min_score=0.5
)
print(result)
```

## Error Messages Reference

| Error | Meaning | Solution |
|-------|---------|----------|
| `HTTP 500` | Server error | Check API Gateway/Ollama status, reduce prompt size |
| `HTTP 401` | Authentication failed | Check token/auth header |
| `HTTP 404` | Endpoint not found | Verify API Gateway URLs |
| `Timeout` | Request took too long | Increase timeout or simplify request |
| `No valid token` | Token not obtained | Check token endpoint and credentials |
| `Collection not found` | Qdrant collection missing | Run scraper to populate collections |

## Getting Help

1. Check logs in console output
2. Review error messages carefully
3. Test endpoints manually with curl
4. Verify all environment variables are set correctly
5. Ensure all services (Qdrant, Ollama) are running
