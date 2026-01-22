# Islamic Finance RAG API Backend

A FastAPI-based backend service that provides RAG (Retrieval Augmented Generation) capabilities for querying Islamic finance documents using LangChain and Qdrant.

## Features

- **RAG-based Question Answering**: Ask questions and get answers based on indexed documents
- **Multi-Collection Support**: Search across BNM, IIFA, and SC document collections
- **Reference Retrieval**: Get source references with similarity scores
- **LangChain Integration**: Uses LangChain for LLM orchestration
- **FastAPI REST API**: Clean RESTful API with automatic documentation

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and configure:
- `LLM_PROVIDER`: Choose `"api_gateway"` (default) or `"openai"`
- **For API Gateway** (default): Pre-configured, no changes needed
- **For OpenAI**: Set `OPENAI_API_KEY` and `OPENAI_MODEL`
- `QDRANT_PATH`: Path to Qdrant database (default: `../Web-Scraper/qdrant_db`)

### 3. Run the Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check

```bash
GET /health
```

Returns the health status of the service.

### Ask a Question

```bash
POST /ask
Content-Type: application/json

{
  "question": "What are the Islamic banking regulations?",
  "collections": ["all"],
  "max_results": 5,
  "min_score": 0.5
}
```

**Request Parameters:**
- `question` (required): The question to ask
- `collections` (optional): List of collections to search. Options: `["bnm_pdfs"]`, `["iifa_resolutions"]`, `["sc_resolutions"]`, or `["all"]` (default)
- `max_results` (optional): Maximum number of references to return (default: 5, max: 20)
- `min_score` (optional): Minimum similarity score threshold (default: 0.5)

**Note**: The API uses API Gateway with Ollama (phi4:14b model) by default. You can switch to OpenAI by setting `LLM_PROVIDER=openai` in `.env`.

**Response:**
```json
{
  "answer": "The answer based on the documents...",
  "question": "What are the Islamic banking regulations?",
  "references": [
    {
      "pdf_title": "Document Title",
      "pdf_url": "https://...",
      "chunk_text": "Relevant text excerpt...",
      "similarity_score": 0.85,
      "chunk_index": 0,
      "total_chunks": 10,
      "date": "2024-01-01",
      "source": "bnm_pdfs"
    }
  ],
  "total_references_found": 5,
  "collections_searched": ["bnm_pdfs", "iifa_resolutions", "sc_resolutions"]
}
```

### Get Collections

```bash
GET /collections
```

Returns a list of available collections.

### Test Token Endpoint

```bash
GET /test-token
```

Tests the API Gateway token endpoint and returns token status.

### Test Chat Endpoint

```bash
POST /test-chat
Content-Type: application/json

{
  "message": "Hello, this is a test"
}
```

Tests the API Gateway chat endpoint with a simple message.

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Usage

### Using curl

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the Shariah ruling on sukuk?",
    "collections": ["all"],
    "max_results": 5
  }'
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/ask",
    json={
        "question": "What are the requirements for Islamic banking?",
        "collections": ["bnm_pdfs"],
        "max_results": 5
    }
)

data = response.json()
print(f"Answer: {data['answer']}")
print(f"References: {len(data['references'])}")
```

## Project Structure

```
backend/
├── main.py              # FastAPI application
├── rag_service.py       # RAG service with LangChain
├── models.py            # Pydantic models
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

## Configuration

All configuration is done through environment variables in `.env`:

- **OPENAI_API_KEY**: Required. Your OpenAI API key
- **QDRANT_PATH**: Path to local Qdrant database
- **QDRANT_URL**: URL to Qdrant server (if using server mode)
- **LLM_MODEL**: OpenAI model name (default: gpt-3.5-turbo)
- **LLM_TEMPERATURE**: LLM temperature (default: 0.7)
- **MAX_RETRIEVAL_RESULTS**: Default max results (default: 5)
- **MIN_SIMILARITY_SCORE**: Default min similarity (default: 0.5)

## Troubleshooting

### RAG service fails to initialize

- Check that Qdrant database exists at the specified path
- Verify that collections are populated (run the scraper first)
- Check OpenAI API key is set correctly

### No results returned

- Try lowering the `min_score` threshold
- Check that documents have been indexed in Qdrant
- Verify the question is relevant to the indexed documents

### LLM errors

- Verify OpenAI API key is valid
- Check API quota/limits
- Try a different model if available

## Development

To run in development mode with auto-reload:

```bash
uvicorn main:app --reload
```

## License

Same as parent project.
