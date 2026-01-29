from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_contracts_collection: str = "shariah-contracts"
    qdrant_regulations_collection: str = "shariah-regulations-law"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    llm_api_url: str = "http://localhost:11434/api/chat"
    llm_model_name: str = "llama2"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
