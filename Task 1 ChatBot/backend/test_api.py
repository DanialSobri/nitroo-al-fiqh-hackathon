"""Test script for the RAG API"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_collections():
    """Test collections endpoint"""
    print("Testing /collections endpoint...")
    response = requests.get(f"{BASE_URL}/collections")
    print(f"Status: {response.status_code}")
    print(f"Collections: {response.json()}")
    print()


def test_ask_question(question: str, collections: list = None):
    """Test ask endpoint"""
    print(f"Testing /ask endpoint with question: '{question}'...")
    
    payload = {
        "question": question,
        "max_results": 3,
        "min_score": 0.5
    }
    
    if collections:
        payload["collections"] = collections
    
    response = requests.post(
        f"{BASE_URL}/ask",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nAnswer: {data['answer']}")
        print(f"\nTotal References: {data['total_references_found']}")
        print(f"Collections Searched: {data['collections_searched']}")
        print(f"\nReferences:")
        for i, ref in enumerate(data['references'], 1):
            print(f"\n  [{i}] {ref['pdf_title']}")
            print(f"      Score: {ref['similarity_score']:.4f}")
            print(f"      Source: {ref['source']}")
            print(f"      Excerpt: {ref['chunk_text'][:200]}...")
    else:
        print(f"Error: {response.text}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print("="*60)
    print("RAG API Test Script")
    print("="*60)
    print()
    
    try:
        # Test health
        test_health()
        
        # Test collections
        test_collections()
        
        # Test questions
        test_ask_question("What is Islamic banking?")
        test_ask_question("What are the Shariah compliance requirements?", ["bnm_pdfs"])
        test_ask_question("What is sukuk?", ["all"])
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure the server is running:")
        print("  python main.py")
    except Exception as e:
        print(f"Error: {e}")
