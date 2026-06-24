# Flipkart Customer Care Chatbot – Full Stack

A production-ready chat interface built with **React + Vite** (frontend) and **FastAPI + OpenAI** (backend), featuring:

- 🤖 **LLM-powered responses** via OpenAI API
- 📚 **Retrieval-Augmented Generation (RAG)** using ChromaDB
- 💾 **Memory management** with mem0
- 🎨 **Modern React UI** with message history and source citations
- ⚡ **Fast development** with Vite HMR

## Quick Start (5 minutes)

### Terminal 1: Start Backend

```bash
cd backend

# Activate virtual environment
myenv\scripts\activate

# Ensure OPENAI_API_KEY is set (or configured in backend/.env)
# Then start FastAPI
python -m uvicorn app.main:app --reload
```

Backend runs on: `http://127.0.0.1:8000`

### Terminal 2: Start Frontend (Dev Mode)

```bash
cd frontend

npm install  # First time only
npm run dev
```

Frontend dev server runs on: `http://localhost:5173`

Visit **`http://localhost:5173`** in your browser and start chatting!

---

## Deployment (Production Build)

### Option A: Monolithic (Recommended)

```bash
# 1. Build React frontend
cd frontend
npm run build

# 2. Start backend (serves frontend + API)
cd ../backend
myenv\scripts\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open: `http://your-server:8000`

### Option B: Separate Services

**Backend** (with CORS enabled):
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend** (Vite preview or static hosting):
```bash
cd frontend
npm run preview
```

---

## Architecture

```
┌─────────────────────────────────────┐
│         React Frontend              │
│  (localhost:5173 or :8000/static)  │
└────────────────────┬────────────────┘
                     │ POST /chat
                     ↓
┌─────────────────────────────────────┐
│         FastAPI Backend             │
│        (:8000/chat endpoint)        │
├─────────────────────────────────────┤
│  • Chat Service                     │
│  • RAG (ChromaDB)                   │
│  • Query Rewriter                   │
│  • Memory Service (mem0)            │
│  • LLM Client (OpenAI)              │
└────────────┬─────────────────────────┘
             │
    ┌────────┴────────┐
    ↓                 ↓
  [ChromaDB]         [OpenAI]
  (Vector Store)     (API)
```

---

## Features & Components

### Frontend UI
- **Message list** with user/assistant bubbles
- **Source citations** below answers
- **User ID tracking** for session context
- **Real-time loading** and error handling
- **Responsive design** (mobile-first)

### Backend Services
- **Chat API** (`POST /chat`) – Main endpoint
- **Chat Service** – Orchestration & response formatting
- **RAG Pipeline** – Document ingestion, chunking, embeddings, retrieval
- **Memory Service** – Persistent conversation context (mem0)
- **Query Rewriter** – Intent/question enhancement
- **OpenAI LLM Client** – Endpoint to OpenAI API

---

## File Structure

```
flipkart-customer-care-chatbot/
├── frontend/                  # React + Vite
│   ├── src/
│   │   ├── App.jsx           # Main UI component
│   │   ├── App.css           # Chat styles
│   │   ├── index.css         # Global styles
│   │   └── main.jsx
│   ├── dist/                 # Build output (production bundle)
│   ├── package.json
│   └── vite.config.js
│
├── backend/                   # FastAPI
│   ├── app/
│   │   ├── main.py           # Entry point + static mount
│   │   ├── api/
│   │   │   └── chat.py       # /chat route
│   │   ├── services/
│   │   │   ├── chat_service.py
│   │   │   ├── memory_service.py
│   │   │   ├── query_rewriter.py
│   │   │   └── chat_history_service.py
│   │   ├── rag/
│   │   │   ├── ingestion_pipeline.py
│   │   │   ├── retriever.py
│   │   │   ├── embeddings.py
│   │   │   ├── vector_store.py
│   │   │   ├── chunker.py
│   │   │   └── prompt_builder.py
│   │   ├── llm/
│   │   │   ├── openai_client.py
│   │   │   └── ollama_client.py
│   │   └── schemas/
│   │       └── chat.py       # Pydantic models
│   ├── data/
│   │   └── docs/             # FAQ, policies (markdown)
│   ├── chroma_db/            # Vector database
│   ├── mem0_storage/         # Memory storage
│   ├── requirements.txt
│   ├── ingest.py
│   ├── test_*.py             # Test files
│   └── myenv/                # Python venv
│
├── FRONTEND_SETUP.md         # Detailed frontend docs
├── README.md                 # This file
└── .gitignore
```

---

## Environment Setup

### Prerequisites
- **Node.js** v16+ (for frontend)
- **Python** 3.9+ (for backend)
- **OpenAI API key**
- **ChromaDB** (installed via pip)

### Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Node Dependencies
```bash
cd frontend
npm install
```

---

## Configuration

### API Endpoint (Frontend)
Edit `frontend/.env.local`:
```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### OpenAI Configuration (Backend)
Create `backend/.env` from `backend/.env.example` and set:
```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_MEMORY_LLM_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_RAG_EMBEDDING_MODEL=text-embedding-3-small
```

After switching embedding providers/models, re-ingest docs to keep vector dimensions consistent:
```bash
cd backend
python ingest.py
```

### Database Paths (Backend)
- **ChromaDB**: `backend/chroma_db/`
- **Memory**: `backend/mem0_storage/`

---

## Testing

### Health Check
```bash
curl http://127.0.0.1:8000/health
# {"status":"healthy"}
```

### Chat Endpoint
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test-user","question":"What is the return policy?"}'

# Response:
# {"answer":"...","sources":["return_policy.md","faq.md"]}
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **"Cannot GET /" on frontend** | Run `npm run build` in frontend folder, ensure backend is running |
| **CORS errors** | Backend CORS is open; check network tab for actual error |
| **Empty chat responses** | Verify OPENAI_API_KEY is set, check backend logs for API/auth errors |
| **Port 8000/5173 in use** | Change port: `uvicorn app.main:app --port 8001` or `npm run dev -- --port 5174` |
| **Vector DB errors** | Delete `backend/chroma_db/` and re-run ingestion: `python ingest.py` |

---

## Development Workflow

### Adding Features
1. **Backend**: Modify files in `backend/app/`, restart uvicorn (`--reload` watches changes)
2. **Frontend**: Modify files in `frontend/src/`, Vite HMR auto-refreshes

### Building for Production
```bash
# 1. Frontend
cd frontend
npm run build

# 2. Optionally, add backend environment variables
cd ../backend
export OPENAI_API_KEY="your_openai_api_key_here"

# 3. Run backend (will serve frontend + API)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Performance Tips

- **Caching**: Vector embeddings are cached in ChromaDB
- **Memory**: mem0 persists context across sessions
- **Query Rewriting**: Improves RAG retrieval relevance
- **Frontend**: React + Vite bundle is ~193KB gzipped (61KB)

---

## License

[Your License Here]

## Support

For issues or questions, check [FRONTEND_SETUP.md](./FRONTEND_SETUP.md) for detailed frontend documentation or backend logs for API errors.

---

**Last Updated**: 2026-06-23  
**Status**: Production Ready ✅
