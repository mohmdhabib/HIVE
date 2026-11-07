const API_BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const isFormData = typeof FormData !== "undefined" && options?.body instanceof FormData;
  const headers: Record<string, string> = {
    ...(!isFormData ? { "Content-Type": "application/json" } : {}),
    ...(options?.headers as Record<string, string> || {}),
  };
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

export interface LiveTrendItem {
  id: string;
  title: string;
  source: "hackernews" | "reddit" | "google_trends" | "rss" | "simulated";
  url?: string | null;
  niche: string;
  score: number;
  comment_count: number;
  published_at?: string | null;
  summary?: string | null;
}

export interface AnalyzedTrendOpportunity {
  source_trend_id: string;
  headline: string;
  hook_angle: string;
  hook_archetype: "contrarian" | "curiosity_gap" | "urgent_warning" | "behind_the_scenes" | "stat_paradox" | "speed_breakdown";
  audience_appeal: string;
  virality_score: number;
  monetization_hypothesis: string;
  suggested_formats: string[];
}

export interface NicheTrendDigest {
  worker_id: string;
  niche: string;
  timestamp: string;
  total_signals: number;
  trends: LiveTrendItem[];
  opportunities: AnalyzedTrendOpportunity[];
}

// ---------------------------------------------------------------------------
// VIDEO INTELLIGENCE ENGINE TYPES
// ---------------------------------------------------------------------------

export interface VisualDirective {
  description: string;
  visual_type: string;
  search_keywords: string[];
  visual_metaphor?: string | null;
  camera_motion: string;
  color_mood?: string | null;
  aspect_ratio?: string | null;
}

export interface AudioDirective {
  voiceover_text: string;
  voiceover_emphasis: string[];
  voice_tone: string;
  sfx_cue?: string | null;
  music_energy: string;
  bgm_track?: string | null;
}

export interface SceneNode {
  scene_id: string;
  emotional_beat: string;
  retention_zone: string;
  duration_seconds: number;
  visual: VisualDirective;
  audio: AudioDirective;
  caption_style: string;
  transition_in: string;
  pacing_note?: string | null;
}

export interface BrandColorPalette {
  primary: string;
  secondary: string;
  accent: string;
  text_primary: string;
  text_secondary: string;
  caption_highlight: string;
  caption_background: string;
}

export interface BrandTypography {
  heading_font: string;
  body_font: string;
  caption_font: string;
  caption_size: number;
}

export interface BrandIdentity {
  worker_id: string;
  brand_name: string;
  colors: BrandColorPalette;
  typography: BrandTypography;
  default_voice: string;
  voice_speed: number;
}

export interface HookVariant {
  variant_id: string;
  variant_label: string;
  hook_text: string;
  hook_visual_description: string;
  predicted_retention_3s: number;
  hook_archetype: string;
}

export interface ThumbnailSpec {
  headline_text: string;
  subtext?: string | null;
  emotion: string;
  layout: string;
  background_image_keywords: string[];
  arrow_or_circle: boolean;
}

export interface ViralityScorecard {
  overall_score: number;
  hook_strength: number;
  pacing_quality: number;
  visual_variety: number;
  audio_energy: number;
  cta_clarity: number;
  shareability: number;
  risk_flags: string[];
  recommendation: string;
}

export interface GenerationTelemetry {
  engine_mode: "ollama_llama3.1" | "agentic_nlp_synthesizer";
  model_name: string;
  research_latency_seconds: number;
  screenplay_archetype: string;
  llm_connected: boolean;
  llm_error_reason?: string | null;
  target_audience: string;
  angle_discovered: string;
  event_trace: Array<{ timestamp: string; phase: string; message: string }>;
}

export interface VideoProductionBlueprint {
  blueprint_id: string;
  worker_id: string;
  source_trend_id?: string | null;
  title: string;
  description: string;
  scenes: SceneNode[];
  total_duration_seconds: number;
  brand: BrandIdentity;
  hook_variants: HookVariant[];
  selected_hook_variant: string;
  thumbnail: ThumbnailSpec;
  virality_score?: ViralityScorecard | null;
  telemetry?: GenerationTelemetry | null;
  hashtags: string[];
  target_platforms: string[];
  created_at?: string | null;
}

export interface SceneClipArtifact {
  scene_idx: number;
  scene_id: string;
  emotional_beat: string;
  duration_seconds: number;
  clip_path: string;
  thumbnail_path?: string | null;
  overlay_path?: string | null;
  voice_path?: string | null;
  voiceover_text: string;
  camera_motion: string;
  search_keywords: string[];
  source_asset?: string | null;
  resolved_footage_type?: string | null;
  resolved_footage_query?: string | null;
  status: "ready" | "rendering" | "failed";
}

