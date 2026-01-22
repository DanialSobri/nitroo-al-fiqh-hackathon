"""Pydantic models for API requests and responses"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class CollectionType(str, Enum):
    """Available document collections"""
    BNM = "bnm_pdfs"
    IIFA = "iifa_resolutions"
    SC = "sc_resolutions"
    ALL = "all"


class SourceReference(BaseModel):
    """Reference to a source document chunk"""
    pdf_title: str = Field(..., description="Title of the PDF document")
    pdf_url: Optional[str] = Field(None, description="URL of the PDF document")
    chunk_text: str = Field(..., description="Text excerpt from the document")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    chunk_index: int = Field(..., description="Index of the chunk in the document")
    total_chunks: int = Field(..., description="Total number of chunks in the document")
    date: Optional[str] = Field(None, description="Date of the document")
    document_type: Optional[str] = Field(None, description="Type of document")
    resolution_number: Optional[str] = Field(None, description="Resolution number (for resolutions)")
    source: Optional[str] = Field(None, description="Source collection name")


class QuestionRequest(BaseModel):
    """Request model for asking a question"""
    question: str = Field(..., description="The question to ask", min_length=1)
    collections: Optional[List[CollectionType]] = Field(
        default=[CollectionType.ALL],
        description="Which collections to search (default: all)"
    )
    max_results: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of reference results to return"
    )
    min_score: Optional[float] = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )


class QuestionResponse(BaseModel):
    """Response model for question answering"""
    answer: str = Field(..., description="The generated answer to the question")
    question: str = Field(..., description="The original question")
    references: List[SourceReference] = Field(..., description="Source references used to generate the answer")
    total_references_found: int = Field(..., description="Total number of references found")
    collections_searched: List[str] = Field(..., description="Collections that were successfully searched")
    failed_collections: Optional[List[str]] = Field(None, description="Collections that failed to search (if any)")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    qdrant_connected: bool
    collections_available: List[str]
    embedding_model_loaded: bool


class CollectionStats(BaseModel):
    """Statistics for a collection"""
    collection_name: str
    total_documents: int
    total_chunks: int
    unique_pdfs: int
    avg_chunks_per_document: float
    last_updated: Optional[str] = None
    last_document_updated: Optional[str] = None
    last_document_title: Optional[str] = None  # Title of the most recent document


class AnalyticsResponse(BaseModel):
    """Analytics response with collection statistics"""
    total_collections: int
    total_documents: int
    total_chunks: int
    collections: List[CollectionStats]
    qdrant_status: str
    embedding_model: str


class DocumentInfo(BaseModel):
    """Information about a document in a collection"""
    pdf_title: str
    pdf_url: Optional[str] = None
    date: Optional[str] = None
    document_type: Optional[str] = None
    resolution_number: Optional[str] = None
    total_chunks: int = 0


class CollectionDocumentsResponse(BaseModel):
    """Response with list of documents in a collection"""
    collection_name: str
    total_documents: int
    documents: List[DocumentInfo]


class ScraperStatus(BaseModel):
    """Scraper status response"""
    is_running: bool
    current_job: Optional[str] = None
    progress: Optional[float] = None
    status_message: str
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    error: Optional[str] = None


class ScraperJobRequest(BaseModel):
    """Request to start a scraper job"""
    source: str = Field(..., description="Source to scrape: 'bnm', 'iifa', 'sc', or 'all'")
    use_selenium: bool = Field(default=False, description="Use Selenium for JavaScript rendering")


class ScraperJobResponse(BaseModel):
    """Response from starting a scraper job"""
    job_id: str
    status: str
    message: str


class ScraperSource(BaseModel):
    """Scraper source configuration"""
    id: str
    name: str
    url: str
    collection_name: str
    output_dir: str
    type: str  # "default" or "custom"
    scraping_strategy: Optional[str] = "direct_links"
    form_selector: Optional[str] = None
    form_button_selector: Optional[str] = None
    created_at: Optional[str] = None


class ScraperSourceRequest(BaseModel):
    """Request to add a new scraper source"""
    name: str = Field(..., description="Display name for the source")
    url: str = Field(..., description="Base URL to scrape")
    collection_name: str = Field(..., description="Qdrant collection name")
    output_dir: Optional[str] = Field(None, description="Output directory for PDFs (optional)")
    scraping_strategy: str = Field("direct_links", description="Scraping strategy: 'direct_links', 'form_based', or 'table_based'")
    form_selector: Optional[str] = Field(None, description="CSS selector for form element (required for form_based strategy)")
    form_button_selector: Optional[str] = Field(None, description="CSS selector for form submit button (required for form_based strategy)")