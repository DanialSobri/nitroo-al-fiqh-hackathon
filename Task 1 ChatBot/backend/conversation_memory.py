"""Conversation memory service using Qdrant"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from config import settings

class ConversationMemory:
    """Manages conversation history in Qdrant"""
    
    COLLECTION_NAME = "conversation_memory"
    
    def __init__(self):
        """Initialize conversation memory service"""
        # Initialize embedding model (same as RAG service)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize Qdrant client
        if settings.qdrant_url:
            self.qdrant_client = QdrantClient(url=settings.qdrant_url)
        else:
            self.qdrant_client = QdrantClient(path=settings.qdrant_path)
        
        # Ensure collection exists
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create conversation memory collection if it doesn't exist"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.COLLECTION_NAME not in collection_names:
                # Create collection with 384 dimensions (all-MiniLM-L6-v2)
                self.qdrant_client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=384,
                        distance=Distance.COSINE
                    )
                )
                print(f"✓ Created conversation memory collection: {self.COLLECTION_NAME}")
            else:
                print(f"✓ Conversation memory collection exists: {self.COLLECTION_NAME}")
        except Exception as e:
            print(f"✗ Error ensuring collection: {e}")
    
    def store_conversation(
        self,
        user_id: str,
        session_id: str,
        question: str,
        answer: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a conversation turn in Qdrant
        
        Args:
            user_id: Unique identifier for the user
            session_id: Session identifier (chat ID)
            question: User's question
            answer: System's answer
            metadata: Additional metadata (collections searched, sources, etc.)
        
        Returns:
            Conversation ID
        """
        # Create conversation text (combine question and answer for better retrieval)
        conversation_text = f"Q: {question}\nA: {answer}"
        
        # Generate embedding
        embedding = self.embedding_model.encode(conversation_text).tolist()
        
        # Create unique ID
        conversation_id = str(uuid.uuid4())
        
        # Create payload with metadata
        payload = {
            'conversation_id': conversation_id,
            'user_id': user_id,
            'session_id': session_id,
            'question': question,
            'answer': answer,
            'conversation_text': conversation_text,
            'timestamp': datetime.now().isoformat(),
        }
        
        # Add optional metadata
        if metadata:
            payload.update(metadata)
        
        # Create point
        point = PointStruct(
            id=conversation_id,
            vector=embedding,
            payload=payload
        )
        
        # Insert into Qdrant
        try:
            self.qdrant_client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[point]
            )
            return conversation_id
        except Exception as e:
            print(f"Error upserting conversation to Qdrant: {e}")
            import traceback
            print(traceback.format_exc())
            raise
    
    def get_relevant_conversations(
        self,
        current_question: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant past conversations based on current question
        
        Args:
            current_question: Current user question
            user_id: Filter by user ID (optional)
            session_id: Filter by session ID (optional)
            limit: Maximum number of conversations to retrieve
            score_threshold: Minimum similarity score (default: 0.5, lower to get more results)
        
        Returns:
            List of relevant conversations with metadata
        """
        try:
            # Generate embedding for current question
            query_embedding = self.embedding_model.encode(current_question).tolist()
            
            # Build filter
            query_filter = None
            if user_id or session_id:
                conditions = []
                if user_id:
                    conditions.append(
                        FieldCondition(key="user_id", match=MatchValue(value=user_id))
                    )
                if session_id:
                    conditions.append(
                        FieldCondition(key="session_id", match=MatchValue(value=session_id))
                    )
                
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # Search Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            conversations = []
            for result in search_results:
                conversations.append({
                    'conversation_id': result.payload.get('conversation_id'),
                    'question': result.payload.get('question'),
                    'answer': result.payload.get('answer'),
                    'timestamp': result.payload.get('timestamp'),
                    'similarity_score': result.score,
                    'user_id': result.payload.get('user_id'),
                    'session_id': result.payload.get('session_id'),
                    'metadata': {k: v for k, v in result.payload.items() 
                               if k not in ['conversation_id', 'question', 'answer', 
                                           'timestamp', 'user_id', 'session_id', 'conversation_text']}
                })
            
            return conversations
        except Exception as e:
            print(f"Error in get_relevant_conversations: {e}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all conversations in a session (chronological order)
        
        Args:
            session_id: Session identifier
            limit: Maximum number of conversations
        
        Returns:
            List of conversations in chronological order
        """
        # Search with session filter
        scroll_result = self.qdrant_client.scroll(
            collection_name=self.COLLECTION_NAME,
            scroll_filter=Filter(
                must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        
        points = scroll_result[0]
        
        # Convert to list and sort by timestamp
        conversations = []
        for point in points:
            conversations.append({
                'conversation_id': point.payload.get('conversation_id'),
                'question': point.payload.get('question'),
                'answer': point.payload.get('answer'),
                'timestamp': point.payload.get('timestamp'),
            })
        
        # Sort by timestamp (oldest first)
        conversations.sort(key=lambda x: x.get('timestamp', ''))
        
        return conversations
    
    def get_recent_sessions(
        self,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent chat sessions with their first question and timestamp
        
        Args:
            user_id: Filter by user ID (optional)
            limit: Maximum number of sessions
        
        Returns:
            List of sessions with metadata
        """
        # Build filter
        query_filter = None
        if user_id:
            query_filter = Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            )
        
        # Scroll through all conversations
        scroll_result = self.qdrant_client.scroll(
            collection_name=self.COLLECTION_NAME,
            scroll_filter=query_filter,
            limit=1000,  # Get many to find unique sessions
            with_payload=True,
            with_vectors=False
        )
        
        points = scroll_result[0]
        
        # Group by session_id and get first question for each
        sessions_dict = {}
        for point in points:
            session_id = point.payload.get('session_id')
            if not session_id:
                continue
            
            timestamp = point.payload.get('timestamp', '')
            question = point.payload.get('question', '')
            
            # If we haven't seen this session, or this is earlier, store it
            if session_id not in sessions_dict:
                sessions_dict[session_id] = {
                    'session_id': session_id,
                    'title': question[:50] + ('...' if len(question) > 50 else ''),
                    'timestamp': timestamp,
                    'user_id': point.payload.get('user_id')
                }
            else:
                # Keep the earliest timestamp
                if timestamp < sessions_dict[session_id]['timestamp']:
                    sessions_dict[session_id]['timestamp'] = timestamp
                    sessions_dict[session_id]['title'] = question[:50] + ('...' if len(question) > 50 else '')
        
        # Convert to list and sort by timestamp (newest first)
        sessions = list(sessions_dict.values())
        sessions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return sessions[:limit]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete all conversations in a session"""
        try:
            # Find all points with this session_id
            scroll_result = self.qdrant_client.scroll(
                collection_name=self.COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]
                ),
                limit=1000,
                with_payload=False,
                with_vectors=False
            )
            
            point_ids = [point.id for point in scroll_result[0]]
            
            if point_ids:
                self.qdrant_client.delete(
                    collection_name=self.COLLECTION_NAME,
                    points_selector=point_ids
                )
                print(f"✓ Deleted {len(point_ids)} conversations for session {session_id}")
                return True
            return False
        except Exception as e:
            print(f"✗ Error deleting session: {e}")
            return False
