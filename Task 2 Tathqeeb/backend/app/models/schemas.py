from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime

class ComplianceCategory(str, Enum):
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"

class TokenUsage(BaseModel):
    """Token usage information for LLM calls"""
    prompt_tokens: int = Field(0, description="Number of input tokens")
    completion_tokens: int = Field(0, description="Number of output tokens")
    total_tokens: int = Field(0, description="Total tokens used")
    process_time: float = Field(0.0, description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RegulationInput(BaseModel):
    title: str = Field(..., description="Title of the Shariah regulation")
    content: str = Field(..., description="Content of the regulation")
    category: Optional[str] = Field(None, description="Category of the regulation")
    reference: Optional[str] = Field(None, description="Reference source")

class RegulationResponse(BaseModel):
    id: str
    title: str
    category: Optional[str]
    reference: Optional[str]
    created_at: datetime

class ContractUploadResponse(BaseModel):
    contract_id: str
    filename: str
    text_length: int
    chunks_created: int
    message: str

class ViolationDetail(BaseModel):
    regulation_title: str
    regulation_reference: Optional[str]
    violated_clause: str
    description: str
    severity: str
    pages: Optional[List[int]] = Field(default_factory=list, description="Page numbers where violation occurs")
    reasoning: Optional[str] = Field(None, description="Step-by-step reasoning for the violation")

class ComplianceCheckResponse(BaseModel):
    contract_id: str
    overall_score: float = Field(..., ge=0, le=100, description="Compliance score 0-100")
    category: ComplianceCategory
    total_regulations_checked: int
    compliant_count: int
    violations_count: int
    violations: List[ViolationDetail]
    summary: str
    recommendations: List[str] = Field(default_factory=list, description="Next best actions for the user")
    checked_at: datetime
    token_usage: Optional[TokenUsage] = Field(None, description="Token usage for this compliance check")

class ComplianceReportRequest(BaseModel):
    contract_id: str
    regulation_filters: Optional[List[str]] = Field(None, description="Filter by regulation categories")

class ContractRatingRequest(BaseModel):
    contract_id: str
    rating: int = Field(..., ge=-1, le=1, description="Rating: 1 for thumbs up, -1 for thumbs down, 0 for neutral")

class ScholarReviewRequest(BaseModel):
    contract_id: str
    notes: Optional[str] = Field(None, description="Additional notes for the scholar")

class ScholarReviewResponse(BaseModel):
    contract_id: str
    status: str
    submitted_at: str
    message: str

class TokenManagementResponse(BaseModel):
    """Response for token management dashboard"""
    contract_id: str
    filename: str
    checked_at: datetime
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    process_time: float = Field(0.0, description="Processing time in seconds")
    compliance_score: Optional[float] = None
    category: Optional[str] = None

class TokenStatisticsResponse(BaseModel):
    """Aggregate token statistics"""
    total_contracts_analyzed: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_process_time: float = Field(0.0, description="Total processing time in seconds")
    avg_tokens_per_contract: float
    avg_process_time_per_contract: float = Field(0.0, description="Average processing time per contract in seconds")
    contracts: List[TokenManagementResponse]

class AnalyticsResponse(BaseModel):
    total_contracts: int
    total_compliant: int
    total_partially_compliant: int
    total_non_compliant: int
    avg_compliance_score: float
    total_thumbs_up: int
    total_thumbs_down: int
    top_violations: List[Dict]
    compliance_trend: List[Dict]
    rating_satisfaction: float

class HealthResponse(BaseModel):
    status: str
    qdrant_connected: bool
    collections: Dict[str, bool]
