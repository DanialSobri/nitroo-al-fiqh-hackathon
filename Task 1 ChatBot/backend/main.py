"""FastAPI application for RAG-based question answering"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import traceback
import sys
import uuid
import asyncio
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from models import (
    QuestionRequest, QuestionResponse, HealthResponse, CollectionType, 
    AnalyticsResponse, CollectionDocumentsResponse, ScraperStatus, 
    ScraperJobRequest, ScraperJobResponse, ScraperSource, ScraperSourceRequest,
    ScraperSchedule, ScraperScheduleRequest, AuditLogResponse, AuditLogStatistics
)
from pydantic import BaseModel, Field
from audit_logging import get_audit_logger
from rag_service import RAGService
from conversation_memory import ConversationMemory
from config import settings
from scraper_config import (
    add_custom_source, delete_custom_source, 
    get_source, get_all_sources, update_custom_source
)
from scheduler_service import (
    add_schedule, update_schedule, delete_schedule, get_all_schedules,
    get_schedule, initialize_schedules, get_scheduler_status
)

# Initialize RAG service (global instance)
rag_service: RAGService = None
conversation_memory: Optional[ConversationMemory] = None

# Scraper state management
scraper_status = {
    "is_running": False,
    "current_job": None,
    "progress": None,
    "status_message": "Idle",
    "last_run": None,
    "last_success": None,
    "error": None
}

# Thread pool for background scraper jobs
executor = ThreadPoolExecutor(max_workers=1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    global rag_service, conversation_memory
    try:
        print("Initializing RAG service...")
        rag_service = RAGService()
        conversation_memory = rag_service.conversation_memory
        print("RAG service initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize RAG service: {e}")
        print(traceback.format_exc())
        # Don't raise - allow server to start but endpoints will return 503
        rag_service = None
        conversation_memory = None
    
    # Initialize scheduled scrapers
    try:
        print("Initializing scheduled scrapers...")
        initialize_schedules()
        print("Scheduled scrapers initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize scheduled scrapers: {e}")
        print(traceback.format_exc())
    
    yield
    
    # Shutdown (if needed)
    # Cleanup code can go here


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Islamic Finance RAG API",
    description="RAG-based question answering API for Islamic finance documents",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "Islamic Finance RAG API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/ask": "Ask a question (POST)",
            "/docs": "API documentation"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check Qdrant connection
        qdrant_connected = rag_service.qdrant_client is not None
        
        # Check collections
        collections_available = list(rag_service.vector_stores.keys())
        
        # Check embedding model
        embedding_model_loaded = rag_service.embedding_model is not None
        
        return HealthResponse(
            status="healthy" if (qdrant_connected and embedding_model_loaded) else "degraded",
            qdrant_connected=qdrant_connected,
            collections_available=collections_available,
            embedding_model_loaded=embedding_model_loaded
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            qdrant_connected=False,
            collections_available=[],
            embedding_model_loaded=False
        )


@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        from cache_manager import get_cache_manager
        from config import settings
        
        if not settings.enable_caching:
            return {
                "enabled": False,
                "message": "Caching is disabled"
            }
        
        cache_manager = get_cache_manager()
        stats = cache_manager.get_stats()
        return {
            "enabled": True,
            **stats
        }
    except Exception as e:
        return {
            "enabled": False,
            "error": str(e)
        }


@app.post("/cache/clear")
async def clear_cache():
    """Clear all caches"""
    try:
        from cache_manager import get_cache_manager
        cache_manager = get_cache_manager()
        cache_manager.clear_all()
        return {
            "success": True,
            "message": "All caches cleared"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question and get an answer with references
    
    - **question**: The question to ask
    - **collections**: Which collections to search (default: all)
    - **max_results**: Maximum number of references (default: 5)
    - **min_score**: Minimum similarity score threshold (default: 0.5)
    """
    if not rag_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service is not initialized"
        )
    
    try:
        # Start timing
        start_time = time.time()
        
        # Validate and convert collections
        if not request.collections:
            request.collections = [CollectionType.ALL]
        else:
            # Convert string collection names to CollectionType enum if needed
            converted_collections = []
            for col in request.collections:
                if isinstance(col, str):
                    # Map string to CollectionType enum
                    col_lower = col.lower()
                    if col_lower == 'all':
                        converted_collections.append(CollectionType.ALL)
                    elif col_lower == 'bnm_pdfs' or col_lower == 'bnm':
                        converted_collections.append(CollectionType.BNM)
                    elif col_lower == 'iifa_resolutions' or col_lower == 'iifa':
                        converted_collections.append(CollectionType.IIFA)
                    elif col_lower == 'sc_resolutions' or col_lower == 'sc':
                        converted_collections.append(CollectionType.SC)
                    else:
                        # Try to match as CollectionType enum value
                        try:
                            converted_collections.append(CollectionType(col))
                        except ValueError:
                            print(f"Warning: Unknown collection '{col}', skipping")
                else:
                    converted_collections.append(col)
            request.collections = converted_collections if converted_collections else [CollectionType.ALL]
        
        # Call RAG service with conversation memory
        result = rag_service.ask_question(
            question=request.question,
            collections=request.collections,
            max_results=request.max_results,
            min_score=request.min_score,
            user_id=request.user_id,
            session_id=request.session_id,
            use_memory=True
        )
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Convert to response model
        response = QuestionResponse(
            answer=result['answer'],
            question=result['question'],
            references=result['references'],
            total_references_found=result['total_references_found'],
            collections_searched=result['collections_searched'],
            failed_collections=result.get('failed_collections'),
            citation_map=result.get('citation_map'),
            response_time_ms=response_time_ms
        )
        
        return response
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error processing question: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


