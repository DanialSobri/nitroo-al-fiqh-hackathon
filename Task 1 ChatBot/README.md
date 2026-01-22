# Neo AI - Next‑Gen Optimized Advisor, driven by Agentic AI

A comprehensive RAG (Retrieval Augmented Generation) system for querying Islamic finance and Shariah compliance documents. The system scrapes official documents from multiple sources, indexes them in a vector database, and provides an intelligent Q&A interface powered by LLMs.

## 🎯 Project Overview

Neo AI is a full-stack application that enables users to ask questions about Islamic finance and Shariah compliance based on official documents from:

- **BNM (Bank Negara Malaysia)**: Islamic banking regulations and guidelines
- **IIFA (International Islamic Fiqh Academy)**: Resolutions and fatwas
- **SC (Securities Commission Malaysia)**: Shariah Advisory Council resolutions
- **Custom Sources**: Add and manage your own document sources dynamically

The system uses advanced RAG techniques to retrieve relevant document chunks and generate accurate, source-backed answers.

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend       │  Next.js + React + shadcn/ui
│   (Port 3000)    │  Chat Interface + Dashboard
└────────┬────────┘
         │ HTTP/REST
┌────────▼────────┐
│   Backend API   │  FastAPI + LangChain
│   (Port 8000)   │  RAG Service + LLM Integration
└────────┬────────┘
         │
┌────────▼────────┐
│  Vector DB     │  Qdrant
│  (Port 6333)   │  Document Embeddings
└────────────────┘
```

## ✨ Features

### Frontend
- 🎨 **Modern UI**: Perplexity.ai-inspired design with dark mode support
- 🏠 **Landing Page**: Beautiful landing page with feature highlights
- 💬 **Chat Interface**: Real-time Q&A with source references
- 📊 **Analytics Dashboard**: Monitor data sources and collection statistics
- 🕷️ **Web Scraper Portal**: Monitor and execute scraper jobs from the UI
- ⚙️ **Settings Page**: Configure API URL, search parameters, and manage data
- 📱 **PWA Support**: Installable as a Progressive Web App
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile
- 🎯 **Chat History**: Persistent chat history with localStorage
- 🔍 **Source Viewing**: View original documents directly from the dashboard
- 🎛️ **Collection Filtering**: Select which collections to search

### Backend
- 🔍 **RAG-based Q&A**: Retrieval Augmented Generation for accurate answers
- 📚 **Multi-Collection Search**: Search across multiple collections dynamically
- 🎯 **Advanced Retrieval**: Multi-stage retrieval, MMR diversity filtering, context compression
- 🤖 **LLM Integration**: Supports Ollama (local) and OpenAI
- 📊 **Analytics API**: Collection statistics and document metadata
- 🔗 **Reference Tracking**: Source citations with similarity scores
- ⚠️ **Error Handling**: Graceful handling of corrupted collections
- 🔄 **Background Jobs**: Asynchronous scraper execution with progress tracking

### Web Scraper
- 🌐 **Multi-Source Scraping**: BNM, IIFA, and SC document sources
- ➕ **Dynamic Source Management**: Add, edit, and delete custom scraper sources
- 📋 **Form-Based Scraping**: Support for websites that use forms to download PDFs
- 🎯 **Scraping Strategies**: Direct links, table-based, and form-based scraping
- 📥 **Automatic PDF Download**: Downloads and processes PDFs automatically
- 🔄 **Incremental Updates**: Only processes new documents
- 📊 **Vector Indexing**: Creates embeddings and stores in Qdrant
- 📅 **Date Extraction**: Extracts and tracks document dates
- 📈 **Real-Time Monitoring**: Track scraper status and progress from the UI

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (for backend and scraper)
- **Node.js 18+** (for frontend)
- **Qdrant** (vector database - can run locally or use server)
- **Ollama** (for local LLM) or **OpenAI API key** (for cloud LLM)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-fiqh
```

### 2. Set Up Web Scraper

**Option A: Using the Web Scraper Portal (Recommended)**
- Start the backend and frontend
- Navigate to the Web Scraper page from the sidebar
- Click "Start Scraping" for any source
- Monitor progress in real-time

**Option B: Using Command Line**
```bash
cd Web-Scraper
pip install -r requirements.txt

# Scrape all sources
python scraper.py --all

# Or scrape individual sources
python scraper.py --bnm      # Bank Negara Malaysia
python scraper.py --iifa      # IIFA Resolutions
python scraper.py --sc        # Securities Commission
```

### 3. Set Up Backend

```bash
cd backend
pip install -r requirements.txt

# Copy environment template
cp ENV_TEMPLATE.txt .env

# Edit .env and configure:
# - LLM_PROVIDER (ollama or openai)
# - OLLAMA_URL (if using Ollama)
# - OPENAI_API_KEY (if using OpenAI)
# - QDRANT_URL (default: http://localhost:6333)

# Run the backend
python main.py
# Or: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Set Up Frontend

```bash
cd frontend
npm install

# Create .env.local
cp env.example .env.local

