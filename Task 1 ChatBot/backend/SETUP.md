# Setup Guide for RAG API Backend

## Step-by-Step Setup Instructions

### Step 1: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

3. Verify the Qdrant path is correct (should point to your Web-Scraper/qdrant_db):
   ```
   QDRANT_PATH=../Web-Scraper/qdrant_db
   ```

### Step 3: Verify Qdrant Database

Make sure you have scraped documents and they are stored in Qdrant:

```bash
# From Web-Scraper directory
cd ../Web-Scraper
python scraper.py --all  # Scrape all sources
```

Verify collections exist:
```bash
python verify_db.py
```

### Step 4: Start the API Server

**Option A: Using Python directly**
```bash
cd backend
python main.py
```

**Option B: Using uvicorn directly**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Option C: Using the run script (Windows)**
```bash
cd backend
run.bat
```

**Option D: Using the run script (Linux/Mac)**
```bash
cd backend
chmod +x run.sh
./run.sh
```

### Step 5: Verify the API is Running

1. Open your browser and go to: `http://localhost:8000/docs`
2. You should see the Swagger UI with API documentation
3. Test the health endpoint: `http://localhost:8000/health`

### Step 6: Test the API

**Using the test script:**
```bash
cd backend
python test_api.py
```

**Using curl:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Islamic banking?",
    "collections": ["all"],
    "max_results": 5
  }'
```

**Using Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/ask",
    json={
        "question": "What are the Shariah compliance requirements?",
        "collections": ["bnm_pdfs"]
    }
)

print(response.json())
```

## Troubleshooting

### Issue: "OPENAI_API_KEY is required"

**Solution:** Make sure you've created `.env` file and set your OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-key-here
```

### Issue: "Collection does not exist"

**Solution:** Run the scraper first to populate the database:
```bash
cd ../Web-Scraper
python scraper.py --all
```

### Issue: "Failed to load collection"

**Solution:** 
1. Check that the Qdrant database path is correct in `.env`
2. Verify collections exist using `verify_db.py`
3. Make sure the path is relative to the backend directory

### Issue: Port already in use

**Solution:** Change the port in `.env`:
```
API_PORT=8001
```

Or kill the process using port 8000.

### Issue: Import errors

**Solution:** Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

If you get LangChain import errors, try:
```bash
pip install --upgrade langchain langchain-community langchain-openai
```

## Next Steps

Once the API is running:

1. **Integrate with frontend**: The API is ready to be consumed by your frontend
2. **Customize prompts**: Edit the prompt in `rag_service.py` to customize answer format
3. **Add authentication**: Add API keys or OAuth for production
4. **Deploy**: Deploy to your preferred hosting platform

## API Endpoints Summary

- `GET /` - Root endpoint with API info
- `GET /health` - Health check
- `GET /collections` - List available collections
- `POST /ask` - Ask a question and get answer with references
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Example Questions to Test

- "What is Islamic banking?"
- "What are the requirements for sukuk?"
- "What is the Shariah ruling on digital currency?"
- "What are the Islamic finance regulations in Malaysia?"
- "What is the difference between conventional and Islamic banking?"
