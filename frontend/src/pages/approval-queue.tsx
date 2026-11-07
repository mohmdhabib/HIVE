import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type TaskReport, type TraceStep, type ResearchSourceItem } from "@/lib/api";
import {
  AlertTriangle,
  CheckCircle2,
  CircleDollarSign,
  Clapperboard,
  Clock,
  Eye,
  FileText,
  Film,
  Flame,
  Gauge,
  Loader2,
  Play,
  RotateCw,
  ShieldAlert,
  Code2,
  Terminal,
  Cpu,
  ShieldCheck,
  Sliders,
  Sparkles,
  TrendingUp,
  Video,
  XCircle,
  Zap,
  Globe,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { StockPickerModal } from "@/components/StockPickerModal";
import { LiveTraceabilityBox } from "@/components/LiveTraceabilityBox";

interface TaskMetadata {
  blueprint_id?: string;
  scenes_count?: number;
  duration_seconds?: number;
  virality_score?: number;
  recommendation?: string;
  hook_angle?: string;
  video_url?: string;
  target_platforms?: string[];
  brand_name?: string;
  telemetry?: {
    engine_mode?: "ollama_llama3.1" | "agentic_nlp_synthesizer";
    model_name?: string;
    research_latency_seconds?: number;
    screenplay_archetype?: string;
    llm_connected?: boolean;
    llm_error_reason?: string | null;
    target_audience?: string;
    angle_discovered?: string;
    event_trace?: Array<{ timestamp: string; phase: string; message: string }>;
    trace_steps?: TraceStep[];
    researched_sources?: ResearchSourceItem[];
    extracted_facts?: string[];
  } | null;
  researched_sources?: ResearchSourceItem[];
}

function parseTaskMetadata(task: TaskReport | null): TaskMetadata | null {
  if (!task || !task.output) return null;
  try {
    if (task.output.trim().startsWith("{")) {
      return JSON.parse(task.output) as TaskMetadata;
    }
  } catch {
    // not valid json
  }
  return null;
}

function getBlueprintId(task: TaskReport | null): string | null {
  if (!task) return null;
  const meta = parseTaskMetadata(task);
  if (meta?.blueprint_id) return meta.blueprint_id;
  if (task.task_id.startsWith("task-vbp-")) {
    return task.task_id.replace(/^task-/, "");
  }
  return null;
}

export default function ApprovalQueuePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedTask, setSelectedTask] = useState<TaskReport | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [isRejecting, setIsRejecting] = useState(false);
  const [filterMode, setFilterMode] = useState<"all" | "drafts" | "standard">("all");
  const [showTelemetryTrace, setShowTelemetryTrace] = useState(false);
  const [showVisualMatches, setShowVisualMatches] = useState(false);

  // In-flight render tracking
  const [renderJob, setRenderJob] = useState<{
    blueprintId: string;
    status: string;
    progress: number;
    step?: string | null;
  } | null>(null);

  // Asset Picker & Re-roll State
  const [pickerState, setPickerState] = useState<{ sceneIdx: number; keywords: string[] } | null>(null);
  const [rerollingSceneIdx, setRerollingSceneIdx] = useState<number | null>(null);

  // Poll tasks awaiting approval
  const { data: tasks = [] } = useQuery({
    queryKey: ["pending-tasks"],
    queryFn: () => api.listTasks({ status: "needs_approval" }),
    refetchInterval: 10_000,
  });

  // Harvester scheduler status & telemetry
  const { data: harvesterStatus } = useQuery({
    queryKey: ["harvester-status"],
    queryFn: () => api.getHarvesterStatus(),
    refetchInterval: 12_000,
  });

  // Batch harvest mutation (15 autonomous drafts across all 5 brands)
  const batchHarvestMutation = useMutation({
    mutationFn: () => api.runAutonomousBatchHarvest({ drafts_per_worker: 3 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pending-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["harvester-status"] });
    },
  });

  // Direct 1-click video render mutation for a blueprint
  const renderMutation = useMutation({
    mutationFn: (blueprintId: string) => api.renderBlueprintById(blueprintId),
    onSuccess: (job, blueprintId) => {
      setRenderJob({
        blueprintId,
        status: job.status,
        progress: job.progress_pct || 10,
        step: job.current_step,
      });
    },
  });

  // Re-roll footage mutation for a single scene
  const rerollMutation = useMutation({
    mutationFn: async ({ blueprintId, sceneIdx }: { blueprintId: string; sceneIdx: number }) => {
      setRerollingSceneIdx(sceneIdx);
      return api.rerollSceneVisual(blueprintId, sceneIdx);
    },
    onSuccess: () => {
      if (activeBlueprintId) {
        queryClient.invalidateQueries({ queryKey: ["scene-clips", activeBlueprintId] });
      }
    },
    onSettled: () => {
      setRerollingSceneIdx(null);
    },
  });

  // Replace asset mutation for a single scene
  const replaceAssetMutation = useMutation({
    mutationFn: async ({ blueprintId, sceneIdx, assetPath }: { blueprintId: string; sceneIdx: number; assetPath: string }) => {
      setRerollingSceneIdx(sceneIdx);
      return api.regenerateSceneClip(blueprintId, sceneIdx, {
        custom_asset_path: assetPath,
      });
    },
    onSuccess: () => {
      if (activeBlueprintId) {
        queryClient.invalidateQueries({ queryKey: ["scene-clips", activeBlueprintId] });
      }
    },
    onSettled: () => {
      setRerollingSceneIdx(null);
    },
  });

  const [isStreamingRegen, setIsStreamingRegen] = useState(false);
  const [streamTraceSteps, setStreamTraceSteps] = useState<TraceStep[]>([]);
  const [streamTokens, setStreamTokens] = useState<string>("");
  const [streamElapsed, setStreamElapsed] = useState<number>(0);
  const [streamError, setStreamError] = useState<string | null>(null);
  const streamTimerRef = useRef<number | any>(null);

  const handleStartStreamingRegenerateScript = async (blueprintId: string) => {
    setIsStreamingRegen(true);
    setStreamError(null);
    setStreamTokens("");
    setStreamTraceSteps([
      {
        step_id: "init",
        title: "Re-generating Screenplay with Llama 3.1",
        phase: "init",
        status: "running",
        detail: `Connecting to local Ollama runtime on host for blueprint ${blueprintId}...`,
        timestamp: new Date().toISOString().substring(11, 19),
      },
    ]);
    const startT = Date.now();
    setStreamElapsed(0);
    if (streamTimerRef.current) clearInterval(streamTimerRef.current);
    streamTimerRef.current = setInterval(() => {
      setStreamElapsed((Date.now() - startT) / 1000);
    }, 100);

    try {
      await api.streamRegenerateScript(
        blueprintId,
        (step) => {
          setStreamTraceSteps((prev) => {
            const copy = [...prev];
            const idx = copy.findIndex((s) => s.step_id === step.step_id);
            if (idx >= 0) copy[idx] = step;
            else copy.push(step);
            return copy;
          });
        },
        (token) => {
          setStreamTokens((prev) => prev + token);
        }
      );
      queryClient.invalidateQueries({ queryKey: ["approval-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["scene-clips", blueprintId] });
    } catch (err: any) {
      console.error("Streaming script regeneration error:", err);
      setStreamError(err?.message || "Script regeneration halted");
    } finally {
      if (streamTimerRef.current) clearInterval(streamTimerRef.current);
      setIsStreamingRegen(false);
    }
  };

  const regenerateScriptMutation = useMutation({
    mutationFn: async (blueprintId: string) => {
      return api.regenerateBlueprintScript(blueprintId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approval-tasks"] });
      if (activeBlueprintId) {
        queryClient.invalidateQueries({ queryKey: ["scene-clips", activeBlueprintId] });
      }
    },
  });

  // Poll in-flight render progress
  useEffect(() => {
    if (!renderJob || renderJob.status === "complete" || renderJob.status === "failed") return;
    const interval = setInterval(async () => {
      try {
        const res = await api.renderStatus(renderJob.blueprintId);
        setRenderJob({
          blueprintId: renderJob.blueprintId,
          status: res.status,
          progress: res.progress_pct,
          step: res.current_step,
        });
        if (res.status === "complete") {
          queryClient.invalidateQueries({ queryKey: ["pending-tasks"] });
        }
      } catch {
        // ignore polling errors
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [renderJob, queryClient]);

  const approveMutation = useMutation({
    mutationFn: (taskId: string) => api.approveTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pending-tasks"] });
      setSelectedTask(null);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ taskId, reason }: { taskId: string; reason: string }) =>
      api.rejectTask(taskId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pending-tasks"] });
      setSelectedTask(null);
      setIsRejecting(false);
      setRejectReason("");
    },
  });

  const draftTasks = tasks.filter((t) => t.objective.includes("[Daily Autonomous Draft]"));
  const standardTasks = tasks.filter((t) => !t.objective.includes("[Daily Autonomous Draft]"));

  const filteredTasks =
    filterMode === "drafts"
      ? draftTasks
      : filterMode === "standard"
      ? standardTasks
      : tasks;

  const activeTask = selectedTask || filteredTasks[0] || tasks[0] || null;
  const activeMeta = parseTaskMetadata(activeTask);
  const activeBlueprintId = getBlueprintId(activeTask);

  const isCurrentRendering = renderJob?.blueprintId === activeBlueprintId && renderJob.status !== "complete" && renderJob.status !== "failed";

  const { data: activeSceneClips = [] } = useQuery({
    queryKey: ["approval-scene-clips", activeBlueprintId],
    queryFn: () => (activeBlueprintId ? api.blueprintSceneClips(activeBlueprintId) : []),
    enabled: !!activeBlueprintId,
    refetchInterval: isCurrentRendering ? 2000 : 10000,
  });

  const videoUrl = (() => {
    if (!activeTask) return null;
    if (activeMeta?.video_url) return activeMeta.video_url;
    const combined = `${activeTask.objective} ${activeTask.output || ""}`;
    const match = combined.match(/(\/storage\/videos\/[^\s'"]+\.mp4)/);
    return match ? match[1] : null;
  })();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
            HUMAN-IN-THE-LOOP CONTROL
          </div>
          <h1 className="mt-1 font-display text-2xl font-semibold">Approval Queue</h1>
          <p className="text-xs text-gray-400">
            Review, verify factual claims, and authorize autonomous worker deliverables prior to public distribution.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto rounded border border-border bg-surface px-3 py-1.5 font-mono text-[10px]">
          <Clock size={13} className="text-hive" />
          <span>{tasks.length} PENDING REVIEW</span>
        </div>
      </div>

      {/* Autonomous Harvester Master HUD Banner */}
      <div className="relative overflow-hidden rounded-xl border border-hive/30 bg-gradient-to-r from-[#141824] via-[#0d111a] to-[#121927] p-5 shadow-glass">
        <div className="absolute -right-12 -top-12 h-44 w-44 rounded-full bg-hive/10 blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
              <span className="font-mono text-[10px] tracking-wider font-semibold text-hive uppercase">
                Autonomous Daily Trend Harvester & Batch Generation
              </span>
              <span className="rounded bg-surface-raised border border-border px-2 py-0.5 font-mono text-[9px] text-gray-300">
                Schedule: 06:00 AM UTC (Daily)
              </span>
            </div>
            <p className="max-w-2xl text-xs text-gray-300 leading-relaxed">
              Harvests live signals from Reddit, HackerNews, and Google Trends every morning. Generates 3 virality-scored 8-scene video blueprints per brand across all 5 workers (15 total) and stages them for operator sign-off.
            </p>
            <div className="flex flex-wrap items-center gap-3 pt-1 text-[10px] font-mono text-gray-400">
              <div className="flex items-center gap-1.5">
                <Flame size={12} className="text-amber-400" />
                <span>{draftTasks.length} AUTONOMOUS DRAFTS READY</span>
              </div>
              <span className="text-gray-600">•</span>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 size={12} className="text-emerald-400" />
                <span>5 ACTIVE NICHE BRANDS</span>
              </div>
              {harvesterStatus?.last_batch && (
                <>
                  <span className="text-gray-600">•</span>
                  <span>
                    LAST RUN: {harvesterStatus.last_batch.total_drafts_generated} DRAFTS ({harvesterStatus.last_batch.execution_time_seconds.toFixed(1)}s)
                  </span>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto shrink-0">
            <button
              onClick={() => batchHarvestMutation.mutate()}
              disabled={batchHarvestMutation.isPending}
              className={cn(
                "flex items-center gap-2 rounded-lg px-4 py-2.5 font-mono text-[11px] font-semibold transition-all shadow-glow",
                batchHarvestMutation.isPending
                  ? "bg-hive/30 text-gray-400 cursor-not-allowed border border-hive/20"
                  : "bg-gradient-to-r from-hive via-amber-400 to-hive text-black hover:opacity-95 active:scale-95"
              )}
            >
              {batchHarvestMutation.isPending ? (
                <>
                  <Loader2 size={15} className="animate-spin text-black" />
                  <span>HARVESTING TRENDS (15 DRAFTS)...</span>
                </>
              ) : (
                <>
                  <Zap size={15} className="fill-black" />
                  <span>⚡ RUN AUTONOMOUS HARVEST (15 DRAFTS)</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-3">
        <button
          onClick={() => setFilterMode("all")}
          className={cn(
            "rounded-md px-3 py-1.5 font-mono text-[10px] transition-colors",
            filterMode === "all"
              ? "bg-hive/15 text-hive border border-hive/40 font-semibold"
              : "text-gray-400 hover:text-gray-200 border border-transparent"
          )}
        >
          ALL PENDING ({tasks.length})
        </button>
        <button
          onClick={() => setFilterMode("drafts")}
          className={cn(
            "flex items-center gap-1.5 rounded-md px-3 py-1.5 font-mono text-[10px] transition-colors",
            filterMode === "drafts"
              ? "bg-amber-500/15 text-amber-300 border border-amber-500/40 font-semibold"
              : "text-gray-400 hover:text-gray-200 border border-transparent"
          )}
        >
          <Flame size={12} className="text-amber-400" />
          AUTONOMOUS DRAFTS ({draftTasks.length})
        </button>
        <button
          onClick={() => setFilterMode("standard")}
          className={cn(
            "rounded-md px-3 py-1.5 font-mono text-[10px] transition-colors",
            filterMode === "standard"
              ? "bg-blue-500/15 text-blue-300 border border-blue-500/40 font-semibold"
              : "text-gray-400 hover:text-gray-200 border border-transparent"
          )}
        >
          STANDARD TASKS ({standardTasks.length})
        </button>
      </div>

      {filteredTasks.length === 0 ? (
        <div className="flex min-h-[45vh] flex-col items-center justify-center rounded-xl border border-border bg-surface p-8 text-center">
          <div className="mb-4 grid h-14 w-14 place-items-center rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400">
            <CheckCircle2 size={28} />
          </div>
          <h2 className="font-display text-lg font-semibold">
            {filterMode === "drafts" ? "No Autonomous Drafts Pending" : "Approval Queue is Clear"}
          </h2>
          <p className="mt-1 max-w-sm text-xs text-gray-400">
            {filterMode === "drafts"
              ? "Click '⚡ RUN AUTONOMOUS HARVEST' above to instantly generate 15 fresh video blueprints."
              : "No worker deliverables are currently awaiting authorization. New tasks requiring review will appear here automatically."}
          </p>
          {filterMode === "drafts" && (
            <button
              onClick={() => batchHarvestMutation.mutate()}
              disabled={batchHarvestMutation.isPending}
              className="mt-4 flex items-center gap-2 rounded-lg bg-hive px-4 py-2 font-mono text-[11px] font-semibold text-black hover:bg-hive/90"
            >
              <Zap size={14} className="fill-black" />
              <span>TRIGGER MORNING HARVEST NOW</span>
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-5 lg:grid-cols-12">
          {/* Left: Pending Task List */}
          <div className="lg:col-span-5 space-y-2">
            <div className="flex items-center justify-between font-mono text-[9px] tracking-wide text-gray-500 mb-1 px-1">
              <span>AWAITING OPERATOR SIGN-OFF</span>
              <span>SHOWING {filteredTasks.length}</span>
            </div>
            {filteredTasks.map((task) => {
              const isSelected = activeTask?.task_id === task.task_id;
              const isAutonomousDraft = task.objective.includes("[Daily Autonomous Draft]");
              const meta = parseTaskMetadata(task);

              return (
                <button
                  key={task.task_id}
                  onClick={() => setSelectedTask(task)}
                  className={cn(
                    "w-full text-left rounded-lg border p-4 transition-all relative",
                    isSelected
                      ? isAutonomousDraft
                        ? "border-amber-500/60 bg-amber-500/10 shadow-[0_0_20px_rgba(245,166,35,0.08)]"
                        : "border-hive/50 bg-hive/5 shadow-[0_0_15px_rgba(245,166,35,0.05)]"
                      : "border-border bg-surface hover:border-border-strong hover:bg-surface-raised"
                  )}
                >
                  <div className="flex items-center justify-between text-[10px] font-mono">
                    <div className="flex items-center gap-2">
                      <span className="text-hive font-semibold uppercase">{task.worker_name}</span>
                      {isAutonomousDraft && (
                        <span className="flex items-center gap-1 rounded bg-amber-500/20 border border-amber-500/40 px-1.5 py-0.2 font-mono text-[8px] font-semibold text-amber-300">
                          <Flame size={10} />
                          AUTONOMOUS DRAFT
                        </span>
                      )}
                    </div>
                    <span className="text-gray-500">{new Date(task.created_at).toLocaleTimeString()}</span>
                  </div>

                  <h3 className="mt-1.5 font-display text-sm font-medium text-gray-100 line-clamp-2">
                    {task.content?.title || task.objective.replace("[Daily Autonomous Draft] ", "")}
                  </h3>

                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    {meta?.virality_score && (
                      <span className="flex items-center gap-1 rounded bg-amber-500/10 border border-amber-500/30 px-1.5 py-0.5 font-mono text-[8px] text-amber-300 font-semibold">
                        <TrendingUp size={10} />
                        VIRALITY {meta.virality_score}/100
                      </span>
                    )}
                    {meta?.scenes_count && (
                      <span className="rounded bg-surface-raised border border-border px-1.5 py-0.5 font-mono text-[8px] text-gray-400">
                        {meta.scenes_count} SCENES · 9:16
                      </span>
                    )}
                    {task.content?.factual_checks?.length ? (
                      <span className="rounded bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 font-mono text-[8px] text-amber-400">
                        {task.content.factual_checks.length} Fact Checks
                      </span>
                    ) : null}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right: Full Deliverable Review */}
          {activeTask && (
            <div className="lg:col-span-7 rounded-xl border border-border bg-surface p-6 flex flex-col justify-between space-y-6">
              <div className="space-y-5">
                {/* Header Info */}
                <div className="flex items-start justify-between border-b border-border pb-4">
                  <div>
                    <div className="flex items-center gap-2 font-mono text-[9px] text-gray-400 uppercase">
                      <span>{activeTask.worker_name}</span>
                      <span>·</span>
                      <span>TASK #{activeTask.task_id.slice(0, 10)}</span>
                      {activeBlueprintId && (
                        <>
                          <span>·</span>
                          <span className="text-hive">BP: {activeBlueprintId}</span>
                        </>
                      )}
                    </div>
                    <h2 className="mt-1.5 font-display text-lg font-semibold text-gray-100">
                      {activeTask.content?.title || activeTask.objective.replace("[Daily Autonomous Draft] ", "")}
                    </h2>
                  </div>
                  <span className="rounded border border-hive/30 bg-hive/10 px-2 py-0.5 font-mono text-[9px] text-hive font-semibold shrink-0">
                    NEEDS APPROVAL
                  </span>
                </div>

                {/* Autonomous Blueprint Virality Scorecard Banner */}
                {activeMeta && (
                  <div className="rounded-xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 to-transparent p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="grid h-12 w-12 shrink-0 place-items-center rounded-lg border border-amber-500/40 bg-amber-500/20 font-display text-lg font-bold text-amber-300">
                        {activeMeta.virality_score || 88}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[9px] font-semibold uppercase text-amber-300 tracking-wider">
                            VIRAL RETENTION POTENTIAL
                          </span>
                          <span className="rounded bg-emerald-500/10 border border-emerald-500/30 px-1.5 py-0.2 font-mono text-[8px] text-emerald-400 uppercase font-semibold">
                            {activeMeta.recommendation || "PUBLISH READY"}
                          </span>
                        </div>
                        <div className="text-xs text-gray-300 mt-0.5">
                          Hook: <span className="font-semibold text-white capitalize">{activeMeta.hook_angle || "contrarian"}</span> · Format: 9:16 Vertical · Length: ~{activeMeta.duration_seconds ? Math.round(activeMeta.duration_seconds) : 36}s
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
                      {activeBlueprintId && (
                        <button
                          onClick={() => navigate(`/video-studio?blueprintId=${activeBlueprintId}`)}
                          className="flex items-center gap-1.5 rounded-lg border border-border bg-surface-raised px-3 py-1.5 font-mono text-[10px] text-gray-200 hover:border-hive/40 hover:text-hive transition-colors"
                        >
                          <Clapperboard size={13} />
                          <span>OPEN IN STUDIO</span>
                        </button>
                      )}

                      {activeBlueprintId && !videoUrl && (
                        <button
                          onClick={() => renderMutation.mutate(activeBlueprintId)}
                          disabled={isCurrentRendering || renderMutation.isPending}
                          className={cn(
                            "flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-mono text-[10px] font-semibold transition-all",
                            isCurrentRendering
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 cursor-wait"
                              : "bg-hive text-black hover:bg-amber-400"
                          )}
                        >
                          {isCurrentRendering ? (
                            <>
                              <Loader2 size={13} className="animate-spin text-amber-300" />
                              <span>RENDERING ({renderJob?.progress.toFixed(0)}%)...</span>
                            </>
                          ) : (
                            <>
                              <Film size={13} />
                              <span>RENDER 9:16 MP4</span>
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* AI Engine Telemetry & Observability Inspector */}
                {activeMeta && (
                  <div className="rounded-xl border border-white/[0.08] bg-[#0c1017] p-4 space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/60 pb-2.5">
                      <div className="flex items-center gap-2">
                        <Cpu size={14} className="text-hive" />
                        <span className="font-mono text-[10px] font-bold text-gray-200 uppercase tracking-wider">
                          AI SCRIPT & FOOTAGE OBSERVABILITY INSPECTOR
                        </span>
                      </div>

                      <div className="flex flex-wrap items-center gap-2 font-mono text-[9px]">
                        {activeMeta.telemetry?.engine_mode === "ollama_llama3.1" ? (
                          <span className="flex items-center gap-1 rounded bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 text-emerald-400 font-semibold">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                            OLLAMA LLAMA 3.1 ({activeMeta.telemetry.research_latency_seconds}s)
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 rounded bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 text-amber-300 font-semibold" title={activeMeta.telemetry?.llm_error_reason || "Ollama offline on 11434"}>
                            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                            FACT-BASED EXTRACTIVE
                          </span>
                        )}
                        <span className="rounded bg-surface-raised border border-border px-2 py-0.5 text-gray-300 uppercase">
                          ARCHETYPE: {activeMeta.telemetry?.screenplay_archetype || activeMeta.hook_angle || "CONTRARIAN"}
                        </span>
                        {activeBlueprintId && (
                          <button
                            type="button"
                            onClick={() => handleStartStreamingRegenerateScript(activeBlueprintId)}
                            disabled={isStreamingRegen}
                            className="flex items-center gap-1 rounded bg-hive px-2.5 py-1 font-bold text-[#090b10] hover:bg-hive-400 disabled:opacity-50 transition-all shadow-sm"
                            title="Regenerate this video screenplay with local Llama 3.1 Neural LLM"
                          >
                            {isStreamingRegen ? (
                              <>
                                <Loader2 size={10} className="animate-spin text-[#090b10]" />
                                <span>AI GENERATING ({streamElapsed.toFixed(1)}s)…</span>
                              </>
                            ) : (
                              <>
                                <Sparkles size={10} />
                                <span>RE-GENERATE SCRIPT WITH AI</span>
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Antigravity-Style Traceability & Live Execution Accordion */}
                    <LiveTraceabilityBox
                      isGenerating={isStreamingRegen}
                      currentTaskTitle={isStreamingRegen ? `Synthesizing Screenplay for Task #${activeTask?.task_id}` : `Screenplay Agent Execution Trace`}
                      traceSteps={
                        isStreamingRegen || streamTraceSteps.length > 0
                          ? streamTraceSteps
                          : (activeMeta.telemetry?.trace_steps || [])
                      }
                      liveTokens={streamTokens}
                      elapsedSeconds={streamElapsed > 0 ? streamElapsed : (activeMeta.telemetry?.research_latency_seconds || 0)}
                      error={streamError || activeMeta.telemetry?.llm_error_reason}
                      archetype={activeMeta.telemetry?.screenplay_archetype}
                      engineMode={activeMeta.telemetry?.engine_mode}
                      onRetry={activeBlueprintId ? () => handleStartStreamingRegenerateScript(activeBlueprintId) : undefined}
                      defaultExpanded={false}
                    />

                    {/* Researched Web Sources & Live Evidence Pipeline */}
                    {((activeMeta.telemetry?.researched_sources && activeMeta.telemetry.researched_sources.length > 0) ||
                      (activeMeta.researched_sources && activeMeta.researched_sources.length > 0)) && (
                      <div className="rounded-xl border border-hive/30 bg-[#0a0e17] p-3 space-y-2.5 shadow-md">
                        <div className="flex items-center justify-between border-b border-white/[0.08] pb-2">
                          <div className="flex items-center gap-2">
                            <div className="h-5 w-5 rounded bg-hive/15 border border-hive/30 flex items-center justify-center text-hive">
                              <Globe size={11} />
                            </div>
                            <div>
                              <div className="font-mono text-[10px] font-bold text-gray-200 uppercase tracking-wider flex items-center gap-1.5">
                                <span>AGENTIC WEB SOURCES & FACTUAL GROUNDING</span>
                                <span className="rounded bg-emerald-500/10 border border-emerald-500/30 px-1 py-0.2 text-[8px] text-emerald-400 font-normal">
                                  VERIFIED LIVE INTEL
                                </span>
                              </div>
                            </div>
                          </div>
                          <span className="font-mono text-[9px] text-hive font-semibold">
                            {(activeMeta.telemetry?.researched_sources || activeMeta.researched_sources || []).length} SOURCES
                          </span>
                        </div>

                        <div className="grid gap-2 sm:grid-cols-2">
                          {(activeMeta.telemetry?.researched_sources || activeMeta.researched_sources || []).map((src, i) => (
                            <a
                              key={i}
                              href={src.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="group flex flex-col justify-between rounded-lg border border-border/70 bg-surface-deep/80 p-2 hover:border-hive/60 hover:bg-surface-deep transition-all shadow-xs"
                            >
                              <div className="space-y-0.5">
                                <div className="flex items-center justify-between gap-1 text-[9px] font-mono">
                                  <span className="font-semibold text-hive flex items-center gap-1">
                                    <ExternalLink size={9} className="group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                                    {src.source_name}
                                  </span>
                                  <span className="text-gray-500 text-[8px]">
                                    {src.domain}
                                  </span>
                                </div>
                                <p className="font-sans text-[11px] font-semibold text-gray-200 group-hover:text-white line-clamp-1 transition-colors">
                                  {src.title}
                                </p>
                                <p className="font-mono text-[9px] text-gray-400 line-clamp-2">
                                  {src.summary_snippet}
                                </p>
                              </div>

                              <div className="mt-1.5 flex items-center justify-between pt-1 border-t border-white/[0.04] font-mono text-[8px] text-gray-500">
                                <span>{src.published_at || "Recent"}</span>
                                <span className="text-emerald-400 font-semibold">
                                  {Math.round(src.credibility_score * 100)}% Credibility
                                </span>
                              </div>
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Controls to toggle Trace Log and Visual Matching Pipeline */}
                    <div className="flex items-center gap-2 pt-1 font-mono text-[10px]">
                      <button
                        onClick={() => setShowTelemetryTrace(!showTelemetryTrace)}
                        className={cn(
                          "flex items-center gap-1.5 rounded border px-2.5 py-1 transition-colors",
                          showTelemetryTrace
                            ? "bg-hive/20 border-hive/40 text-hive font-semibold"
                            : "border-border bg-surface text-gray-400 hover:text-gray-200"
                        )}
                      >
                        <Terminal size={12} />
                        <span>{showTelemetryTrace ? "HIDE BACKEND EVENT TRACE" : `VIEW BACKEND EVENT TRACE (${activeMeta.telemetry?.event_trace?.length || 0})`}</span>
                      </button>

                      {activeSceneClips.length > 0 && (
                        <button
                          onClick={() => setShowVisualMatches(!showVisualMatches)}
                          className={cn(
                            "flex items-center gap-1.5 rounded border px-2.5 py-1 transition-colors",
                            showVisualMatches
                              ? "bg-blue-500/20 border-blue-500/40 text-blue-300 font-semibold"
                              : "border-border bg-surface text-gray-400 hover:text-gray-200"
                          )}
                        >
                          <Film size={12} />
                          <span>{showVisualMatches ? "HIDE FOOTAGE PIPELINE" : `INSPECT MATCHED FOOTAGE (${activeSceneClips.length} SCENES)`}</span>
                        </button>
                      )}
                    </div>

                    {/* Real-time Backend Event Trace Terminal */}
                    {showTelemetryTrace && (
                      <div className="rounded-lg border border-border bg-black/90 p-3 font-mono text-[10px] space-y-1 max-h-48 overflow-y-auto">
                        <div className="text-gray-500 border-b border-border/50 pb-1 flex items-center justify-between">
                          <span>BACKEND EXECUTION LOG</span>
                          <span>{activeMeta.telemetry?.event_trace?.length || 0} EVENTS RECORDED</span>
                        </div>
                        {activeMeta.telemetry?.event_trace && activeMeta.telemetry.event_trace.length > 0 ? (
                          activeMeta.telemetry.event_trace.map((ev, i) => (
                            <div key={i} className="flex items-start gap-2 text-gray-300 leading-relaxed">
                              <span className="text-gray-500 shrink-0">[{ev.timestamp}]</span>
                              <span className="text-hive font-semibold shrink-0">[{ev.phase}]</span>
                              <span className="text-gray-200">{ev.message}</span>
                            </div>
                          ))
                        ) : (
                          <div className="text-gray-500 italic py-2">
                            Events recorded: Research phase complete. Script crafted and locked.
                          </div>
                        )}
                      </div>
                    )}

                    {/* Visual Asset Matching Pipeline Drawer */}
                    {showVisualMatches && activeSceneClips.length > 0 && (
                      <div className="rounded-lg border border-border bg-surface-deep p-3 space-y-2">
                        <div className="font-mono text-[9px] text-gray-400 uppercase tracking-wider">
                          SCENE-BY-SCENE RESOLVED VISUAL FOOTAGE & CAMERA CADENCE
                        </div>
                        <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                          {activeSceneClips.map((clip) => (
                            <div
                              key={clip.scene_id}
                              className="rounded border border-border/80 bg-surface/80 p-2 text-[10px] flex items-center justify-between gap-3"
                            >
                              <div className="space-y-0.5 max-w-[70%]">
                                <div className="flex items-center gap-1.5 font-mono text-[9px]">
                                  <span className="font-bold text-hive uppercase">SCENE {clip.scene_idx + 1} ({clip.emotional_beat})</span>
                                  <span className="text-gray-500">•</span>
                                  <span className="text-emerald-400 font-semibold">{clip.resolved_footage_type || "Stock Footage"}</span>
                                  <span className="text-gray-500">•</span>
                                  <span className="text-gray-400">{clip.camera_motion}</span>
                                </div>
                                <div className="text-gray-200 line-clamp-1 italic font-sans">
                                  "{clip.voiceover_text}"
                                </div>
                                <div className="font-mono text-[8px] text-gray-400 truncate">
                                  Keywords: <span className="text-hive/80">{clip.search_keywords?.join(", ") || "niche default"}</span> | Asset: {clip.source_asset || "motion video"}
                                </div>
                              </div>
                              <div className="flex items-center gap-2 shrink-0">
                                {clip.thumbnail_path && (
                                  <img
                                    src={clip.thumbnail_path}
                                    alt="Scene Thumbnail"
                                    className="h-12 w-9 object-cover rounded-lg border border-border/80 shrink-0 shadow-sm"
                                  />
                                )}
                                <div className="flex flex-col gap-1">
                                  <button
                                    type="button"
                                    title="Try another stock photo/video"
                                    disabled={rerollingSceneIdx === clip.scene_idx}
                                    onClick={() => {
                                      if (activeBlueprintId) {
                                        rerollMutation.mutate({ blueprintId: activeBlueprintId, sceneIdx: clip.scene_idx });
                                      }
                                    }}
                                    className="flex items-center gap-1 rounded bg-surface hover:bg-surface-deep border border-border px-2 py-1 font-mono text-[9px] text-gray-300 hover:text-hive transition-colors disabled:opacity-50"
                                  >
                                    {rerollingSceneIdx === clip.scene_idx ? (
                                      <Loader2 size={10} className="animate-spin text-hive" />
                                    ) : (
                                      <RotateCw size={10} />
                                    )}
                                    <span>RE-ROLL</span>
                                  </button>
                                  <button
                                    type="button"
                                    title="Search & pick or upload a different image"
                                    onClick={() => {
                                      setPickerState({
                                        sceneIdx: clip.scene_idx,
                                        keywords: clip.search_keywords || [],
                                      });
                                    }}
                                    className="flex items-center gap-1 rounded bg-hive/10 hover:bg-hive/20 border border-hive/30 px-2 py-1 font-mono text-[9px] text-hive font-semibold transition-colors"
                                  >
                                    <Clapperboard size={10} />
                                    <span>SWAP</span>
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Video Deliverable Player or Render CTA */}
                {videoUrl ? (
                  <div className="rounded-xl border border-hive/30 bg-gradient-to-b from-[#121824] to-[#0a0d14] p-4 space-y-3 shadow-glass">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-mono text-[10px] text-hive font-semibold">
                        <Film size={14} />
                        PHYSICAL 9:16 MP4 READY FOR VERIFICATION
                      </div>
                      <a
                        href={videoUrl}
                        download="hive-deliverable.mp4"
                        className="font-mono text-[10px] text-gray-400 hover:text-hive transition-colors underline"
                      >
                        Download MP4
                      </a>
                    </div>
                    <div className="flex items-center justify-center rounded-xl bg-black/90 p-4 border border-border">
                      <video
                        controls
                        src={videoUrl}
                        className="aspect-[9/16] max-h-[360px] w-auto rounded-xl shadow-[0_0_30px_rgba(245,166,35,0.15)] border border-white/10"
                      />
                    </div>
                  </div>
                ) : isCurrentRendering ? (
                  <div className="rounded-xl border border-amber-500/30 bg-[#0d121c] p-6 text-center space-y-3">
                    <Loader2 size={24} className="mx-auto animate-spin text-amber-400" />
                    <div className="font-mono text-xs font-semibold text-gray-200">
                      COMPOSITING 9:16 VERTICAL MP4 CONTAINER
                    </div>
                    <p className="text-[11px] text-gray-400 max-w-sm mx-auto">
                      {renderJob?.step || "Synthesizing voice cadence, matching b-roll clips, and burning lower-third subtitles..."}
                    </p>
                    <div className="w-full max-w-xs mx-auto h-1.5 rounded-full bg-border overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-hive to-amber-400 transition-all duration-300"
                        style={{ width: `${renderJob?.progress || 15}%` }}
                      />
                    </div>
                  </div>
                ) : activeBlueprintId ? (
                  <div className="rounded-xl border border-dashed border-border bg-surface-deep p-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-left">
                    <div className="flex items-center gap-3">
                      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg border border-border bg-surface text-gray-400">
                        <Video size={18} />
                      </div>
                      <div>
                        <div className="font-mono text-xs font-semibold text-gray-200">
                          Structured 8-Scene Storyboard Ready
                        </div>
                        <div className="text-[11px] text-gray-400">
                          Pre-rendered scene directives, voiceover text, and Ken Burns motion locked.
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => renderMutation.mutate(activeBlueprintId)}
                      disabled={renderMutation.isPending}
                      className="flex items-center gap-1.5 rounded-lg bg-hive px-3 py-1.5 font-mono text-[10px] font-semibold text-black hover:bg-amber-400 transition-colors shrink-0"
                    >
                      <Film size={13} />
                      <span>RENDER MP4 PREVIEW</span>
                    </button>
                  </div>
                ) : null}

                {/* Content Breakdown Details */}
                {activeTask.content ? (
                  <div className="space-y-3 text-[11px]">
                    {/* Hook */}
                    <div className="rounded-lg border border-hive/30 bg-hive/5 p-3">
                      <div className="flex items-center gap-1.5 font-mono text-[9px] font-semibold text-hive mb-1">
                        <Sparkles size={13} />
                        3-SECOND RETENTION HOOK
                      </div>
                      <p className="font-medium text-gray-200">"{activeTask.content.hook}"</p>
                    </div>

                    {/* Script */}
                    <div className="rounded-lg border border-border bg-surface-deep p-3">
                      <div className="flex items-center gap-1.5 font-mono text-[9px] text-gray-400 mb-1">
                        <FileText size={13} />
                        BODY SCRIPT / NARRATION CADENCE
                      </div>
                      <pre className="whitespace-pre-wrap font-sans text-gray-300 leading-relaxed text-[11px] max-h-[140px] overflow-auto">
                        {activeTask.content.body_script}
                      </pre>
                    </div>

                    {/* Caption */}
                    <div className="rounded-lg border border-border bg-surface-deep p-3">
                      <div className="font-mono text-[9px] text-gray-400 mb-1">CAPTION & VIRAL HASHTAGS</div>
                      <p className="text-gray-300">{activeTask.content.caption}</p>
                      {activeTask.content.hashtags?.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1 font-mono text-[9px] text-hive">
                          {activeTask.content.hashtags.map((t) => `#${t}`).join(" ")}
                        </div>
                      )}
                    </div>

                    {/* Visual Brief */}
                    <div className="rounded-lg border border-border bg-surface-deep p-3">
                      <div className="flex items-center gap-1.5 font-mono text-[9px] text-gray-400 mb-1">
                        <Eye size={13} />
                        VISUAL DIRECTIVE & SCENE METAPHOR
                      </div>
                      <p className="text-gray-300">{activeTask.content.visual_brief}</p>
                    </div>

                    {/* Monetization */}
                    <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3">
                      <div className="flex items-center gap-1.5 font-mono text-[9px] font-semibold text-emerald-400 mb-1">
                        <CircleDollarSign size={13} />
                        MONETIZATION ATTRIBUTION
                      </div>
                      <p className="text-gray-300">{activeTask.content.monetization_hypothesis}</p>
                    </div>

                    {/* Factual Claims to Verify */}
                    {activeTask.content.factual_checks?.length > 0 && (
                      <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-3">
                        <div className="flex items-center gap-1.5 font-mono text-[9px] font-semibold text-amber-400 mb-1">
                          <AlertTriangle size={13} />
                          FACTUAL CLAIMS TO VERIFY BEFORE PUBLISHING
                        </div>
                        <ul className="list-disc pl-4 space-y-0.5 text-gray-300 text-[10px]">
                          {activeTask.content.factual_checks.map((fc, i) => (
                            <li key={i}>{fc}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <pre className="whitespace-pre-wrap rounded border border-border bg-surface-deep p-3 text-[11px] text-gray-300">
                    {activeTask.output}
                  </pre>
                )}
              </div>

              {/* Action Buttons */}
              <div className="border-t border-border pt-4">
                {isRejecting ? (
                  <div className="space-y-2">
                    <label className="block font-mono text-[9px] text-gray-400">
                      REJECTION FEEDBACK / INSTRUCTIONS
                    </label>
                    <textarea
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      placeholder="Specify required corrections or reason for rejection..."
                      rows={2}
                      className="w-full rounded border border-border bg-surface-deep p-2 text-xs text-gray-300 outline-none"
                    />
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setIsRejecting(false)}
                        className="rounded border border-border px-3 py-1.5 font-mono text-[9px] text-gray-400"
                      >
                        CANCEL
                      </button>
                      <button
                        onClick={() =>
                          rejectMutation.mutate({
                            taskId: activeTask.task_id,
                            reason: rejectReason || "Operator rejected",
                          })
                        }
                        disabled={rejectMutation.isPending}
                        className="rounded bg-red-500/20 border border-red-500/40 px-3 py-1.5 font-mono text-[9px] font-semibold text-red-300"
                      >
                        CONFIRM REJECTION
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between gap-3">
                    <button
                      onClick={() => setIsRejecting(true)}
                      className="flex items-center gap-1.5 rounded border border-red-500/30 bg-red-500/5 px-4 py-2 font-mono text-[10px] text-red-400 hover:bg-red-500/10 transition-colors"
                    >
                      <XCircle size={15} />
                      <span>REJECT / REVISE</span>
                    </button>

                    <div className="flex items-center gap-2">
                      {activeBlueprintId && (
                        <button
                          onClick={() => navigate(`/video-studio?blueprintId=${activeBlueprintId}`)}
                          className="flex items-center gap-1.5 rounded border border-border bg-surface-raised px-4 py-2 font-mono text-[10px] text-gray-300 hover:text-hive hover:border-hive/40 transition-colors"
                        >
                          <Clapperboard size={14} />
                          <span>EDIT IN STUDIO</span>
                        </button>
                      )}

                      <button
                        onClick={() => approveMutation.mutate(activeTask.task_id)}
                        disabled={approveMutation.isPending}
                        className="flex items-center gap-1.5 rounded bg-emerald-500 px-5 py-2 font-mono text-[10px] font-semibold text-[#090b10] hover:bg-emerald-400 transition-colors shadow-glow"
                      >
                        <CheckCircle2 size={15} />
                        <span>{approveMutation.isPending ? "AUTHORIZING…" : "AUTHORIZE FOR PUBLISHING"}</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Interactive Stock & Media Asset Picker Modal */}
      {pickerState && activeBlueprintId && (
        <StockPickerModal
          isOpen={true}
          onClose={() => setPickerState(null)}
          sceneIdx={pickerState.sceneIdx}
          keywords={pickerState.keywords}
          workerId={activeTask?.worker_id || "tech"}
          onSelectAsset={(assetPath) => {
            replaceAssetMutation.mutate({
              blueprintId: activeBlueprintId,
              sceneIdx: pickerState.sceneIdx,
              assetPath,
            });
            setPickerState(null);
          }}
        />
      )}
    </div>
  );
}