# Edit .env.local and set:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Run the frontend
npm run dev
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
  - **Landing Page**: http://localhost:3000
  - **Chat**: http://localhost:3000/chat
  - **Dashboard**: http://localhost:3000/dashboard
  - **Web Scraper**: http://localhost:3000/scraper
  - **Settings**: http://localhost:3000/settings
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📁 Project Structure

```
ai-fiqh/
├── Web-Scraper/          # PDF scraping and indexing
│   ├── scraper.py        # Main scraper script
│   ├── pdfs/            # Downloaded PDFs (gitignored)
│   └── qdrant_db/        # Local Qdrant database (gitignored)
│
├── backend/              # FastAPI backend
│   ├── main.py          # FastAPI application
│   ├── rag_service.py   # RAG service with LangChain
│   ├── models.py        # Pydantic models
│   ├── config.py        # Configuration management
│   ├── ollama_llm.py    # Ollama LLM client
│   └── requirements.txt # Python dependencies
│
├── frontend/            # Next.js frontend
│   ├── app/             # Next.js app router
│   │   ├── page.tsx     # Landing page
│   │   ├── chat/        # Chat interface
│   │   ├── dashboard/   # Analytics dashboard
│   │   ├── scraper/     # Web scraper portal
│   │   └── settings/    # Settings page
│   ├── components/      # React components
│   │   ├── chat/        # Chat components
│   │   ├── sidebar/     # Sidebar components
│   │   └── ui/          # shadcn/ui components
│   ├── lib/             # Utilities and API client
│   └── public/          # Static assets
│
├── backend/              # FastAPI backend
│   ├── scraper_config.py # Scraper source management
│   ├── generic_scraper.py # Generic scraper for custom sources
│   └── scraper_sources.json # Custom scraper sources (auto-generated)
│
├── .gitignore           # Git ignore patterns
├── README.md            # This file
└── NGROK_SETUP.md       # Ngrok tunneling guide
```

## 🔧 Configuration

### Backend Configuration

See `backend/ENV_TEMPLATE.txt` for all available environment variables:

**Key Settings:**
- `LLM_PROVIDER`: `ollama` (default) or `openai`
- `OLLAMA_URL`: Ollama server URL (default: `https://example.com.my/`)
- `OLLAMA_MODEL`: Model name (default: `phi4:14b`)
- `QDRANT_URL`: Qdrant server URL (default: `http://localhost:6333`)
- `OPENAI_API_KEY`: Required if using OpenAI

### Frontend Configuration

See `frontend/env.example`:

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: `http://localhost:8000`)

## 📚 Documentation

### Component READMEs

- **[Backend README](backend/README.md)**: Backend API documentation
- **[Frontend README](frontend/README.md)**: Frontend setup and features
- **[Web Scraper README](Web-Scraper/README.md)**: Scraper usage and configuration

### Additional Guides

- **[Ngrok Setup](NGROK_SETUP.md)**: Guide for exposing the app via ngrok
- **[PWA Setup](frontend/PWA_SETUP.md)**: Progressive Web App configuration
- **[Context Window Strategies](backend/CONTEXT_WINDOW_STRATEGIES.md)**: RAG optimization techniques
- **[Payload Optimization](backend/PAYLOAD_OPTIMIZATION.md)**: API payload size reduction

## 🛠️ Development

### Running in Development Mode

**Backend (with auto-reload):**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (with hot reload):**
```bash
cd frontend
npm run dev
```

### Testing

**Backend API:**
```bash
cd backend
python test_api.py
```

**Manual Testing:**
- Use the Swagger UI at http://localhost:8000/docs
- Test chat interface at http://localhost:3000

## 🌐 Deployment

### Using Ngrok (Development/Testing)

See [NGROK_SETUP.md](NGROK_SETUP.md) for detailed instructions.

**Quick Setup:**
1. Start backend ngrok: `ngrok http 8000`
2. Update `frontend/.env.local` with backend ngrok URL
3. Start frontend ngrok: `ngrok http 3000`
4. Access via frontend ngrok URL

### Production Deployment

**Backend:**
- Deploy to cloud service (AWS, GCP, Azure)
- Use production-grade Qdrant server
- Set up proper CORS origins
- Use environment variables for secrets

**Frontend:**
- Build: `npm run build`
- Deploy to Vercel, Netlify, or similar
- Set `NEXT_PUBLIC_API_URL` to production backend URL

## 🔍 API Endpoints

### Main Endpoints

- `POST /ask` - Ask a question and get RAG-based answer
- `GET /collections` - Get list of available collections
- `GET /analytics` - Get collection statistics
- `GET /collections/{name}/documents` - Get documents in a collection
- `GET /health` - Health check

### Scraper Endpoints

- `GET /scraper/status` - Get current scraper status
- `POST /scraper/start` - Start a scraper job
- `GET /scraper/sources` - Get all scraper sources (default + custom)
- `POST /scraper/sources` - Add a new custom scraper source
- `PUT /scraper/sources/{source_id}` - Update a custom scraper source
- `DELETE /scraper/sources/{source_id}` - Delete a custom scraper source

See http://localhost:8000/docs for full API documentation.

