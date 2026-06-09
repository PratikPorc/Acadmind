# AcadMind

**A Unified Agentic AI System for Academic Query Resolution and Intelligent Memory Management**

AcadMind merges two complementary modules:

- **Query Assistant** — RAG-powered institutional knowledge chat (Neo4j + LangChain/CrewAI)
- **Jarvis** — Screenshot OCR, event extraction, reminders, NL-to-Cypher memory queries

## Repository Structure

```
Acadmind/
├── docs/
│   ├── ARCHITECTURE.md      # System design & layer responsibilities
│   └── PHASES.md            # Phased delivery roadmap
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST routes (thin controllers)
│   │   ├── agents/          # CrewAI agent pipelines (Phase 2+)
│   │   ├── core/            # Security, shared utilities
│   │   ├── db/              # Neo4j, Redis, Supabase clients
│   │   └── models/          # Pydantic schemas
│   ├── scripts/             # Neo4j init Cypher
│   └── tests/
├── frontend/                # React + Vite + Tailwind
├── docker-compose.yml       # Neo4j + Redis
└── AcadMind_Research_Report.docx
```

## Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **Docker Desktop** (for Neo4j and Redis)
- **Supabase account** (Phase 1 — auth, free tier)
- **Google AI Studio API key** (Phase 2+ — Gemini free tier; recommended for zero-budget MVP)
- **OpenAI API key** (optional paid alternative)
- **Ollama** (optional fully local LLM, no API key)

---

## Environment Setup

### 1. Clone and enter the project

```powershell
cd C:\Projects\Acadmind
```

### 2. Start infrastructure (Neo4j + Redis)

```powershell
docker compose up -d
```

| Service | URL | Default credentials |
|---------|-----|---------------------|
| Neo4j Browser | http://localhost:7474 | `neo4j` / `acadmind_dev_password` |
| Neo4j Bolt | bolt://localhost:7687 | same |
| Redis | localhost:6379 | no password |

**Initialize graph constraints** (optional, after Neo4j is up):

```powershell
Get-Content backend\scripts\init_neo4j.cypher | docker exec -i acadmind-neo4j cypher-shell -u neo4j -p acadmind_dev_password
```

### 3. Backend configuration

```powershell
cd backend
copy .env.example .env
```

Edit `backend/.env`:

| Variable | Required (Phase 0) | Description |
|----------|-------------------|-------------|
| `NEO4J_URI` | Yes | `bolt://localhost:7687` |
| `NEO4J_PASSWORD` | Yes | Must match `docker-compose.yml` |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` |
| `SUPABASE_URL` | Phase 1 | From Supabase project settings |
| `SUPABASE_ANON_KEY` | Phase 1 | Public anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Phase 1 | Server-side key (keep secret) |
| `SUPABASE_JWT_SECRET` | Phase 1 | JWT secret from Supabase |
| `GEMINI_API_KEY` | Phase 2 | Free at [Google AI Studio](https://aistudio.google.com/apikey) |
| `LLM_PROVIDER` | Phase 2 | `gemini` (default), `openai`, or `ollama` |
| `OPENAI_API_KEY` | Optional | Paid alternative to Gemini |

Install and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs  
Health check: http://localhost:8000/api/v1/health

### 4. Frontend configuration

```powershell
cd ..\frontend
copy .env.example .env.local
```

For local dev, leave `VITE_API_BASE_URL` empty — Vite proxies `/api` to the backend.

```powershell
npm install
npm run dev
```

App: http://localhost:5173

**Parallel testing:** open `/faculty` and `/student` in two tabs — each keeps a separate login session.

### 5. Supabase setup (Phase 1)

1. Create a project at [supabase.com](https://supabase.com)
2. Copy **Project URL**, **anon key**, **service role key**, and **JWT secret** into `backend/.env`
3. Copy URL + anon key into `frontend/.env.local` as `VITE_SUPABASE_*`
4. Enable Email and/or Google auth in Supabase Authentication settings

---

## Development Phases

| Phase | Focus | Status |
|-------|-------|--------|
| **0** | Monorepo scaffold, health checks, UI shell | ✅ Current |
| **1** | Supabase auth, JWT middleware, profiles | Next |
| **2** | Query Assistant + Neo4j seed + RAG agents | Planned |
| **3** | Jarvis OCR + event extraction | Planned |
| **4** | Unified graph + NL-to-Cypher | Planned |
| **5** | Reminders + Celery + notifications | Planned |
| **6** | Docker deploy + viva demo | Planned |

See [docs/PHASES.md](docs/PHASES.md) for detailed deliverables.

---

## Zero-budget MVP stack

AcadMind is designed to run without paid APIs:

| Component | Free option | Notes |
|-----------|-------------|-------|
| **LLM (chat + vision)** | **Gemini** via [Google AI Studio](https://aistudio.google.com/apikey) | `gemini-2.0-flash` supports text + images (Jarvis screenshots) |
| **Embeddings (RAG)** | **Gemini** `text-embedding-004` | Set `EMBEDDING_PROVIDER=gemini` |
| **OCR fallback** | Tesseract / EasyOCR | Free; use before calling vision API |
| **Auth + DB** | Supabase free tier | Email/Google auth, PostgreSQL |
| **Knowledge graph** | Neo4j Docker (local) | Already in `docker-compose.yml` |
| **Task queue** | Redis Docker (local) | Already in `docker-compose.yml` |
| **Fully offline LLM** | Ollama + Llama 3 | Set `LLM_PROVIDER=ollama` (needs local GPU/RAM) |

**Gemini setup** (recommended):

1. Go to https://aistudio.google.com/apikey
2. Create an API key
3. Add to `backend/.env`:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-2.0-flash
EMBEDDING_PROVIDER=gemini
GEMINI_EMBEDDING_MODEL=models/text-embedding-004
```

4. Verify: `GET http://localhost:8000/api/v1/llm/status`

Free tier has rate limits — fine for MVP demos and viva; monitor usage in AI Studio.

---

## API Endpoints (Phase 0)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Service health (Neo4j, Redis, Supabase, LLM) |
| GET | `/api/v1/llm/status` | LLM provider configuration status |
| GET | `/api/v1/auth/status` | Auth configuration status |
| POST | `/api/v1/query/chat` | Query Assistant (stub → Phase 2) |
| POST | `/api/v1/jarvis/upload` | Screenshot upload (stub → Phase 3) |
| GET | `/api/v1/jarvis/events` | User events (stub → Phase 3) |

---

## Team

Pratik Guha Roy · Swapnil Kobi · Eager Nandi · Sarthack Das · Reck Roy  
Techno India University, West Bengal — B.Tech CSE, 2024–2025
