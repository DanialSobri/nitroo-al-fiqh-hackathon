"""RAG (Retrieval Augmented Generation) service using LangChain and Qdrant"""
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_openai import ChatOpenAI
import numpy as np
from config import settings
from models import CollectionType, SourceReference
from ollama_llm import OllamaLLM, OllamaChatLLM
from audit_logging import get_audit_logger
from conversation_memory import ConversationMemory
from pdf_page_extractor import extract_sentence_location
from cache_manager import get_cache_manager
# API Gateway imports are conditional (deprecated)

# Try to import pdfplumber for page number lookup
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Warning: pdfplumber not available. Page number lookup from PDF will be disabled.")


class RAGService:
    """Service for RAG operations using LangChain and Qdrant"""
    
    def __init__(self):
        """Initialize the RAG service"""
        self.embedding_model = None
        self.qdrant_client = None
        self.vector_stores: Dict[str, Qdrant] = {}
        self.llm = None
        self.conversation_memory = ConversationMemory()
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
        
        # CACHE OPTIMIZATION: Check cache for query embedding
        if settings.enable_caching:
            cache_manager = get_cache_manager()
            query_embedding = cache_manager.get_embedding(query)
            
            if query_embedding is None:
                # Generate query embedding if not cached
                query_embedding = self.embedding_model.encode(query).tolist()
                # Cache it for future use
                cache_manager.set_embedding(query, query_embedding)
            else:
                print(f"  ✓ Using cached embedding for query")
        else:
            # Generate query embedding without caching
            query_embedding = self.embedding_model.encode(query).tolist()
        
        # Stage 1: Initial ANN retrieval (retrieve more candidates)
        # OPTIMIZATION: Search collections in parallel for faster response
        failed_collections = []
        
        def search_collection(collection_name: str) -> tuple[str, List[Dict[str, Any]], Optional[str]]:
            """Search a single collection and return results or error"""
            try:
                # Use Qdrant client directly for ANN search
                search_results = self.qdrant_client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    limit=initial_limit,
                    score_threshold=min_score  # Filter low-quality results early
                )
                
                # Convert to our format
                collection_results = []
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
                    collection_results.append(result_dict)
                
                return collection_name, collection_results, None
            except Exception as e:
                error_msg = str(e)
                error_lower = error_msg.lower()
                
                # Check for specific Qdrant errors (corruption, panic, server errors)
                is_corrupted = (
                    "offsetoutofbounds" in error_lower or 
                    "500" in error_msg or 
                    "internal server error" in error_lower or
                    "panicked" in error_lower or
                    "panic" in error_lower or
                    "corrupted" in error_lower or
                    "data issues" in error_lower
                )
                
                if is_corrupted:
                    print(f"⚠ Warning: Collection '{collection_name}' appears to be corrupted or has data issues.")
                    # Extract more readable error message
                    if "panicked" in error_lower:
                        print(f"   Error: Qdrant service panicked while accessing this collection.")
                        print(f"   This usually indicates corrupted data or a Qdrant internal error.")
                    elif "500" in error_msg or "internal server error" in error_lower:
                        print(f"   Error: Qdrant returned 500 Internal Server Error.")
                    else:
                        print(f"   Error: {error_msg[:200]}...")  # Truncate long error messages
                    print(f"   Suggestion: Consider re-scraping this collection or checking Qdrant logs.")
                    print(f"   The system will continue searching other collections.")
                else:
                    print(f"⚠ Error searching collection '{collection_name}': {error_msg[:200]}...")
                
                return collection_name, [], error_msg
        
        # Search all collections in parallel
        with ThreadPoolExecutor(max_workers=min(len(collections), 5)) as executor:
            future_to_collection = {
                executor.submit(search_collection, collection_name): collection_name
                for collection_name in collections
            }
            
            for future in as_completed(future_to_collection):
                collection_name, collection_results, error = future.result()
                if error:
                    failed_collections.append(collection_name)
                else:
                    all_results.extend(collection_results)
        
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
        min_score: float,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        use_memory: bool = True
    ) -> Dict[str, Any]:
        """Ask a question and get an answer with references"""
        # Get conversation memory (retrieve relevant past conversations)
        context_conversations = []
        if use_memory and (user_id or session_id):
            try:
                print(f"  🔍 Retrieving conversation memory (user_id: {user_id}, session_id: {session_id})...")
                context_conversations = self.conversation_memory.get_relevant_conversations(
                    current_question=question,
                    user_id=user_id,
                    session_id=session_id,
                    limit=5,  # Get top 5 relevant past conversations
                    score_threshold=0.5  # Lower threshold to get more results
                )
                if context_conversations:
                    print(f"  📝 Found {len(context_conversations)} relevant past conversations")
                    for i, conv in enumerate(context_conversations, 1):
                        print(f"    {i}. Score: {conv.get('similarity_score', 0):.3f} - Q: {conv.get('question', '')[:50]}...")
                else:
                    print(f"  ℹ No relevant past conversations found (threshold: 0.5)")
            except Exception as e:
                print(f"  ⚠ Error retrieving conversation memory: {e}")
                import traceback
                print(traceback.format_exc())
                context_conversations = []
        
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
        
        # Build context from past conversations
        conversation_context = ""
        if context_conversations:
            conversation_context = "\n\n--- Previous Conversations (for context) ---\n"
            for conv in context_conversations:
                conversation_context += f"Q: {conv['question']}\n"
                conversation_context += f"A: {conv['answer'][:200]}...\n\n"
        
        # Prepare context for LLM with smart prioritization and citation numbering
        context_parts, citation_map = self._prepare_context_with_citations(
            retrieved_docs,
            settings.max_context_length,
            settings.enable_smart_truncation
        )
        
        # Validate context is not empty
        if not context_parts or not any(context_parts):
            print(f"  ⚠ Warning: No context parts generated from retrieved documents")
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
        
        # Use more compact separator to save characters
        if settings.use_compact_prompt:
            separator = "\n\n"  # Shorter separator
        else:
            separator = "\n\n---\n\n"
        context = separator.join(context_parts)
        
        # Validate context is not empty after joining
        if not context or not context.strip():
            print(f"  ⚠ Warning: Context is empty after joining parts")
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
        
        # Apply context compression if enabled
        if settings.enable_context_compression and len(context) > settings.max_context_length:
            context = self._compress_context(context, settings.max_context_length)
        
        # Final safety check: truncate if still too long
        if len(context) > settings.max_context_length:
            print(f"  ⚠ Truncating context from {len(context)} to {settings.max_context_length} characters")
            context = context[:settings.max_context_length] + "... [context truncated]"
        
        # Count how many sources are provided
        num_sources = len(context_parts)
        
        # Create prompt with enhanced multi-source synthesis instructions
        if settings.use_compact_prompt:
            if num_sources > 1:
                # Enhanced compact prompt with examples - PUT CONTEXT FIRST, THEN QUESTION
                prompt = f"""You are an expert assistant with DIRECT ACCESS to authoritative Shariah documents. Answer questions using ONLY the source documents provided below.

═══════════════════════════════════════════════════════════════
SOURCE DOCUMENTS PROVIDED BELOW - USE THESE TO ANSWER:
═══════════════════════════════════════════════════════════════
{context}
═══════════════════════════════════════════════════════════════

{conversation_context}

⚠️ CRITICAL RULES - THE DOCUMENTS ARE PROVIDED ABOVE:
1. Look at the "SOURCE DOCUMENTS" section ABOVE - it contains {num_sources} documents numbered [1] to [{num_sources}]
2. These documents contain REAL text from official Shariah documents - you can see the actual content above
3. You MUST answer using ONLY the information from these documents shown above
4. DO NOT say "I need the documents" or "please provide" - they ARE PROVIDED ABOVE in the section you just read
5. DO NOT say "I cannot access" or "the content was not provided" - you CAN see the content in the section above
6. DO NOT ask the user to share documents - they are already shared above
7. If information exists in the documents above, USE IT to answer directly
8. If information is NOT in the documents above, say "The provided documents do not contain information about this specific question"
9. Cite sources: "According to [1] and [2]..." or "[1] states X, while [2] adds Y [3]"
10. Provide key financial ratios, numerical thresholds, and inclusion/exclusion criteria from the documents

EXAMPLE: If the question is "What is the threshold?" and document [1] above says "The threshold is 5%", then answer "According to [1], the threshold is 5%."

Question: {question}

Answer based on the source documents provided above:"""
            else:
                # Single source - PUT CONTEXT FIRST
                prompt = f"""You are an expert assistant with DIRECT ACCESS to authoritative Shariah documents. Answer questions using ONLY the source document provided below.

═══════════════════════════════════════════════════════════════
SOURCE DOCUMENT PROVIDED BELOW - USE THIS TO ANSWER:
═══════════════════════════════════════════════════════════════
{context}
═══════════════════════════════════════════════════════════════

{conversation_context}

⚠️ CRITICAL RULES - THE DOCUMENT IS PROVIDED ABOVE:
1. Look at the "SOURCE DOCUMENT" section ABOVE - it contains document [1] with actual text content
2. This document contains REAL information from official Shariah documents - you can see the actual content above
3. You MUST answer using ONLY the information from this document shown above
4. DO NOT say "I need the document" or "please provide" - it IS PROVIDED ABOVE in the section you just read
5. DO NOT say "I cannot access" or "the content was not provided" - you CAN see the content in the section above
6. DO NOT ask the user to share the document - it is already shared above
7. If information exists in the document above, USE IT to answer directly
8. If information is NOT in the document above, say "The provided document does not contain information about this specific question"
9. Cite source [1] after claims
10. Provide key financial ratios, numerical thresholds, and inclusion/exclusion criteria from the document

EXAMPLE: If the question is "What is the threshold?" and the document above says "The threshold is 5%", then answer "According to [1], the threshold is 5%."

Question: {question}

Answer based on the source document provided above:"""
        else:
            if num_sources > 1:
                # Enhanced full prompt - PUT CONTEXT FIRST, THEN QUESTION
                prompt = f"""You are an expert assistant in Islamic finance and Shariah compliance with DIRECT ACCESS to authoritative Shariah documents. Answer questions using ONLY the source documents provided below.

═══════════════════════════════════════════════════════════════
SOURCE DOCUMENTS PROVIDED BELOW - USE THESE TO ANSWER:
═══════════════════════════════════════════════════════════════
{context}
═══════════════════════════════════════════════════════════════

{conversation_context}

Question: {question}

═══════════════════════════════════════════════════════════════
CRITICAL REQUIREMENTS - READ CAREFULLY:
═══════════════════════════════════════════════════════════════

0. ⚠️ CRITICAL: USE PROVIDED CONTEXT ONLY - THE DOCUMENTS ARE PROVIDED ABOVE:
   - You MUST answer based ONLY on the provided source documents in the "SOURCE DOCUMENTS" section above
   - The documents ARE PROVIDED above - you can see them in the "SOURCE DOCUMENTS" section
   - DO NOT say "I cannot access sources" or "the content was not provided" - IT IS PROVIDED ABOVE
   - DO NOT say "please share the documents" - they are already shared in the context above
   - DO NOT provide general knowledge or disclaimers about not having access - you HAVE access through the context above
   - The documents above are REAL and contain the actual text from official Shariah documents
   - If information is not in the provided context, say "The provided documents do not contain information about this specific question"
   - If the answer IS in the documents above, provide it directly using the information from those documents

1. CONTENT REQUIREMENTS:
   - Provide the key financial ratios, numerical thresholds, and inclusion/exclusion criteria from the provided documents
   - Base your answer on the authoritative Shariah documents provided above
   - Synthesise guidance across multiple sources rather than relying on a single document
   - When providing numerical values, thresholds, or ratios, cite the specific sources

2. MANDATORY MULTI-SOURCE CITATION:
   - You MUST cite at least 2-3 DIFFERENT source numbers in your answer
   - Using ONLY [1] is STRICTLY PROHIBITED when multiple sources are available
   - Your answer will be evaluated on how well you integrate multiple sources

3. SYNTHESIS PATTERNS - Use these approaches:
   
   Pattern A - Multiple sources supporting same point:
   "The requirement states that... [1] [2] [3]"
   
   Pattern B - Sources providing complementary information:
   "According to [1], the threshold is 5%. Additionally, [2] clarifies that this applies to... Meanwhile, [3] provides guidance on..."
   
   Pattern C - Sources with different perspectives:
   "[1] establishes the framework, while [2] details the implementation process. [3] adds specific examples of..."
   
   Pattern D - Sequential integration:
   "[1] defines the concept as... Building on this, [2] explains... Finally, [3] illustrates..."

4. CITATION RULES:
   - Cite sources immediately after each claim: "The rule states X [1] [2]"
   - When synthesizing, cite all relevant sources: "[1] and [2] both indicate..."
   - Use multiple citations per sentence when appropriate: "The framework [1] requires compliance [2] with specific criteria [3]"
   - Do NOT cluster all citations at the end - distribute them throughout

5. ANSWER STRUCTURE:
   - Start by synthesizing key points from multiple sources
   - Compare and contrast information from different sources when relevant
   - Integrate complementary details from various sources
   - Conclude by showing how multiple sources support your answer

6. QUALITY INDICATORS:
   ✓ Good: References 3+ different source numbers throughout
   ✓ Good: Shows synthesis: "While [1] focuses on X, [2] emphasizes Y, and [3] adds Z"
   ✗ Bad: Only cites [1] repeatedly
   ✗ Bad: Mentions other sources exist but doesn't cite them

═══════════════════════════════════════════════════════════════

REMEMBER: Your goal is to demonstrate comprehensive understanding by integrating information from MULTIPLE sources. A well-synthesized answer will naturally reference 2-3+ different source numbers.

Begin your answer now:"""
            else:
                prompt = f"""You are an expert assistant in Islamic finance and Shariah compliance with DIRECT ACCESS to authoritative Shariah documents. The SOURCE DOCUMENT section below contains EXACT EXTRACTS from official documents that you MUST use to answer the question.

⚠️ CRITICAL INSTRUCTIONS - READ CAREFULLY:
- You have 1 source document [1] PROVIDED BELOW in the "SOURCE DOCUMENT" section
- This document is REAL and contains the information you need to answer the question
- You MUST answer based ONLY on the information in this source document
- DO NOT say "I don't have access" or "the content was not provided" - the content IS provided below
- DO NOT ask the user to share documents - the document is already shared in the context below
- If the answer is in the document below, provide it. If not, say "The provided document does not contain information about this specific question."

{conversation_context}

═══════════════════════════════════════════════════════════════
SOURCE DOCUMENT (READ AND USE THIS TO ANSWER):
═══════════════════════════════════════════════════════════════
{context}
═══════════════════════════════════════════════════════════════

Question: {question}

IMPORTANT: Provide the key financial ratios, numerical thresholds, and inclusion/exclusion criteria from the document above. Base your answer on the authoritative Shariah document provided in the context. Cite source [1] after claims.

Provide a clear, accurate, and comprehensive answer based ONLY on the provided context above. If the question relates to previous conversations, use that context to provide a coherent answer. If the context doesn't contain enough information to fully answer the question, say "The provided document does not contain information about this specific question." explicitly."""
        
        print(f"  Prompt size: {len(prompt)} characters ({len(context_parts)} documents)")
        print(f"  Context preview: {context[:200]}..." if len(context) > 200 else f"  Context: {context}")
        print(f"  Context preview: {context[:200]}..." if len(context) > 200 else f"  Context: {context}")
        if num_sources > 1:
            print(f"  ⚠ Multiple sources provided ({num_sources}) - LLM should cite at least 2-3 sources")

        # Generate answer using LLM with token tracking
        start_time = time.time()
        token_usage = {
            'prompt_tokens': None,
            'completion_tokens': None,
            'total_tokens': None
        }
        error_message = None
        success = True
        cited_numbers = set()  # Initialize to empty set
        
        try:
            print(f"  Generating answer using LLM...")
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # Extract token usage from response if available
            if hasattr(response, 'response_metadata'):
                metadata = response.response_metadata
                if isinstance(metadata, dict):
                    # OpenAI format
                    if 'token_usage' in metadata:
                        usage = metadata['token_usage']
                        token_usage['prompt_tokens'] = usage.get('prompt_tokens')
                        token_usage['completion_tokens'] = usage.get('completion_tokens')
                        token_usage['total_tokens'] = usage.get('total_tokens')
                    # Ollama format (if available in metadata)
                    elif 'prompt_eval_count' in metadata:
                        token_usage['prompt_tokens'] = metadata.get('prompt_eval_count')
                        token_usage['completion_tokens'] = metadata.get('eval_count')
                        if token_usage['prompt_tokens'] and token_usage['completion_tokens']:
                            token_usage['total_tokens'] = token_usage['prompt_tokens'] + token_usage['completion_tokens']
            
            # Try to get token usage from raw response if available
            if hasattr(self.llm, 'last_response') and self.llm.last_response:
                raw_response = self.llm.last_response
                if isinstance(raw_response, dict):
                    # Ollama format
                    if 'prompt_eval_count' in raw_response:
                        token_usage['prompt_tokens'] = raw_response.get('prompt_eval_count')
                        token_usage['completion_tokens'] = raw_response.get('eval_count')
                        if token_usage['prompt_tokens'] and token_usage['completion_tokens']:
                            token_usage['total_tokens'] = token_usage['prompt_tokens'] + token_usage['completion_tokens']
                    # OpenAI format
                    elif 'usage' in raw_response:
                        usage = raw_response['usage']
                        token_usage['prompt_tokens'] = usage.get('prompt_tokens')
                        token_usage['completion_tokens'] = usage.get('completion_tokens')
                        token_usage['total_tokens'] = usage.get('total_tokens')
            
            # Validate answer
            if not answer or answer.strip() == "":
                raise ValueError("LLM returned empty response")
            
            # Check how many sources were actually cited
            import re
            cited_numbers = set(re.findall(r'\[(\d+)\]', answer))
            num_cited = len(cited_numbers)
            if num_sources > 1 and num_cited < 2:
                print(f"  ⚠ WARNING: Only {num_cited} source(s) cited in answer ([{', '.join(cited_numbers)}]) despite {num_sources} sources being provided")
            else:
                print(f"  ✓ Answer generated ({len(answer)} characters) - Cited {num_cited} source(s): [{', '.join(sorted(cited_numbers, key=int))}]")
            
            # Log token usage if available
            if token_usage['total_tokens']:
                print(f"  📊 Token usage: {token_usage['total_tokens']} total ({token_usage['prompt_tokens']} prompt + {token_usage['completion_tokens']} completion)")
        except Exception as e:
            error_message = str(e)
            success = False
            print(f"  ✗ Error generating answer: {error_message}")
            
            # Extract cited numbers even from error responses (if any citations exist)
            import re
            if 'answer' in locals():
                cited_numbers = set(re.findall(r'\[(\d+)\]', answer))
            else:
                cited_numbers = set()
            
            # Provide more helpful error message based on error type
            if "tenant activation" in error_message.lower():
                answer = f"I encountered an API Gateway configuration error: Tenant activation issue.\n\nThis indicates that the API Gateway tenant/service is not properly activated. This is a configuration issue that needs to be resolved by the API Gateway administrator.\n\nError details: {error_message}\n\nPlease contact your API Gateway administrator to:\n- Verify tenant activation status\n- Check service subscription\n- Ensure proper authentication setup"
            elif "API Gateway Error" in error_message or "API Gateway" in error_message:
                answer = f"I encountered an API Gateway error.\n\nThis is typically a configuration or service issue with the API Gateway. Please verify:\n- API Gateway service is properly configured\n- Authentication credentials are correct\n- Service endpoints are accessible\n- Tenant/service is properly activated\n\nError details: {error_message}"
            elif "500" in error_message or "Internal Server Error" in error_message:
                answer = f"I encountered a server error while generating an answer. The system attempted retries but the error persisted.\n\nThis may be due to:\n- The LLM service being temporarily unavailable\n- The request being too large or complex\n- An issue with the API Gateway service\n\nPlease try again with a shorter or simpler question. Error details: {error_message}"
            elif "timeout" in error_message.lower():
                answer = f"The LLM request timed out. This may be because the question or context is too complex. Please try rephrasing your question or breaking it into smaller parts. Error details: {error_message}"
            elif "authentication" in error_message.lower() or "authorization" in error_message.lower():
                answer = f"I encountered an authentication/authorization error with the API Gateway.\n\nPlease verify:\n- API Gateway credentials are correct\n- Token endpoint is accessible\n- Service permissions are properly configured\n\nError details: {error_message}"
            else:
                answer = f"I encountered an error while generating an answer: {error_message}"
        
        # Extract cited citation numbers from the answer (if not already extracted)
        # cited_numbers should already be set from the try/except block above
        
        # Filter to only include references that were actually cited in the answer
        # Convert cited_numbers to integers for comparison
        cited_indices = set(int(num) for num in cited_numbers if num.isdigit())
        
        # Filter retrieved_docs to only those that were cited
        # citation_map maps citation number (1-indexed) to doc index (0-indexed)
        # So we need to find which doc indices correspond to cited citation numbers
        cited_doc_indices = set()
        for citation_num in cited_indices:
            if citation_num in citation_map:
                doc_idx = citation_map[citation_num]
                cited_doc_indices.add(doc_idx)
        
        # If no citations found, fall back to all references (shouldn't happen, but safety check)
        if not cited_doc_indices:
            print(f"  ⚠ No citations found in answer, showing all {len(retrieved_docs)} retrieved references")
            cited_doc_indices = set(range(len(retrieved_docs)))
        else:
            print(f"  ✓ Filtering references: showing {len(cited_doc_indices)} cited reference(s) out of {len(retrieved_docs)} retrieved")
        
        # Filter retrieved_docs to only cited ones
        cited_retrieved_docs = [retrieved_docs[i] for i in cited_doc_indices]
        
        # Create a new citation_map that maps citation numbers to the new filtered reference indices
        # First, create a mapping from old doc index to new reference index
        old_to_new_index = {old_idx: new_idx for new_idx, old_idx in enumerate(sorted(cited_doc_indices))}
        
        # Update citation_map to only include cited references with new indices
        filtered_citation_map = {}
        for citation_num, old_doc_idx in citation_map.items():
            if old_doc_idx in old_to_new_index:
                filtered_citation_map[citation_num] = old_to_new_index[old_doc_idx]
        
        # Format references with citation numbers - ONLY for cited references
        # Get current timestamp for when sources were retrieved
        retrieved_timestamp = datetime.now().isoformat()
        
        references = []
        # First pass: create references with stored page numbers (only for cited docs)
        for new_idx, old_idx in enumerate(sorted(cited_doc_indices)):
            doc = retrieved_docs[old_idx]
            metadata = doc['metadata']
            chunk_text = doc['content']
            
            # Use stored page number if available
            stored_page_number = metadata.get('page_number')
            page_number = stored_page_number if stored_page_number is not None else None
            page_source = 'stored' if page_number is not None else None
            
            ref = SourceReference(
                pdf_title=metadata.get('pdf_title', 'Unknown'),
                pdf_url=metadata.get('pdf_url'),
                chunk_text=doc['content'],
                similarity_score=doc['similarity_score'],
                chunk_index=metadata.get('chunk_index', 0),
                total_chunks=metadata.get('total_chunks', 0),
                page_number=page_number,
                page_number_source=page_source,
                date=metadata.get('date'),
                document_type=metadata.get('document_type'),
                resolution_number=metadata.get('resolution_number'),
                source=doc['collection'],
                retrieved_at=retrieved_timestamp
            )
            references.append(ref)
        
        # Second pass: Automatically find page numbers for references without stored page numbers
        # Do this in parallel to avoid blocking
        # Map new reference indices back to original doc indices for metadata lookup
        sorted_cited_indices = sorted(cited_doc_indices)
        refs_needing_page_lookup = [
            (new_idx, ref, retrieved_docs[sorted_cited_indices[new_idx]]['metadata']) 
            for new_idx, ref in enumerate(references) 
            if not ref.page_number and (ref.pdf_url or ref.chunk_text)
        ]
        
        # OPTIMIZATION: Page lookup is now optional and has shorter timeout
        # If it takes too long, we skip it to avoid blocking the response
        if refs_needing_page_lookup and settings.enable_page_lookup:
            print(f"  🔍 Finding page numbers for {len(refs_needing_page_lookup)} references (max 10s timeout)...")
            
            def find_page_for_ref(ref: SourceReference, ref_idx: int, doc_metadata: Dict[str, Any]) -> Tuple[int, Optional[int], Optional[str]]:
                """Find page number for a single reference"""
                if ref.page_number is not None:
                    # Already has page number, skip
                    return ref_idx, ref.page_number, ref.page_number_source
                
                try:
                    # Try to get filepath from metadata
                    filepath = doc_metadata.get('filepath') or doc_metadata.get('pdf_filepath')
                    
                    page_num, page_source = self._find_page_number_from_pdf(
                        chunk_text=ref.chunk_text,
                        filepath=filepath,
                        pdf_url=ref.pdf_url,
                        stored_page_number=None,
                        chunk_index=ref.chunk_index,
                        total_chunks=ref.total_chunks
                    )
                    return ref_idx, page_num, page_source
                except Exception as e:
                    print(f"  ⚠ Error finding page for reference {ref_idx}: {e}")
                    return ref_idx, None, None
            
            # Run page lookup in parallel with reduced timeout
            # OPTIMIZATION: Reduced timeout from 30s to configurable timeout, max time from config
            page_lookup_start = time.time()
            max_total_time = settings.max_page_lookup_time
            per_ref_timeout = settings.page_lookup_timeout
            
            with ThreadPoolExecutor(max_workers=min(len(refs_needing_page_lookup), 5)) as executor:
                # Submit all tasks with their corresponding metadata
                future_to_ref = {
                    executor.submit(find_page_for_ref, ref, idx, metadata): idx 
                    for idx, ref, metadata in refs_needing_page_lookup
                }
                
                # Update references as results come in (with timeout)
                completed = 0
                for future in as_completed(future_to_ref):
                    # Check if we've exceeded max total time
                    if time.time() - page_lookup_start > max_total_time:
                        print(f"  ⚠ Page lookup timeout ({max_total_time}s), skipping remaining lookups")
                        # Cancel remaining futures
                        for f in future_to_ref:
                            if not f.done():
                                f.cancel()
                        break
                    
                    try:
                        ref_idx, page_num, page_source = future.result(timeout=per_ref_timeout)
                        if page_num is not None:
                            references[ref_idx].page_number = page_num
                            references[ref_idx].page_number_source = page_source
                            completed += 1
                            print(f"  ✓ Found page {page_num} for reference {ref_idx + 1}")
                    except Exception as e:
                        ref_idx = future_to_ref[future]
                        print(f"  ⚠ Failed to find page for reference {ref_idx + 1}: {e}")
                
                if completed > 0:
                    print(f"  ✓ Completed page lookup for {completed}/{len(refs_needing_page_lookup)} references")
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Get collection names as strings
        collection_names = [c.value if hasattr(c, 'value') else str(c) for c in successfully_searched]
        
        # Log to audit logger
        try:
            audit_logger = get_audit_logger()
            audit_logger.log_query(
                question=question,
                answer=answer if success else None,
                llm_provider=settings.llm_provider,
                llm_model=settings.ollama_model if settings.llm_provider == "ollama" else (settings.openai_model if settings.llm_provider == "openai" else "unknown"),
                prompt_tokens=token_usage['prompt_tokens'],
                completion_tokens=token_usage['completion_tokens'],
                total_tokens=token_usage['total_tokens'],
                collections_searched=collection_names,
                num_sources_found=len(retrieved_docs),
                num_sources_cited=len(cited_numbers),
                max_results=max_results,
                min_score=min_score,
                answer_length=len(answer) if answer else None,
                response_time_ms=response_time_ms,
                error_message=error_message,
                success=success
            )
        except Exception as e:
            print(f"  ⚠ Warning: Failed to log to audit logger: {e}")
        
        # Store conversation in memory
        if use_memory and (user_id or session_id) and success:
            try:
                print(f"  💾 Storing conversation in memory (user_id: {user_id}, session_id: {session_id})...")
                conversation_id = self.conversation_memory.store_conversation(
                    user_id=user_id or "anonymous",
                    session_id=session_id or "default",
                    question=question,
                    answer=answer,
                    metadata={
                        'collections_searched': successfully_searched,
                        'num_sources': len(references),
                        'total_tokens': token_usage.get('total_tokens', 0)
                    }
                )
                print(f"  ✓ Stored conversation in memory (ID: {conversation_id})")
            except Exception as e:
                print(f"  ✗ Error storing conversation memory: {e}")
                import traceback
                print(traceback.format_exc())
        
        return {
            'answer': answer,
            'question': question,
            'references': references,
            'total_references_found': len(retrieved_docs),  # Total retrieved (for info)
            'collections_searched': successfully_searched,
            'failed_collections': self._last_failed_collections if self._last_failed_collections else None,
            'citation_map': filtered_citation_map,  # Map citation numbers to filtered reference indices
            'token_usage': token_usage  # Include token usage in the result
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
    
    def _prepare_context_with_citations(
        self,
        retrieved_docs: List[Dict[str, Any]],
        max_length: int,
        smart_truncation: bool
    ) -> tuple[List[str], Dict[int, int]]:
        """
        Prepare context with citation numbering for source anchoring
        
        Returns:
            Tuple of (context_parts with numbered citations, citation_map)
            citation_map maps citation number (1-indexed) to reference index (0-indexed)
        """
        context_parts = []
        citation_map = {}  # Maps citation number to reference index
        current_length = 0
        seen_sources = set()
        citation_num = 1
        
        for doc_idx, doc in enumerate(retrieved_docs):
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
            
            # Use enhanced format with citation number and clear source separation
            # Format makes it clear these are multiple sources to synthesize
            if settings.use_compact_prompt:
                # Format: "[1] [Title] text..." for citations
                doc_entry = f"[{citation_num}] [{title}] {doc_text}"
            else:
                # Enhanced format with clear source boundaries and emphasis on multiple sources
                doc_entry = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SOURCE [{citation_num}] of {len(retrieved_docs)}: {title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{doc_text}
"""
            
            # Check if adding this document would exceed limit
            if current_length + len(doc_entry) > max_length and context_parts:
                print(f"  ⚠ Context limit reached, using {len(context_parts)} documents")
                break
            
            # Prioritize diverse sources (if not already seen)
            if smart_truncation and source_key in seen_sources and len(context_parts) >= 3:
                # Skip if we already have content from this source and have enough diversity
                continue
            
            # Map citation number to reference index
            citation_map[citation_num] = doc_idx
            context_parts.append(doc_entry)
            current_length += len(doc_entry)
            seen_sources.add(source_key)
            citation_num += 1
        
        return context_parts, citation_map
    
    def _find_page_number_from_pdf(
        self,
        chunk_text: str,
        filepath: Optional[str],
        pdf_url: Optional[str],
        stored_page_number: Optional[int],
        chunk_index: Optional[int],
        total_chunks: int
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Find the actual page number in PDF by searching for the chunk text.
        Uses extract_sentence_location for accurate page finding.
        
        Args:
            chunk_text: The text chunk to search for
            filepath: Local file path to the PDF (if available)
            pdf_url: URL of the PDF (for downloading if needed)
            stored_page_number: Previously stored page number (if available)
            chunk_index: Chunk index for estimation fallback
            total_chunks: Total chunks for estimation fallback
            
        Returns:
            Tuple of (page_number, page_source) where page_source is:
            - 'stored': From stored metadata (most reliable)
            - 'pdf_search': Found by searching PDF file
            - 'estimated': Estimated from chunk index
            - None: No page number available
        """
        # If we have a stored page number, use it (most reliable)
        if stored_page_number is not None:
            return stored_page_number, 'stored'
        
        # If chunk text is too short, fall back to estimation
        if len(chunk_text.strip()) < 15:
            if chunk_index is not None:
                estimated_page = max(1, (chunk_index // 4) + 1) if total_chunks > 0 else None
                return estimated_page, 'estimated' if estimated_page else None
            return None, None
        
        # Try to find PDF file path if we have filepath but need to locate it
        pdf_filepath = None
        if filepath:
            pdf_path = Path(filepath)
            if pdf_path.exists() and pdf_path.is_file():
                pdf_filepath = str(pdf_path)
        
        # If filepath doesn't work, try to find PDF in common output directories
        if not pdf_filepath and pdf_url:
            # Try common PDF storage locations
            possible_dirs = [
                Path("../Web-Scraper/pdfs"),
                Path("./pdfs"),
                Path("pdfs"),
                Path("../pdfs"),
            ]
            
            # Try to extract filename from URL
            from urllib.parse import urlparse
            parsed_url = urlparse(pdf_url)
            filename = os.path.basename(parsed_url.path)
            if not filename or not filename.endswith('.pdf'):
                filename = None
            
            if filename:
                for pdf_dir in possible_dirs:
                    potential_path = pdf_dir / filename
                    if potential_path.exists():
                        pdf_filepath = str(potential_path)
                        break
        
        # Use extract_sentence_location to find the page
        try:
            if pdf_filepath or pdf_url:
                print(f"  🔍 Searching PDF for chunk text using extract_sentence_location")
                result = extract_sentence_location(
                    pdf_url=pdf_url if not pdf_filepath else None,
                    pdf_filepath=pdf_filepath,
                    sentence_text=chunk_text,
                    case_sensitive=False,
                    fuzzy_match=True
                )
                
                if result.get('found') and result.get('page_number'):
                    print(f"    ✓ Found match on page {result['page_number']}")
                    return result['page_number'], 'pdf_search'
                else:
                    print(f"    ⚠ Text not found in PDF")
            else:
                print(f"  ⚠ No PDF source available (filepath or URL)")
        except Exception as e:
            print(f"  ⚠ Warning: Could not search PDF for page number: {e}")
            import traceback
            print(f"  Traceback: {traceback.format_exc()}")
        
        # Fall back to estimation if PDF search failed
        if chunk_index is not None:
            estimated_page = max(1, (chunk_index // 4) + 1) if total_chunks > 0 else None
            return estimated_page, 'estimated' if estimated_page else None
        
        return None, None
    
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