export interface SceneUpdateRequest {
  voiceover_text?: string;
  search_keywords?: string[];
  camera_motion?: string;
  visual_description?: string;
  custom_asset_path?: string;
  caption_position?: "bottom" | "center" | "top" | "bottom_center" | "top_center";
  caption_font_size?: number;
  caption_highlight_color?: string;
  caption_style?: "pill" | "outline" | "minimal";
  sfx_cue?: string;
  voice_speed?: number;
  bgm_track?: string;
  visual_filter?: "none" | "vibrant" | "cinematic" | "cyberpunk";
  aspect_ratio?: "9:16" | "1:1" | "16:9";
}

export interface SceneReorderRequest {
  from_idx: number;
  to_idx: number;
}

export interface SceneAddRequest {
  scene_idx?: number;
  voiceover_text: string;
  search_keywords?: string[];
  camera_motion?: string;
  emotional_beat?: string;
}

export interface EnhanceScriptRequest {
  style: "punchy" | "curiosity_gap" | "controversial" | "conversational";
}

export interface SFXCatalogItem {
  id: string;
  name: string;
  category: string;
  description: string;
  duration_sec: number;
  tags: string[];
}

export interface StockMaterialItem {
  filename: string;
  asset_type: "image" | "video";
  file_path: string;
  relative_url: string;
  thumbnail_url: string;
  niche: string;
  tags: string[];
}

export interface RenderJobStatus {
  job_id: string;
  blueprint_id: string;
  worker_id: string;
  status: "queued" | "downloading_assets" | "generating_tts" | "compositing" | "encoding" | "complete" | "failed";
  progress_pct: number;
  current_step?: string | null;
  output_path?: string | null;
  thumbnail_path?: string | null;
  error_message?: string | null;
  duration_seconds?: number | null;
  file_size_mb?: number | null;
  scene_clips?: SceneClipArtifact[];
}

export interface RenderedVideoItem {
  blueprint_id: string;
  filename: string;
  video_url: string;
  thumbnail_url?: string | null;
  size_mb: number;
  created_at: string;
}

export interface VaultAsset {
  asset_id: string;
  niche: string;
  filename: string;
  asset_type: "video" | "image";
  file_path: string;
  relative_url: string;
  thumbnail_url?: string | null;
  tags: string[];
  duration_sec: number;
  width: number;
  height: number;
  source: string;
  created_at: string;
}

export interface HarvestedBlueprintDraft {
  draft_id: string;
  worker_id: string;
  worker_name: string;
  trend_title: string;
  source: string;
  virality_score: number;
  recommendation: string;
  hook_preview: string;
  blueprint_id: string;
  task_id: string;
  status: string;
  scenes_count: number;
  duration_seconds: number;
  created_at: string;
}

export interface BatchHarvestReport {
  batch_id: string;
  timestamp: string;
  total_signals_scanned: number;
  total_drafts_generated: number;
  workers_covered: string[];
  drafts: HarvestedBlueprintDraft[];
  status: string;
  execution_time_seconds: number;
}

export interface HarvesterStatus {
  status: "idle" | "running";
  schedule: {
    enabled: boolean;
    cron_expression: string;
    drafts_per_worker: number;
    last_run: string | null;
    next_run: string | null;
    last_batch_id: string | null;
    total_runs: number;
  };
  queued_drafts_count: number;
  recent_batches_count: number;
  last_batch: BatchHarvestReport | null;
}

export interface WorkerPerformanceDigest {
  worker_id: string;
  worker_name: string;
  niche: string;
  yesterday_reach: number;
  avg_3s_retention_pct: number;
  top_performing_hook?: string | null;
  top_performing_archetype: string;
  status_signal: "viral" | "high_performing" | "average" | "underperforming" | "hook_fatigue";
  diagnosis: string;
  recommended_pivot: string;
  proposed_topic: string;
  proposed_daily_hook: string;
  virality_probability: number;
}

