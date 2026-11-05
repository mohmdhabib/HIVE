# Development Guide

## Prerequisites

- Windows 10/11 with Docker Desktop (WSL2 backend)
- Ollama installed with `llama3.1` model
- Node.js 20+
- Python 3.11+ (for local development without Docker)

## Quick Start

### 1. Start Ollama

```powershell
ollama serve
# In another terminal, verify:
ollama list
# Pull the model if needed:
ollama pull llama3.1
```

### 2. Start the Backend

```powershell
# Copy environment config
copy .env.example .env

# Start all services
docker compose up --build
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

### 3. Start the Frontend

```powershell
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

## Project Structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed component descriptions.

## Running Tests

### Backend

```powershell
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

### Frontend

```powershell
cd frontend
npm run lint    # TypeScript type checking
npm run build   # Full build verification
```

## Docker Commands

```powershell
# Start all services
docker compose up --build

# Start in background
docker compose up -d --build

# View logs
docker compose logs -f api

# Stop all services
docker compose down

# Clean rebuild
docker compose down -v && docker compose up --build
```

## Adding a New Worker

Workers are data-driven. To add a new worker:

1. Add a new entry to the worker registry (currently in `backend/app/workers/registry.py`, will move to database in Milestone 3)
2. Define: `id`, `name`, `niche`, `audience`, `voice`, `objective`
3. The reusable worker engine handles execution automatically

## Adding a New Platform Integration

1. Create `backend/app/integrations/<platform>.py`
2. Implement the `PlatformAdapter` interface from `base.py`
3. Register the adapter in the integration registry
4. Add any platform-specific schemas

## Environment Variables

See [.env.example](.env.example) for all configuration options.

| Variable | Required | Default | Description |
|---|---|---|---|
| `OLLAMA_URL` | Yes | `http://host.docker.internal:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | Yes | `llama3.1` | Model to use for inference |
| `OLLAMA_TIMEOUT` | No | `180.0` | Inference timeout in seconds |
| `OLLAMA_MAX_CONCURRENT` | No | `2` | Max concurrent LLM requests |
| `DEBUG` | No | `false` | Enable debug logging |
| `GLOBAL_KILL_SWITCH` | No | `false` | Emergency stop all operations |
| `SUPABASE_URL` | No | — | Supabase project URL |
| `SUPABASE_ANON_KEY` | No | — | Supabase anonymous key |
| `SUPABASE_SERVICE_ROLE_KEY` | No | — | Supabase service role key |

