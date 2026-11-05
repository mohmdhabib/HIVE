const API_BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

export interface WorkerRevenueTarget {
  monthly_target_usd: number;
  primary_stream: string;
  target_rpm: number;
}

export interface Worker {
  id: string;
  name: string;
  niche: string;
  audience: string;
  voice: string;
  objective: string;
  content_pillars?: string[];
  revenue_target?: WorkerRevenueTarget;
  status: string;
  enabled: boolean;
}

export interface ContentPiece {
  title: string;
  hook: string;
  body_script: string;
  caption: string;
  hashtags: string[];
  visual_brief: string;
  target_platform: string;
  monetization_hypothesis: string;
  factual_checks: string[];
  estimated_risk_level: "low" | "medium" | "high";
  risks_and_caveats: string[];
}

export interface QualityCheckResult {
  passed: boolean;
  score: number;
  feedback: string[];
  flags: string[];
}

export interface TopicOpportunity {
  title: string;
  hook_angle: string;
  timeliness_factor: string;
  target_audience_segment: string;
  estimated_reach_potential: "standard" | "high" | "viral";
  monetization_angle: string;
}

export interface SlideItem {
  slide_number: number;
  headline: string;
  body_text: string;
  visual_direction: string;
}

export interface ThreadPost {
  post_number: number;
  text: string;
  suggested_media?: string;
}

export interface CreativeAssetBrief {
  asset_type: "thumbnail" | "broll_video" | "carousel_slide" | "infographic";
  prompt: string;
  negative_prompt?: string;
  aspect_ratio: "9:16" | "1:1" | "16:9";
  overlay_text?: string;
  color_palette?: string[];
}

export interface MultiFormatDeliverable {
  topic: TopicOpportunity;
  worker_id: string;
  worker_name: string;
  short_video?: ContentPiece | null;
  thread_posts: ThreadPost[];
  carousel_slides: SlideItem[];
  creative_assets: CreativeAssetBrief[];
  created_at: string;
}

export interface TaskRequest {
  worker_id: string;
  objective: string;
  require_approval?: boolean;
  target_platform?: "instagram" | "youtube_shorts" | "x" | "facebook";
}

export interface TaskReport {
  task_id: string;
  worker_id: string;
  worker_name: string;
  objective: string;
  status: string;
  content?: ContentPiece | null;
  output?: string | null;
  quality_check?: QualityCheckResult | null;
  approval_required: boolean;
  priority?: "low" | "medium" | "high" | "critical";
  created_at: string;
}

export interface MemoryEntry {
  id: string;
  worker_id: string;
  category: string;
  key: string;
  content: Record<string, any>;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  actor: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, any>;
  created_at: string;
}

export interface AccountConnection {
  id: string;
  worker_id: string;
  platform: "instagram" | "youtube" | "facebook" | "twitter" | "manual";
  account_handle: string;
  display_name: string;
  status: "connected" | "disconnected" | "unauthorized" | "manual_only";
  permissions: string[];
  token_expiry?: string | null;
  created_at: string;
}

export interface ScheduledPublication {
  id: string;
  worker_id: string;
  task_id: string;
  platform: "instagram" | "youtube" | "facebook" | "twitter" | "manual";
  status: "draft" | "scheduled" | "publishing" | "published" | "failed" | "manual_required";
  scheduled_at: string;
  published_at?: string | null;
  platform_post_id?: string | null;
  platform_url?: string | null;
  error_message?: string | null;
  retry_count: number;
  manual_instructions?: string | null;
  created_at: string;
}

export interface RevenueEvent {
  id: string;
  worker_id: string;
  task_id?: string | null;
  platform: string;
  stream: "affiliate" | "sponsorship" | "lead_gen" | "digital_product" | "platform_creator_fund";
  gross_amount: number;
  currency: string;
  attribution_type: "measured" | "imported" | "estimated";
  campaign_id?: string | null;
  conversion_metadata: Record<string, any>;
  verified: boolean;
  created_at: string;
}

export interface WorkerProfitability {
  worker_id: string;
  worker_name: string;
  gross_revenue: number;
  total_costs: number;
  net_profit: number;
  profit_margin_pct: number;
  monthly_target_usd: number;
  target_progress_pct: number;
  primary_stream: string;
  measured_revenue: number;
  estimated_revenue: number;
}

export interface FinancialSummary {
  total_gross_revenue: number;
  total_costs: number;
  net_profit: number;
  profit_margin_pct: number;
  stream_breakdown: Record<string, number>;
  attribution_breakdown: Record<string, number>;
  worker_rankings: WorkerProfitability[];
  recent_events: RevenueEvent[];
}