class FindPageRequest(BaseModel):
    """Request to find page number for a reference"""
    chunk_text: str = Field(..., description="The chunk text to search for")
    pdf_url: Optional[str] = Field(None, description="URL of the PDF")
    filepath: Optional[str] = Field(None, description="Local file path to the PDF")


class FindPageResponse(BaseModel):
    """Response for finding page number for a reference"""
    found: bool
    page_number: Optional[int] = None
    page_number_source: Optional[str] = None
    context: Optional[str] = None
    error: Optional[str] = None


@app.post("/references/find-page", response_model=FindPageResponse)
async def find_reference_page(request: FindPageRequest):
    """
    Find the exact page number for a reference by searching the PDF.
    This is called on-demand when a user clicks on a reference link.
    """
    if not rag_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service is not initialized"
        )
    
    if not request.pdf_url and not request.filepath:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either pdf_url or filepath must be provided"
        )
    
    try:
        from pdf_page_extractor import extract_sentence_location
        
        if not request.chunk_text or len(request.chunk_text.strip()) < 10:
            return FindPageResponse(
                found=False,
                page_number=None,
                page_number_source=None,
                error="Chunk text is too short or empty. Need at least 10 characters to search."
            )
        
        print(f"Finding page for PDF: {request.pdf_url or request.filepath}")
        print(f"Searching for text (first 200 chars): {request.chunk_text[:200] if request.chunk_text else 'None'}...")
        print(f"Text length: {len(request.chunk_text)} characters")
        
        # Run PDF processing in thread pool to avoid blocking
        # Use asyncio.wait_for to add a timeout (60 seconds)
        def run_extraction():
            try:
                return extract_sentence_location(
                    pdf_url=request.pdf_url,
                    pdf_filepath=request.filepath,
                    sentence_text=request.chunk_text,
                    case_sensitive=False,
                    fuzzy_match=True
                )
            except Exception as e:
                print(f"Error in extract_sentence_location: {e}")
                import traceback
                traceback.print_exc()
                return {
                    'found': False,
                    'page_number': None,
                    'sentence': request.chunk_text,
                    'context': None,
                    'error': str(e)
                }
        
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, run_extraction),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            print("PDF processing timed out after 60 seconds")
            return FindPageResponse(
                found=False,
                page_number=None,
                page_number_source=None,
                error="PDF processing timed out. The PDF may be too large or the text may not be found."
            )
        
        print(f"Find page result: found={result.get('found')}, page={result.get('page_number')}, error={result.get('error')}")
        
        if result.get('found') and result.get('page_number'):
            return FindPageResponse(
                found=True,
                page_number=result['page_number'],
                page_number_source='pdf_search',
                context=result.get('context')
            )
        else:
            error_msg = result.get('error', 'Text not found in PDF')
            print(f"Page not found. Error: {error_msg}")
            return FindPageResponse(
                found=False,
                page_number=None,
                page_number_source=None,
                error=error_msg
            )
    except Exception as e:
        print(f"Error finding page number: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find page number: {str(e)}"
        )


