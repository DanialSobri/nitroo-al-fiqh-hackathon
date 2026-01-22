from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from app.config import settings

class EmbeddingService:
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        try:
            self.model = SentenceTransformer(settings.embedding_model)
        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model: {str(e)}")
    
    def embed_text(self, text: str) -> List[float]:
        if self.model is None:
            self._load_model()
        
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if self.model is None:
            self._load_model()
        
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        return settings.embedding_dimension

embedding_service = EmbeddingService()
