"""RAG (Retrieval Augmented Generation) service using LangChain and Qdrant"""
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_openai import ChatOpenAI
import numpy as np
from config import settings
from models import CollectionType, SourceReference
from ollama_llm import OllamaLLM, OllamaChatLLM
# API Gateway imports are conditional (deprecated)


class RAGService:
    """Service for RAG operations using LangChain and Qdrant"""
    
    def __init__(self):
        """Initialize the RAG service"""
        self.embedding_model = None
        self.qdrant_client = None
        self.vector_stores: Dict[str, Qdrant] = {}
        self.llm = None
        self._initialize()
    
    def _initialize(self):
        """Initialize embedding model, Qdrant client, and LLM"""
        print("Initializing RAG Service...")
        
        # Initialize embedding model
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize HuggingFace embeddings for LangChain
        # Try to use langchain-huggingface if available, otherwise fall back to community
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name='sentence-transformers/all-MiniLM-L6-v2',
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        except ImportError:
            # Fall back to deprecated version if new package not available
            from langchain_community.embeddings import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name='sentence-transformers/all-MiniLM-L6-v2',
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        
        # Initialize Qdrant client
        print("Connecting to Qdrant...")
        if settings.qdrant_url:
            try:
                self.qdrant_client = QdrantClient(url=settings.qdrant_url)
                # Test connection
                collections = self.qdrant_client.get_collections()
                print(f"✓ Connected to Qdrant server at: {settings.qdrant_url}")
                print(f"  Found {len(collections.collections)} collections")
            except Exception as e:
                print(f"✗ Failed to connect to Qdrant server: {e}")
                print(f"  Falling back to local database at: {settings.qdrant_path}")
                self.qdrant_client = QdrantClient(path=settings.qdrant_path)
        else:
            self.qdrant_client = QdrantClient(path=settings.qdrant_path)
            print(f"Using local Qdrant database at: {settings.qdrant_path}")
        
        # Initialize vector stores for each collection
        print("Initializing vector stores...")
        for collection_name in settings.collections:
            try:
                # Check if collection exists
                collections = self.qdrant_client.get_collections()
                collection_names = [col.name for col in collections.collections]
                
                if collection_name in collection_names:
                    vector_store = Qdrant(
                        client=self.qdrant_client,
                        collection_name=collection_name,
                        embeddings=self.embeddings
                    )
                    self.vector_stores[collection_name] = vector_store
                    print(f"  ✓ Loaded collection: {collection_name}")
                else:
                    print(f"  ⚠ Collection {collection_name} does not exist yet")
            except Exception as e:
                print(f"  ✗ Failed to load collection {collection_name}: {e}")
        
        # Initialize LLM based on provider
        print(f"Initializing LLM (provider: {settings.llm_provider})...")
        
        if settings.llm_provider == "ollama":
            # Use direct Ollama
            print(f"  Initializing Ollama LLM (model: {settings.ollama_model})...")
            ollama_llm = OllamaLLM(
                base_url=settings.ollama_url,
                model=settings.ollama_model
            )
            self.llm = OllamaChatLLM(ollama_llm)
            print(f"  ✓ Ollama LLM ready")
        elif settings.llm_provider == "api_gateway":
            # Deprecated: Use ollama instead
            print(f"  ⚠ Warning: api_gateway provider is deprecated. Use 'ollama' instead.")
            print(f"  Initializing API Gateway LLM (model: {settings.api_gateway_model})...")
            try:
                from api_gateway_llm import APIGatewayLLM, APIGatewayChatLLM
                api_gateway_llm = APIGatewayLLM(
                    token_url=settings.api_gateway_token_url,
                    chat_url=settings.api_gateway_chat_url,
                    auth_header=settings.api_gateway_auth_header,
                    model=settings.api_gateway_model,
                    cookie=settings.api_gateway_cookie
                )
                self.llm = APIGatewayChatLLM(api_gateway_llm)
                print(f"  ✓ API Gateway LLM ready (deprecated)")
            except ImportError:
                raise ValueError("API Gateway support requires api_gateway_llm module. Use 'ollama' provider instead.")
        elif settings.llm_provider == "openai":
            # Use OpenAI
            if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
                raise ValueError("OPENAI_API_KEY is required when using OpenAI provider. Set it in .env file")
            
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=settings.llm_temperature,
                openai_api_key=settings.openai_api_key
            )
            print(f"  Using OpenAI with model: {settings.openai_model}")
        else:
            raise ValueError(f"Unknown LLM provider: {settings.llm_provider}. Use 'openai', 'ollama', or 'api_gateway' (deprecated)")
        
        print("RAG Service initialized successfully!")
    
    def _get_collections_to_search(self, requested_collections: List[CollectionType]) -> List[str]:
        """Convert requested collection types to actual collection names"""
        print(f"  Requested collections: {requested_collections}")
        print(f"  Available vector stores: {list(self.vector_stores.keys())}")
        print(f"  Configured collections: {settings.collections}")
        
        if CollectionType.ALL in requested_collections:
            # Return all available collections that exist in vector_stores
            available_collections = [col for col in settings.collections if col in self.vector_stores]
            if not available_collections:
                # Fallback to all configured collections if vector stores not initialized
                print(f"  ⚠ No vector stores initialized, using configured collections: {settings.collections}")
                return settings.collections
            print(f"  ✓ Searching all available collections: {available_collections}")
            return available_collections
        
        collections = []
        for col_type in requested_collections:
            if col_type == CollectionType.BNM:
                collections.append("bnm_pdfs")
            elif col_type == CollectionType.IIFA:
                collections.append("iifa_resolutions")
            elif col_type == CollectionType.SC:
                collections.append("sc_resolutions")
        
        # Filter to only include collections that exist in vector_stores
        available = [col for col in collections if col in self.vector_stores]
        if not available and collections:
            # If none available but collections requested, return requested anyway
            # (they might be created during scraping)
            print(f"  ⚠ Requested collections not in vector stores, using requested: {collections}")
            return list(set(collections))
        
        print(f"  ✓ Searching collections: {available}")
        return list(set(available))  # Remove duplicates
    
    def _retrieve_documents(
        self,
        query: str,
        collections: List[str],
        max_results: int,
        min_score: float
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using advanced ANN vector search strategies
        
        Implements:
        - Multi-stage retrieval (retrieve more, then filter)
        - Diversity filtering (MMR) if enabled
        - Adaptive retrieval based on query complexity
        """
        # Adaptive retrieval: adjust based on query complexity
        query_length = len(query.split())
        is_complex_query = query_length > 10 or '?' in query or any(
            word in query.lower() for word in ['what', 'how', 'why', 'explain', 'describe']
        )
        
        # Determine initial retrieval count
        if settings.enable_diversity_filtering or settings.enable_reranking:
            initial_limit = max(settings.initial_retrieval_count, max_results * 3)
        else:
            initial_limit = max_results
        
        # Increase for complex queries
        if is_complex_query:
            initial_limit = int(initial_limit * 1.5)
        
        all_results = []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Stage 1: Initial ANN retrieval (retrieve more candidates)
        failed_collections = []
        for collection_name in collections:
            try:
                # Use Qdrant client directly for ANN search
                search_results = self.qdrant_client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    limit=initial_limit,
                    score_threshold=min_score  # Filter low-quality results early
                )
                
                # Convert to our format
                for result in search_results:
                    similarity_score = result.score
                    payload = result.payload
                    
                    result_dict = {
                        'content': payload.get('chunk_text', ''),
                        'similarity_score': similarity_score,
                        'collection': collection_name,
                        'metadata': payload,
                        'embedding': None  # Store for diversity calculation if needed
                    }
                    all_results.append(result_dict)
            
            except Exception as e:
                error_msg = str(e)
                # Check for specific Qdrant errors
                if "OffsetOutOfBounds" in error_msg or "500" in error_msg:
                    print(f"⚠ Warning: Collection '{collection_name}' appears to be corrupted or has data issues.")
                    print(f"   Error: {error_msg[:200]}...")  # Truncate long error messages
                    print(f"   Suggestion: Consider re-scraping this collection or checking Qdrant logs.")
                else:
                    print(f"⚠ Error searching collection '{collection_name}': {error_msg[:200]}...")
                
                failed_collections.append(collection_name)
                continue
        
        # Store failed collections for reporting
        if failed_collections:
            self._last_failed_collections = failed_collections
        
        # Sort by similarity score (descending)
        all_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Stage 2: Apply diversity filtering (MMR) if enabled
        if settings.enable_diversity_filtering and len(all_results) > max_results:
            all_results = self._apply_diversity_filtering(
                all_results, 
                query_embedding, 
                max_results,
                settings.diversity_threshold
            )
        
        # Stage 3: Re-ranking (if enabled and re-ranker available)
        if settings.enable_reranking and len(all_results) > 1:
            try:
                all_results = self._rerank_documents(query, all_results)
            except Exception as e:
                print(f"  ⚠ Re-ranking failed: {e}, using original ranking")
        
        # Return top results
        return all_results[:max_results]
    
    def _apply_diversity_filtering(
        self,
        results: List[Dict[str, Any]],
        query_embedding: List[float],
        max_results: int,
        lambda_param: float
    ) -> List[Dict[str, Any]]:
        """
        Apply Maximal Marginal Relevance (MMR) for diverse retrieval
        
        MMR balances relevance and diversity:
        - lambda_param = 1: Pure relevance (no diversity)
        - lambda_param = 0: Pure diversity (no relevance)
        - lambda_param = 0.7: Balanced (default)
        """
        if not results:
            return []
        
        # Get embeddings for all results (lazy loading)
        result_embeddings = []
        for result in results:
            if result['embedding'] is None:
                # Generate embedding for the chunk
                chunk_text = result['content']
                result['embedding'] = self.embedding_model.encode(chunk_text).tolist()
            result_embeddings.append(result['embedding'])
        
        # Convert to numpy for efficient computation
        query_vec = np.array(query_embedding)
        result_vecs = np.array(result_embeddings)
        
        # Calculate relevance scores (cosine similarity)
        query_norm = np.linalg.norm(query_vec)
        result_norms = np.linalg.norm(result_vecs, axis=1)
        relevance_scores = np.dot(result_vecs, query_vec) / (query_norm * result_norms)
        
        # MMR algorithm
        selected = []
        remaining_indices = set(range(len(results)))
        
        # Select first result (highest relevance)
        best_idx = np.argmax(relevance_scores)
        selected.append(best_idx)
        remaining_indices.remove(best_idx)
        
        # Iteratively select most MMR-scored document
        while len(selected) < max_results and remaining_indices:
            max_mmr_score = -float('inf')
            best_candidate_idx = None
            
            for candidate_idx in remaining_indices:
                # Relevance component
                relevance = relevance_scores[candidate_idx]
                
                # Diversity component (max similarity to already selected)
                max_similarity = 0.0
                if selected:
                    selected_vecs = result_vecs[selected]
                    candidate_vec = result_vecs[candidate_idx]
                    candidate_norm = np.linalg.norm(candidate_vec)
                    
                    similarities = np.dot(selected_vecs, candidate_vec) / (
                        np.linalg.norm(selected_vecs, axis=1) * candidate_norm
                    )
                    max_similarity = np.max(similarities)
                
                # MMR score: lambda * relevance - (1 - lambda) * max_similarity
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity
                
                if mmr_score > max_mmr_score:
                    max_mmr_score = mmr_score
                    best_candidate_idx = candidate_idx
            
            if best_candidate_idx is not None:
                selected.append(best_candidate_idx)
                remaining_indices.remove(best_candidate_idx)
            else:
                break
        
        # Return selected results in order
        return [results[i] for i in selected]
    
    def _rerank_documents(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Re-rank documents using cross-encoder (if available)
        
        Note: Cross-encoder re-ranking requires additional model.
        For now, this is a placeholder for future implementation.
        """
        # TODO: Implement cross-encoder re-ranking
        # This would require installing: sentence-transformers[cross-encoder]
        # Example:
        # from sentence_transformers import CrossEncoder
        # cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        # pairs = [[query, result['content']] for result in results]
        # scores = cross_encoder.predict(pairs)
        # # Re-sort results by scores
        
        # For now, return original results
        return results
    
    def ask_question(
        self,
        question: str,
        collections: List[CollectionType],
        max_results: int,
        min_score: float
    ) -> Dict[str, Any]:
        """Ask a question and get an answer with references"""
        # Get collections to search
        collections_to_search = self._get_collections_to_search(collections)
        
        if not collections_to_search:
            return {
                'answer': "No collections available to search.",
                'question': question,
                'references': [],
                'total_references_found': 0,
                'collections_searched': []
            }
        
        # Reset failed collections tracking
        self._last_failed_collections = []
        
        # Retrieve relevant documents
        retrieved_docs = self._retrieve_documents(
            question,
            collections_to_search,
            max_results,
            min_score
        )
        
        # Get successfully searched collections (exclude failed ones)
        successfully_searched = [c for c in collections_to_search if c not in self._last_failed_collections]
        
        if not retrieved_docs:
            answer = "I couldn't find any relevant information to answer your question. Please try rephrasing your question or checking if the relevant documents have been indexed."
            if self._last_failed_collections:
                answer += f" Note: Some collections ({', '.join(self._last_failed_collections)}) could not be searched due to errors."
            return {
                'answer': answer,
                'question': question,
                'references': [],
                'total_references_found': 0,
                'collections_searched': successfully_searched,
                'failed_collections': self._last_failed_collections if self._last_failed_collections else None
            }
        
        # Prepare context for LLM with smart prioritization
        context_parts = self._prepare_context(
            retrieved_docs,
            settings.max_context_length,
            settings.enable_smart_truncation
        )
        
        # Use more compact separator to save characters
        if settings.use_compact_prompt:
            separator = "\n\n"  # Shorter separator
        else:
            separator = "\n\n---\n\n"
        context = separator.join(context_parts)
        
        # Apply context compression if enabled
        if settings.enable_context_compression and len(context) > settings.max_context_length:
            context = self._compress_context(context, settings.max_context_length)
        
        # Final safety check: truncate if still too long
        if len(context) > settings.max_context_length:
            print(f"  ⚠ Truncating context from {len(context)} to {settings.max_context_length} characters")
            context = context[:settings.max_context_length] + "... [context truncated]"
        
        # Create prompt with size-optimized context
        # Use compact prompt if enabled (saves ~200 chars)
        if settings.use_compact_prompt:
            prompt = f"""Answer based on the context:

{context}

Q: {question}
A:"""
        else:
            prompt = f"""You are an expert in Islamic finance and Shariah compliance. Answer the following question based on the provided context from official documents.

Context from documents:
{context}

Question: {question}

Provide a clear, accurate, and comprehensive answer based on the context. If the context doesn't contain enough information to fully answer the question, say so. Include specific details from the documents when relevant."""
        
        print(f"  Prompt size: {len(prompt)} characters ({len(context_parts)} documents)")

        # Generate answer using LLM
        try:
            print(f"  Generating answer using LLM...")
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # Validate answer
            if not answer or answer.strip() == "":
                raise ValueError("LLM returned empty response")
            
            print(f"  ✓ Answer generated ({len(answer)} characters)")
        except Exception as e:
            error_msg = str(e)
            print(f"  ✗ Error generating answer: {error_msg}")
            
            # Provide more helpful error message based on error type
            if "tenant activation" in error_msg.lower():
                answer = f"I encountered an API Gateway configuration error: Tenant activation issue.\n\nThis indicates that the API Gateway tenant/service is not properly activated. This is a configuration issue that needs to be resolved by the API Gateway administrator.\n\nError details: {error_msg}\n\nPlease contact your API Gateway administrator to:\n- Verify tenant activation status\n- Check service subscription\n- Ensure proper authentication setup"
            elif "API Gateway Error" in error_msg or "API Gateway" in error_msg:
                answer = f"I encountered an API Gateway error.\n\nThis is typically a configuration or service issue with the API Gateway. Please verify:\n- API Gateway service is properly configured\n- Authentication credentials are correct\n- Service endpoints are accessible\n- Tenant/service is properly activated\n\nError details: {error_msg}"
            elif "500" in error_msg or "Internal Server Error" in error_msg:
                answer = f"I encountered a server error while generating an answer. The system attempted retries but the error persisted.\n\nThis may be due to:\n- The LLM service being temporarily unavailable\n- The request being too large or complex\n- An issue with the API Gateway service\n\nPlease try again with a shorter or simpler question. Error details: {error_msg}"
            elif "timeout" in error_msg.lower():
                answer = f"The LLM request timed out. This may be because the question or context is too complex. Please try rephrasing your question or breaking it into smaller parts. Error details: {error_msg}"
            elif "authentication" in error_msg.lower() or "authorization" in error_msg.lower():
                answer = f"I encountered an authentication/authorization error with the API Gateway.\n\nPlease verify:\n- API Gateway credentials are correct\n- Token endpoint is accessible\n- Service permissions are properly configured\n\nError details: {error_msg}"
            else:
                answer = f"I encountered an error while generating an answer: {error_msg}"
        
        # Format references
        references = []
        for doc in retrieved_docs:
            metadata = doc['metadata']
            ref = SourceReference(
                pdf_title=metadata.get('pdf_title', 'Unknown'),
                pdf_url=metadata.get('pdf_url'),
                chunk_text=doc['content'],
                similarity_score=doc['similarity_score'],
                chunk_index=metadata.get('chunk_index', 0),
                total_chunks=metadata.get('total_chunks', 0),
                date=metadata.get('date'),
                document_type=metadata.get('document_type'),
                resolution_number=metadata.get('resolution_number'),
                source=doc['collection']
            )
            references.append(ref)
        
        return {
            'answer': answer,
            'question': question,
            'references': references,
            'total_references_found': len(retrieved_docs),
            'collections_searched': successfully_searched,
            'failed_collections': self._last_failed_collections if self._last_failed_collections else None
        }
    
    def _prepare_context(
        self,
        retrieved_docs: List[Dict[str, Any]],
        max_length: int,
        smart_truncation: bool
    ) -> List[str]:
        """
        Prepare context with smart prioritization
        
        Strategies:
        - Prioritize high-scoring documents
        - Ensure diversity (different sources)
        - Smart truncation: truncate individual chunks if needed
        """
        context_parts = []
        current_length = 0
        seen_sources = set()
        
        for doc in retrieved_docs:
            title = doc['metadata'].get('pdf_title', 'Unknown Document')
            doc_text = doc['content']
            source_key = f"{doc['collection']}_{title}"
            
            # Smart truncation: truncate individual chunks if needed
            if smart_truncation:
                # Calculate available space (reduce reserve for compact format)
                reserve = 50 if settings.use_compact_prompt else 100
                available_space = max_length - current_length - reserve
                
                # If chunk is too long, truncate intelligently
                if len(doc_text) > available_space and available_space > 200:
                    # Try to truncate at sentence boundary
                    truncated = doc_text[:available_space]
                    last_period = truncated.rfind('.')
                    last_newline = truncated.rfind('\n')
                    
                    # Prefer sentence boundary, then paragraph boundary
                    if last_period > available_space * 0.8:
                        doc_text = truncated[:last_period + 1] + "... [truncated]"
                    elif last_newline > available_space * 0.8:
                        doc_text = truncated[:last_newline] + "\n... [truncated]"
                    else:
                        doc_text = truncated + "... [truncated]"
            
            # Use compact format to save characters
            if settings.use_compact_prompt:
                # Shorter format: "[Title] text..." instead of "From Title:\ntext..."
                doc_entry = f"[{title}] {doc_text}"
            else:
                doc_entry = f"From {title}:\n{doc_text}"
            
            # Check if adding this document would exceed limit
            if current_length + len(doc_entry) > max_length and context_parts:
                print(f"  ⚠ Context limit reached, using {len(context_parts)} documents")
                break
            
            # Prioritize diverse sources (if not already seen)
            if smart_truncation and source_key in seen_sources and len(context_parts) >= 3:
                # Skip if we already have content from this source and have enough diversity
                continue
            
            context_parts.append(doc_entry)
            current_length += len(doc_entry)
            seen_sources.add(source_key)
        
        return context_parts
    
    def _compress_context(self, context: str, target_length: int) -> str:
        """
        Compress context using summarization (if LLM available)
        
        Note: This is a placeholder. Full implementation would use:
        - Extractive summarization (sentence selection)
        - Abstractive summarization (LLM-based)
        """
        # Simple extractive approach: keep first N characters
        # TODO: Implement proper summarization
        if len(context) <= target_length:
            return context
        
        # For now, just truncate intelligently
        truncated = context[:target_length]
        last_period = truncated.rfind('.')
        if last_period > target_length * 0.8:
            return truncated[:last_period + 1] + "... [compressed]"
        return truncated + "... [compressed]"
    
    def get_collection_statistics(self) -> Dict[str, Any]:
        """Get statistics for all collections"""
        stats = {
            'total_collections': 0,
            'total_documents': 0,
            'total_chunks': 0,
            'collections': []
        }
        
        if not self.qdrant_client:
            return stats
        
        try:
            # Get all collections
            collections_info = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections_info.collections]
            
            stats['total_collections'] = len(collection_names)
            
            # Helper functions for date parsing and comparison
            def parse_date(date_str: str) -> Optional[datetime]:
                """Parse various date formats"""
                if not date_str:
                    return None
                # Common date formats
                formats = [
                    '%Y-%m-%d',
                    '%d %B %Y',
                    '%d %b %Y',
                    '%B %d, %Y',
                    '%b %d, %Y',
                    '%Y',
                    '%d/%m/%Y',
                    '%m/%d/%Y',
                    '%d-%m-%Y',
                    '%m-%d-%Y',
                ]
                for fmt in formats:
                    try:
                        parsed = datetime.strptime(date_str.strip(), fmt)
                        # Validate: dates shouldn't be too far in the future (more than 2 years)
                        current_year = datetime.now().year
                        if parsed.year > current_year + 2:
                            # Likely a parsing error, skip this format
                            continue
                        return parsed
                    except:
                        continue
                return None
            
            def compare_dates(date1: str, date2: str) -> bool:
                """Compare two date strings, return True if date1 > date2"""
                parsed1 = parse_date(date1)
                parsed2 = parse_date(date2)
                if parsed1 and parsed2:
                    return parsed1 > parsed2
                # Fallback to string comparison if parsing fails
                return date1 > date2
            
            for collection_name in collection_names:
                try:
                    # Get collection info
                    collection_info = self.qdrant_client.get_collection(collection_name)
                    point_count = collection_info.points_count
                    
                    # Get unique PDFs and track dates
                    unique_pdfs = set()
                    pdf_dates = {}  # Track dates for each PDF
                    last_document_date = None
                    last_document_title = None
                    try:
                        # Scroll through all points to get unique PDF titles and dates
                        scroll_result = self.qdrant_client.scroll(
                            collection_name=collection_name,
                            limit=10000,  # Increased limit to get more data
                            with_payload=True
                        )
                        
                        for point in scroll_result[0]:
                            if point.payload:
                                pdf_title = point.payload.get('pdf_title', '')
                                if pdf_title:
                                    unique_pdfs.add(pdf_title)
                                    
                                    # Track document dates
                                    doc_date = point.payload.get('date', '')
                                    if doc_date:
                                        # Store the most recent date for this PDF
                                        if pdf_title not in pdf_dates or compare_dates(doc_date, pdf_dates[pdf_title]):
                                            pdf_dates[pdf_title] = doc_date
                                        
                                        # Track overall most recent document date
                                        if not last_document_date or compare_dates(doc_date, last_document_date):
                                            last_document_date = doc_date
                                            last_document_title = pdf_title
                                            last_document_date_parsed = parse_date(doc_date)
                        
                        # If we didn't get all points, continue scrolling
                        offset = scroll_result[1]
                        while offset:
                            try:
                                scroll_result = self.qdrant_client.scroll(
                                    collection_name=collection_name,
                                    limit=10000,
                                    offset=offset,
                                    with_payload=True
                                )
                                
                                for point in scroll_result[0]:
                                    if point.payload:
                                        pdf_title = point.payload.get('pdf_title', '')
                                        if pdf_title:
                                            unique_pdfs.add(pdf_title)
                                            
                                            doc_date = point.payload.get('date', '')
                                            if doc_date:
                                                if pdf_title not in pdf_dates or compare_dates(doc_date, pdf_dates[pdf_title]):
                                                    pdf_dates[pdf_title] = doc_date
                                                
                                                if not last_document_date or compare_dates(doc_date, last_document_date):
                                                    last_document_date = doc_date
                                                    last_document_title = pdf_title
                                                    last_document_date_parsed = parse_date(doc_date)
                                
                                offset = scroll_result[1]
                            except Exception as e:
                                print(f"  ⚠ Error scrolling collection {collection_name}: {e}")
                                break
                                
                    except Exception as e:
                        print(f"  ⚠ Could not get unique PDFs for {collection_name}: {e}")
                    
                    # Calculate average chunks per document
                    unique_count = len(unique_pdfs) if unique_pdfs else 1
                    avg_chunks = point_count / unique_count if unique_count > 0 else 0
                    
                    # Get collection creation/update time from Qdrant
                    # Qdrant doesn't directly provide this, so we'll use the most recent document date
                    # or try to get it from collection info
                    collection_last_updated = None
                    try:
                        # Try to get collection config which might have creation info
                        # For now, use the most recent document date as proxy
                        collection_last_updated = last_document_date
                    except:
                        pass
                    
                    collection_stat = {
                        'collection_name': collection_name,
                        'total_documents': unique_count,
                        'total_chunks': point_count,
                        'unique_pdfs': unique_count,
                        'avg_chunks_per_document': round(avg_chunks, 2),
                        'last_updated': collection_last_updated,
                        'last_document_updated': last_document_date,
                        'last_document_title': last_document_title
                    }
                    
                    stats['collections'].append(collection_stat)
                    stats['total_chunks'] += point_count
                    stats['total_documents'] += unique_count
                    
                except Exception as e:
                    print(f"  ⚠ Error getting stats for {collection_name}: {e}")
                    # Add collection with zero stats
                    stats['collections'].append({
                        'collection_name': collection_name,
                        'total_documents': 0,
                        'total_chunks': 0,
                        'unique_pdfs': 0,
                        'avg_chunks_per_document': 0.0,
                        'last_updated': None,
                        'last_document_updated': None,
                        'last_document_title': None
                    })
            
        except Exception as e:
            print(f"Error getting collection statistics: {e}")
        
        return stats
    
    def get_collection_documents(self, collection_name: str) -> Dict[str, Any]:
        """Get list of all unique documents in a collection"""
        documents = {}
        
        if not self.qdrant_client:
            return {
                'collection_name': collection_name,
                'total_documents': 0,
                'documents': []
            }
        
        try:
            # Scroll through all points to get unique documents
            offset = None
            while True:
                scroll_result = self.qdrant_client.scroll(
                    collection_name=collection_name,
                    limit=10000,
                    offset=offset,
                    with_payload=True
                )
                
                points = scroll_result[0]
                if not points:
                    break
                
                for point in points:
                    if point.payload:
                        pdf_title = point.payload.get('pdf_title', '')
                        if not pdf_title:
                            continue
                        
                        # Use pdf_title as key to get unique documents
                        if pdf_title not in documents:
                            documents[pdf_title] = {
                                'pdf_title': pdf_title,
                                'pdf_url': point.payload.get('pdf_url'),
                                'date': point.payload.get('date'),
                                'document_type': point.payload.get('document_type'),
                                'resolution_number': point.payload.get('resolution_number'),
                                'total_chunks': point.payload.get('total_chunks', 0)
                            }
                        else:
                            # Update total_chunks if we find a higher value
                            existing_chunks = documents[pdf_title].get('total_chunks', 0)
                            current_chunks = point.payload.get('total_chunks', 0)
                            if current_chunks > existing_chunks:
                                documents[pdf_title]['total_chunks'] = current_chunks
                
                offset = scroll_result[1]
                if not offset:
                    break
                    
        except Exception as e:
            print(f"Error getting documents for collection {collection_name}: {e}")
            return {
                'collection_name': collection_name,
                'total_documents': 0,
                'documents': []
            }
        
        # Convert to list and sort by date (most recent first) or title
        documents_list = list(documents.values())
        documents_list.sort(key=lambda x: (
            x.get('date', '') or '',
            x.get('pdf_title', '')
        ), reverse=True)
        
        return {
            'collection_name': collection_name,
            'total_documents': len(documents_list),
            'documents': documents_list
        }