@app.get("/collections", response_model=List[str])
async def get_collections():
    """Get list of available collections"""
    if not rag_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service is not initialized"
        )
    
    # Get collections from settings (configured collections)
    configured_collections = settings.collections
    
    # Get collection names from all scraper sources (including custom sources)
    scraper_sources = get_all_sources()
    source_collections = set()
    for source in scraper_sources:
        collection_name = source.get('collection_name')
        if collection_name:
            source_collections.add(collection_name)
    
    # Also include any collections that exist in vector_stores
    initialized_collections = set(rag_service.vector_stores.keys())
    
    # Combine all sources: configured, from scraper sources, and initialized
    all_collections = set(configured_collections) | source_collections | initialized_collections
    
    # Sort to ensure consistent order (configured first, then from sources, then others)
    configured_set = set(configured_collections)
    sorted_collections = sorted(all_collections, key=lambda x: (
        0 if x in configured_set else (1 if x in source_collections else 2),
        x
    ))
    
    return sorted_collections


@app.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics():
    """Get analytics and statistics about collections and documents"""
    if not rag_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service is not initialized"
        )
    
    try:
        stats = rag_service.get_collection_statistics()
        
        # Get Qdrant status
        qdrant_status = "connected" if rag_service.qdrant_client else "disconnected"
        
        # Get embedding model name
        embedding_model = "all-MiniLM-L6-v2"
        
        return AnalyticsResponse(
            total_collections=stats['total_collections'],
            total_documents=stats['total_documents'],
            total_chunks=stats['total_chunks'],
            collections=stats['collections'],
            qdrant_status=qdrant_status,
            embedding_model=embedding_model
        )
    except Exception as e:
        print(f"Error getting analytics: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


@app.get("/collections/{collection_name}/documents", response_model=CollectionDocumentsResponse)
async def get_collection_documents(collection_name: str):
    """Get list of all documents in a specific collection"""
    if not rag_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service is not initialized"
        )
    
    # Validate collection exists
    if collection_name not in rag_service.vector_stores:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection_name}' not found"
        )
    
    try:
        result = rag_service.get_collection_documents(collection_name)
        return CollectionDocumentsResponse(
            collection_name=result['collection_name'],
            total_documents=result['total_documents'],
            documents=result['documents']
        )
    except Exception as e:
        print(f"Error getting documents for collection {collection_name}: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents: {str(e)}"
        )


@app.get("/test-token", response_model=dict)
async def test_token():
    """Test Ollama/OLLM connection (deprecated endpoint name - kept for compatibility)"""
    if not rag_service or not hasattr(rag_service, 'llm'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service is not initialized"
        )
    
    try:
        # Check if using Ollama
        if hasattr(rag_service.llm, 'ollama_llm'):
            ollama_llm = rag_service.llm.ollama_llm
            return {
                "status": "success",
                "message": "Ollama connection ready",
                "ollama_url": ollama_llm.base_url,
                "chat_url": ollama_llm.chat_url,
                "model": ollama_llm.model
            }
        # Check if using API Gateway (deprecated)
        elif hasattr(rag_service.llm, 'api_gateway_llm'):
            api_llm = rag_service.llm.api_gateway_llm
            token = api_llm._get_token()
            return {
                "status": "success",
                "message": "Token obtained successfully (deprecated API Gateway)",
                "token_preview": f"{token[:20]}..." if token else "No token",
                "token_url": api_llm.token_url,
                "chat_url": api_llm.chat_url
            }
        else:
            return {
                "status": "info",
                "message": f"Using {settings.llm_provider} provider",
                "provider": settings.llm_provider
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to test connection: {str(e)}",
            "error_type": type(e).__name__
        }


