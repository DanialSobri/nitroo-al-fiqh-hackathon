"""
Verify and inspect the Qdrant database contents.
"""

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import json

def main():
    import sys
    
    # Check if server mode is requested
    use_server = "--server" in sys.argv or "-s" in sys.argv
    
    if use_server:
        print("Connecting to Qdrant server at http://localhost:6333")
        client = QdrantClient(url="http://localhost:6333")
    else:
        print("Connecting to local Qdrant database")
        client = QdrantClient(path="./qdrant_db")
    
    # Get collection info
    try:
        collection_info = client.get_collection("bnm_pdfs")
        print(f"Collection: bnm_pdfs")
        print(f"Total points: {collection_info.points_count}")
        print(f"Status: {collection_info.status}")
        print()
        
        # Get a sample of points
        print("Fetching sample points...")
        points, _ = client.scroll(
            collection_name="bnm_pdfs",
            limit=5,
            with_payload=True,
            with_vectors=False
        )
        
        print(f"\nSample of {len(points)} points:")
        print("=" * 80)
        
        seen_titles = set()
        for point in points:
            payload = point.payload
            title = payload.get('pdf_title', 'Unknown')
            
            if title not in seen_titles:
                seen_titles.add(title)
                print(f"\nTitle: {title}")
                print(f"Date: {payload.get('date', 'N/A')}")
                print(f"Type: {payload.get('document_type', 'N/A')}")
                print(f"URL: {payload.get('pdf_url', 'N/A')}")
                print(f"Chunk {payload.get('chunk_index', 0) + 1} of {payload.get('total_chunks', 0)}")
                print(f"Text preview: {payload.get('chunk_text', '')[:100]}...")
                print("-" * 80)
        
        # Count unique PDFs
        all_points, _ = client.scroll(
            collection_name="bnm_pdfs",
            limit=10000,
            with_payload=True,
            with_vectors=False
        )
        
        unique_pdfs = set()
        for point in all_points:
            url = point.payload.get('pdf_url', '')
            if url:
                unique_pdfs.add(url)
        
        print(f"\nSummary:")
        print(f"Total points (chunks): {collection_info.points_count}")
        print(f"Unique PDFs: {len(unique_pdfs)}")
        
        # List all unique PDFs
        print(f"\nPDFs in database:")
        for i, url in enumerate(sorted(unique_pdfs), 1):
            # Get title for this PDF
            pdf_points = [p for p in all_points if p.payload.get('pdf_url') == url]
            if pdf_points:
                title = pdf_points[0].payload.get('pdf_title', 'Unknown')
                date = pdf_points[0].payload.get('date', '')
                doc_type = pdf_points[0].payload.get('document_type', '')
                chunks = len(pdf_points)
                print(f"{i}. {title} ({chunks} chunks)")
                if date:
                    print(f"   Date: {date}, Type: {doc_type}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
