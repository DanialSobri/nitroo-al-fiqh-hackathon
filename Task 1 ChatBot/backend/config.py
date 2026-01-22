"""Configuration management for the backend API"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # LLM Provider Selection
    llm_provider: str = "ollama"  # Options: "openai", "ollama", or "api_gateway" (deprecated)
    
    # OpenAI Configuration (if using OpenAI)
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.7
    
    # Ollama Configuration (if using direct Ollama)
    ollama_url: str = "https://example.com.my/"  # Base URL for Ollama
    ollama_model: str = "phi4:14b"  # Model name to use
    
    # API Gateway Configuration (deprecated - use ollama instead)
    api_gateway_token_url: str = ""
    api_gateway_chat_url: str = ""
    api_gateway_auth_header: str = ""
    api_gateway_cookie: str = ""
    api_gateway_model: str = "phi4:14b"
    
    # Legacy support (for backward compatibility)
    llm_model: str = "phi4:14b"  # Default model name
    
    # Qdrant Configuration
    qdrant_path: str = "../Web-Scraper/qdrant_db"
    qdrant_url: Optional[str] = "http://localhost:6333"  # Default to Qdrant server
    
    # RAG Configuration
    max_retrieval_results: int = 5
    min_similarity_score: float = 0.5
    
    # Advanced RAG Configuration (Context Window Optimization)
    enable_reranking: bool = False  # Enable cross-encoder re-ranking
    enable_query_expansion: bool = False  # Generate query variations
    enable_diversity_filtering: bool = True  # Use MMR for diverse results
    enable_context_compression: bool = False  # Summarize context before LLM
    enable_hybrid_search: bool = False  # Combine vector + keyword search
    
    # Multi-stage retrieval parameters
    initial_retrieval_count: int = 20  # Retrieve more candidates initially
    final_retrieval_count: int = 5  # Final count after filtering/re-ranking
    diversity_threshold: float = 0.7  # MMR lambda (0=diversity, 1=relevance)
    
    # Context management
    max_context_length: int = 4000  # Maximum context size in characters (reduced for smaller payloads)
    enable_smart_truncation: bool = True  # Smart context prioritization
    use_compact_prompt: bool = True  # Use shorter, more compact prompt template
    
    # Available collections
    collections: list[str] = ["bnm_pdfs", "iifa_resolutions", "sc_resolutions"]
    
    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