@app.post("/test-chat", response_model=dict)
async def test_chat(request: dict):
    """Test Ollama/LLM chat endpoint with a simple message"""
    if not rag_service or not hasattr(rag_service, 'llm'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service is not initialized"
        )
    
    test_message = request.get("message", "Hello, this is a test message.")
    
    try:
        # Check if using Ollama
        if hasattr(rag_service.llm, 'ollama_llm'):
            ollama_llm = rag_service.llm.ollama_llm
            response = ollama_llm.invoke(test_message)
            return {
                "status": "success",
                "message": "Ollama chat test successful",
                "response": response[:500] if len(response) > 500 else response,
                "response_length": len(response),
                "model": ollama_llm.model
            }
        # Check if using API Gateway (deprecated)
        elif hasattr(rag_service.llm, 'api_gateway_llm'):
            api_llm = rag_service.llm.api_gateway_llm
            response = api_llm.invoke(test_message)
            return {
                "status": "success",
                "message": "Chat API test successful (deprecated API Gateway)",
                "response": response[:500] if len(response) > 500 else response,
                "response_length": len(response)
            }
        else:
            return {
                "status": "info",
                "message": f"Using {settings.llm_provider} provider",
                "provider": settings.llm_provider
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Chat API test failed: {str(e)}",
            "error_type": type(e).__name__,
            "error_details": str(e)
        }


def run_scraper(source: str, use_selenium: bool = False):
    """Run scraper in background thread"""
    global scraper_status
    
    try:
        scraper_status["is_running"] = True
        scraper_status["current_job"] = source
        scraper_status["progress"] = 0.0
        scraper_status["status_message"] = f"Starting {source} scraper..."
        scraper_status["error"] = None
        
        # Add Web-Scraper to path
        scraper_path = Path(__file__).parent.parent / "Web-Scraper"
        if str(scraper_path) not in sys.path:
            sys.path.insert(0, str(scraper_path))
        
        # Import scraper modules
        from scraper import BNMScraper, IIFAScraper, SCScraper
        from generic_scraper import GenericScraper
        
        qdrant_url = settings.qdrant_url or None
        qdrant_path = settings.qdrant_path if not qdrant_url else None
        
        # Check if source is a custom source
        source_config = get_source(source)
        
        if source_config:
            # Custom or default source from config
            current_source = 1
            total_sources = 1
            scraper_status["status_message"] = f"Scraping {source_config['name']}... ({current_source}/{total_sources})"
            scraper_status["progress"] = 0.5
            
            # Determine output directory path
            output_dir_path = source_config["output_dir"]
            if not Path(output_dir_path).is_absolute():
                output_dir_path = str(scraper_path / output_dir_path)
            
            if source_config["type"] == "default":
                # Use specific scraper class for default sources
                if source == "bnm":
                    scraper = BNMScraper(
                        base_url=source_config["url"],
                        output_dir=output_dir_path,
                        qdrant_url=qdrant_url,
                        qdrant_path=qdrant_path
                    )
                elif source == "iifa":
                    scraper = IIFAScraper(
                        base_url=source_config["url"],
                        output_dir=output_dir_path,
                        qdrant_url=qdrant_url,
                        qdrant_path=qdrant_path
                    )
                elif source == "sc":
                    scraper = SCScraper(
                        base_url=source_config["url"],
                        output_dir=output_dir_path,
                        qdrant_url=qdrant_url,
                        qdrant_path=qdrant_path
                    )
                else:
                    scraper = GenericScraper(
                        base_url=source_config["url"],
                        collection_name=source_config["collection_name"],
                        output_dir=output_dir_path,
                        qdrant_url=qdrant_url,
                        qdrant_path=qdrant_path,
                        scraping_strategy=source_config.get("scraping_strategy", "direct_links"),
                        form_selector=source_config.get("form_selector"),
                        form_button_selector=source_config.get("form_button_selector")
                    )
            else:
                # Custom source - use generic scraper
                scraper = GenericScraper(
                    base_url=source_config["url"],
                    collection_name=source_config["collection_name"],
                    output_dir=output_dir_path,
                    qdrant_url=qdrant_url,
                    qdrant_path=qdrant_path,
                    scraping_strategy=source_config.get("scraping_strategy", "direct_links"),
                    form_selector=source_config.get("form_selector"),
                    form_button_selector=source_config.get("form_button_selector")
                )
            
            scraper.scrape_and_store(use_selenium=use_selenium)
            scraper_status["progress"] = 1.0
            
        elif source == "all":
            # Scrape all default sources
            all_sources = get_all_sources()
            default_sources = [s for s in all_sources if s["type"] == "default"]
            total_sources = len(default_sources)
            current_source = 0
            
            for source_item in default_sources:
                current_source += 1
                source_id = source_item["id"]
                scraper_status["status_message"] = f"Scraping {source_item['name']}... ({current_source}/{total_sources})"
                scraper_status["progress"] = (current_source - 0.5) / total_sources
                
                # Determine output directory path
                output_dir_path = source_item["output_dir"]
                if not Path(output_dir_path).is_absolute():
                    output_dir_path = str(scraper_path / output_dir_path)
                
                if source_id == "bnm":
                    scraper = BNMScraper(
                        base_url=source_item["url"],
                        output_dir=output_dir_path,
                        qdrant_url=qdrant_url,
                        qdrant_path=qdrant_path
                    )
                elif source_id == "iifa":
                    scraper = IIFAScraper(
                        base_url=source_item["url"],
                        output_dir=output_dir_path,
                        qdrant_url=qdrant_url,
                        qdrant_path=qdrant_path
                    )
                elif source_id == "sc":
                    scraper = SCScraper(
                        base_url=source_item["url"],
                        output_dir=output_dir_path,
                        qdrant_url=qdrant_url,
                        qdrant_path=qdrant_path
                    )
                else:
                    scraper = GenericScraper(
                        base_url=source_item["url"],
                        collection_name=source_item["collection_name"],
                        output_dir=output_dir_path,
                        qdrant_url=qdrant_url,
                        qdrant_path=qdrant_path
                    )
                
                scraper.scrape_and_store(use_selenium=use_selenium)
                scraper_status["progress"] = current_source / total_sources
        else:
            raise ValueError(f"Unknown source: {source}")
        
        scraper_status["status_message"] = f"Successfully completed {source} scraping"
        scraper_status["last_success"] = datetime.now()
        scraper_status["error"] = None
        
    except Exception as e:
        scraper_status["error"] = str(e)
        scraper_status["status_message"] = f"Error: {str(e)}"
        print(f"Scraper error: {e}")
        traceback.print_exc()
    finally:
        scraper_status["is_running"] = False
        scraper_status["current_job"] = None
        scraper_status["progress"] = None
        scraper_status["last_run"] = datetime.now()


