from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from app.models.schemas import RegulationInput, RegulationResponse
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service
from datetime import datetime

router = APIRouter(prefix="/regulations", tags=["regulations"])

@router.post("/add", response_model=RegulationResponse)
async def add_regulation(regulation: RegulationInput):
    try:
        regulation_id = str(uuid.uuid4())
        
        embedding = embedding_service.embed_text(regulation.content)
        
        qdrant_service.insert_regulation(
            regulation_id=regulation_id,
            title=regulation.title,
            content=regulation.content,
            embedding=embedding,
            category=regulation.category,
            reference=regulation.reference
        )
        
        return RegulationResponse(
            id=regulation_id,
            title=regulation.title,
            category=regulation.category,
            reference=regulation.reference,
            created_at=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add regulation: {str(e)}")

@router.post("/bulk-add", response_model=List[RegulationResponse])
async def bulk_add_regulations(regulations: List[RegulationInput]):
    try:
        results = []
        
        for regulation in regulations:
            regulation_id = str(uuid.uuid4())
            
            embedding = embedding_service.embed_text(regulation.content)
            
            qdrant_service.insert_regulation(
                regulation_id=regulation_id,
                title=regulation.title,
                content=regulation.content,
                embedding=embedding,
                category=regulation.category,
                reference=regulation.reference
            )
            
            results.append(RegulationResponse(
                id=regulation_id,
                title=regulation.title,
                category=regulation.category,
                reference=regulation.reference,
                created_at=datetime.utcnow()
            ))
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk add regulations: {str(e)}")

@router.get("/list")
async def list_regulations():
    try:
        regulations = qdrant_service.get_all_regulations()
        return {
            "total": len(regulations),
            "regulations": regulations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list regulations: {str(e)}")

@router.get("/search")
async def search_regulations(query: str, limit: int = 10):
    try:
        query_embedding = embedding_service.embed_text(query)
        
        results = qdrant_service.search_similar_regulations(
            query_embedding=query_embedding,
            limit=limit,
            score_threshold=0.3
        )
        
        return {
            "query": query,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search regulations: {str(e)}")
