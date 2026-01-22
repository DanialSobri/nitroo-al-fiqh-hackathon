# Backend Architecture

## Overview

The backend is a FastAPI-based REST API that provides RAG (Retrieval Augmented Generation) capabilities for querying Islamic finance documents. It uses LangChain for LLM orchestration and Qdrant as the vector database.

## Architecture Diagram

```
┌─────────────┐
│   Client    │
│  (Frontend) │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────────────────────────────┐
│         FastAPI Application         │
│  ┌───────────────────────────────┐  │
│  │      API Endpoints            │  │
│  │  - POST /ask                  │  │
│  │  - GET /health                │  │
│  │  - GET /collections           │  │
│  └───────────┬───────────────────┘  │
│              │                      │
│  ┌───────────▼───────────────────┐  │
│  │      RAG Service              │  │
│  │  - Question Processing       │  │
│  │  - Document Retrieval        │  │
│  │  - Answer Generation         │  │
│  └───────────┬───────────────────┘  │
└──────────────┼──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐  ┌──────────────┐
│   Qdrant    │  │   OpenAI     │
│  Vector DB  │  │     LLM      │
│             │  │              │
│ Collections:│  │  GPT-3.5/4   │
│ - bnm_pdfs  │  │              │
│ - iifa_*    │  └──────────────┘
│ - sc_*      │
└─────────────┘
```

## Components

### 1. FastAPI Application (`main.py`)

- **Purpose**: HTTP server and API endpoints
- **Key Features**:
  - RESTful API with automatic OpenAPI documentation
  - CORS middleware for frontend integration
  - Error handling and validation
  - Health check endpoints

### 2. RAG Service (`rag_service.py`)

- **Purpose**: Core RAG functionality
- **Responsibilities**:
  - Initialize embedding model (sentence-transformers)
  - Connect to Qdrant vector database
  - Retrieve relevant documents based on queries
  - Generate answers using LLM (OpenAI)
  - Format responses with references

### 3. Models (`models.py`)

- **Purpose**: Pydantic models for request/response validation
- **Key Models**:
  - `QuestionRequest`: Input validation for questions
  - `QuestionResponse`: Structured response with answer and references
  - `SourceReference`: Metadata for each source document
  - `CollectionType`: Enum for collection selection

### 4. Configuration (`config.py`)

- **Purpose**: Environment-based configuration management
- **Settings**:
  - OpenAI API key
  - Qdrant connection (path or URL)
  - LLM model selection
  - RAG parameters (max results, min score)

## Data Flow

### Question Answering Flow

1. **Client Request**: POST `/ask` with question
2. **Request Validation**: Pydantic validates input
3. **Query Embedding**: Question converted to vector using sentence-transformers
4. **Vector Search**: Qdrant searches across selected collections
5. **Document Retrieval**: Top-k relevant chunks retrieved with metadata
6. **Context Preparation**: Retrieved chunks formatted as context
7. **LLM Generation**: OpenAI LLM generates answer based on context
8. **Response Formatting**: Answer + references formatted as JSON
9. **Client Response**: Structured response returned

### Reference Retrieval

Each reference includes:
- PDF title and URL
- Relevant text chunk
- Similarity score
- Document metadata (date, type, resolution number)
- Source collection name
- Chunk position information

## Collections

The system supports multiple document collections:

- **bnm_pdfs**: Bank Negara Malaysia Islamic Banking documents
- **iifa_resolutions**: International Islamic Fiqh Academy resolutions
- **sc_resolutions**: Securities Commission Shariah Advisory Council resolutions

Users can query:
- All collections (default)
- Specific collection(s)
- Multiple collections

## Technology Stack

- **FastAPI**: Modern Python web framework
- **LangChain**: LLM orchestration framework
- **OpenAI**: LLM provider (GPT-3.5/4)
- **Qdrant**: Vector database
- **Sentence Transformers**: Embedding model
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

## Security Considerations

- API keys stored in environment variables
- Input validation via Pydantic
- Error handling to prevent information leakage
- CORS configuration for frontend integration

## Scalability

- Stateless API design (can scale horizontally)
- Vector database can be scaled separately
- LLM calls are stateless
- Embedding model cached in memory

## Future Enhancements

- Authentication and authorization
- Rate limiting
- Caching for common queries
- Support for additional LLM providers
- Streaming responses
- Conversation history
- Multi-language support
