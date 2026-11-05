# Changelog

All notable changes to the HIVE project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-11-05

### Added
- **Milestone 7: Production Hardening, System Telemetry & Supabase Client Integration**
  - **System Health Monitor**:
    - Built `SystemMonitorService` (`app/services/system_monitor.py`) collecting real-time operational diagnostics: active worker counts, LLM inference latency, pending task queue depths, local storage directory write status, and audit volume.
    - Global kill switch state management and emergency REST control: `GET /api/system/metrics` and `POST /api/system/kill-switch`.
  - **Supabase Client Layer**:
    - Installed official `@supabase/supabase-js` SDK.
    - Added `frontend/src/utils/supabase.ts` and `frontend/src/lib/supabase.ts` configured from `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`.
    - Added `frontend/src/vite-env.d.ts` for strict Vite environment typing.
  - **Frontend Diagnostics & Settings**:
    - Built `SystemHealthPage` (`src/pages/system-health.tsx`): Real-time fleet health cards, database status, LLM ping, queue backlog, and emergency kill-switch controls.
    - Built `SettingsPage` (`src/pages/settings.tsx`): Fleet operational configuration, LLM parameters, retry policies, and platform defaults.
  - **Verification & QA**:
    - 31 automated tests passing synchronously in under 0.1s (`backend/tests/test_units.py`).
    - Clean TypeScript production build (`vite build`) producing minified production bundle.

## [0.6.0] - 2026-11-05

### Added
- **Milestone 6: Revenue Engine & Attributable Monetization**
  - **Revenue & Financial Schemas**:
    - Created `app/schemas/revenue.py` defining `RevenueStreamType` (`affiliate`, `sponsorship`, `lead_gen`, `digital_product`, `platform_rpm`), `AttributionConfidence` (`measured`, `imported`, `estimated`), `RevenueEvent`, `CostEvent`, `WorkerProfitability`, and `FinancialSummary`.
  - **Attribution & Cost Service**:
    - Built `RevenueService` (`app/services/revenue_service.py`):
      - Ingests revenue events attributed to worker, platform, campaign, and content piece.
      - Tracks infrastructure, LLM generation, and creative asset costs.
      - Calculates net revenue, net profit margin, and performance rankings per worker.
    - Mounted REST endpoints in `app/api/routes.py`:
      - `GET /api/revenue/summary`: Global network financial breakdown (gross, costs, net, margin, stream shares).
      - `GET /api/revenue/workers/{worker_id}`: Granular worker profitability and stream distribution.
      - `POST /api/revenue/events`: Record new measured or imported revenue events with idempotency.
      - `POST /api/revenue/costs`: Log production and operational costs.
  - **Revenue & Analytics Frontend**:
    - Built `RevenuePage` (`src/pages/revenue.tsx`): Financial overview cards, stream distribution breakdown, worker profitability leaderboard, and recent attributable transaction ledger.
    - Enhanced `AnalyticsPage` (`src/pages/analytics.tsx`): Platform reach distribution and worker brand attention benchmarks.

## [0.5.0] - 2026-11-05

### Added
- **Milestone 5: Social Media Platform Integrations & Distribution Queue**
  - **Platform Adapters & Abstraction**:
    - Created `PlatformAdapter` ABC (`app/integrations/base.py`) standardizing `check_eligibility`, `publish`, `get_manual_instructions`, and `fetch_analytics`.
    - `InstagramAdapter` (`app/integrations/instagram.py`): Meta Graph API v20.0 adapter checking `instagram_content_publish` scopes.
    - `YouTubeAdapter` (`app/integrations/youtube.py`): YouTube Data API v3 adapter for YouTube Shorts.
    - `TwitterAdapter` (`app/integrations/twitter.py`): X API v2 adapter for thread publishing.
    - `FacebookAdapter` (`app/integrations/facebook.py`): Meta Graph Pages adapter.
    - `ManualPublishingAdapter` (`app/integrations/manual.py`): Universal sanctioned fallback formatting clean copy-paste instructions with retention hook, formatted captions, hashtags, and monetization URLs.
  - **Publishing & Scheduling Service**:
    - Built `PublishingService` (`app/services/publishing_service.py`) enforcing mandatory human approval gates before scheduling any deliverable.
    - Added API endpoints: `GET /api/integrations/accounts`, `GET /api/publishing/schedule`, `POST /api/publishing/schedule`, `POST /api/publishing/{id}/publish-now`, `POST /api/publishing/{id}/complete-manual`.
  - **Frontend Experience**:
    - Built `PublishingPage` (`src/pages/publishing.tsx`): Real-time queue showing scheduled, live, and manual required posts, with 1-click publishing, manual dispatch copy-paste tools, and quick-schedule for approved content.
    - Built `IntegrationsPage` (`src/pages/integrations.tsx`): Overview of all official platform adapters, required OAuth2 scopes, connection status, zero-scraping policy, and worker account mappings.

