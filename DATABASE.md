# Database Schema

## Overview

HIVE uses Supabase PostgreSQL for persistence. The schema will be implemented in Milestone 3.

## Planned Tables

### `workers`
Worker brand configurations.

| Column | Type | Description |
|---|---|---|
| `id` | `text` PK | Unique worker identifier |
| `name` | `text` | Brand display name |
| `niche` | `text` | Content niche |
| `audience` | `text` | Target audience description |
| `voice` | `text` | Tone and writing guidelines |
| `objective` | `text` | Business objective |
| `status` | `text` | Current operational status |
| `enabled` | `boolean` | Whether worker can accept tasks |
| `created_at` | `timestamptz` | Creation timestamp |
| `updated_at` | `timestamptz` | Last update timestamp |

### `tasks`
Task execution history.

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` PK | Task identifier |
| `worker_id` | `text` FK | Assigned worker |
| `objective` | `text` | Task objective |
| `status` | `text` | Execution status |
| `output` | `text` | LLM-generated output |
| `approval_required` | `boolean` | Requires human approval |
| `approved_at` | `timestamptz` | When approved |
| `approved_by` | `uuid` FK | Who approved |
| `created_at` | `timestamptz` | Task creation time |
| `completed_at` | `timestamptz` | Task completion time |

### `worker_memory`
Per-worker isolated memory entries.

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` PK | Memory entry ID |
| `worker_id` | `text` FK | Owning worker |
| `category` | `text` | Memory type (topic, performance, pattern) |
| `content` | `jsonb` | Memory content |
| `created_at` | `timestamptz` | Entry timestamp |

### `audit_log`
All state-changing operations.

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` PK | Log entry ID |
| `actor` | `text` | Who performed the action |
| `action` | `text` | Action type |
| `resource_type` | `text` | What was acted on |
| `resource_id` | `text` | Resource identifier |
| `details` | `jsonb` | Action details |
| `created_at` | `timestamptz` | Timestamp |

### `revenue_events`
Revenue attribution tracking.

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` PK | Event ID |
| `worker_id` | `text` FK | Attributing worker |
| `source` | `text` | Revenue source type |
| `amount` | `decimal` | Revenue amount |
| `currency` | `text` | Currency code |
| `attribution` | `jsonb` | Attribution details |
| `verified` | `boolean` | Whether independently verified |
| `created_at` | `timestamptz` | Event timestamp |

## Row Level Security

All tables will have RLS policies requiring authenticated users. Workers cannot access other workers' memory or credentials.

## Migrations

Migrations are stored in `supabase/migrations/` and applied via the Supabase CLI.