export interface SystemMetrics {
  status: string;
  kill_switch_active: boolean;
  uptime_seconds: number;
  timestamp: string;
  llm: {
    model: string;
    endpoint: string;
    status: string;
    model_available: boolean;
    latency_ms: number;
    max_concurrency: number;
  };
  fleet: {
    total_brands: number;
    active_brands: number;
    paused_brands: number;
  };
  operations: {
    pending_approvals: number;
    completed_tasks: number;
    failed_tasks: number;
    pending_publications: number;
    manual_dispatches_needed: number;
  };
  storage: {
    volumes_mounted: boolean;
    directories: Record<string, boolean>;
  };
  security: {
    kill_switch_enforced: boolean;
    approval_gates_enforced: boolean;
    credential_isolation_enforced: boolean;
    audit_logs_count: number;
  };
}

export interface MasterStatus {
  status: string;
  kill_switch_active: boolean;
  worker_count: number;
  workers_enabled: number;
  pending_approvals_count?: number;
  model: string;
  max_concurrent: number;
}

export interface HealthStatus {
  status: string;
  service: string;
  ollama: {
    ollama: string;
    model: string;
    model_available: boolean;
    available_models?: string[];
    error?: string;
  };
}

export const api = {
  health: () => request<HealthStatus>("/health"),
  systemMetrics: () => request<SystemMetrics>("/system/metrics"),
  toggleKillSwitch: (active: boolean, reason?: string) =>
    request<{ status: string; kill_switch_active: boolean; message: string }>("/system/kill-switch", {
      method: "POST",
      body: JSON.stringify({ active, reason: reason || "Operator manual toggle" }),
    }),
  masterStatus: () => request<MasterStatus>("/master/status"),
  financialSummary: () => request<FinancialSummary>("/revenue/summary"),
  workerProfitability: (id: string) => request<WorkerProfitability>(`/revenue/workers/${id}`),
  workers: () => request<Worker[]>("/workers"),
  workerDetail: (id: string) => request<Worker>(`/workers/${id}`),
  pauseWorker: (id: string) => request<Worker>(`/workers/${id}/pause`, { method: "POST" }),
  resumeWorker: (id: string) => request<Worker>(`/workers/${id}/resume`, { method: "POST" }),
  workerMemory: (id: string, category?: string) =>
    request<MemoryEntry[]>(`/workers/${id}/memory${category ? `?category=${category}` : ""}`),
  createTask: (data: TaskRequest) =>
    request<TaskReport>("/tasks", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  listTasks: (options?: { worker_id?: string; status?: string }) => {
    const params = new URLSearchParams();
    if (options?.worker_id) params.append("worker_id", options.worker_id);
    if (options?.status) params.append("status", options.status);
    const query = params.toString() ? `?${params.toString()}` : "";
    return request<TaskReport[]>(`/tasks${query}`);
  },
  getTask: (id: string) => request<TaskReport>(`/tasks/${id}`),
  approveTask: (id: string) => request<TaskReport>(`/tasks/${id}/approve`, { method: "POST" }),
  rejectTask: (id: string, reason?: string) =>
    request<TaskReport>(`/tasks/${id}/reject${reason ? `?reason=${encodeURIComponent(reason)}` : ""}`, {
      method: "POST",
    }),
  auditLogs: () => request<AuditLogEntry[]>("/audit-logs"),
  researchTopics: (data: { worker_id: string; keyword?: string }) =>
    request<TopicOpportunity[]>("/content/research", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  generateMultiFormat: (data: { worker_id: string; topic: TopicOpportunity }) =>
    request<MultiFormatDeliverable>("/content/generate-multi-format", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  listAccounts: (worker_id?: string) => {
    const query = worker_id ? `?worker_id=${encodeURIComponent(worker_id)}` : "";
    return request<AccountConnection[]>(`/integrations/accounts${query}`);
  },
  listSchedule: (options?: { worker_id?: string; status?: string }) => {
    const params = new URLSearchParams();
    if (options?.worker_id) params.append("worker_id", options.worker_id);
    if (options?.status) params.append("status", options.status);
    const query = params.toString() ? `?${params.toString()}` : "";
    return request<ScheduledPublication[]>(`/publishing/schedule${query}`);
  },
  schedulePublication: (data: { task_id: string; platform: string; scheduled_at: string }) =>
    request<ScheduledPublication>("/publishing/schedule", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  publishNow: (schedule_id: string) =>
    request<ScheduledPublication>(`/publishing/${schedule_id}/publish-now`, {
      method: "POST",
    }),
  completeManual: (schedule_id: string, platform_url: string) =>
    request<ScheduledPublication>(`/publishing/${schedule_id}/complete-manual`, {
      method: "POST",
      body: JSON.stringify({ platform_url }),
    }),
};
