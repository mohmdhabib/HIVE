# AGENTS.md — Permanent instructions for AI coding assistants

## Project: HIVE — Autonomous AI Media Network

### Repository overview

HIVE is a modular AI-powered media network. A Master Agent coordinates
independent niche media workers through a shared Ollama LLM runtime.

### Tech stack

| Layer | Stack |
|---|---|
| Frontend | Vite, React 18, TypeScript, Tailwind CSS, shadcn/ui, React Router, TanStack Query, Zustand, Recharts, Lucide React |
| Backend | Python, FastAPI, Pydantic, LangGraph, LangChain Ollama |
| AI | Ollama with Llama 3.1 (local), structured outputs via Pydantic |
| Database | Supabase PostgreSQL, pgvector (when justified) |
| Queue | Redis + Celery |
| Infrastructure | Docker Compose |

### Directory structure

```
HIVE/
├── backend/           Python FastAPI backend
│   ├── app/
│   │   ├── api/       Route handlers (thin — delegate to services)
│   │   ├── core/      Logging, security, middleware, exceptions
│   │   ├── master/    Master Agent LangGraph workflows
│   │   ├── models/    SQLAlchemy DB models
│   │   ├── schemas/   Pydantic request/response schemas
│   │   ├── services/  Business logic (LLM, workers, content, revenue)
│   │   ├── workers/   Worker engine, pipeline, memory
│   │   ├── integrations/  Platform adapters (Instagram, YouTube, etc.)
│   │   └── tasks/     Celery background tasks
│   └── tests/
├── frontend/          Vite + React dashboard
│   └── src/
│       ├── components/
│       │   ├── ui/        shadcn/ui primitives
│       │   └── layout/    Shell, Sidebar, Topbar
│       ├── hooks/         TanStack Query hooks
│       ├── lib/           Utilities (cn, api client)
│       ├── pages/         Route pages
│       └── stores/        Zustand stores
├── supabase/          Database migrations
├── storage/           Media files (gitignored content)
└── infrastructure/    Deployment configs
```

### Critical rules

1. **Never hardcode secrets.** Use `.env` files and Pydantic Settings.
2. **Keep API routes thin.** Business logic belongs in `services/`.
3. **All LLM outputs must be validated** with Pydantic schemas.
4. **Human approval is required** for publishing, sponsorships, and sensitive content.
5. **Worker data is stored in the database**, not hardcoded in Python.
6. **Use the shared LLM service** (`services/llm.py`) — never create direct Ollama HTTP calls.
7. **Structured logging** via `core/logging.py` — never use bare `print()`.
8. **Frontend uses the `@/` import alias** for all project imports.
9. **Frontend API calls use TanStack Query hooks** in `hooks/` — never raw `fetch` in components.
10. **Tailwind CSS only** — no inline styles, no CSS files except `index.css` base layer.

### Running locally

```powershell
# Prerequisites: Docker Desktop, Ollama with llama3.1, Node.js 20+

# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start backend
docker compose up --build

# Terminal 3: Start frontend
cd frontend && npm install && npm run dev
```

### Adding a new worker

1. Add the worker config to the database (currently `workers/registry.py`).
2. The reusable worker engine (`workers/engine.py`) handles execution.
3. No new Python class or file is needed per worker.

### Adding a platform integration

1. Create a new adapter in `backend/app/integrations/` extending `base.py`.
2. Implement the platform adapter interface.
3. Register the adapter in the platform registry.
4. Add platform-specific schemas in `schemas/platform.py`.

### Key design decisions

- **Shared model runtime**: All workers use one Ollama server with a concurrency semaphore.
- **LangGraph for orchestration**: Master Agent and worker pipelines use LangGraph state machines.
- **Revenue-first architecture**: Revenue tracking is a first-class concern, not an afterthought.
- **Approval gates**: All external actions require human approval by default.
- **Platform abstraction**: Social media integrations use a common adapter interface.

