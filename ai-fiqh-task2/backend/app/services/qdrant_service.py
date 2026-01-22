from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime
from app.config import settings

class QdrantService:
    def __init__(self):
        self.client = None
        self._connect()
    
    def _connect(self):
        try:
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port
            )
            self._ensure_collections()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Qdrant: {str(e)}")
    
    def _ensure_collections(self):
        collections = [
            settings.qdrant_contracts_collection,
            settings.qdrant_regulations_collection
        ]
        
        existing_collections = [col.name for col in self.client.get_collections().collections]
        
        for collection_name in collections:
            if collection_name not in existing_collections:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=settings.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
    
    def insert_contract_chunks(
        self,
        contract_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: Dict
    ) -> int:
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            payload = {
                "contract_id": contract_id,
                "chunk_index": idx,
                "text": chunk,
                "filename": metadata.get("filename", ""),
                "created_at": datetime.utcnow().isoformat()
            }
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            ))
        
        self.client.upsert(
            collection_name=settings.qdrant_contracts_collection,
            points=points
        )
        return len(points)
    
    def insert_regulation(
        self,
        regulation_id: str,
        title: str,
        content: str,
        embedding: List[float],
        category: Optional[str] = None,
        reference: Optional[str] = None
    ):
        payload = {
            "regulation_id": regulation_id,
            "title": title,
            "content": content,
            "category": category,
            "reference": reference,
            "created_at": datetime.utcnow().isoformat()
        }
        
        point = PointStruct(
            id=regulation_id,
            vector=embedding,
            payload=payload
        )
        
        self.client.upsert(
            collection_name=settings.qdrant_regulations_collection,
            points=[point]
        )

    def update_contract_status(self, contract_id: str, score: float, category: str, status_summary: str, full_report: Optional[Dict] = None):
        # Find the first chunk (metadata holder)
        results = self.client.scroll(
            collection_name=settings.qdrant_contracts_collection,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="contract_id", match=MatchValue(value=contract_id)),
                    FieldCondition(key="chunk_index", match=MatchValue(value=0))
                ]
            ),
            limit=1
        )
        
        if not results[0]:
            return
            
        point = results[0][0]
        
        # Update payload
        new_payload = point.payload.copy()
        new_payload.update({
            "compliance_score": score,
            "compliance_category": category,
            "compliance_summary": status_summary,
            "last_checked_at": datetime.utcnow().isoformat()
        })
        
        # Store full report if provided
        if full_report:
            new_payload["compliance_report"] = full_report
        
        self.client.set_payload(
            collection_name=settings.qdrant_contracts_collection,
            payload=new_payload,
            points=[point.id]
        )
    
    def get_contract_report(self, contract_id: str) -> Optional[Dict]:
        # Get the first chunk which contains metadata
        results = self.client.scroll(
            collection_name=settings.qdrant_contracts_collection,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="contract_id", match=MatchValue(value=contract_id)),
                    FieldCondition(key="chunk_index", match=MatchValue(value=0))
                ]
            ),
            limit=1,
            with_payload=True,
            with_vectors=False
        )
        
        if not results[0]:
            return None
        
        point = results[0][0]
        return point.payload.get("compliance_report")
    
    def search_similar_regulations(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: float = 0.5
    ) -> List[Dict]:
        results = self.client.search(
            collection_name=settings.qdrant_regulations_collection,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        
        return [
            {
                "id": result.id,
                "score": result.score,
                **result.payload
            }
            for result in results
        ]
    
    def get_contract_chunks(self, contract_id: str) -> List[Dict]:
        results = self.client.scroll(
            collection_name=settings.qdrant_contracts_collection,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="contract_id",
                        match=MatchValue(value=contract_id)
                    )
                ]
            ),
            limit=100
        )
        
        return [
            {
                "id": point.id,
                **point.payload
            }
            for point in results[0]
        ]
    
    def get_all_regulations(self) -> List[Dict]:
        results = self.client.scroll(
            collection_name=settings.qdrant_regulations_collection,
            limit=100
        )
        
        return [
            {
                "id": point.id,
                **point.payload
            }
            for point in results[0]
        ]
    
    def get_all_contracts(self) -> List[Dict]:
        # Optimize by getting only the first chunk of each contract
        results = self.client.scroll(
            collection_name=settings.qdrant_contracts_collection,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="chunk_index",
                        match=MatchValue(value=0)
                    )
                ]
            ),
            limit=100,
            with_payload=True,
            with_vectors=False
        )
        
        return [
            {
                "contract_id": point.payload.get("contract_id"),
                "filename": point.payload.get("filename"),
                "created_at": point.payload.get("created_at"),
                "compliance_score": point.payload.get("compliance_score"),
                "compliance_category": point.payload.get("compliance_category"),
                "compliance_summary": point.payload.get("compliance_summary"),
                "last_checked_at": point.payload.get("last_checked_at"),
                "has_report": point.payload.get("compliance_report") is not None,
                "user_rating": point.payload.get("user_rating"),
                "scholar_status": point.payload.get("scholar_status"),
                "scholar_submitted_at": point.payload.get("scholar_submitted_at")
            }
            for point in results[0]
        ]
    
    def update_contract_rating(self, contract_id: str, rating: int):
        """Update user rating for a contract (1 for thumbs up, -1 for thumbs down, 0 for neutral)"""
        # Find the first chunk (metadata holder)
        results = self.client.scroll(
            collection_name=settings.qdrant_contracts_collection,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="contract_id", match=MatchValue(value=contract_id)),
                    FieldCondition(key="chunk_index", match=MatchValue(value=0))
                ]
            ),
            limit=1
        )
        
        if not results[0]:
            raise ValueError(f"Contract {contract_id} not found")
            
        point = results[0][0]
        
        # Update payload with rating
        new_payload = point.payload.copy()
        new_payload["user_rating"] = rating
        new_payload["rated_at"] = datetime.utcnow().isoformat()
        
        self.client.set_payload(
            collection_name=settings.qdrant_contracts_collection,
            payload=new_payload,
            points=[point.id]
        )
    
    def submit_to_scholar(self, contract_id: str, notes: Optional[str] = None) -> Dict:
        """Submit contract for scholar review"""
        # Find the first chunk (metadata holder)
        results = self.client.scroll(
            collection_name=settings.qdrant_contracts_collection,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="contract_id", match=MatchValue(value=contract_id)),
                    FieldCondition(key="chunk_index", match=MatchValue(value=0))
                ]
            ),
            limit=1
        )
        
        if not results[0]:
            raise ValueError(f"Contract {contract_id} not found")
            
        point = results[0][0]
        
        # Update payload with scholar submission status
        new_payload = point.payload.copy()
        new_payload["scholar_status"] = "pending"
        new_payload["scholar_submitted_at"] = datetime.utcnow().isoformat()
        if notes:
            new_payload["scholar_notes"] = notes
        
        self.client.set_payload(
            collection_name=settings.qdrant_contracts_collection,
            payload=new_payload,
            points=[point.id]
        )
        
        return {
            "contract_id": contract_id,
            "status": "pending",
            "submitted_at": new_payload["scholar_submitted_at"]
        }
    
    def get_analytics_data(self) -> Dict:
        """Get analytics data from all contracts"""
        contracts = self.get_all_contracts()
        
        total_contracts = len(contracts)
        compliant = sum(1 for c in contracts if c.get("compliance_category") == "compliant")
        partial = sum(1 for c in contracts if c.get("compliance_category") == "partially_compliant")
        non_compliant = sum(1 for c in contracts if c.get("compliance_category") == "non_compliant")
        
        scores = [c.get("compliance_score") for c in contracts if c.get("compliance_score") is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        thumbs_up = sum(1 for c in contracts if c.get("user_rating") == 1)
        thumbs_down = sum(1 for c in contracts if c.get("user_rating") == -1)
        
        # Calculate satisfaction rate
        total_ratings = thumbs_up + thumbs_down
        satisfaction = (thumbs_up / total_ratings * 100) if total_ratings > 0 else 0
        
        # Get top violations from stored reports
        violation_counts = {}
        for contract in contracts:
            report = self.get_contract_report(contract.get("contract_id"))
            if report and "violations" in report:
                for violation in report["violations"]:
                    title = violation.get("regulation_title", "Unknown")
                    violation_counts[title] = violation_counts.get(title, 0) + 1
        
        top_violations = [
            {"regulation": reg, "count": count}
            for reg, count in sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Compliance trend (by date)
        trend_data = {}
        for contract in contracts:
            created_date = contract.get("created_at", "")[:10] if contract.get("created_at") else "Unknown"
            if created_date not in trend_data:
                trend_data[created_date] = {"date": created_date, "compliant": 0, "partial": 0, "non_compliant": 0}
            
            category = contract.get("compliance_category")
            if category == "compliant":
                trend_data[created_date]["compliant"] += 1
            elif category == "partially_compliant":
                trend_data[created_date]["partial"] += 1
            elif category == "non_compliant":
                trend_data[created_date]["non_compliant"] += 1
        
        compliance_trend = sorted(trend_data.values(), key=lambda x: x["date"])
        
        return {
            "total_contracts": total_contracts,
            "total_compliant": compliant,
            "total_partially_compliant": partial,
            "total_non_compliant": non_compliant,
            "avg_compliance_score": round(avg_score, 2),
            "total_thumbs_up": thumbs_up,
            "total_thumbs_down": thumbs_down,
            "rating_satisfaction": round(satisfaction, 2),
            "top_violations": top_violations,
            "compliance_trend": compliance_trend
        }
    
    def health_check(self) -> Dict:
        try:
            collections_info = self.client.get_collections()
            existing_collections = [col.name for col in collections_info.collections]
            
            return {
                "connected": True,
                "collections": {
                    settings.qdrant_contracts_collection: settings.qdrant_contracts_collection in existing_collections,
                    settings.qdrant_regulations_collection: settings.qdrant_regulations_collection in existing_collections
                }
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }

qdrant_service = QdrantService()