export interface MasterExecutiveBriefing {
  briefing_id: string;
  date: string;
  headline: string;
  executive_summary: string;
  network_reach_24h: number;
  network_retention_avg_pct: number;
  viral_winners: WorkerPerformanceDigest[];
  underperformers: WorkerPerformanceDigest[];
  worker_directives: WorkerPerformanceDigest[];
  system_recommendation: string;
  status: "pending_review" | "approved" | "executing";
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
  revenueSummary: () => request<FinancialSummary>("/revenue/summary"),
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
  pendingTasks: () => request<TaskReport[]>("/tasks?status=needs_approval"),
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
  liveTrends: (worker_id: string = "tech", limit: number = 8) =>
    request<LiveTrendItem[]>(`/trends/live?worker_id=${encodeURIComponent(worker_id)}&limit=${limit}`),
  analyzeTrends: (data: { worker_id: string; trend_ids?: string[] }) =>
    request<NicheTrendDigest>("/trends/analyze", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  generateVideoBlueprint: (data: { worker_id: string; trend_title: string; trend_summary?: string; source_trend_id?: string }) =>
    request<VideoProductionBlueprint>("/video/blueprint", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  masterBriefing: () => request<MasterExecutiveBriefing>("/master/briefing"),
  generateMasterBriefing: () =>
    request<MasterExecutiveBriefing>("/master/briefing/generate", {
      method: "POST",
    }),
  approveMasterBriefing: () =>
    request<MasterExecutiveBriefing>("/master/briefing/approve", {
      method: "POST",
    }),
  renderVideo: (blueprint: VideoProductionBlueprint) =>
    request<RenderJobStatus>("/video/render", {
      method: "POST",
      body: JSON.stringify(blueprint),
    }),
  renderStatus: (jobId: string) => request<RenderJobStatus>(`/video/render/${encodeURIComponent(jobId)}`),
  videoLibrary: () => request<RenderedVideoItem[]>("/video/library"),
  vaultMaterials: (niche?: string) => {
    const query = niche ? `?niche=${encodeURIComponent(niche)}` : "";
    return request<VaultAsset[]>(`/materials/vault${query}`);
  },
  harvestUrl: (data: { url: string; niche?: string; tags?: string[] }) =>
    request<VaultAsset[]>("/materials/harvest-url", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  harvestBatch: (data: { niche?: string; count?: number }) =>
    request<VaultAsset[]>("/materials/harvest-batch", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  blueprintSceneClips: (blueprintId: string) =>
    request<SceneClipArtifact[]>(`/video/blueprint/${encodeURIComponent(blueprintId)}/clips`),
  getBlueprint: (blueprintId: string) =>
    request<VideoProductionBlueprint>(`/video/blueprint/${encodeURIComponent(blueprintId)}`),
  renderBlueprintById: (blueprintId: string) =>
    request<RenderJobStatus>(`/video/blueprint/${encodeURIComponent(blueprintId)}/render`, {
      method: "POST",
    }),
  stockMaterials: (worker_id?: string) => {
    const query = worker_id ? `?worker_id=${encodeURIComponent(worker_id)}` : "";
    return request<StockMaterialItem[]>(`/video/stock-materials${query}`);
  },
  regenerateSceneClip: (blueprintId: string, sceneIdx: number, data: SceneUpdateRequest) =>
    request<RenderJobStatus>(`/video/blueprint/${encodeURIComponent(blueprintId)}/scene/${sceneIdx}/render`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  reorderScene: (blueprintId: string, fromIdx: number, toIdx: number) =>
    request<RenderJobStatus>(`/video/blueprint/${encodeURIComponent(blueprintId)}/scene/reorder`, {
      method: "POST",
      body: JSON.stringify({ from_idx: fromIdx, to_idx: toIdx }),
    }),
  addScene: (blueprintId: string, data: SceneAddRequest) =>
    request<RenderJobStatus>(`/video/blueprint/${encodeURIComponent(blueprintId)}/scene/add`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  deleteScene: (blueprintId: string, sceneIdx: number) =>
    request<RenderJobStatus>(`/video/blueprint/${encodeURIComponent(blueprintId)}/scene/${sceneIdx}`, {
      method: "DELETE",
    }),
  duplicateScene: (blueprintId: string, sceneIdx: number) =>
    request<RenderJobStatus>(`/video/blueprint/${encodeURIComponent(blueprintId)}/scene/${sceneIdx}/duplicate`, {
      method: "POST",
    }),
  enhanceScript: (blueprintId: string, sceneIdx: number, style: string) =>
    request<{ original_script: string; enhanced_script: string; style: string }>(
      `/video/blueprint/${encodeURIComponent(blueprintId)}/scene/${sceneIdx}/enhance-script`,
      {
        method: "POST",
        body: JSON.stringify({ style }),
      }
    ),
  uploadAsset: async (file: File, niche: string = "tech", tags: string = "") => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("niche", niche);
    formData.append("tags", tags);
    return request<StockMaterialItem>("/video/upload-asset", {
      method: "POST",
      body: formData,
    });
  },
  sfxCatalog: () => request<SFXCatalogItem[]>("/video/sfx-catalog"),
  runAutonomousBatchHarvest: (data?: { worker_ids?: string[]; drafts_per_worker?: number; min_virality_score?: number }) =>
    request<BatchHarvestReport>("/trends/harvest-batch", {
      method: "POST",
      body: JSON.stringify(data || {}),
    }),
  getHarvesterStatus: () => request<HarvesterStatus>("/trends/harvest-batch/status"),
  updateHarvesterSchedule: (data: { enabled: boolean; cron_expression?: string; drafts_per_worker?: number }) =>
    request<HarvesterStatus["schedule"]>("/trends/harvest-batch/schedule", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};
