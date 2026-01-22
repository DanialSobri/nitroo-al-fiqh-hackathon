# Ollama Setup Guide

## Overview
This guide explains how to use direct Ollama instead of API Gateway.

## Configuration

### 1. Update `.env` file

```bash
# Set provider to ollama
LLM_PROVIDER=ollama

# Configure Ollama URL and model
OLLAMA_URL=https://v-wkp54x2qz-11434.tma01.com.my/
OLLAMA_MODEL=phi4:14b
```

### 2. Benefits of Direct Ollama

- ✅ **No token management** - Ollama doesn't require authentication tokens
- ✅ **Simpler setup** - Just need the base URL
- ✅ **Better performance** - Direct connection without API Gateway overhead
- ✅ **No tenant activation issues** - Direct access to Ollama instance

## API Format

Ollama uses a simple REST API:

**Endpoint**: `{OLLAMA_URL}/api/chat`

**Request**:
```json
{
  "model": "phi4:14b",
  "messages": [
    {
      "role": "user",
      "content": "Your prompt here"
    }
  ],
  "stream": false
}
```

**Response**:
```json
{
  "model": "phi4:14b",
  "created_at": "2026-01-20T18:35:02.45712385Z",
  "message": {
    "role": "assistant",
    "content": "Response text here"
  },
  "done": true
}
```

## Testing

### Test Connection

```bash
curl http://localhost:8000/test-token
```

Expected response:
```json
{
  "status": "success",
  "message": "Ollama connection ready",
  "ollama_url": "https://v-wkp54x2qz-11434.tma01.com.my/",
  "chat_url": "https://v-wkp54x2qz-11434.tma01.com.my/api/chat",
  "model": "phi4:14b"
}
```

### Test Chat

```bash
curl -X POST http://localhost:8000/test-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, this is a test"}'
```

## Migration from API Gateway

If you were using API Gateway before:

1. **Update `.env`**:
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_URL=https://v-wkp54x2qz-11434.tma01.com.my/
   OLLAMA_MODEL=phi4:14b
   ```

2. **Remove API Gateway settings** (optional):
   ```bash
   # These are no longer needed
   # API_GATEWAY_TOKEN_URL=
   # API_GATEWAY_CHAT_URL=
   # API_GATEWAY_AUTH_HEADER=
   # API_GATEWAY_COOKIE=
   ```

3. **Restart the backend**:
   ```bash
   python main.py
   ```

## Troubleshooting

### Connection Issues

If you see connection errors:

1. **Verify Ollama URL**:
   - Ensure the URL ends with `/`
   - Check if the URL is accessible: `curl {OLLAMA_URL}/api/tags`

2. **Check Model Availability**:
   - Verify the model exists: `curl {OLLAMA_URL}/api/tags`
   - Ensure model name matches exactly (case-sensitive)

3. **Network Issues**:
   - Check firewall settings
   - Verify VPN/network access if required

### Common Errors

**"Connection refused"**:
- Ollama server may not be running
- URL may be incorrect
- Network connectivity issue

**"Model not found"**:
- Model name doesn't match
- Model not pulled/downloaded on Ollama server

**"Timeout"**:
- Increase timeout in code (default: 120s)
- Check Ollama server performance
- Reduce context size if prompt is too large

## Debug Mode

The implementation includes detailed debug logging. Check console output for:
- Request/response details
- Payload structure
- Error messages

## API Gateway (Deprecated)

API Gateway support is still available but deprecated. To use it:

```bash
LLM_PROVIDER=api_gateway
# ... API Gateway settings ...
```

However, **direct Ollama is recommended** for better performance and simpler setup.