@app.get("/scraper/status", response_model=ScraperStatus)
async def get_scraper_status():
    """Get current scraper status"""
    return ScraperStatus(
        is_running=scraper_status["is_running"],
        current_job=scraper_status["current_job"],
        progress=scraper_status["progress"],
        status_message=scraper_status["status_message"],
        last_run=scraper_status["last_run"],
        last_success=scraper_status["last_success"],
        error=scraper_status["error"]
    )


@app.post("/scraper/start", response_model=ScraperJobResponse)
async def start_scraper_job(request: ScraperJobRequest):
    """Start a scraper job"""
    global scraper_status
    
    if scraper_status["is_running"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scraper is already running: {scraper_status['current_job']}"
        )
    
    # Validate source exists (check in config)
    source_config = get_source(request.source)
    if not source_config and request.source != "all":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source: {request.source}. Source not found in configuration."
        )
    
    job_id = str(uuid.uuid4())
    
    # Submit to thread pool
    executor.submit(run_scraper, request.source, request.use_selenium)
    
    return ScraperJobResponse(
        job_id=job_id,
        status="started",
        message=f"Scraper job started for {request.source}"
    )


@app.get("/scraper/sources", response_model=List[ScraperSource])
async def get_scraper_sources():
    """Get all available scraper sources"""
    sources = get_all_sources()
    print(f"DEBUG: Found {len(sources)} sources: {[s.get('id', 'unknown') for s in sources]}")
    
    result = []
    for source in sources:
        try:
            # Ensure all required fields have defaults
            source_dict = {
                "id": source.get("id", ""),
                "name": source.get("name", ""),
                "url": source.get("url", ""),
                "collection_name": source.get("collection_name", ""),
                "output_dir": source.get("output_dir", ""),
                "type": source.get("type", "default"),
                "scraping_strategy": source.get("scraping_strategy", "direct_links"),
                "form_selector": source.get("form_selector"),
                "form_button_selector": source.get("form_button_selector"),
                "created_at": source.get("created_at")
            }
            result.append(ScraperSource(**source_dict))
        except Exception as e:
            print(f"ERROR: Failed to parse source {source.get('id', 'unknown')}: {e}")
            print(f"  Source data: {source}")
            continue
    
    print(f"DEBUG: Returning {len(result)} valid sources")
    return result


