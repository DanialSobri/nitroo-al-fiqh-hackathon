"""
Query script to search the Qdrant vector database for BNM PDFs.
"""

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import sys


class BNMQuery:
    def __init__(self, qdrant_path: str = None, qdrant_url: str = None, collection_name: str = "bnm_pdfs"):
        self.collection_name = collection_name
        
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        print("Connecting to Qdrant...")
        # Prefer URL (server) over path (local file)
        if qdrant_url:
            self.client = QdrantClient(url=qdrant_url)
            print(f"Connected to Qdrant server at: {qdrant_url}")
        elif qdrant_path:
            self.client = QdrantClient(path=qdrant_path)
            print(f"Using local Qdrant database at: {qdrant_path}")
        else:
            # Default to server if available, otherwise local
            try:
                self.client = QdrantClient(url="http://localhost:6333")
                print("Connected to Qdrant server at: http://localhost:6333")
            except:
                self.client = QdrantClient(path="./qdrant_db")
                print("Using local Qdrant database at: ./qdrant_db")
    
    def search(self, query: str, limit: int = 5):
        """Search the vector database"""
        print(f"\nSearching for: '{query}'")
        print("-" * 60)
        
        # Generate query embedding
        query_vector = self.embedding_model.encode(query).tolist()
        
        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )
        
        if not results:
            print("No results found.")
            return
        
        # Display results
        for idx, result in enumerate(results, 1):
            print(f"\n[Result {idx}] (Similarity: {result.score:.4f})")
            print(f"PDF Title: {result.payload.get('pdf_title', 'Unknown')}")
            
            # Display metadata if available
            if result.payload.get('date'):
                print(f"Date: {result.payload.get('date')}")
            if result.payload.get('document_type'):
                print(f"Type: {result.payload.get('document_type')}")
            
            print(f"PDF URL: {result.payload.get('pdf_url', 'Unknown')}")
            print(f"Chunk {result.payload.get('chunk_index', 0) + 1} of {result.payload.get('total_chunks', 0)}")
            print(f"\nText excerpt:")
            chunk_text = result.payload.get('chunk_text', '')
            print(f"{chunk_text[:300]}..." if len(chunk_text) > 300 else chunk_text)
            print("-" * 60)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python query_db.py '<search query>' [limit] [--server]")
        print("Example: python query_db.py 'Islamic banking regulations' 5")
        print("         python query_db.py 'risk management' 5 --server")
        sys.exit(1)
    
    query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] not in ['--server', '-s'] else 5
    use_server = "--server" in sys.argv or "-s" in sys.argv
    
    qdrant_url = "http://localhost:6333" if use_server else None
    qdrant_path = None if use_server else "./qdrant_db"
    
    querier = BNMQuery(qdrant_url=qdrant_url, qdrant_path=qdrant_path)
    querier.search(query, limit)


if __name__ == "__main__":
    main()