## [0.4.0] - 2026-11-05

### Added
- **Milestone 4: Multi-Format Content Production Pipeline**
  - **Multi-Format Schemas**:
    - `TopicOpportunity`: Headline, hook angle, timeliness factor, audience segment, reach potential (`standard`, `high`, `viral`), and monetization angle.
    - `SlideItem`: Educational carousel slide structure with visual direction.
    - `ThreadPost`: Numbered social post for X/Twitter threads within character limits.
    - `CreativeAssetBrief`: Generative AI image/video prompts (Midjourney, Flux, SDXL) with aspect ratio control (`9:16`, `1:1`, `16:9`), overlay copy, and color palettes.
    - `MultiFormatDeliverable`: Aggregated content deliverable package.
  - **Content Pipeline Service**:
    - Built `ContentPipelineService` (`app/services/content_pipeline.py`) providing automated trend research, topic generation, and multi-format packaging.
    - Added API endpoints: `POST /api/content/research` and `POST /api/content/generate-multi-format`.
  - **Content Studio UI**:
    - Built `ContentStudioPage` (`src/pages/content-studio.tsx`):
      - Step 1: Automated topic discovery with keyword filtering and virality tags.
      - Step 2: Tabbed multi-format preview (Short Video script, Twitter Thread, Carousel slides, Creative Prompts).
      - Step 3: Direct dispatch to the Master Agent Approval Queue.

## [0.3.0] - 2026-11-05

### Added
- **Milestone 3: Persistence, Worker Memory & Approval Lifecycle**
  - **Database Migration**:
    - Created `supabase/migrations/001_initial_schema.sql` with tables for `workers`, `tasks`, `content_pieces`, `worker_memory`, `audit_logs`, and `revenue_events`.
    - Seeded initial 5 workers with content pillars and revenue targets.
    - Added Row Level Security (RLS) policies for service role and authenticated users.
  - **Worker Memory Engine**:
    - Built `WorkerMemoryService` (`app/services/memory.py`) providing per-worker isolated memory for topic history, winning hooks, and failed patterns.
    - Implemented cross-worker pattern learning that anonymizes and sanitizes patterns across brands without credential or private data leakage.
    - Injected topic history into the worker execution pipeline to eliminate topic repetition.
  - **Persistent Task Execution & Approval Store**:
    - Built `TaskStoreService` (`app/services/task_store.py`) managing task lifecycle (`needs_approval`, `completed`, `failed`).
    - Added API endpoints: `GET /api/tasks`, `GET /api/tasks/{id}`, `POST /api/tasks/{id}/approve`, `POST /api/tasks/{id}/reject`.
  - **Audit Logging**:
    - Built `AuditLogService` (`app/services/audit.py`) and `GET /api/audit-logs` recording security and state transitions.
  - **Frontend Operations**:
    - Fully operational `ApprovalQueuePage` (`src/pages/approval-queue.tsx`) with real-time pending list, full deliverable breakdown, and 1-click Approve / Reject with custom feedback.
    - Fully operational `WorkerDetailsPage` (`src/pages/worker-details.tsx`) displaying worker memory inspector, historical tasks, and operator pause/resume controls.

## [0.2.0] - 2026-11-05