## 🎨 Features in Detail

### Landing Page
- Hero section with gradient styling
- Feature highlights
- Call-to-action buttons
- Modern, responsive design

### Chat Interface
- Real-time question answering
- Source references with similarity scores
- Expandable reference sections
- Chat history persistence
- Collection filtering (select which collections to search)
- Uses saved settings for max results and min score

### Dashboard
- Collection statistics (documents, chunks, PDFs)
- Last updated timestamps
- Document list with view links
- System information (Qdrant status, embedding model)

### Web Scraper Portal
- **Real-Time Monitoring**: View scraper status and progress
- **Execute Jobs**: Start scraping for any source with one click
- **Add Custom Sources**: Add new websites to scrape
  - Direct links scraping
  - Table-based scraping
  - Form-based scraping (with form selectors)
- **Edit Sources**: Update existing custom sources
- **Delete Sources**: Remove custom sources
- **Progress Tracking**: Visual progress bar during execution
- **Error Handling**: Clear error messages and suggestions

### Settings Page
- **API Configuration**: Change backend API URL
- **Search Settings**: Configure max results and min similarity score
- **Default Collections**: Set default collections for new chats
- **Data Management**: Clear chat history
- **Import/Export**: Backup and restore settings
- **Reset**: Reset all settings to defaults

### RAG Features
- Multi-stage retrieval (coarse-to-fine)
- MMR (Maximal Marginal Relevance) diversity filtering
- Context compression for large documents
- Smart truncation and prioritization
- Configurable similarity thresholds
- Graceful error handling for corrupted collections
- Failed collection reporting

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
- Check Qdrant is running: `curl http://localhost:6333/health`
- Verify environment variables in `.env`
- Check Python dependencies: `pip install -r requirements.txt`

**Frontend can't connect to backend:**
- Verify `NEXT_PUBLIC_API_URL` in `.env.local` or check Settings page
- Check backend is running on port 8000
- Check CORS settings in backend
- Update API URL in Settings page if changed

**No search results:**
- Verify documents are scraped and indexed
- Check Qdrant collections exist
- Lower `min_score` threshold in Settings or API request
- Check if collections are selected in sidebar

**Collection errors (OffsetOutOfBounds):**
- Collection may be corrupted
- Re-scrape the affected collection from Web Scraper portal
- System will continue working with other collections

**Scraper not working:**
- Check if Selenium is installed for form-based scraping
- Verify website URLs are accessible
- Check form selectors are correct for form-based sources
- Review scraper status in the portal

**Service worker errors:**
- Normal in development mode
- Service workers only work in production builds

See component-specific troubleshooting guides:
- [Backend Troubleshooting](backend/TROUBLESHOOTING.md)
- [Frontend Troubleshooting](frontend/TROUBLESHOOTING.md)

## 🆕 Recent Updates

### Version 2.0 Features

- ✨ **Landing Page**: Beautiful new landing page with feature highlights
- 🕷️ **Web Scraper Portal**: Monitor and execute scraper jobs from the UI
- ➕ **Dynamic Source Management**: Add, edit, and delete custom scraper sources
- 📋 **Form-Based Scraping**: Support for websites using forms to download PDFs
- ⚙️ **Settings Page**: Comprehensive settings management
- 🎯 **Improved Error Handling**: Graceful handling of collection errors
- 🔄 **Background Jobs**: Asynchronous scraper execution with progress tracking
- 📊 **Collection Management**: Better collection filtering and selection

### How to Add Custom Scraper Sources

1. Navigate to **Web Scraper** page
2. Click **"Add Source"** button
3. Fill in the form:
   - **Source Name**: Display name
   - **Website URL**: Base URL to scrape
   - **Collection Name**: Qdrant collection name
   - **Scraping Strategy**: Choose from:
     - Direct Links (default)
     - Table Based
     - Form Based (requires form selectors)
4. For form-based scraping, provide:
   - **Form Selector**: CSS selector (e.g., `#download-file`)
   - **Form Button Selector**: CSS selector for submit button (optional)
5. Click **"Add Source"** to save

### Settings Configuration

Access the Settings page to configure:
- **API URL**: Change backend API endpoint
- **Max Results**: Number of references per query (1-20)
- **Min Score**: Similarity threshold (0.0-1.0)
- **Default Collections**: Collections to search by default
- **Data Management**: Clear chat history
- **Import/Export**: Backup and restore settings

## 📝 License

[Add your license here]

## 👥 Contributors

[Add contributors here]

## 🙏 Acknowledgments

- **Bank Negara Malaysia** for Islamic banking documents
- **International Islamic Fiqh Academy** for resolutions
- **Securities Commission Malaysia** for Shariah Advisory Council resolutions
- **Qdrant** for vector database
- **LangChain** for RAG framework
- **Next.js** and **shadcn/ui** for frontend framework

## 📞 Support

For issues and questions:
- Check component-specific READMEs
- Review troubleshooting guides
- Check API documentation at `/docs`
- Use the Settings page to configure API connections

---

**Built with ❤️ for Islamic Finance and Shariah Compliance**
