# API Gateway Setup Guide

## Overview

The backend now supports using API Gateway to access Ollama models locally. The API Gateway acts as a proxy to your local Ollama instance.

## Configuration

The API Gateway configuration is pre-configured in `.env.example` with the following settings:

```env
LLM_PROVIDER=api_gateway
API_GATEWAY_TOKEN_URL=https://api.apigate.com/token
API_GATEWAY_CHAT_URL=https://api.apigate.com/t/com.my/Inventory-AI-LLM/1.0.0/api/chat
API_GATEWAY_AUTH_HEADER=Basic cFFjZTVKk0kFRcFY0Q1lh
API_GATEWAY_COOKIE=visid_incap_2987376=mDFwBkeLRNOhB/BKqta1eNwKu2gAAAAAQUIPAAAAAAAYa6w/RznO64PTVP3jVW0q
API_GATEWAY_MODEL=phi4:14b
```

## How It Works

1. **Token Authentication**: The system automatically obtains an access token from the API Gateway token endpoint
2. **Token Caching**: Tokens are cached and automatically refreshed when they expire
3. **Chat API**: Uses the token to make requests to the chat API endpoint
4. **Model**: Uses the specified Ollama model (default: phi4:14b)

## Setup Steps

1. **Copy environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Verify configuration**: The API Gateway settings are already configured. No changes needed unless you have different endpoints.

3. **Start the server**:
   ```bash
   python main.py
   ```

## Switching Between Providers

### Use API Gateway (Default)
```env
LLM_PROVIDER=api_gateway
```

### Use OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-3.5-turbo
```

## API Gateway Flow

```
┌─────────────┐
│   Backend   │
└──────┬──────┘
       │
       │ 1. Request Token
       ▼
┌─────────────────────┐
│  API Gateway Token  │
│      Endpoint       │
└──────┬──────────────┘
       │
       │ 2. Return Token
       ▼
┌─────────────┐
│   Backend   │
│ (Cache Token)│
└──────┬──────┘
       │
       │ 3. Chat Request with Token
       ▼
┌─────────────────────┐
│  API Gateway Chat   │
│      Endpoint       │
└──────┬──────────────┘
       │
       │ 4. Forward to Ollama
       ▼
┌─────────────┐
│   Ollama    │
│  (Local)    │
└─────────────┘
```

## Troubleshooting

### Token Issues

If you get token errors:
- Check that `API_GATEWAY_AUTH_HEADER` is correct
- Verify the token URL is accessible
- Check network connectivity

### Model Not Found

If the model doesn't exist:
- Verify Ollama is running locally
- Check that the model `phi4:14b` is installed: `ollama list`
- Update `API_GATEWAY_MODEL` in `.env` if using a different model

### Connection Errors

- Ensure API Gateway endpoints are accessible
- Check firewall settings
- Verify cookie and auth header are still valid

## Testing

Test the API Gateway connection:

```python
from api_gateway_llm import APIGatewayLLM

llm = APIGatewayLLM(
    token_url="https://api.apigate.com/token",
    chat_url="https://api.apigate.com/t/com.my/Inventory-AI-LLM/1.0.0/api/chat",
    auth_header="Basic cFFjZTVKk0kFRcFY0Q1lh",
    model="phi4:14b"
)

response = llm.invoke("What is Islamic banking?")
print(response)
```

## Model Options

Available Ollama models you can use:
- `phi4:14b` (default) - Microsoft Phi-4 14B
- `llama2:13b` - Meta Llama 2 13B
- `mistral:7b` - Mistral 7B
- `qwen:14b` - Qwen 14B

Update `API_GATEWAY_MODEL` in `.env` to use a different model.
