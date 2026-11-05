# API Reference

## Base URL

Development: `http://localhost:8000/api`

## Endpoints

### Health

#### `GET /api/health`

Returns system health status including Ollama connectivity.

**Response:**
```json
{
  "status": "ok",
  "service": "hive-api",
  "ollama": {
    "ollama": "connected",
    "model": "llama3.1",
    "model_available": true,
    "available_models": ["llama3.1:latest"]
  }
}
```

### Workers

#### `GET /api/workers`

Returns all configured worker brands.

**Response:**
```json
[
  {
    "id": "tech",
    "name": "Signal Tech",
    "niche": "AI and technology",
    "audience": "Curious professionals and builders",
    "voice": "Clear, useful, curious, evidence-led",
    "objective": "Grow a trusted AI and technology audience",
    "status": "idle",
    "enabled": true
  }
]
```

### Tasks

#### `POST /api/tasks`

Delegate a task to a worker through the Master Agent.

**Request:**
```json
{
  "worker_id": "tech",
  "objective": "Research 3 timely content opportunities for this brand.",
  "require_approval": true
}
```

**Validation:**
- `objective`: 8–2000 characters
- `worker_id`: must match a registered worker

**Response:**
```json
{
  "task_id": "uuid",
  "worker_id": "tech",
  "worker_name": "Signal Tech",
  "objective": "...",
  "status": "needs_approval",
  "output": "...",
  "approval_required": true,
  "created_at": "2026-01-01T00:00:00Z"
}
```

**Error Responses:**
- `400`: Worker disabled or invalid request
- `404`: Worker not found
- `422`: Validation error (Pydantic)
- `502`: LLM service error
- `503`: Kill switch active

### Tasks & Approval Lifecycle

#### `POST /api/tasks`
Delegate a task to a worker through the Master Agent.

#### `GET /api/tasks/pending-approval`
Returns all content deliverables awaiting human operator editorial approval.

#### `POST /api/tasks/{task_id}/approve`
Approve a pending deliverable with optional reviewer notes. Moves status to `approved`.

#### `POST /api/tasks/{task_id}/reject`
Reject a pending deliverable with feedback/revision instructions.

### Memory & Learning

#### `GET /api/workers/{worker_id}/memory`
Inspect isolated worker memory (recent topic history, winning content hooks, performance logs).

#### `GET /api/workers/shared-learning`
Retrieve cross-worker strategic insights sanitized of all brand-private data or credentials.

### Content Studio

#### `POST /api/content/research`
Run automated niche trend discovery returning scored `TopicOpportunity` items.

#### `POST /api/content/generate-multi-format`
Generate multi-channel deliverables for an approved topic (short video script, X thread, carousel slides, visual asset briefs).

### Platform Integrations & Publishing

#### `GET /api/integrations/accounts`
List all connected official platform adapters, health status, and authorized OAuth2 scopes.

#### `GET /api/publishing/schedule`
Get all scheduled, pending manual dispatch, and live published content items.

#### `POST /api/publishing/schedule`
Schedule an approved deliverable to a target platform at a designated timestamp.

#### `POST /api/publishing/{item_id}/publish-now`
Attempt immediate API dispatch via official platform adapter.

#### `POST /api/publishing/{item_id}/complete-manual`
Mark a manual fallback dispatch as completed with external post URL.

### Revenue Engine (Milestone 6)

#### `GET /api/revenue/summary`
Returns global network financial overview: gross revenue, total operational costs, net profit, profit margin, and revenue breakdown by stream.

#### `GET /api/revenue/workers/{worker_id}`
Returns granular profitability, margin, and stream distribution for a specific worker brand.

#### `POST /api/revenue/events`
Record an attributable revenue event (`affiliate`, `sponsorship`, `lead_gen`, `digital_product`, `platform_rpm`). Supports idempotency.

#### `POST /api/revenue/costs`
Log an infrastructure, LLM, or production cost event.

### System Telemetry & Circuit Breaker (Milestone 7)

#### `GET /api/system/metrics`
Real-time telemetry: active workers, LLM inference latency, pending task queue depths, local storage directory write status, and audit log velocity.

#### `POST /api/system/kill-switch`
Emergency circuit breaker control (`?enabled=true` or `?enabled=false`). Instantly halts or resumes autonomous agent execution.

## Authentication

Authentication via Supabase Auth will be added in Milestone 3.
Currently all endpoints are open for local development.