@app.post("/scraper/sources", response_model=ScraperSource)
async def add_scraper_source(request: ScraperSourceRequest):
    """Add a new custom scraper source"""
    try:
        new_source = add_custom_source(
            name=request.name,
            url=request.url,
            collection_name=request.collection_name,
            output_dir=request.output_dir,
            scraping_strategy=request.scraping_strategy,
            form_selector=request.form_selector,
            form_button_selector=request.form_button_selector
        )
        
        # Update RAG service collections if it's initialized
        if rag_service:
            try:
                # Reload collections
                from config import settings
                if new_source["collection_name"] not in settings.collections:
                    settings.collections.append(new_source["collection_name"])
            except Exception as e:
                print(f"Warning: Could not update RAG service collections: {e}")
        
        return ScraperSource(**new_source)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add scraper source: {str(e)}"
        )


@app.put("/scraper/sources/{source_id}", response_model=ScraperSource)
async def update_scraper_source(source_id: str, request: ScraperSourceRequest):
    """Update an existing custom scraper source"""
    if source_id in ["bnm", "iifa", "sc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update default sources"
        )
    
    try:
        updated_source = update_custom_source(
            source_id=source_id,
            name=request.name,
            url=request.url,
            collection_name=request.collection_name,
            output_dir=request.output_dir,
            scraping_strategy=request.scraping_strategy,
            form_selector=request.form_selector,
            form_button_selector=request.form_button_selector
        )
        
        if not updated_source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source '{source_id}' not found"
            )
        
        # Update RAG service collections if it's initialized
        if rag_service:
            try:
                # Reload collections
                from config import settings
                if updated_source["collection_name"] not in settings.collections:
                    settings.collections.append(updated_source["collection_name"])
            except Exception as e:
                print(f"Warning: Could not update RAG service collections: {e}")
        
        return ScraperSource(**updated_source)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scraper source: {str(e)}"
        )


@app.delete("/scraper/sources/{source_id}")
async def delete_scraper_source(source_id: str):
    """Delete a custom scraper source"""
    if source_id in ["bnm", "iifa", "sc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default sources"
        )
    
    success = delete_custom_source(source_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{source_id}' not found"
        )
    
    return {"message": f"Source '{source_id}' deleted successfully"}


# ==================== Scraper Schedule Endpoints ====================

@app.get("/scraper/schedules", response_model=List[ScraperSchedule])
async def get_scraper_schedules():
    """Get all scraper schedules"""
    try:
        schedules = get_all_schedules()
        
        # Get scheduler status to include next_run times
        scheduler_status = get_scheduler_status()
        job_map = {job['id']: job for job in scheduler_status['jobs']}
        
        result = []
        for schedule in schedules:
            schedule_dict = schedule.copy()
            # Add next_run from scheduler if available
            if schedule_dict['id'] in job_map:
                next_run = job_map[schedule_dict['id']].get('next_run_time')
                if next_run:
                    schedule_dict['next_run'] = next_run
            
            result.append(ScraperSchedule(**schedule_dict))
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schedules: {str(e)}"
        )


