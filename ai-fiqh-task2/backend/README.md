# Shariah Compliance Checker API

AI-powered FastAPI service for checking Islamic contract compliance against Shariah regulations.

## Features

- PDF contract upload and text extraction
- Sentence transformer embeddings (all-MiniLM-L6-v2)
- Vector storage in Qdrant
- AI agent for compliance checking
- Detailed violation reporting with severity levels
- Compliance scoring and categorization

## Prerequisites

- Docker and Docker Compose
- Local LLM API (Ollama or similar) running on port 11434

## Quick Start

1. Copy environment variables:
```bash
cp .env.example .env
```

2. Start the services:
```bash
docker-compose up -d
```

3. Access the API:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Qdrant: http://localhost:6333

## API Endpoints

### Regulations
- `POST /regulations/add` - Add a single Shariah regulation
- `POST /regulations/bulk-add` - Add multiple regulations
- `GET /regulations/list` - List all regulations
- `GET /regulations/search` - Search regulations by query

### Contracts
- `POST /contracts/upload` - Upload PDF contract
- `POST /contracts/check-compliance/{contract_id}` - Check compliance
- `GET /contracts/compliance-report/{contract_id}` - Get detailed report
- `GET /contracts/{contract_id}/chunks` - View contract chunks

### System
- `GET /health` - Health check
- `GET /` - API info

## Usage Example

1. Add Shariah Regulation:
```bash
curl -X POST "http://localhost:8000/regulations/add" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Prohibition of Riba",
    "content": "Interest-based transactions are strictly prohibited in Islamic finance",
    "category": "Interest",
    "reference": "Quran 2:275"
  }'
```

2. Upload Contract:
```bash
curl -X POST "http://localhost:8000/contracts/upload" \
  -F "file=@contract.pdf"
```

3. Check Compliance:
```bash
curl -X POST "http://localhost:8000/contracts/check-compliance/{contract_id}"
```

## Project Structure

```
backend/
├── app/
│   ├── agents/          # AI compliance agent
│   ├── models/          # Pydantic schemas
│   ├── routers/         # API endpoints
│   └── services/        # Business logic
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Environment Variables

- `QDRANT_HOST` - Qdrant host (default: qdrant)
- `QDRANT_PORT` - Qdrant port (default: 6333)
- `EMBEDDING_MODEL` - Sentence transformer model
- `LLM_API_URL` - Local LLM API endpoint
- `LLM_MODEL_NAME` - LLM model name

## Development

To run in development mode:
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
