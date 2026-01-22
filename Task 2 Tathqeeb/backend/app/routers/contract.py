from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid
from app.models.schemas import (
    ContractUploadResponse, 
    ComplianceCheckResponse, 
    ComplianceReportRequest,
    ContractRatingRequest,
    AnalyticsResponse,
    ScholarReviewRequest,
    ScholarReviewResponse
)
from app.services.pdf_service import pdf_service
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service
from app.agents.shariah_agent import ShariahComplianceAgent
from app.config import settings

router = APIRouter(prefix="/contracts", tags=["contracts"])

shariah_agent = ShariahComplianceAgent(
    llm_api_url=settings.llm_api_url,
    llm_model_name=settings.llm_model_name
)

@router.post("/upload", response_model=ContractUploadResponse)
async def upload_contract(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        pdf_content = await file.read()
        
        text = pdf_service.extract_text_from_pdf(pdf_content)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF")
        
        chunks = pdf_service.chunk_text(text)
        
        embeddings = embedding_service.embed_texts(chunks)
        
        contract_id = str(uuid.uuid4())
        
        chunks_count = qdrant_service.insert_contract_chunks(
            contract_id=contract_id,
            chunks=chunks,
            embeddings=embeddings,
            metadata={"filename": file.filename}
        )
        
        return ContractUploadResponse(
            contract_id=contract_id,
            filename=file.filename,
            text_length=len(text),
            chunks_created=chunks_count,
            message="Contract uploaded and processed successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process contract: {str(e)}")

@router.post("/check-compliance/{contract_id}", response_model=ComplianceCheckResponse)
async def check_contract_compliance(contract_id: str):
    """Re-run compliance check and update stored report"""
    try:
        result = await shariah_agent.check_compliance(contract_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check compliance: {str(e)}")

@router.get("/report/{contract_id}", response_model=ComplianceCheckResponse)
async def get_stored_report(contract_id: str):
    """Get cached compliance report without re-running analysis"""
    try:
        # Try to get stored report from Qdrant
        report = qdrant_service.get_contract_report(contract_id)
        
        if not report:
            raise HTTPException(
                status_code=404, 
                detail="No compliance report found. Please run compliance check first."
            )
        
        return ComplianceCheckResponse(**report)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve report: {str(e)}")

@router.get("/history")
async def get_contract_history():
    try:
        contracts = qdrant_service.get_all_contracts()
        return contracts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve contract history: {str(e)}")

@router.get("/{contract_id}/chunks")
async def get_contract_chunks(contract_id: str):
    try:
        chunks = qdrant_service.get_contract_chunks(contract_id)
        if not chunks:
            raise HTTPException(status_code=404, detail="Contract not found")
        return {"contract_id": contract_id, "chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chunks: {str(e)}")

@router.post("/rate")
async def rate_contract(rating_request: ContractRatingRequest):
    """Update user rating for a contract"""
    try:
        qdrant_service.update_contract_rating(
            contract_id=rating_request.contract_id,
            rating=rating_request.rating
        )
        return {"message": "Rating updated successfully", "contract_id": rating_request.contract_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update rating: {str(e)}")

@router.get("/analytics/summary", response_model=AnalyticsResponse)
async def get_analytics():
    """Get analytics and insights from all contracts"""
    try:
        analytics = qdrant_service.get_analytics_data()
        return AnalyticsResponse(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}")

@router.post("/submit-to-scholar", response_model=ScholarReviewResponse)
async def submit_to_scholar(review_request: ScholarReviewRequest):
    """Submit contract to scholar for double-checking"""
    try:
        result = qdrant_service.submit_to_scholar(
            contract_id=review_request.contract_id,
            notes=review_request.notes
        )
        return ScholarReviewResponse(
            contract_id=result["contract_id"],
            status=result["status"],
            submitted_at=result["submitted_at"],
            message="Contract successfully submitted to scholar for review. You will be notified once the review is complete."
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit to scholar: {str(e)}")