@app.get("/scraper/schedules/{schedule_id}", response_model=ScraperSchedule)
async def get_scraper_schedule(schedule_id: str):
    """Get a specific scraper schedule"""
    try:
        schedule = get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule not found: {schedule_id}"
            )
        
        # Get next_run from scheduler
        scheduler_status = get_scheduler_status()
        for job in scheduler_status['jobs']:
            if job['id'] == schedule_id:
                if job.get('next_run_time'):
                    schedule['next_run'] = job['next_run_time']
                break
        
        return ScraperSchedule(**schedule)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schedule: {str(e)}"
        )


@app.post("/scraper/schedules", response_model=ScraperSchedule)
async def create_scraper_schedule(request: ScraperScheduleRequest):
    """Create a new scraper schedule"""
    try:
        # Validate schedule type and required fields
        if request.schedule_type == 'interval':
            if not request.interval_value or not request.interval_unit:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="interval_value and interval_unit are required for interval schedules"
                )
        elif request.schedule_type == 'cron':
            # At least one cron field should be specified
            if not any([request.cron_hour, request.cron_minute, request.cron_day, request.cron_day_of_week]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one cron field must be specified"
                )
        elif request.schedule_type == 'once':
            if not request.run_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="run_at is required for 'once' schedules"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid schedule_type: {request.schedule_type}. Must be 'interval', 'cron', or 'once'"
            )
        
        # Validate source exists
        source_config = get_source(request.source)
        if not source_config and request.source != "all":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source: {request.source}. Source not found in configuration."
            )
        
        schedule_data = request.dict(exclude_none=True)
        new_schedule = add_schedule(schedule_data)
        
        return ScraperSchedule(**new_schedule)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schedule: {str(e)}"
        )


@app.put("/scraper/schedules/{schedule_id}", response_model=ScraperSchedule)
async def update_scraper_schedule(schedule_id: str, request: ScraperScheduleRequest):
    """Update an existing scraper schedule"""
    try:
        # Validate source if provided
        if request.source:
            source_config = get_source(request.source)
            if not source_config and request.source != "all":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid source: {request.source}. Source not found in configuration."
                )
        
        schedule_data = request.dict(exclude_none=True)
        updated_schedule = update_schedule(schedule_id, schedule_data)
        
        if not updated_schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule not found: {schedule_id}"
            )
        
        return ScraperSchedule(**updated_schedule)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update schedule: {str(e)}"
        )


@app.delete("/scraper/schedules/{schedule_id}")
async def delete_scraper_schedule(schedule_id: str):
    """Delete a scraper schedule"""
    try:
        deleted = delete_schedule(schedule_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule not found: {schedule_id}"
            )
        return {"message": f"Schedule {schedule_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete schedule: {str(e)}"
        )


@app.get("/scraper/scheduler/status")
async def get_scheduler_status_endpoint():
    """Get scheduler status"""
    try:
        return get_scheduler_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scheduler status: {str(e)}"
        )


@app.get("/audit/logs", response_model=AuditLogResponse)
async def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    llm_provider: Optional[str] = None,
    success_only: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get audit logs with optional filtering"""
    try:
        logger = get_audit_logger()
        logs = logger.get_logs(
            limit=limit,
            offset=offset,
            llm_provider=llm_provider,
            success_only=success_only,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get total count for pagination
        all_logs = logger.get_logs(limit=10000, offset=0)  # Get all for count
        total = len(all_logs)
        
        return AuditLogResponse(
            logs=logs,
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit logs: {str(e)}"
        )


@app.get("/audit/statistics", response_model=AuditLogStatistics)
async def get_audit_statistics():
    """Get audit log statistics"""
    try:
        logger = get_audit_logger()
        stats = logger.get_statistics()
        return AuditLogStatistics(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit statistics: {str(e)}"
        )


@app.get("/conversations/recent")
async def get_recent_conversations(
    user_id: Optional[str] = None,
    limit: int = 20
):
    """Get recent chat sessions"""
    if not conversation_memory:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversation memory not available"
        )
    
    try:
        sessions = conversation_memory.get_recent_sessions(
            user_id=user_id,
            limit=limit
        )
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )


@app.get("/conversations/{session_id}")
async def get_session_conversations(session_id: str):
    """Get all conversations in a session"""
    if not conversation_memory:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversation memory not available"
        )
    
    try:
        conversations = conversation_memory.get_session_history(session_id)
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
