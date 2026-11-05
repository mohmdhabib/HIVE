# Changelog

All notable changes to the HIVE project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.14.0] - 2026-11-06

### Added
- **Real 30 FPS Motion Video Engine & Footage Compositor (Beyond Static Boxes)**
  - **Eliminated Static Cards**: Replaced static Pillow box graphics with a dual-layer video compositor:
    1. **Real Motion Background Footage**:
       - Added `MaterialService` (`app/services/material_service.py`) supporting real Pexels stock video downloads via search keywords (`PEXELS_API_KEY`).
       - Built a 30 FPS procedural kinetic motion engine generating dynamic cyber grids, downward perspective grids, sweeping laser scanlines, floating glowing particle fields, and pulsing neural node connections.
    2. **Transparent Subtitle & HUD Layer**:
       - Centered kinetic Hormozi/MrBeast subtitles with active keyword highlight capsules overlaid directly on the moving footage.
       - Emotional beat badges (`★ HOOK`, `★ REVELATION`, `★ CTA`) and brand telemetry watermarks.
    3. **FFmpeg Multi-Layer Video Compositing**:
       - Composites moving video background + transparent subtitle overlay + mixed audio (cadence voiceover + lo-fi BGM) into crisp 1080×1920 30 FPS MP4 video.
  - **Verified Output**: Produced real 25.5s motion video [vbp-ddf956ab5438.mp4](file:///e:/HIVE/storage/videos/vbp-ddf956ab5438.mp4) (12.52 MB).

## [0.13.0] - 2026-11-06

### Added
- **Dynamic Ken Burns Video Motion Engine & Live Render Progress HUD**
  - **FFmpeg Ken Burns Camera Motion (`zoompan`)**:
    - Upgraded `VideoRenderService` (`app/services/video_renderer.py`) with continuous cinematic camera motion on every scene using FFmpeg's `zoompan` filter (`1.0x` to `1.15x` slow drift with 30 FPS `yuv420p` encoding).
  - **Multi-Track Audio Mixing (Voiceover + Lo-Fi Ambiance)**:
    - Added speech cadence synthesis timed to sentence length and syllable count with natural vocal inflection.
    - Added ambient lo-fi synthwave chord progression (A minor sub-bass, harmonic pads, and rhythmic hi-hat ticks).
    - Integrated FFmpeg `amix` to duck background music at `-18dB` beneath the narration track.
  - **Asynchronous Background Rendering**:
    - `POST /api/video/render` now starts an asynchronous background daemon thread and returns immediately with a tracking job ID.
    - `GET /api/video/render/{job_id}` streams live progress percentage (`0% -> 100%`) and human-readable step descriptions.
  - **Live Render HUD & Phase Stepper**:
    - Upgraded `frontend/src/pages/video-studio.tsx` with a real-time progress monitor that polls every 700ms during rendering.
    - Displays glowing progress bar, active phase indicator (`1. Scene Graph`, `2. Speech Cadence`, `3. Ken Burns Motion`, `4. H.264 Assembly`), and auto-switches to the Smartphone Player upon completion.
  - **Automated Verification**:
    - Real render execution completed in 5.0 seconds generating 16.57 MB 1080×1920 MP4 video.
    - 42/42 backend unit tests passing in 3.92s.
    - `npm run build` passing in 3.21s with zero errors.

## [0.12.0] - 2026-11-06

### Added
- **Obsidian Glass Design System & Studio UX Overhaul**
  - **Cyber-Minimalist Design Tokens**:
    - Upgraded `frontend/tailwind.config.ts` and `frontend/src/index.css` with dark obsidian glass card surfaces (`#0d111a`, `#111622`), radial warm amber back-glows (`#f5a623`), and blur-enhanced borders.
  - **Sleek Smartphone Chassis Mockup**:
    - Overhauled the Video Player in `frontend/src/pages/video-studio.tsx` with a physical smartphone mockup (curved bezels, titanium rim, top Dynamic Island notch, animated bottom overlay badges).
    - Added an **Interactive Scene Seeker** that computes scene second offsets and seeks the HTML5 player to individual emotional beats on click.
    - Added **Production Telemetry** cards with resolution (1080×1920), H.264/AAC encoding, and FFmpeg v7.1 specifications.
  - **Cross-Studio Trend Bridge**:
    - Added `preloadedTrend` state in Zustand `useAppStore`.
    - Content Studio live trend cards now feature a 1-click **"⚡ VIDEO ENGINE"** button that transfers live trends directly to the 9:16 Video Engine.
  - **In-Queue Video Verification**:
    - Upgraded `frontend/src/pages/approval-queue.tsx` to automatically detect rendered `.mp4` video files in task deliverables and display an inline vertical player so human operators can watch the exact video before authorizing publication.
  - **Mission Control Overview**:
    - Upgraded `frontend/src/pages/overview.tsx` with mission control hero banner, 24h impression telemetry, 3s retention hold metrics, and active creator fleet cards.
    - Upgraded `Topbar` with dynamic Llama 3.1 latency telemetry and emergency kill-switch toggle.
  - **Build Verification**:
    - Zero TypeScript errors (`npm run build` passing in 3.3s).
    - 42/42 backend unit tests passing (`python -m pytest backend/tests/test_units.py`).

## [0.11.0] - 2026-11-05

### Added
- **Autonomous Video Rendering Pipeline & Studio Player**
  - **FFmpeg 7.1 Composite Rendering Engine**:
    - Created `VideoRenderService` (`app/services/video_renderer.py`) providing automated end-to-end rendering of 1080x1920 HD MP4 short videos into `storage/videos/`.
    - Scene card synthesis with Pillow: Brand gradient backgrounds, glassmorphism headers, emotional beat badges, kinetic typography, and Hormozi/MrBeast active-word subtitle highlight boxes.
    - Neural and synthetic audio synchronization with FFmpeg.
    - Automated thumbnail generation into `storage/images/`.
  - **FastAPI Static Media Serving**:
    - Mounted `/storage` in `app/main.py` allowing instant streaming, playback, and direct downloading of rendered videos.
  - **REST API Endpoints**:
    - `POST /api/video/render`: Triggers physical MP4 rendering from a Video Production Blueprint.
    - `GET /api/video/render/{job_id}`: Real-time progress polling.
    - `GET /api/video/library`: Lists all produced videos in the storage vault.
  - **Interactive Studio Video Player**:
    - Built a dark-mode 9:16 vertical video player in `frontend/src/pages/video-studio.tsx`.
    - Direct MP4 download button and 1-click dispatch to the Master Approval Queue.
    - Video Vault tab allowing operators to browse, rewatch, and download past renders.
  - **Automated Verification**:
    - 42/42 tests passing with 0 failures (`backend/tests/test_units.py`).

## [0.10.0] - 2026-11-05

### Added
- **Master Agent Daily Executive Standup & Attention Director**
  - **Executive Standup Briefing**:
    - Created `MasterBriefingService` (`app/services/master_briefing.py`) acting as Chief Content Officer speaking directly to the Human Operator.
    - Evaluates the 5 niche media brands over the trailing 24h, analyzing attention metrics, 3s hook retention benchmarks, and virality versus hook fatigue.
    - Synthesizes diagnosed root causes (e.g., contrasting Signal Tech's high-retention contrarian warnings against Curiosity Daily's passive trivia fatigue).
    - Formulates tailored strategy pivots and proposed daily hook formulas for each worker brand.
  - **Master Agent Briefing API**:
    - `GET /api/master/briefing`: Returns the structured daily standup and per-worker directive matrix.
    - `POST /api/master/briefing/generate`: Re-runs LLM synthesis over live signals.
    - `POST /api/master/briefing/approve`: 1-click authorization that dispatches daily directives to all 5 creator agents.
  - **Master Agent Operations UI**:
    - Enhanced `MasterAgentPage` (`src/pages/master-agent.tsx`) with daily standup executive card, spoken AI message, winner/flop status badges, and 1-click directive dispatch.

## [0.9.0] - 2026-11-05

### Added
- **Video Intelligence Engine & Studio (Beyond MoneyPrinterTurbo)**
  - **Advanced Story Arc & Retention Modelling**:
    - Created `app/schemas/video.py` introducing `SceneNode`, `EmotionalBeat` (`hook`, `tension`, `revelation`, `escalation`, `payoff`, `cta`), and `RetentionZone` (`critical`, `build`, `core`, `close`).
    - Added `BrandIdentity` registry with unique color palettes, typography, neural voices (Edge-TTS IDs), and pacing speed multipliers per worker brand.
    - Added `HookVariant` generator with 3 psychologically distinct hook archetypes (Contrarian, Curiosity Gap, Stat Shock) for pre-publish A/B testing.
    - Added `ViralityScorecard` predicting 3s retention, pacing quality, visual variety, and audio energy.
  - **Video Engine Service & REST API**:
    - Created `VideoIntelligenceEngine` (`app/services/video_engine.py`) and endpoints `POST /api/video/blueprint` and `GET /api/video/render/{id}`.
  - **Video Production Studio UI**:
    - Created `VideoStudioPage` (`src/pages/video-studio.tsx`) with interactive timeline, scene inspector, A/B hook comparison, brand palette preview, thumbnail builder, and full script view.
    - Added to primary sidebar navigation (`/video-studio`).
  - **Automated Tests**:
    - 40/40 tests passing with 0 failures (`backend/tests/test_units.py`).

## [0.8.0] - 2026-11-05

### Added
- **Live Trend Research Service & Real-Time Signal Ingestion**
  - **Multi-Source Signal Ingestion**:
    - Created `LiveTrendResearchService` (`app/services/trend_research.py`) collecting live signals from Hacker News API, Reddit public JSON endpoints (r/technology, r/startups, r/todayilearned, etc.), and Google Trends RSS search velocity feeds.
    - Zero-scraping, zero-paid API dependencies with resilient fallback cache for offline/restricted environments.
  - **Pydantic Trend & Hook Schemas**:
    - Created `app/schemas/trend.py` defining `LiveTrendItem`, `AnalyzedTrendOpportunity`, `TrendSource`, `HookArchetype` (`contrarian`, `curiosity_gap`, `urgent_warning`, `stat_paradox`, `speed_breakdown`), and `NicheTrendDigest`.
  - **REST API Endpoints**:
    - `GET /api/trends/live`: Gathers real-time trending signals tailored to the worker brand's niche.
    - `POST /api/trends/analyze`: Uses Ollama Llama 3.1 to transform raw trend items into 3-second scroll-stopping hooks and monetization proposals.
  - **Content Studio Live Ingestion UI**:
    - Updated `ContentStudioPage` (`src/pages/content-studio.tsx`) with dual mode toggle: **LIVE WEB SIGNALS** vs **KEYWORD BRAINSTORM**.
    - Live trend cards showing source badges (Reddit, HackerNews, Google Trends), upvote/comment counts, external links, and 1-click selection into the multi-format video scripting pipeline.
  - **Automated Tests**:
    - 34/34 backend tests passing with 0 failures (`backend/tests/test_units.py`).

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

