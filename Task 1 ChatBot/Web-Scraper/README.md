# Islamic Finance PDF Scraper

This project scrapes PDF documents from multiple sources:
- **BNM**: Bank Negara Malaysia Islamic Banking page
- **IIFA**: International Islamic Fiqh Academy Resolutions page

All documents are stored in a local Qdrant vector database for semantic search, with separate collections for each source.

## Features

- Web scraping to find PDF links from multiple sources
- Automatic PDF download and text extraction
- Text chunking for optimal embedding
- Vector embeddings using sentence transformers
- Local Qdrant vector database storage with separate collections per source
- Support for E-Book downloads (IIFA)

## Requirements

- Python 3.8+
- Internet connection for downloading PDFs

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the scraper with different options:

```bash
# Scrape BNM only (default)
python scraper.py

# Scrape IIFA only
python scraper.py --iifa

# Scrape both sources
python scraper.py --all

# Use Qdrant server instead of local file database
python scraper.py --server

# Combine options
python scraper.py --iifa --server
```

### What each scraper does:

**BNM Scraper** (`--bnm` or default):
1. Scrapes the BNM Islamic Banking page for PDF links
2. Downloads all found PDFs to `pdfs/bnm/` directory
3. Extracts text from each PDF
4. Creates embeddings and stores them in collection `bnm_pdfs`

**IIFA Scraper** (`--iifa`):
1. Scrapes the IIFA Resolutions page
2. Finds and downloads the "Download E-Book" PDF (contains all resolutions)
3. Finds and downloads individual resolution PDFs
4. Downloads PDFs to `pdfs/iifa/` directory
5. Extracts text from each PDF
6. Creates embeddings and stores them in collection `iifa_resolutions`

## Project Structure

```
.
├── scraper.py          # Main scraping script (BNMScraper and IIFAScraper classes)
├── requirements.txt    # Python dependencies
├── pdfs/              # Downloaded PDF files (created automatically)
│   ├── bnm/          # BNM PDFs
│   └── iifa/         # IIFA PDFs
└── qdrant_db/         # Local Qdrant database (created automatically)
```

## Configuration

The scrapers use the following collections:
- **BNM**: Collection name `bnm_pdfs` (stored in `pdfs/bnm/`)
- **IIFA**: Collection name `iifa_resolutions` (stored in `pdfs/iifa/`)

You can modify the following in `scraper.py`:
- `output_dir`: Directory to store downloaded PDFs
- `qdrant_path`: Path to Qdrant database (default: "./qdrant_db")
- `collection_name`: Qdrant collection name (per scraper)
- Embedding model: Currently using `all-MiniLM-L6-v2` (384 dimensions)

## Querying the Vector Database

### Using the Query Script

After scraping, you can query the vector database using the provided script:

```bash
python query_db.py "Islamic banking regulations" 5
```

### Using Python Code

You can also query programmatically:

```python
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Initialize
client = QdrantClient(path="./qdrant_db")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Search
query = "What are the Islamic banking regulations?"
query_vector = model.encode(query).tolist()

# Search BNM collection
results = client.search(
    collection_name="bnm_pdfs",
    query_vector=query_vector,
    limit=5
)

# Or search IIFA collection
results = client.search(
    collection_name="iifa_resolutions",
    query_vector=query_vector,
    limit=5
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Title: {result.payload['pdf_title']}")
    print(f"Chunk: {result.payload['chunk_text'][:200]}...")
    print("---")
```

### Verifying Database Contents

To verify what's stored in the database:

```bash
python verify_db.py
```

This will show:
- Total number of points (chunks) stored
- List of all PDFs with their metadata
- Sample chunks from the database

## Viewing in Qdrant Portal

**Note:** The Qdrant portal (web UI) connects to a Qdrant server, not local file-based databases. 

To view your data in the portal, you have two options:

### Option 1: Use Qdrant Server (Recommended for Portal Access)

1. Install Qdrant server: https://qdrant.tech/documentation/guides/installation/
2. Start Qdrant server: `qdrant`
3. Import your local database or use the server's API

### Option 2: Use Python Scripts (Current Setup)

The current setup uses a local file-based database (`./qdrant_db`). You can:
- Use `query_db.py` to search the database
- Use `verify_db.py` to inspect contents
- Use the Python client directly in your code

The local file-based approach is simpler and doesn't require running a server.

## Notes

- The script respects each website's structure and uses appropriate headers
- PDFs are chunked into 500-word segments with 50-word overlap
- Each chunk is stored as a separate vector in Qdrant with metadata
- BNM and IIFA documents are stored in separate collections for easy querying
- IIFA scraper attempts to download both the E-Book (all resolutions) and individual resolution PDFs
- Selenium is optional but recommended for JavaScript-heavy pages