### Added
- **Milestone 2: Master Agent & Reusable Worker Engine**
  - **Structured Deliverable Schemas**:
    - `ContentPiece`: Structured Pydantic schema containing internal title, 3s retention hook, full body script, caption, contextual hashtags, visual brief, target platform, monetization attribution hypothesis, factual checks needed, and risk assessment (`app/schemas/content.py`).
    - `QualityCheckResult`: Quality scoring (0.0 to 1.0), editorial feedback, and human attention flags.
    - `TaskPlan`: Dynamic task priority (`low`, `medium`, `high`, `critical`), token budget calculation, and approval gates.
  - **Master Agent State Machine**:
    - 5-node stateful LangGraph (`app/master/agent.py`):
      1. `check_kill_switch`: Circuit breaker.
      2. `prioritize_and_plan`: Channel and keyword priority scoring (`app/master/strategy.py`).
      3. `validate_assignment`: Worker readiness and brand voice alignment check.
      4. `delegate_to_worker`: Worker pipeline invocation.
      5. `evaluate_report`: Post-execution quality audit, forcing approval on high-risk content or unverified facts (`app/master/evaluator.py`).
  - **Reusable Worker Pipeline**:
    - 4-node LangGraph pipeline (`app/workers/pipeline.py`):
      1. `research_and_angle`: Brand pillar and audience alignment.
      2. `generate_content_piece`: Pydantic structured JSON inference via Ollama (`app/services/llm.py`).
      3. `quality_and_factuality_check`: Rule-based and risk scoring.
      4. `compile_task_report`: Packaging into typed report.
  - **Richer Brand Identity Registry**:
    - Enhanced all 5 workers with content pillars, monthly revenue targets ($1,500 to $3,000/mo), and primary monetization streams (affiliate, sponsorships, digital products).
  - **Frontend Experience**:
    - Full structured deliverable viewer on `OverviewPage`: Dedicated cards for 3-Second Retention Hook, Script/Narration, Social Caption & Hashtags, Visual Brief, Monetization Hypothesis, Factuality Check badges, and Risk Level warnings.
    - Upgraded `WorkersPage`: Full directory view displaying brand niche, audience, voice, content pillars, and monthly revenue targets.
    - Upgraded `MasterAgentPage`: Visual pipeline cards showing all 5 nodes of the LangGraph state machine, live runtime status, and concurrency control metrics.

## [0.1.0] - 2026-11-05

### Added
- **Milestone 0: Complete Repository Audit**
  - Architecture breakdown, component readiness matrix, security and dependency risks.
- **Milestone 1: Production Foundation Architecture**
  - **Backend Core**:
    - Centralized Pydantic Settings configuration (`app/config.py`).
    - Structured logging pipeline (`app/core/logging.py`).
    - Domain exception hierarchy (`app/core/exceptions.py`).
    - FastAPI dependency injection (`app/dependencies.py`).
  - **LLM Engine & Master Agent**:
    - Concurrency-controlled shared Ollama service with `asyncio.Semaphore` (`app/services/llm.py`).
    - LangGraph Master Agent state machine with kill-switch circuit breaker and assignment validation (`app/master/agent.py`).
    - Reusable worker execution engine with structured telemetry (`app/workers/engine.py`).
  - **Frontend Modernization**:
    - Migrated UI from legacy CSS to Tailwind CSS with custom HIVE amber/gold aesthetic.
    - Set up React Router with 12 operational routes: Overview, Master Agent, Workers, Worker Details, Content Studio, Approval Queue, Publishing, Analytics, Revenue, Integrations, System Health, Settings.
    - Added TanStack Query hooks for asynchronous API fetching and mutation.
    - Added Zustand global application state store.
  - **Infrastructure & Testing**:
    - Docker Compose configuration updated with Redis 7 Alpine cache/queue and container health checks.
    - Pytest automated test harness with API test cases in `backend/tests/test_health.py`.
    - Complete documentation suite: `AGENTS.md`, `ARCHITECTURE.md`, `DEVELOPMENT.md`, `API.md`, `DATABASE.md`, `DEPLOYMENT.md`, `SECURITY.md`, `TESTING.md`, `ROADMAP.md`, `CHANGELOG.md`.

