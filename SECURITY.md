# Security Policy & Implementation

## Core Security Principles

1. **Defense in Depth**: Every layer (API, Agent Orchestrator, Worker Pipeline, Database) enforces its own validation and boundary limits.
2. **Credential Isolation**: Workers cannot access credentials or private data of other workers. Platform tokens are scoped strictly per worker identity.
3. **No Unrestricted Free-Form Agent Actions**: LLM outputs are strictly constrained via typed Pydantic schemas and deterministic validation.
4. **Mandatory Human-in-the-Loop (HITL)**: All publishing, commercial actions, and sensitive content decisions require explicit operator sign-off (`require_approval=True` by default).

## Global Kill Switch

HIVE includes an emergency circuit breaker:
- Setting `GLOBAL_KILL_SWITCH=true` in environment or triggering via admin route halts all autonomous worker activities immediately.
- The Master Agent validates this state as the entry point in its LangGraph execution pipeline before any task delegation occurs.

## Worker Safety Controls

- **Worker-level Pause/Resume**: Workers can be individually disabled (`enabled=False`). Any task dispatched to a paused worker throws `WorkerDisabledError` and halts cleanly.
- **Concurrency Rate Limiting**: The shared LLM service throttles simultaneous requests using an `asyncio.Semaphore` (configurable via `OLLAMA_MAX_CONCURRENT`) to prevent local compute starvation.
- **Input Sanitization**: Task objectives enforce character boundaries (`min_length=8`, `max_length=2000`) and structured schema validation.

## Supabase & Database Security (Milestone 3+)

- Row Level Security (RLS) enabled on all database tables.
- Public anon keys limited strictly to read-only non-sensitive operations.
- Service role keys restricted strictly to backend application containers.

## Revenue & Commercial Safety (Milestone 6)

- **Attribution Confidence Integrity**: Measured revenue (direct affiliate postbacks / Stripe hooks) is strictly separated from estimated or imported metrics. Fabricating or faking engagement/revenue is forbidden.
- **Commercial Claim Verification**: Any deliverable containing affiliate claims, sponsorship agreements, or commercial promotions is automatically flagged with `risk_level='high'` by the editorial evaluator, enforcing human approval before scheduling or distribution.
- **Idempotent Financial Transactions**: Revenue and cost events require an idempotency key to prevent double-counting or duplicated reconciliation entries.

## Production Hardening & Circuit Breakers (Milestone 7)

- **Instantaneous Kill-Switch REST Endpoint**: Operators can immediately toggle the network-wide kill-switch at `POST /api/system/kill-switch?enabled=true`, interrupting all active pipelines and rejecting incoming tasks.
- **Real-Time Fleet Telemetry**: System monitor continuously checks memory isolation, audit logs, disk write accessibility, and response latency to flag degraded states before failures cascade.

