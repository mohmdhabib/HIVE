import { useState, useEffect, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  api,
  type VideoProductionBlueprint,
  type SceneNode,
  type HookVariant,
  type LiveTrendItem,
  type RenderJobStatus,
  type RenderedVideoItem,
  type VaultAsset,
  type StockMaterialItem,
} from "@/lib/api";
import { useWorkers } from "@/hooks/use-workers";
import { useAppStore } from "@/stores/app-store";
import {
  ArrowDownToLine,
  Bot,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clapperboard,
  Clock,
  Download,
  ExternalLink,
  Eye,
  FileVideo,
  Film,
  Flame,
  Gauge,
  Globe,
  Image as ImageIcon,
  Layers,
  Link2,
  Loader2,
  MessageSquare,
  Mic,
  Music,
  Palette,
  Play,
  RefreshCw,
  RotateCw,
  Scissors,
  Send,
  Sliders,
  Sparkles,
  Target,
  TrendingUp,
  Type,
  Video,
  Volume2,
  X,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const BEAT_COLORS: Record<string, string> = {
  hook: "bg-red-500/20 text-red-400 border-red-500/30",
  tension: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  revelation: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  escalation: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  payoff: "bg-violet-500/20 text-violet-400 border-violet-500/30",
  twist: "bg-pink-500/20 text-pink-400 border-pink-500/30",
  cta: "bg-hive/20 text-hive border-hive/30",
};

const ZONE_LABELS: Record<string, string> = {
  critical: "CRITICAL — 3s hook window",
  build: "BUILD — audience deciding to stay",
  core: "CORE — value delivery",
  close: "CLOSE — conversion window",
};

export default function VideoStudioPage() {
  const queryClient = useQueryClient();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const { data: workers = [] } = useWorkers();
  const { selectedWorkerId, setSelectedWorker, preloadedTrend, setPreloadedTrend } = useAppStore();
  const [trendTitle, setTrendTitle] = useState("");
  const [trendSummary, setTrendSummary] = useState("");

  useEffect(() => {
    if (preloadedTrend) {
      setTrendTitle(preloadedTrend.title);
      if (preloadedTrend.summary) {
        setTrendSummary(preloadedTrend.summary);
      }
      setPreloadedTrend(null);
    }
  }, [preloadedTrend, setPreloadedTrend]);
  const [blueprint, setBlueprint] = useState<VideoProductionBlueprint | null>(null);
  const [activePanel, setActivePanel] = useState<"scenes" | "hooks" | "brand" | "thumbnail" | "score" | "player" | "vault">("scenes");
  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null);
  const [renderJob, setRenderJob] = useState<RenderJobStatus | null>(null);
  const [dispatchedApproval, setDispatchedApproval] = useState(false);

  // Scene Clip Editor Form State
  const [editedVoiceover, setEditedVoiceover] = useState<string>("");
  const [editedKeywords, setEditedKeywords] = useState<string>("");
  const [editedMotion, setEditedMotion] = useState<string>("slow_zoom_in");
  const [selectedVaultAsset, setSelectedVaultAsset] = useState<string>("");
  const [sceneLayerTab, setSceneLayerTab] = useState<"clip" | "overlay" | "audio">("clip");
  const [editedCaptionPosition, setEditedCaptionPosition] = useState<"bottom" | "center" | "top">("bottom");
  const [editedHighlightColor, setEditedHighlightColor] = useState<string>("#FFE600");
  const [editedFontSize, setEditedFontSize] = useState<number>(72);
  const [editedCaptionStyle, setEditedCaptionStyle] = useState<"pill" | "outline" | "minimal">("pill");
  const [isAssetPickerOpen, setIsAssetPickerOpen] = useState<boolean>(false);
  const sceneVideoRef = useRef<HTMLVideoElement | null>(null);

  const activeWorker = workers.find((w) => w.id === selectedWorkerId) || workers[0];

  // Video Library Query
  const { data: library = [], refetch: refetchLibrary } = useQuery({
    queryKey: ["video-library"],
    queryFn: api.videoLibrary,
  });

  const [importUrl, setImportUrl] = useState("");
  const [vaultNiche, setVaultNiche] = useState("tech");

  // Media Vault Query
  const { data: vaultAssets = [], refetch: refetchVault, isFetching: isFetchingVault } = useQuery({
    queryKey: ["materials-vault", vaultNiche],
    queryFn: () => api.vaultMaterials(vaultNiche),
  });

  // Stock Materials Library Query
  const { data: stockMaterials = [] } = useQuery({
    queryKey: ["stock-materials", selectedWorkerId],
    queryFn: () => api.stockMaterials(selectedWorkerId || undefined),
  });

  // Scene Clips Query
  const { data: sceneClips = [], refetch: refetchClips } = useQuery({
    queryKey: ["scene-clips", blueprint?.blueprint_id],
    queryFn: () => (blueprint ? api.blueprintSceneClips(blueprint.blueprint_id) : []),
    enabled: !!blueprint?.blueprint_id,
  });

  const activeClips = renderJob?.scene_clips && renderJob.scene_clips.length > 0
    ? renderJob.scene_clips
    : sceneClips;

  const selectedSceneIndex = blueprint?.scenes.findIndex((s) => s.scene_id === selectedSceneId) ?? -1;
  const selectedScene = blueprint?.scenes.find((s) => s.scene_id === selectedSceneId) || null;
  const currentSceneClip = selectedSceneIndex >= 0 ? activeClips.find((c) => c.scene_idx === selectedSceneIndex) : null;

  useEffect(() => {
    if (selectedScene) {
      setEditedVoiceover(selectedScene.audio.voiceover_text);
      setEditedKeywords(selectedScene.visual.search_keywords.join(", "));
      setEditedMotion(selectedScene.visual.camera_motion || "slow_zoom_in");
      setSelectedVaultAsset("");
      setSceneLayerTab("clip");
      setEditedCaptionPosition("bottom");
      setEditedHighlightColor("#FFE600");
      setEditedFontSize(72);
      setEditedCaptionStyle("pill");
      setIsAssetPickerOpen(false);
    }
  }, [selectedSceneId, selectedScene]);

  // Harvest Batch Mutation
  const harvestBatchMutation = useMutation({
    mutationFn: () => api.harvestBatch({ niche: vaultNiche, count: 4 }),
    onSuccess: () => {
      refetchVault();
    },
  });

  // Harvest URL Mutation (yt-dlp)
  const harvestUrlMutation = useMutation({
    mutationFn: () => api.harvestUrl({ url: importUrl.trim(), niche: vaultNiche }),
    onSuccess: () => {
      setImportUrl("");
      refetchVault();
    },
  });

  // Regenerate Single Scene Mutation
  const regenerateSceneMutation = useMutation({
    mutationFn: () => {
      if (!blueprint || selectedSceneIndex < 0) return Promise.reject("No scene selected");
      const keywords = editedKeywords.split(",").map((k) => k.trim()).filter(Boolean);
      return api.regenerateSceneClip(blueprint.blueprint_id, selectedSceneIndex, {
        voiceover_text: editedVoiceover.trim() || undefined,
        search_keywords: keywords.length > 0 ? keywords : undefined,
        camera_motion: editedMotion || undefined,
        custom_asset_path: selectedVaultAsset || undefined,
        caption_position: editedCaptionPosition,
        caption_font_size: editedFontSize,
        caption_highlight_color: editedHighlightColor,
        caption_style: editedCaptionStyle,
      });
    },
    onSuccess: (updatedJob) => {
      setRenderJob(updatedJob);
      refetchClips();
      queryClient.invalidateQueries({ queryKey: ["video-library"] });
    },
  });

  const blueprintMutation = useMutation({
    mutationFn: () =>
      api.generateVideoBlueprint({
        worker_id: selectedWorkerId || "tech",
        trend_title: trendTitle.trim(),
        trend_summary: trendSummary.trim() || undefined,
      }),
    onSuccess: (data) => {
      setBlueprint(data);
      setRenderJob(null);
      setDispatchedApproval(false);
      setActivePanel("scenes");
      setSelectedSceneId(data.scenes[0]?.scene_id || null);
    },
  });

  // Render Full MP4 Video Mutation
  const renderMutation = useMutation({
    mutationFn: (bp: VideoProductionBlueprint) => api.renderVideo(bp),
    onSuccess: (data) => {
      setRenderJob(data);
      if (data.status === "complete") {
        setActivePanel("player");
        queryClient.invalidateQueries({ queryKey: ["video-library"] });
      }
    },
  });

  const isRendering =
    renderMutation.isPending ||
    (!!renderJob && renderJob.status !== "complete" && renderJob.status !== "failed");

  // Active Live Polling Query for Real-Time Render Telemetry
  useQuery({
    queryKey: ["render-status", renderJob?.job_id],
    queryFn: async () => {
      if (!renderJob?.job_id) return null;
      const updated = await api.renderStatus(renderJob.job_id);
      setRenderJob(updated);
      if (updated.status === "complete") {
        queryClient.invalidateQueries({ queryKey: ["video-library"] });
      }
      return updated;
    },
    enabled: isRendering && !!renderJob?.job_id,
    refetchInterval: isRendering ? 700 : false,
  });

  // Dispatch to Master Approval Queue
  const dispatchMutation = useMutation({
    mutationFn: () => {
      if (!blueprint || !selectedWorkerId) return Promise.reject("No blueprint");
      return api.createTask({
        worker_id: selectedWorkerId,
        objective: `Approve rendered video campaign: "${blueprint.title}". Video: ${renderJob?.output_path || "Ready"}`,
        require_approval: true,
        target_platform: "instagram",
      });
    },
    onSuccess: () => {
      setDispatchedApproval(true);
      queryClient.invalidateQueries({ queryKey: ["pending-tasks"] });
    },
  });

  const virality = blueprint?.virality_score;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
            VIDEO INTELLIGENCE ENGINE
          </div>
          <h1 className="mt-1 font-display text-2xl font-semibold">Video Production Studio</h1>
          <p className="text-xs text-gray-400">
            Scene-graph storytelling, retention-curve pacing, A/B hook variants, brand identity overlay, and pre-publish virality scoring.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded border border-border bg-surface px-3 py-1.5 font-mono text-[10px]">
          <Clapperboard size={13} className="text-hive" />
          <span>BEYOND MONEYPRINTER</span>
        </div>
      </div>

      {/* Worker Selector */}
      <div className="rounded-xl border border-border bg-surface p-4">
        <label className="block font-mono text-[9px] tracking-[1.1px] text-gray-400 mb-2">
          PRODUCTION BRAND
        </label>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          {workers.map((w) => (
            <button
              key={w.id}
              onClick={() => { setSelectedWorker(w.id); setBlueprint(null); }}
              className={cn(
                "flex items-center gap-2 rounded-lg border p-2.5 text-left text-xs transition-colors",
                selectedWorkerId === w.id
                  ? "border-hive/50 bg-hive/10 text-gray-100 font-medium"
                  : "border-border bg-surface-deep text-gray-400 hover:text-gray-200"
              )}
            >
              <Bot size={15} className={selectedWorkerId === w.id ? "text-hive" : "text-gray-500"} />
              <div className="truncate">
                <div className="truncate font-medium">{w.name}</div>
                <div className="text-[9px] text-gray-500 capitalize truncate">{w.niche}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Input Panel: Topic Entry */}
      <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
        <div className="flex items-center gap-2 border-b border-border pb-3">
          <Sparkles size={16} className="text-hive" />
          <h2 className="font-display text-base font-semibold">Generate Video Blueprint</h2>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <label className="block font-mono text-[9px] text-gray-400 mb-1.5">TREND / TOPIC TITLE</label>
            <input
              type="text"
              value={trendTitle}
              onChange={(e) => setTrendTitle(e.target.value)}
              placeholder="e.g. Open-source LLMs reach 90% benchmark parity with cloud APIs"
              className="w-full rounded-lg border border-border bg-surface-deep px-3.5 py-2.5 text-xs text-gray-200 outline-none focus:border-hive/50"
            />
          </div>
          <div>
            <label className="block font-mono text-[9px] text-gray-400 mb-1.5">CONTEXT / SUMMARY (OPTIONAL)</label>
            <input
              type="text"
              value={trendSummary}
              onChange={(e) => setTrendSummary(e.target.value)}
              placeholder="Additional context about why this is trending right now..."
              className="w-full rounded-lg border border-border bg-surface-deep px-3.5 py-2.5 text-xs text-gray-200 outline-none focus:border-hive/50"
            />
          </div>
        </div>

        <button
          onClick={() => blueprintMutation.mutate()}
          disabled={blueprintMutation.isPending || !trendTitle.trim()}
          className="flex items-center gap-1.5 rounded-lg bg-hive px-5 py-2.5 font-mono text-xs font-semibold text-[#090b10] hover:bg-hive-400 transition-colors disabled:opacity-50"
        >
          <Film size={14} />
          {blueprintMutation.isPending ? "BUILDING BLUEPRINT…" : "GENERATE VIDEO BLUEPRINT"}
        </button>
      </div>

      {/* Blueprint Output */}
      {blueprint && (
        <>
          {/* Virality Score Banner */}
          {virality && (
            <div className={cn(
              "rounded-xl border p-5",
              virality.overall_score >= 80
                ? "border-emerald-500/30 bg-emerald-500/5"
                : virality.overall_score >= 60
                  ? "border-hive/30 bg-hive/5"
                  : "border-red-500/30 bg-red-500/5"
            )}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "grid h-14 w-14 place-items-center rounded-xl font-display text-2xl font-bold",
                    virality.overall_score >= 80 ? "bg-emerald-500/20 text-emerald-400" :
                    virality.overall_score >= 60 ? "bg-hive/20 text-hive" : "bg-red-500/20 text-red-400"
                  )}>
                    {virality.overall_score}
                  </div>
                  <div>
                    <div className="font-mono text-[9px] text-gray-400 tracking-wider">PRE-PUBLISH VIRALITY SCORE</div>
                    <div className="font-display text-lg font-semibold">
                      {virality.recommendation === "publish" ? "Ready to Produce" :
                       virality.recommendation === "revise_hook" ? "Hook Needs Work" :
                       virality.recommendation === "revise_pacing" ? "Pacing Revision Recommended" : "Needs Revision"}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-1.5 font-mono text-[10px]">
                  <Clock size={12} className="text-gray-400" />
                  {blueprint.total_duration_seconds.toFixed(1)}s
                  <span className="text-gray-500">|</span>
                  {blueprint.scenes.length} scenes
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
                {[
                  { label: "HOOK", value: virality.hook_strength, icon: Zap },
                  { label: "PACING", value: virality.pacing_quality, icon: Scissors },
                  { label: "VISUALS", value: virality.visual_variety, icon: Eye },
                  { label: "AUDIO", value: virality.audio_energy, icon: Volume2 },
                  { label: "CTA", value: virality.cta_clarity, icon: Target },
                  { label: "SHARE", value: virality.shareability, icon: TrendingUp },
                ].map((metric) => (
                  <div key={metric.label} className="rounded-lg border border-border bg-surface-deep p-3 text-center">
                    <metric.icon size={14} className="mx-auto mb-1 text-gray-400" />
                    <div className={cn(
                      "font-display text-lg font-bold",
                      metric.value >= 80 ? "text-emerald-400" : metric.value >= 60 ? "text-hive" : "text-red-400"
                    )}>
                      {metric.value}
                    </div>
                    <div className="font-mono text-[8px] text-gray-500">{metric.label}</div>
                  </div>
                ))}
              </div>

              {virality.risk_flags.length > 0 && (
                <div className="mt-3 rounded-lg border border-red-500/20 bg-red-500/5 p-3">
                  <div className="font-mono text-[9px] text-red-400 font-semibold mb-1">RISK FLAGS</div>
                  {virality.risk_flags.map((flag, i) => (
                    <div key={i} className="text-[11px] text-red-300/80">• {flag}</div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Production & Render Action Banner / Live Render HUD */}
          <div className="rounded-xl border border-hive/40 bg-gradient-to-r from-[#0e1422] via-[#090d16] to-[#121929] p-5 shadow-[0_0_25px_rgba(245,166,35,0.12)] space-y-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[9px] uppercase tracking-widest text-hive font-bold">
                    AUTONOMOUS RENDER PIPELINE
                  </span>
                  <span className="rounded bg-hive/10 px-2 py-0.5 font-mono text-[9px] text-hive border border-hive/20">
                    FFmpeg 7.1 Ken Burns & Audio Mix
                  </span>
                  {isRendering && (
                    <span className="flex items-center gap-1.5 rounded bg-amber-500/10 px-2 py-0.5 font-mono text-[9px] text-amber-400 border border-amber-500/20 animate-pulse">
                      <Loader2 size={10} className="animate-spin" />
                      LIVE RENDERING ACTIVE
                    </span>
                  )}
                </div>
                <h3 className="font-display text-base font-semibold text-gray-100 mt-1">
                  {renderJob?.status === "complete"
                    ? "✓ 1080×1920 HD Short Video Rendered & Verified"
                    : isRendering
                    ? "Compiling Motion Scene Graphics, Speech Cadence & Lo-Fi Ambiance…"
                    : "Ready to Produce 1080×1920 MP4 Video with Dynamic Motion"}
                </h3>
              </div>

              <div className="flex items-center gap-2">
                {renderJob?.output_path && (
                  <>
                    <button
                      onClick={() => setActivePanel("player")}
                      className="flex items-center gap-1.5 rounded-lg border border-hive/50 bg-hive/10 px-3.5 py-2 font-mono text-xs font-semibold text-hive hover:bg-hive/20 transition-all"
                    >
                      <Play size={13} className="fill-current" />
                      WATCH IN PLAYER
                    </button>
                    <a
                      href={renderJob.output_path}
                      download={`${blueprint.blueprint_id}.mp4`}
                      className="flex items-center gap-1.5 rounded-lg border border-border bg-surface-deep px-3.5 py-2 font-mono text-xs text-gray-200 hover:text-white hover:bg-surface transition-colors"
                    >
                      <Download size={13} />
                      DOWNLOAD MP4
                    </a>
                  </>
                )}

                <button
                  onClick={() => renderMutation.mutate(blueprint)}
                  disabled={isRendering}
                  className={cn(
                    "flex items-center gap-2 rounded-lg px-5 py-2.5 font-mono text-xs font-bold transition-all",
                    isRendering
                      ? "bg-hive/50 text-[#090b10] cursor-wait"
                      : "bg-hive text-[#090b10] hover:bg-hive-400 shadow-[0_0_20px_rgba(245,166,35,0.3)]"
                  )}
                >
                  {isRendering ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      RENDERING ({renderJob?.progress_pct.toFixed(0) || "15"}%)…
                    </>
                  ) : (
                    <>
                      <Play size={14} className="fill-current" />
                      PRODUCE & RENDER MP4
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Live Progress HUD & Phase Stepper */}
            {isRendering && (
              <div className="rounded-lg border border-white/[0.08] bg-black/40 p-4 space-y-3">
                <div className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2 text-gray-200">
                    <span className="h-2 w-2 rounded-full bg-hive animate-ping" />
                    <span className="font-semibold text-hive">
                      {renderJob?.current_step || "Executing pipeline steps..."}
                    </span>
                  </div>
                  <span className="font-bold text-hive text-sm">
                    {renderJob?.progress_pct.toFixed(0) || "10"}%
                  </span>
                </div>

                {/* Glowing Progress Bar */}
                <div className="w-full h-2.5 rounded-full bg-surface-deep border border-border overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 via-hive to-emerald-400 transition-all duration-500 shadow-[0_0_15px_rgba(245,166,35,0.8)]"
                    style={{ width: `${Math.max(8, renderJob?.progress_pct || 10)}%` }}
                  />
                </div>

                {/* 4-Stage Production Stepper */}
                <div className="grid grid-cols-4 gap-2 text-[9px] font-mono text-center pt-1">
                  <div className={cn("p-1.5 rounded border", (renderJob?.progress_pct || 0) >= 15 ? "border-hive/50 bg-hive/10 text-hive font-bold" : "border-border text-gray-500")}>
                    1. SCENE GRAPH
                  </div>
                  <div className={cn("p-1.5 rounded border", (renderJob?.progress_pct || 0) >= 35 ? "border-hive/50 bg-hive/10 text-hive font-bold" : "border-border text-gray-500")}>
                    2. SPEECH CADENCE
                  </div>
                  <div className={cn("p-1.5 rounded border", (renderJob?.progress_pct || 0) >= 65 ? "border-hive/50 bg-hive/10 text-hive font-bold" : "border-border text-gray-500")}>
                    3. KEN BURNS MOTION
                  </div>
                  <div className={cn("p-1.5 rounded border", (renderJob?.progress_pct || 0) >= 90 ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-400 font-bold" : "border-border text-gray-500")}>
                    4. H.264 ASSEMBLY
                  </div>
                </div>
              </div>
            )}

            {/* Error Notification Banner */}
            {renderJob?.status === "failed" && (
              <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3.5 flex items-center justify-between text-xs text-red-300">
                <span>Render Error: {renderJob.error_message || "Video assembly failed"}</span>
                <button
                  onClick={() => renderMutation.mutate(blueprint)}
                  className="rounded bg-red-500/20 border border-red-500/40 px-3 py-1 font-mono text-[10px] text-red-200 hover:bg-red-500/30"
                >
                  RETRY RENDER
                </button>
              </div>
            )}
          </div>

          {/* Panel Tabs */}
          <div className="flex items-center gap-1 rounded-lg border border-border bg-surface p-1 font-mono text-[10px]">
            {[
              { id: "scenes" as const, label: "SCENE GRAPH", icon: Film },
              { id: "player" as const, label: renderJob?.output_path ? "★ VIDEO PLAYER" : "VIDEO PLAYER", icon: Play },
              { id: "hooks" as const, label: "A/B HOOKS", icon: Zap },
              { id: "brand" as const, label: "BRAND IDENTITY", icon: Palette },
              { id: "thumbnail" as const, label: "THUMBNAIL", icon: ImageIcon },
              { id: "score" as const, label: "FULL SCRIPT", icon: Type },
              { id: "vault" as const, label: `VAULT (${vaultAssets.length})`, icon: Clapperboard },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActivePanel(tab.id)}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-2 transition-colors",
                  activePanel === tab.id
                    ? "bg-hive font-semibold text-[#090b10]"
                    : "text-gray-400 hover:text-gray-200"
                )}
              >
                <tab.icon size={12} />
                {tab.label}
              </button>
            ))}
          </div>

          {/* VIDEO PLAYER PANEL */}
          {activePanel === "player" && (
            <div className="rounded-xl border border-border bg-surface p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <Play size={16} className="text-hive" />
                  <h3 className="font-display text-base font-semibold">Studio Video Preview & Review</h3>
                </div>
                <span className="font-mono text-[9px] text-gray-400">
                  9:16 Vertical HD (1080×1920)
                </span>
              </div>

              {renderJob?.output_path ? (
                <div className="grid gap-8 lg:grid-cols-12 items-start">
                  {/* Left Column: Smartphone Chassis Mockup with Ambient Glow & Scene Jump */}
                  <div className="lg:col-span-5 flex flex-col items-center">
                    <div className="relative mx-auto flex flex-col items-center w-full">
                      {/* Ambient backlight glow */}
                      <div className="absolute -inset-6 rounded-[52px] bg-gradient-to-b from-hive/20 via-amber-500/10 to-transparent blur-3xl pointer-events-none" />

                      {/* Smartphone chassis */}
                      <div className="relative w-full max-w-[310px] rounded-[42px] border-[5px] border-[#222834] bg-[#0c1017] p-2.5 shadow-[0_20px_60px_rgba(0,0,0,0.85)] ring-1 ring-white/10">
                        {/* Dynamic Island / Notch */}
                        <div className="absolute top-3.5 left-1/2 -translate-x-1/2 z-20 flex items-center justify-between px-2.5 h-4 w-20 rounded-full bg-black/90 border border-white/10">
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                          <div className="h-2 w-2 rounded-full bg-[#1c2230]" />
                        </div>

                        {/* Screen viewport */}
                        <div className="relative aspect-[9/16] w-full overflow-hidden rounded-[32px] bg-black">
                          <video
                            key={renderJob.output_path}
                            ref={videoRef}
                            controls
                            autoPlay
                            src={renderJob.output_path}
                            className="h-full w-full object-cover"
                          />

                          {/* Overlay simulation badge */}
                          <div className="pointer-events-none absolute bottom-3 left-3 right-3 flex items-center justify-between rounded-lg bg-black/60 backdrop-blur-md px-2.5 py-1.5 border border-white/10 text-[9px] font-mono text-white/90">
                            <span className="flex items-center gap-1.5">
                              <span className="h-1.5 w-1.5 rounded-full bg-hive animate-pulse" />
                              {blueprint.brand.brand_name}
                            </span>
                            <span className="text-gray-300">1080×1920 HD</span>
                          </div>
                        </div>

                        {/* Home Indicator Bar */}
                        <div className="mx-auto mt-2 h-1 w-24 rounded-full bg-white/20" />
                      </div>

                      {/* Interactive Scene Seek Ribbon */}
                      <div className="mt-5 w-full max-w-[330px] rounded-xl border border-border bg-surface-deep p-3 space-y-2">
                        <div className="flex items-center justify-between font-mono text-[9px] text-gray-400">
                          <span>INTERACTIVE SCENE SEEKER</span>
                          <span className="text-hive">{blueprint.scenes.length} BEATS</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {blueprint.scenes.map((scene, idx) => {
                            const offsetSeconds = blueprint.scenes
                              .slice(0, idx)
                              .reduce((acc, s) => acc + s.duration_seconds, 0);
                            return (
                              <button
                                key={scene.scene_id}
                                onClick={() => {
                                  if (videoRef.current) {
                                    videoRef.current.currentTime = offsetSeconds;
                                    videoRef.current.play();
                                  }
                                }}
                                className={cn(
                                  "rounded px-2 py-0.5 text-[9px] font-mono border transition-all hover:scale-105",
                                  BEAT_COLORS[scene.emotional_beat] || "border-border bg-surface text-gray-400"
                                )}
                                title={`Jump to ${scene.scene_id} (${offsetSeconds.toFixed(1)}s)`}
                              >
                                {scene.emotional_beat.toUpperCase()} ({offsetSeconds.toFixed(0)}s)
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Actions, Specs & Virality Scorecard */}
                  <div className="lg:col-span-7 space-y-4">
                    <div className="rounded-xl border border-border bg-surface-deep p-5 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[9px] text-gray-500 uppercase">DELIVERABLE TITLE</span>
                        <span className="font-mono text-[9px] text-emerald-400 border border-emerald-500/30 bg-emerald-500/10 rounded px-2 py-0.5">
                          FFMPEG RENDER READY
                        </span>
                      </div>
                      <h4 className="font-display text-lg font-semibold text-gray-100">{blueprint.title}</h4>
                      <p className="text-xs text-gray-400 italic">"{blueprint.scenes[0]?.audio.voiceover_text}"</p>
                    </div>

                    {/* Production Specifications Table */}
                    <div className="rounded-xl border border-border bg-surface-deep p-4 space-y-2.5">
                      <div className="font-mono text-[9px] text-gray-400 uppercase tracking-wider">
                        RENDER SPECIFICATIONS & TELEMETRY
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-[10px] font-mono">
                        <div className="rounded border border-border bg-surface p-2">
                          <span className="text-gray-500 block text-[8px]">RESOLUTION</span>
                          <span className="text-gray-200 font-semibold">1080 × 1920 (9:16)</span>
                        </div>
                        <div className="rounded border border-border bg-surface p-2">
                          <span className="text-gray-500 block text-[8px]">ENCODING</span>
                          <span className="text-gray-200 font-semibold">H.264 / AAC 30 FPS</span>
                        </div>
                        <div className="rounded border border-border bg-surface p-2">
                          <span className="text-gray-500 block text-[8px]">FILE SIZE</span>
                          <span className="text-hive font-semibold">{renderJob.file_size_mb} MB</span>
                        </div>
                        <div className="rounded border border-border bg-surface p-2">
                          <span className="text-gray-500 block text-[8px]">TOTAL DURATION</span>
                          <span className="text-gray-200 font-semibold">{renderJob.duration_seconds}s</span>
                        </div>
                        <div className="rounded border border-border bg-surface p-2">
                          <span className="text-gray-500 block text-[8px]">RENDER ENGINE</span>
                          <span className="text-gray-200 font-semibold">FFmpeg v7.1 GPU/CPU</span>
                        </div>
                        <div className="rounded border border-border bg-surface p-2">
                          <span className="text-gray-500 block text-[8px]">VIRALITY RATING</span>
                          <span className="text-emerald-400 font-bold font-mono">
                            {blueprint.virality_score?.overall_score || 94}/100
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Virality Scorecard Breakdown */}
                    {blueprint.virality_score && (
                      <div className="rounded-xl border border-border bg-surface-deep p-4 space-y-3">
                        <div className="flex items-center justify-between text-[10px] font-mono">
                          <span className="text-gray-400">VIRALITY SCORECARD BREAKDOWN</span>
                          <span className="text-hive font-bold">
                            {blueprint.virality_score.recommendation}
                          </span>
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-center text-[10px] font-mono">
                          <div className="rounded border border-border bg-surface p-2">
                            <span className="text-gray-500 block text-[8px]">HOOK STRENGTH</span>
                            <span className="text-emerald-400 font-bold">
                              {blueprint.virality_score.hook_strength}/100
                            </span>
                          </div>
                          <div className="rounded border border-border bg-surface p-2">
                            <span className="text-gray-500 block text-[8px]">PACING QUALITY</span>
                            <span className="text-hive font-bold">
                              {blueprint.virality_score.pacing_quality}/100
                            </span>
                          </div>
                          <div className="rounded border border-border bg-surface p-2">
                            <span className="text-gray-500 block text-[8px]">SHAREABILITY</span>
                            <span className="text-blue-400 font-bold">
                              {blueprint.virality_score.shareability}/100
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Action Triggers */}
                    <div className="flex flex-col gap-2.5 pt-2">
                      <div className="grid grid-cols-2 gap-2">
                        <a
                          href={renderJob.output_path}
                          download={`${blueprint.blueprint_id}.mp4`}
                          className="flex items-center justify-center gap-2 rounded-xl bg-hive px-4 py-3 font-mono text-xs font-bold text-[#090b10] hover:bg-hive-400 transition-all shadow-[0_0_20px_rgba(245,166,35,0.25)]"
                        >
                          <ArrowDownToLine size={15} />
                          DOWNLOAD MP4
                        </a>
                        <a
                          href={renderJob.output_path}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center justify-center gap-2 rounded-xl border border-hive/40 bg-hive/10 px-4 py-3 font-mono text-xs font-semibold text-hive hover:bg-hive/20 transition-all"
                        >
                          <ExternalLink size={15} />
                          OPEN IN NEW TAB
                        </a>
                      </div>

                      <button
                        onClick={() => dispatchMutation.mutate()}
                        disabled={dispatchMutation.isPending || dispatchedApproval}
                        className={cn(
                          "flex items-center justify-center gap-2 rounded-xl border px-5 py-3 font-mono text-xs font-semibold transition-all",
                          dispatchedApproval
                            ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400 cursor-default"
                            : "border-border bg-surface-deep text-gray-200 hover:bg-surface hover:border-hive/40"
                        )}
                      >
                        <Send size={14} className={dispatchedApproval ? "text-emerald-400" : "text-hive"} />
                        {dispatchedApproval ? "✓ DISPATCHED TO APPROVAL QUEUE" : "TRANSMIT TO MASTER APPROVAL QUEUE"}
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Film size={36} className="text-gray-600 mb-3" />
                  <h4 className="font-display text-sm font-semibold text-gray-300">No Rendered Video Yet</h4>
                  <p className="text-xs text-gray-500 max-w-sm mt-1 mb-4">
                    Click "Produce & Render MP4" to compile the scene graph, neural voiceover, and visual overlays into a vertical short video.
                  </p>
                  <button
                    onClick={() => renderMutation.mutate(blueprint)}
                    disabled={renderMutation.isPending}
                    className="flex items-center gap-1.5 rounded-lg bg-hive px-4 py-2 font-mono text-xs font-bold text-[#090b10] hover:bg-hive-400"
                  >
                    <Play size={13} className="fill-current" />
                    RENDER THIS BLUEPRINT NOW
                  </button>
                </div>
              )}
            </div>
          )}

          {/* VIDEO VAULT & LIBRARY PANEL */}
          {activePanel === "vault" && (
            <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <Clapperboard size={16} className="text-hive" />
                  <h3 className="font-display text-base font-semibold">Rendered Video Repository</h3>
                </div>
                <button
                  onClick={() => refetchLibrary()}
                  className="rounded border border-border bg-surface-deep px-2.5 py-1 font-mono text-[10px] text-gray-400 hover:text-gray-200"
                >
                  REFRESH VAULT
                </button>
              </div>

              {library.length > 0 ? (
                <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
                  {library.map((item: RenderedVideoItem) => (
                    <div
                      key={item.blueprint_id}
                      className="rounded-lg border border-border bg-surface-deep p-3.5 space-y-3 flex flex-col justify-between"
                    >
                      <div>
                        {item.thumbnail_url ? (
                          <div className="relative aspect-[9/16] max-h-[180px] w-full overflow-hidden rounded border border-border bg-black mb-2">
                            <img src={item.thumbnail_url} alt={item.filename} className="h-full w-full object-cover" />
                          </div>
                        ) : (
                          <div className="flex items-center justify-center aspect-[9/16] max-h-[140px] rounded border border-border bg-black mb-2">
                            <Film size={24} className="text-gray-600" />
                          </div>
                        )}
                        <b className="block font-mono text-xs text-gray-200 truncate">{item.filename}</b>
                        <div className="flex items-center justify-between text-[10px] font-mono text-gray-500 mt-1">
                          <span>{item.size_mb} MB</span>
                          <span>{new Date(item.created_at).toLocaleTimeString()}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 pt-2 border-t border-border">
                        <button
                          onClick={() => {
                            setRenderJob({
                              job_id: `job-${item.blueprint_id}`,
                              blueprint_id: item.blueprint_id,
                              worker_id: "tech",
                              status: "complete",
                              progress_pct: 100.0,
                              output_path: item.video_url,
                              thumbnail_path: item.thumbnail_url,
                              duration_seconds: 15.0,
                              file_size_mb: item.size_mb,
                            });
                            setActivePanel("player");
                          }}
                          className="flex-1 rounded bg-surface border border-border px-2 py-1.5 text-center font-mono text-[10px] text-gray-200 hover:text-white hover:border-hive/50"
                        >
                          WATCH PREVIEW
                        </button>
                        <a
                          href={item.video_url}
                          download={item.filename}
                          className="rounded bg-hive px-2.5 py-1.5 text-center font-mono text-[10px] font-bold text-[#090b10] hover:bg-hive-400"
                        >
                          DOWNLOAD
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500 text-xs">
                  No videos rendered yet. Generate a blueprint and click "Produce & Render MP4".
                </div>
              )}
            </div>
          )}

          {/* SCENE CLIPS & INTERACTIVE VIDEO EDITOR PANEL */}
          {activePanel === "scenes" && (
            <div className="space-y-6">
              {/* Top Storyboard Strip: Horizontal Visual Scene Cards */}
              <div className="rounded-xl border border-border bg-surface p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Scissors size={15} className="text-hive" />
                    <span className="font-mono text-xs font-semibold text-gray-200">
                      INTERACTIVE STORYBOARD & CLIP REPOSITORY
                    </span>
                    <span className="rounded bg-hive/10 px-2 py-0.5 font-mono text-[9px] text-hive border border-hive/20">
                      {blueprint.scenes.length} INDEPENDENT SCENES
                    </span>
                  </div>
                  <span className="font-mono text-[10px] text-gray-400">
                    Click any scene to inspect, play isolated clip, or edit & regenerate
                  </span>
                </div>

                <div className="flex gap-3 overflow-x-auto pb-2 pt-1 scrollbar-thin">
                  {blueprint.scenes.map((scene, i) => {
                    const isActive = selectedSceneId === scene.scene_id;
                    const clip = activeClips.find((c) => c.scene_idx === i);
                    return (
                      <button
                        key={scene.scene_id}
                        onClick={() => setSelectedSceneId(scene.scene_id)}
                        className={cn(
                          "group relative flex-shrink-0 w-44 rounded-xl border p-2.5 text-left transition-all",
                          isActive
                            ? "border-hive bg-hive/10 shadow-[0_0_20px_rgba(245,166,35,0.18)] scale-[1.02]"
                            : "border-border bg-surface-deep hover:border-gray-500 hover:bg-surface"
                        )}
                      >
                        {/* Visual Thumbnail Frame */}
                        <div className="relative aspect-[9/16] w-full overflow-hidden rounded-lg bg-black border border-white/10 mb-2">
                          {clip?.thumbnail_path ? (
                            <img
                              src={clip.thumbnail_path}
                              alt={`Scene ${i + 1}`}
                              className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
                            />
                          ) : clip?.overlay_path ? (
                            <div className="h-full w-full bg-gradient-to-b from-[#151c2c] to-[#0c1017] p-2 flex flex-col items-center justify-center text-center">
                              <img src={clip.overlay_path} alt="Overlay" className="max-h-full object-contain" />
                            </div>
                          ) : (
                            <div className="h-full w-full bg-gradient-to-b from-[#182030] to-[#0d121c] p-2.5 flex flex-col items-center justify-center text-center space-y-1.5">
                              <Film size={22} className="text-gray-600 group-hover:text-hive transition-colors" />
                              <span className="font-mono text-[8px] text-gray-500 uppercase tracking-wider">
                                {scene.visual.camera_motion.replace("_", " ")}
                              </span>
                            </div>
                          )}

                          {/* Hover Play Button Overlay */}
                          {clip?.clip_path && (
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                              <span className="flex items-center gap-1 rounded-full bg-hive px-2.5 py-1 text-[9px] font-mono font-bold text-[#090b10] shadow-lg">
                                <Play size={10} className="fill-current" />
                                PLAY CLIP
                              </span>
                            </div>
                          )}

                          {/* Beat Badge Top */}
                          <div className="absolute top-1.5 left-1.5 right-1.5 flex items-center justify-between pointer-events-none">
                            <span className={cn("rounded px-1.5 py-0.5 text-[8px] font-mono font-bold border backdrop-blur-md shadow", BEAT_COLORS[scene.emotional_beat] || "")}>
                              S{i + 1}: {scene.emotional_beat.toUpperCase()}
                            </span>
                            <span className="rounded bg-black/70 backdrop-blur-md px-1.5 py-0.5 text-[8px] font-mono text-gray-300 border border-white/10">
                              {scene.duration_seconds.toFixed(1)}s
                            </span>
                          </div>

                          {/* Ready / Status Badge Bottom */}
                          <div className="absolute bottom-1.5 left-1.5 pointer-events-none">
                            {clip?.clip_path ? (
                              <span className="flex items-center gap-1 rounded bg-emerald-500/80 backdrop-blur-md px-1.5 py-0.5 text-[7px] font-mono text-white font-semibold">
                                <Check size={8} />
                                READY
                              </span>
                            ) : (
                              <span className="rounded bg-black/60 backdrop-blur-md px-1.5 py-0.5 text-[7px] font-mono text-gray-400">
                                PENDING
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Voiceover preview line */}
                        <div className="text-[10px] text-gray-300 line-clamp-2 leading-tight">
                          {scene.audio.voiceover_text}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 2-Column Split: Scene Clip Viewer (Left) + Interactive Scene Editor (Right) */}
              <div className="grid gap-6 lg:grid-cols-12">
                {/* Left Column (5 cols): Focused Scene Clip Player & Layer Diagnostic */}
                <div className="lg:col-span-5 rounded-xl border border-border bg-surface p-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-border pb-3">
                    <div className="flex items-center gap-2">
                      <FileVideo size={16} className="text-hive" />
                      <h3 className="font-display text-sm font-semibold text-gray-100">
                        Scene {selectedSceneIndex + 1} Clip Viewer
                      </h3>
                    </div>
                    {currentSceneClip?.clip_path && (
                      <span className="font-mono text-[9px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 rounded px-2 py-0.5">
                        ✓ RENDERED 1080×1920
                      </span>
                    )}
                  </div>

                  {/* Layer Tabs: Composited Clip vs Subtitle Overlay vs Narration Audio */}
                  <div className="flex items-center gap-1 rounded-lg border border-border bg-surface-deep p-1 font-mono text-[9px]">
                    <button
                      onClick={() => setSceneLayerTab("clip")}
                      className={cn(
                        "flex-1 rounded py-1.5 text-center transition-colors font-medium",
                        sceneLayerTab === "clip" ? "bg-hive text-[#090b10] font-bold" : "text-gray-400 hover:text-gray-200"
                      )}
                    >
                      ★ COMPOSITED CLIP
                    </button>
                    <button
                      onClick={() => setSceneLayerTab("overlay")}
                      className={cn(
                        "flex-1 rounded py-1.5 text-center transition-colors font-medium",
                        sceneLayerTab === "overlay" ? "bg-hive text-[#090b10] font-bold" : "text-gray-400 hover:text-gray-200"
                      )}
                    >
                      SUBTITLES ONLY
                    </button>
                    <button
                      onClick={() => setSceneLayerTab("audio")}
                      className={cn(
                        "flex-1 rounded py-1.5 text-center transition-colors font-medium",
                        sceneLayerTab === "audio" ? "bg-hive text-[#090b10] font-bold" : "text-gray-400 hover:text-gray-200"
                      )}
                    >
                      VOICEOVER AUDIO
                    </button>
                  </div>

                  {/* Scene Clip Smartphone Frame */}
                  <div className="relative mx-auto w-full max-w-[280px] rounded-[36px] border-[4px] border-[#222834] bg-[#0c1017] p-2 shadow-2xl ring-1 ring-white/10">
                    <div className="relative aspect-[9/16] w-full overflow-hidden rounded-[28px] bg-black">
                      {sceneLayerTab === "clip" && currentSceneClip?.clip_path ? (
                        <video
                          key={currentSceneClip.clip_path}
                          ref={sceneVideoRef}
                          controls
                          autoPlay
                          loop
                          src={currentSceneClip.clip_path}
                          className="h-full w-full object-cover"
                        />
                      ) : sceneLayerTab === "overlay" && currentSceneClip?.overlay_path ? (
                        <div className="h-full w-full bg-gradient-to-b from-[#182030] to-[#0c1017] flex items-center justify-center p-3">
                          <img src={currentSceneClip.overlay_path} alt="Subtitle Layer" className="w-full object-contain" />
                        </div>
                      ) : sceneLayerTab === "audio" && currentSceneClip?.voice_path ? (
                        <div className="h-full w-full bg-gradient-to-b from-[#1a2336] to-[#0d121c] flex flex-col items-center justify-center p-4 text-center space-y-4">
                          <div className="h-16 w-16 rounded-full bg-hive/20 border border-hive/40 flex items-center justify-center text-hive">
                            <Volume2 size={28} />
                          </div>
                          <div>
                            <span className="font-mono text-[9px] text-hive uppercase tracking-widest block">NEURAL VOICE CADENCE</span>
                            <span className="text-xs text-gray-300 font-medium line-clamp-3 mt-1">"{selectedScene?.audio.voiceover_text}"</span>
                          </div>
                          <audio controls src={currentSceneClip.voice_path} className="w-full h-8" />
                        </div>
                      ) : (
                        <div className="h-full w-full bg-gradient-to-b from-[#182030] to-[#0c1017] flex flex-col items-center justify-center p-4 text-center space-y-2">
                          <Film size={32} className="text-gray-600" />
                          <span className="font-mono text-[10px] text-gray-400">Clip not rendered yet</span>
                          <p className="text-[9px] text-gray-500 max-w-[200px]">
                            Click "Regenerate This Scene" on the right or run full render to preview this clip.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Scene Quality Verification Checklist */}
                  <div className="rounded-lg border border-border bg-surface-deep p-3.5 space-y-2 text-[10px] font-mono">
                    <span className="font-bold text-gray-400 block tracking-wider text-[9px]">SCENE QUALITY DIAGNOSTICS</span>
                    <div className="flex items-center justify-between text-gray-300">
                      <span>VISUAL SOURCING:</span>
                      <span className="text-hive">{selectedScene?.visual.camera_motion.replace("_", " ")}</span>
                    </div>
                    <div className="flex items-center justify-between text-gray-300">
                      <span>SUBTITLE POSITION:</span>
                      <span className="text-emerald-400 font-bold uppercase">{editedCaptionPosition} (Viral Safe Zone)</span>
                    </div>
                    <div className="flex items-center justify-between text-gray-300">
                      <span>HIGHLIGHT COLOR:</span>
                      <span className="flex items-center gap-1.5 text-hive">
                        <span className="h-2 w-2 rounded-full border border-white/40" style={{ backgroundColor: editedHighlightColor }} />
                        {editedHighlightColor}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-gray-300">
                      <span>DURATION & SYNC:</span>
                      <span>{selectedScene?.duration_seconds.toFixed(1)}s (Locked — 0.00s Overlap)</span>
                    </div>
                    {currentSceneClip?.clip_path && (
                      <div className="flex items-center justify-between text-gray-300 pt-1 border-t border-border">
                        <span>CLIP ARTIFACT:</span>
                        <a href={currentSceneClip.clip_path} download className="text-hive hover:underline flex items-center gap-1">
                          <Download size={10} />
                          scene_{selectedSceneIndex}.mp4
                        </a>
                      </div>
                    )}
                  </div>
                </div>

                {/* Right Column (7 cols): Interactive Scene Editor & Regenerator */}
                <div className="lg:col-span-7 rounded-xl border border-border bg-surface p-5 space-y-4">
                  {selectedScene ? (
                    <>
                      <div className="flex items-center justify-between border-b border-border pb-3">
                        <div>
                          <div className="font-mono text-[9px] text-gray-400">
                            INTERACTIVE SCENE EDITOR — SCENE {selectedSceneIndex + 1} OF {blueprint.scenes.length}
                          </div>
                          <h3 className="font-display text-lg font-semibold mt-0.5">{selectedScene.scene_id}</h3>
                        </div>

                        {/* Navigation controls */}
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              if (selectedSceneIndex > 0) {
                                setSelectedSceneId(blueprint.scenes[selectedSceneIndex - 1].scene_id);
                              }
                            }}
                            disabled={selectedSceneIndex <= 0}
                            className="rounded border border-border bg-surface-deep p-1.5 text-gray-300 hover:text-white disabled:opacity-30"
                            title="Previous Scene"
                          >
                            <ChevronLeft size={14} />
                          </button>
                          <span className="font-mono text-[10px] text-gray-400">
                            {selectedSceneIndex + 1} / {blueprint.scenes.length}
                          </span>
                          <button
                            onClick={() => {
                              if (selectedSceneIndex < blueprint.scenes.length - 1) {
                                setSelectedSceneId(blueprint.scenes[selectedSceneIndex + 1].scene_id);
                              }
                            }}
                            disabled={selectedSceneIndex >= blueprint.scenes.length - 1}
                            className="rounded border border-border bg-surface-deep p-1.5 text-gray-300 hover:text-white disabled:opacity-30"
                            title="Next Scene"
                          >
                            <ChevronRight size={14} />
                          </button>
                        </div>
                      </div>

                      {/* Field 1: Voiceover Narration */}
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between">
                          <label className="font-mono text-[9px] text-gray-400 uppercase tracking-wider">
                            VOICEOVER NARRATION TEXT
                          </label>
                          <span className="font-mono text-[9px] text-gray-500">
                            {editedVoiceover.split(/\s+/).filter(Boolean).length} words
                          </span>
                        </div>
                        <textarea
                          rows={3}
                          value={editedVoiceover}
                          onChange={(e) => setEditedVoiceover(e.target.value)}
                          className="w-full rounded-lg border border-border bg-surface-deep p-3 text-xs text-gray-100 outline-none focus:border-hive/50 font-sans leading-relaxed"
                          placeholder="Enter exact narration text for this scene..."
                        />
                      </div>

                      {/* Field 2 & 3: Keywords & Camera Motion */}
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div className="space-y-1.5">
                          <label className="font-mono text-[9px] text-gray-400 uppercase tracking-wider">
                            B-ROLL SEARCH KEYWORDS
                          </label>
                          <input
                            type="text"
                            value={editedKeywords}
                            onChange={(e) => setEditedKeywords(e.target.value)}
                            className="w-full rounded-lg border border-border bg-surface-deep px-3 py-2 text-xs text-gray-200 outline-none focus:border-hive/50 font-mono"
                            placeholder="e.g. fashion, runway, luxury"
                          />
                        </div>

                        <div className="space-y-1.5">
                          <label className="font-mono text-[9px] text-gray-400 uppercase tracking-wider">
                            CAMERA MOTION
                          </label>
                          <select
                            value={editedMotion}
                            onChange={(e) => setEditedMotion(e.target.value)}
                            className="w-full rounded-lg border border-border bg-surface-deep px-3 py-2 text-xs text-gray-200 outline-none focus:border-hive/50 font-mono"
                          >
                            <option value="slow_zoom_in">Slow Zoom In (Hook & Punch)</option>
                            <option value="pan_left">Cinematic Pan Left</option>
                            <option value="slow_zoom_out">Slow Zoom Out (Reveal)</option>
                            <option value="pan_right">Cinematic Pan Right</option>
                            <option value="ken_burns">Ken Burns Diagonal Drift</option>
                          </select>
                        </div>
                      </div>

                      {/* Subtitle Positioning & Styling Controls */}
                      <div className="rounded-xl border border-border bg-surface-deep p-3.5 space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5 font-mono text-[9px] text-gray-300 font-semibold uppercase tracking-wider">
                            <Type size={12} className="text-hive" />
                            <span>SUBTITLE POSITIONING & STYLING</span>
                          </div>
                          <span className="font-mono text-[8px] text-hive bg-hive/10 border border-hive/20 rounded px-1.5 py-0.5">
                            VIRAL LOWER-THIRD DEFAULT
                          </span>
                        </div>

                        <div className="grid gap-3 sm:grid-cols-2">
                          {/* Position Selector */}
                          <div className="space-y-1.5">
                            <label className="font-mono text-[9px] text-gray-400 uppercase tracking-wider block">
                              CAPTION POSITION
                            </label>
                            <div className="grid grid-cols-3 gap-1 rounded-lg border border-border bg-surface p-1 text-center font-mono text-[9px]">
                              {[
                                { id: "bottom" as const, label: "BOTTOM" },
                                { id: "center" as const, label: "CENTER" },
                                { id: "top" as const, label: "TOP" },
                              ].map((pos) => (
                                <button
                                  key={pos.id}
                                  type="button"
                                  onClick={() => setEditedCaptionPosition(pos.id)}
                                  className={cn(
                                    "rounded py-1.5 font-bold transition-colors",
                                    editedCaptionPosition === pos.id
                                      ? "bg-hive text-[#090b10] shadow"
                                      : "text-gray-400 hover:text-gray-200"
                                  )}
                                >
                                  {pos.label}
                                </button>
                              ))}
                            </div>
                          </div>

                          {/* Style Selector */}
                          <div className="space-y-1.5">
                            <label className="font-mono text-[9px] text-gray-400 uppercase tracking-wider block">
                              CAPTION STYLE
                            </label>
                            <div className="grid grid-cols-3 gap-1 rounded-lg border border-border bg-surface p-1 text-center font-mono text-[9px]">
                              {[
                                { id: "pill" as const, label: "PILL" },
                                { id: "outline" as const, label: "STROKE" },
                                { id: "minimal" as const, label: "MINIMAL" },
                              ].map((st) => (
                                <button
                                  key={st.id}
                                  type="button"
                                  onClick={() => setEditedCaptionStyle(st.id)}
                                  className={cn(
                                    "rounded py-1.5 font-bold transition-colors",
                                    editedCaptionStyle === st.id
                                      ? "bg-hive text-[#090b10] shadow"
                                      : "text-gray-400 hover:text-gray-200"
                                  )}
                                >
                                  {st.label}
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Highlight Color & Font Size Row */}
                        <div className="grid gap-3 sm:grid-cols-2 pt-1 border-t border-border/50">
                          <div className="space-y-1.5">
                            <label className="font-mono text-[9px] text-gray-400 uppercase tracking-wider block">
                              HIGHLIGHT COLOR
                            </label>
                            <div className="flex items-center gap-1.5">
                              {[
                                { color: "#FFE600", name: "Gold" },
                                { color: "#00FF66", name: "Neon" },
                                { color: "#00F0FF", name: "Cyan" },
                                { color: "#FF5757", name: "Coral" },
                                { color: "#FFFFFF", name: "White" },
                              ].map((c) => (
                                <button
                                  key={c.color}
                                  type="button"
                                  onClick={() => setEditedHighlightColor(c.color)}
                                  className={cn(
                                    "h-6 w-6 rounded-full border-2 transition-transform hover:scale-110",
                                    editedHighlightColor.toUpperCase() === c.color.toUpperCase()
                                      ? "border-white scale-110 ring-2 ring-hive/40"
                                      : "border-transparent opacity-80"
                                  )}
                                  style={{ backgroundColor: c.color }}
                                  title={c.name}
                                />
                              ))}
                              <span className="font-mono text-[9px] text-gray-400 ml-1">{editedHighlightColor}</span>
                            </div>
                          </div>

                          <div className="space-y-1.5">
                            <div className="flex items-center justify-between">
                              <label className="font-mono text-[9px] text-gray-400 uppercase tracking-wider block">
                                FONT SIZE
                              </label>
                              <span className="font-mono text-[9px] text-hive">{editedFontSize}px</span>
                            </div>
                            <div className="grid grid-cols-3 gap-1 rounded-lg border border-border bg-surface p-1 text-center font-mono text-[9px]">
                              {[
                                { size: 54, label: "54px" },
                                { size: 72, label: "72px" },
                                { size: 84, label: "84px" },
                              ].map((sz) => (
                                <button
                                  key={sz.size}
                                  type="button"
                                  onClick={() => setEditedFontSize(sz.size)}
                                  className={cn(
                                    "rounded py-1 font-bold transition-colors",
                                    editedFontSize === sz.size
                                      ? "bg-hive text-[#090b10] shadow"
                                      : "text-gray-400 hover:text-gray-200"
                                  )}
                                >
                                  {sz.label}
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Field 4: Visual Footage & Background Asset Selector */}
                      <div className="space-y-2 rounded-xl border border-border bg-surface-deep p-3.5">
                        <div className="flex items-center justify-between">
                          <label className="font-mono text-[9px] text-gray-400 uppercase tracking-wider">
                            VISUAL FOOTAGE & BACKGROUND ASSET
                          </label>
                          <div className="flex items-center gap-2">
                            {selectedVaultAsset && (
                              <button
                                onClick={() => setSelectedVaultAsset("")}
                                className="text-[9px] font-mono text-red-400 hover:underline"
                              >
                                RESET TO DYNAMIC MATCH
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => setIsAssetPickerOpen(true)}
                              className="flex items-center gap-1 rounded bg-hive/10 border border-hive/30 px-2.5 py-1 font-mono text-[9px] font-bold text-hive hover:bg-hive/20"
                            >
                              <Clapperboard size={10} />
                              BROWSE ASSET VAULT ({stockMaterials.length + vaultAssets.length})
                            </button>
                          </div>
                        </div>

                        {selectedVaultAsset ? (
                          <div className="flex items-center justify-between rounded-lg border border-hive/40 bg-black/40 p-2.5 text-xs">
                            <div className="flex items-center gap-2 truncate">
                              <span className="h-2 w-2 rounded-full bg-emerald-400" />
                              <span className="font-mono text-[10px] text-gray-200 truncate">{selectedVaultAsset}</span>
                            </div>
                            <button
                              type="button"
                              onClick={() => setSelectedVaultAsset("")}
                              className="text-gray-400 hover:text-white p-1"
                              title="Clear override"
                            >
                              <X size={12} />
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between rounded-lg border border-border bg-black/20 p-2.5 text-xs">
                            <span className="font-mono text-[10px] text-gray-400">
                              ⚡ Dynamic AI Stock Matching (Curated Stock Bank / Unsplash HD)
                            </span>
                            <span className="rounded bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 font-mono text-[8px] text-emerald-400">
                              ACTIVE
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Scene Metadata Preview */}
                      <div className="grid grid-cols-3 gap-2.5 rounded-lg border border-border bg-surface-deep p-3 text-[10px] font-mono">
                        <div>
                          <span className="text-gray-500 block text-[8px]">EMOTIONAL BEAT</span>
                          <span className={cn("rounded px-1.5 py-0.5 text-[8px] font-bold border inline-block mt-0.5", BEAT_COLORS[selectedScene.emotional_beat] || "")}>
                            {selectedScene.emotional_beat.toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500 block text-[8px]">RETENTION ZONE</span>
                          <span className="text-gray-300 font-semibold">{selectedScene.retention_zone}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 block text-[8px]">TRANSITION IN</span>
                          <span className="text-hive font-semibold">{selectedScene.transition_in}</span>
                        </div>
                      </div>

                      {/* Action Button: Regenerate Single Scene */}
                      <div className="pt-2">
                        <button
                          onClick={() => regenerateSceneMutation.mutate()}
                          disabled={regenerateSceneMutation.isPending}
                          className={cn(
                            "w-full flex items-center justify-center gap-2 rounded-xl py-3 font-mono text-xs font-bold transition-all shadow-lg",
                            regenerateSceneMutation.isPending
                              ? "bg-hive/50 text-[#090b10] cursor-wait"
                              : "bg-hive text-[#090b10] hover:bg-hive-400 shadow-[0_0_20px_rgba(245,166,35,0.25)]"
                          )}
                        >
                          {regenerateSceneMutation.isPending ? (
                            <>
                              <Loader2 size={14} className="animate-spin" />
                              RE-RENDERING SCENE {selectedSceneIndex + 1} & UPDATING MASTER VIDEO…
                            </>
                          ) : (
                            <>
                              <RefreshCw size={14} />
                              REGENERATE SCENE {selectedSceneIndex + 1} CLIP & RE-STITCH VIDEO
                            </>
                          )}
                        </button>
                        {regenerateSceneMutation.isSuccess && (
                          <div className="mt-2 text-center text-[10px] font-mono text-emerald-400 flex items-center justify-center gap-1">
                            <CheckCircle2 size={12} />
                            Scene {selectedSceneIndex + 1} updated and full master video re-stitched successfully!
                          </div>
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="text-center text-gray-500 py-12">Select a scene from the storyboard above</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* A/B HOOKS PANEL */}
          {activePanel === "hooks" && (
            <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <Zap size={16} className="text-hive" />
                  <h3 className="font-display text-base font-semibold">A/B Hook Variants</h3>
                </div>
                <span className="font-mono text-[9px] text-gray-400">
                  {blueprint.hook_variants.length} variants generated
                </span>
              </div>

              <div className="grid gap-3 md:grid-cols-3">
                {blueprint.hook_variants.map((variant) => {
                  const isSelected = blueprint.selected_hook_variant === variant.variant_id;
                  return (
                    <div
                      key={variant.variant_id}
                      className={cn(
                        "rounded-lg border p-4 space-y-3 transition-all",
                        isSelected
                          ? "border-hive/50 bg-hive/5 shadow-[0_0_15px_rgba(245,166,35,0.1)]"
                          : "border-border bg-surface-deep"
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <span className={cn(
                          "rounded px-2 py-0.5 text-[9px] font-mono font-bold border",
                          isSelected ? "border-hive/50 bg-hive/20 text-hive" : "border-border bg-surface text-gray-400"
                        )}>
                          {variant.hook_archetype.replace("_", " ").toUpperCase()}
                        </span>
                        {isSelected && (
                          <span className="flex items-center gap-1 text-[9px] font-mono text-hive font-bold">
                            <CheckCircle2 size={11} /> SELECTED
                          </span>
                        )}
                      </div>

                      <div>
                        <div className="font-mono text-[9px] text-gray-500 mb-1">{variant.variant_label}</div>
                        <p className="text-sm text-gray-100 font-medium italic">"{variant.hook_text}"</p>
                      </div>

                      <div className="text-[11px] text-gray-400">
                        <div className="font-mono text-[9px] text-gray-500 mb-0.5">VISUAL</div>
                        {variant.hook_visual_description}
                      </div>

                      <div className="flex items-center justify-between border-t border-border pt-2.5">
                        <span className="font-mono text-[9px] text-gray-500">
                          PREDICTED 3s RETENTION
                        </span>
                        <span className={cn(
                          "font-display text-lg font-bold",
                          variant.predicted_retention_3s >= 0.7 ? "text-emerald-400" :
                          variant.predicted_retention_3s >= 0.6 ? "text-hive" : "text-red-400"
                        )}>
                          {(variant.predicted_retention_3s * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* BRAND IDENTITY PANEL */}
          {activePanel === "brand" && (
            <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <Palette size={16} className="text-hive" />
                  <h3 className="font-display text-base font-semibold">Brand Identity System</h3>
                </div>
                <span className="font-mono text-[9px] text-gray-400">
                  {blueprint.brand.brand_name}
                </span>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                {/* Color Palette */}
                <div className="rounded-lg border border-border bg-surface-deep p-4 space-y-3">
                  <div className="font-mono text-[9px] text-gray-400">COLOR PALETTE</div>
                  <div className="grid grid-cols-4 gap-2">
                    {Object.entries(blueprint.brand.colors).filter(([k]) => !k.includes("caption")).map(([key, color]) => (
                      <div key={key} className="text-center">
                        <div className="h-10 rounded-lg border border-border mb-1.5" style={{ backgroundColor: color }} />
                        <div className="font-mono text-[8px] text-gray-500 uppercase">{key.replace("_", " ")}</div>
                        <div className="font-mono text-[9px] text-gray-400">{color}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Typography */}
                <div className="rounded-lg border border-border bg-surface-deep p-4 space-y-3">
                  <div className="font-mono text-[9px] text-gray-400">TYPOGRAPHY</div>
                  <div className="space-y-2.5">
                    <div>
                      <span className="font-mono text-[9px] text-gray-500 block">HEADING</span>
                      <span className="text-sm text-gray-200">{blueprint.brand.typography.heading_font}</span>
                    </div>
                    <div>
                      <span className="font-mono text-[9px] text-gray-500 block">CAPTION</span>
                      <span className="text-sm text-gray-200">{blueprint.brand.typography.caption_font}</span>
                    </div>
                    <div>
                      <span className="font-mono text-[9px] text-gray-500 block">CAPTION SIZE</span>
                      <span className="text-sm text-gray-200">{blueprint.brand.typography.caption_size}px</span>
                    </div>
                  </div>
                </div>

                {/* Voice */}
                <div className="rounded-lg border border-border bg-surface-deep p-4 space-y-3">
                  <div className="font-mono text-[9px] text-gray-400">NEURAL VOICE</div>
                  <div className="space-y-2.5">
                    <div>
                      <span className="font-mono text-[9px] text-gray-500 block">VOICE ID</span>
                      <span className="text-sm text-gray-200">{blueprint.brand.default_voice}</span>
                    </div>
                    <div>
                      <span className="font-mono text-[9px] text-gray-500 block">SPEED</span>
                      <span className="text-sm text-gray-200">{blueprint.brand.voice_speed}×</span>
                    </div>
                  </div>
                </div>

                {/* Export Formats */}
                <div className="rounded-lg border border-border bg-surface-deep p-4 space-y-3">
                  <div className="font-mono text-[9px] text-gray-400">EXPORT FORMATS</div>
                  <div className="flex gap-3">
                    {blueprint.target_platforms.map((p) => (
                      <span key={p} className="rounded-lg border border-border bg-surface px-3 py-1.5 text-[10px] font-mono text-gray-300">
                        {p.replace("_", " ")}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* THUMBNAIL PANEL */}
          {activePanel === "thumbnail" && (
            <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
              <div className="flex items-center gap-2 border-b border-border pb-3">
                <ImageIcon size={16} className="text-hive" />
                <h3 className="font-display text-base font-semibold">Thumbnail Composition</h3>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                {/* Thumbnail Preview */}
                <div
                  className="rounded-xl border-2 border-border flex flex-col items-center justify-center p-8 space-y-4"
                  style={{
                    backgroundColor: blueprint.brand.colors.secondary,
                    aspectRatio: "16/9",
                    minHeight: "240px",
                  }}
                >
                  <div
                    className="font-display text-2xl font-bold text-center px-4 leading-tight"
                    style={{ color: blueprint.brand.colors.text_primary }}
                  >
                    {blueprint.thumbnail.headline_text}
                  </div>
                  {blueprint.thumbnail.subtext && (
                    <div className="font-mono text-xs" style={{ color: blueprint.brand.colors.primary }}>
                      {blueprint.thumbnail.subtext}
                    </div>
                  )}
                  {blueprint.thumbnail.arrow_or_circle && (
                    <div className="text-red-500 text-3xl font-bold">⬇</div>
                  )}
                </div>

                {/* Thumbnail Config */}
                <div className="space-y-3">
                  <div className="rounded-lg border border-border bg-surface-deep p-3">
                    <span className="font-mono text-[9px] text-gray-500 block mb-1">HEADLINE</span>
                    <span className="text-sm text-gray-200 font-semibold">{blueprint.thumbnail.headline_text}</span>
                  </div>
                  <div className="rounded-lg border border-border bg-surface-deep p-3">
                    <span className="font-mono text-[9px] text-gray-500 block mb-1">EMOTION</span>
                    <span className="text-sm text-gray-200">{blueprint.thumbnail.emotion}</span>
                  </div>
                  <div className="rounded-lg border border-border bg-surface-deep p-3">
                    <span className="font-mono text-[9px] text-gray-500 block mb-1">LAYOUT</span>
                    <span className="text-sm text-gray-200">{blueprint.thumbnail.layout.replace(/_/g, " ")}</span>
                  </div>
                  <div className="rounded-lg border border-border bg-surface-deep p-3">
                    <span className="font-mono text-[9px] text-gray-500 block mb-1">B-ROLL KEYWORDS</span>
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {blueprint.thumbnail.background_image_keywords.map((kw) => (
                        <span key={kw} className="rounded bg-surface px-2 py-0.5 text-[10px] text-gray-300 border border-border">
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* FULL SCRIPT PANEL */}
          {activePanel === "score" && (
            <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
              <div className="flex items-center gap-2 border-b border-border pb-3">
                <Type size={16} className="text-hive" />
                <h3 className="font-display text-base font-semibold">Full Video Script</h3>
              </div>

              <div className="space-y-3">
                {blueprint.scenes.map((scene, i) => (
                  <div key={scene.scene_id} className="rounded-lg border border-border bg-surface-deep p-4">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-mono text-[10px] text-gray-500 w-6">{String(i + 1).padStart(2, "0")}</span>
                      <span className={cn("rounded px-1.5 py-0.5 text-[9px] font-mono font-bold border", BEAT_COLORS[scene.emotional_beat] || "")}>
                        {scene.emotional_beat.toUpperCase()}
                      </span>
                      <span className="font-mono text-[10px] text-gray-500">{scene.duration_seconds.toFixed(1)}s</span>
                      <span className="ml-auto font-mono text-[9px] text-gray-600">{scene.visual.visual_type}</span>
                    </div>
                    <p className="text-sm text-gray-100 pl-9">
                      {scene.audio.voiceover_text}
                    </p>
                    {scene.pacing_note && (
                      <p className="text-[10px] text-gray-500 italic pl-9 mt-1">
                        ↳ {scene.pacing_note}
                      </p>
                    )}
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-3 pt-2">
                <div className="rounded-lg border border-border bg-surface-deep px-3 py-2 font-mono text-[10px] text-gray-400">
                  Total: {blueprint.total_duration_seconds.toFixed(1)}s
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {blueprint.hashtags.map((tag) => (
                    <span key={tag} className="rounded bg-surface px-2 py-0.5 text-[10px] text-hive border border-hive/20">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* MEDIA VAULT & AUTOMATED HARVESTER PANEL */}
          {activePanel === "vault" && (
            <div className="rounded-xl border border-border bg-surface p-6 space-y-6">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Clapperboard size={18} className="text-hive" />
                    <h3 className="font-display text-lg font-semibold">Automated Media Vault & Harvester</h3>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Continuous automated stock video & photography ingestion powered by Unsplash, Wikimedia & yt-dlp.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => harvestBatchMutation.mutate()}
                    disabled={harvestBatchMutation.isPending}
                    className="flex items-center gap-1.5 rounded-lg bg-hive px-4 py-2 font-mono text-xs font-semibold text-[#090b10] hover:bg-hive-400 transition-colors disabled:opacity-50"
                  >
                    {harvestBatchMutation.isPending ? (
                      <Loader2 size={13} className="animate-spin" />
                    ) : (
                      <Sparkles size={13} />
                    )}
                    {harvestBatchMutation.isPending ? "HARVESTING..." : "HARVEST STOCK BATCH (4 CLIPS)"}
                  </button>
                </div>
              </div>

              {/* Automated URL Ingestion (yt-dlp) */}
              <div className="rounded-lg border border-border bg-surface-deep p-4 space-y-3">
                <div className="flex items-center gap-2 font-mono text-xs font-semibold text-gray-200">
                  <Link2 size={14} className="text-hive" />
                  <span>AUTOMATED URL HARVESTER (YT-DLP)</span>
                </div>
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="url"
                    value={importUrl}
                    onChange={(e) => setImportUrl(e.target.value)}
                    placeholder="Paste YouTube Shorts, video link, or direct MP4 URL to automatically cut & harvest..."
                    className="flex-1 rounded-lg border border-border bg-surface px-3 py-2 text-xs text-gray-200 outline-none focus:border-hive/50"
                  />
                  <button
                    onClick={() => harvestUrlMutation.mutate()}
                    disabled={harvestUrlMutation.isPending || !importUrl.trim()}
                    className="flex items-center justify-center gap-1.5 rounded-lg bg-surface border border-hive/40 px-4 py-2 font-mono text-xs text-hive hover:bg-hive/10 disabled:opacity-50 transition-colors"
                  >
                    {harvestUrlMutation.isPending ? (
                      <Loader2 size={13} className="animate-spin" />
                    ) : (
                      <Download size={13} />
                    )}
                    {harvestUrlMutation.isPending ? "INGESTING..." : "INGEST & CUT 9:16"}
                  </button>
                </div>
              </div>

              {/* Niche Filter Pills */}
              <div className="flex items-center gap-2 font-mono text-xs">
                <span className="text-gray-500 text-[10px] uppercase">NICHE FILTER:</span>
                {["tech", "business", "curiosity", "lifestyle", "entertainment"].map((n) => (
                  <button
                    key={n}
                    onClick={() => setVaultNiche(n)}
                    className={cn(
                      "rounded-lg px-3 py-1 text-[11px] font-mono capitalize transition-colors border",
                      vaultNiche === n
                        ? "bg-hive/20 border-hive text-hive font-semibold"
                        : "border-border text-gray-400 hover:text-gray-200"
                    )}
                  >
                    {n}
                  </button>
                ))}
              </div>

              {/* Vault Assets Grid */}
              <div className="space-y-3">
                <div className="flex items-center justify-between font-mono text-xs text-gray-400">
                  <span>PRE-CACHED 9:16 VERTICAL ASSETS ({vaultAssets.length})</span>
                  {isFetchingVault && <span className="text-hive flex items-center gap-1"><Loader2 size={11} className="animate-spin" /> Updating vault...</span>}
                </div>

                {vaultAssets.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-border p-8 text-center space-y-2">
                    <p className="text-xs text-gray-400">No pre-cached assets found in vault for niche "{vaultNiche}".</p>
                    <p className="text-[11px] text-gray-500">
                      Click <strong>"HARVEST STOCK BATCH"</strong> above or paste a video URL to automatically ingest clips!
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
                    {vaultAssets.map((asset) => (
                      <div key={asset.asset_id} className="rounded-lg border border-border bg-surface-deep overflow-hidden group">
                        <div className="aspect-[9/16] relative bg-black">
                          {asset.thumbnail_url ? (
                            <img src={asset.thumbnail_url} alt={asset.filename} className="w-full h-full object-cover" />
                          ) : (
                            <video src={asset.relative_url} className="w-full h-full object-cover" />
                          )}
                          <div className="absolute top-2 left-2 rounded bg-black/70 px-1.5 py-0.5 font-mono text-[9px] text-white">
                            {asset.duration_sec}s
                          </div>
                          <div className="absolute top-2 right-2 rounded bg-hive/90 px-1.5 py-0.5 font-mono text-[8px] text-black font-bold uppercase">
                            {asset.source}
                          </div>
                        </div>
                        <div className="p-2 space-y-1">
                          <div className="font-mono text-[10px] text-gray-300 truncate">{asset.filename}</div>
                          <div className="flex flex-wrap gap-1">
                            {asset.tags.slice(0, 3).map((t, idx) => (
                              <span key={idx} className="rounded bg-surface px-1.5 py-0.2 text-[8px] text-gray-400 font-mono">
                                #{t}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Rendered Production History */}
              <div className="pt-4 border-t border-border space-y-3">
                <div className="font-mono text-xs font-semibold text-gray-300">
                  RENDERED SHORT-FORM PRODUCTION HISTORY ({library.length})
                </div>
                <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                  {library.map((item) => (
                    <div key={item.blueprint_id} className="rounded-lg border border-border bg-surface-deep p-3 flex items-center justify-between">
                      <div className="truncate mr-2">
                        <div className="font-mono text-xs text-gray-200 truncate">{item.filename}</div>
                        <div className="font-mono text-[10px] text-gray-500">{item.size_mb} MB • {new Date(item.created_at).toLocaleTimeString()}</div>
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0">
                        <a
                          href={item.video_url}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded p-1.5 text-gray-400 hover:text-hive hover:bg-surface"
                          title="Open in new tab"
                        >
                          <ExternalLink size={13} />
                        </a>
                        <a
                          href={item.video_url}
                          download={item.filename}
                          className="rounded p-1.5 text-gray-400 hover:text-hive hover:bg-surface"
                          title="Download MP4"
                        >
                          <Download size={13} />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Visual Stock & Media Vault Asset Picker Modal */}
      {isAssetPickerOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-4xl max-h-[85vh] flex flex-col rounded-2xl border border-hive/40 bg-[#0c1017] shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-border p-4 bg-surface">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-hive/10 border border-hive/30 text-hive">
                  <Clapperboard size={16} />
                </div>
                <div>
                  <h3 className="font-display text-sm font-semibold text-gray-100">
                    Visual Stock & Media Vault Browser
                  </h3>
                  <p className="font-mono text-[10px] text-gray-400">
                    Select any real photo or motion video to assign directly to Scene {selectedSceneIndex + 1}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsAssetPickerOpen(false)}
                className="rounded-lg border border-border p-1.5 text-gray-400 hover:text-white hover:bg-surface-deep transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            {/* Modal Body: Assets Grid */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              <div className="flex items-center justify-between text-xs font-mono text-gray-400">
                <span>AVAILABLE ASSETS ({stockMaterials.length + vaultAssets.length} total)</span>
                <span className="text-hive">Click an asset card to apply to this scene</span>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
                {/* Option 0: Dynamic Stock Matching */}
                <button
                  type="button"
                  onClick={() => {
                    setSelectedVaultAsset("");
                    setIsAssetPickerOpen(false);
                  }}
                  className={cn(
                    "flex flex-col items-center justify-center rounded-xl border p-4 text-center transition-all h-48",
                    !selectedVaultAsset
                      ? "border-hive bg-hive/10 ring-2 ring-hive/30"
                      : "border-dashed border-border bg-surface-deep hover:border-gray-400"
                  )}
                >
                  <Sparkles size={24} className="text-hive mb-2" />
                  <span className="font-mono text-xs font-bold text-gray-100">Dynamic AI Matching</span>
                  <span className="text-[10px] text-gray-400 mt-1">
                    Auto-fetches best stock photo & camera motion
                  </span>
                  {!selectedVaultAsset && (
                    <span className="mt-2 rounded bg-hive px-2 py-0.5 text-[8px] font-mono font-bold text-[#090b10]">
                      CURRENTLY ACTIVE
                    </span>
                  )}
                </button>

                {/* Stock Materials Library */}
                {stockMaterials.map((item) => {
                  const isSelected = selectedVaultAsset === item.file_path;
                  return (
                    <button
                      key={item.filename}
                      type="button"
                      onClick={() => {
                        setSelectedVaultAsset(item.file_path);
                        setIsAssetPickerOpen(false);
                      }}
                      className={cn(
                        "group relative flex flex-col rounded-xl border overflow-hidden text-left transition-all h-48",
                        isSelected
                          ? "border-hive bg-hive/10 ring-2 ring-hive/40 shadow-lg scale-[1.02]"
                          : "border-border bg-surface-deep hover:border-hive/50 hover:bg-surface"
                      )}
                    >
                      <div className="relative h-28 w-full bg-black overflow-hidden">
                        <img
                          src={item.thumbnail_url || item.relative_url}
                          alt={item.filename}
                          className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                        <span className="absolute top-1.5 left-1.5 rounded bg-black/70 backdrop-blur-md px-1.5 py-0.5 text-[8px] font-mono font-bold text-hive border border-white/10 uppercase">
                          {item.asset_type}
                        </span>
                        <span className="absolute top-1.5 right-1.5 rounded bg-black/70 backdrop-blur-md px-1.5 py-0.5 text-[8px] font-mono text-gray-300 border border-white/10 uppercase">
                          {item.niche}
                        </span>
                        {isSelected && (
                          <div className="absolute inset-0 bg-hive/20 flex items-center justify-center">
                            <span className="rounded-full bg-hive p-1 text-[#090b10]">
                              <Check size={16} />
                            </span>
                          </div>
                        )}
                      </div>

                      <div className="p-2 flex-1 flex flex-col justify-between">
                        <div className="font-mono text-[10px] font-semibold text-gray-200 truncate">
                          {item.filename}
                        </div>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {item.tags.slice(0, 3).map((t) => (
                            <span key={t} className="rounded bg-black/40 px-1 py-0.2 text-[8px] text-gray-400 font-mono">
                              #{t}
                            </span>
                          ))}
                        </div>
                      </div>
                    </button>
                  );
                })}

                {/* Vault Assets */}
                {vaultAssets.map((asset) => {
                  const isSelected = selectedVaultAsset === asset.file_path;
                  return (
                    <button
                      key={asset.asset_id}
                      type="button"
                      onClick={() => {
                        setSelectedVaultAsset(asset.file_path);
                        setIsAssetPickerOpen(false);
                      }}
                      className={cn(
                        "group relative flex flex-col rounded-xl border overflow-hidden text-left transition-all h-48",
                        isSelected
                          ? "border-hive bg-hive/10 ring-2 ring-hive/40 shadow-lg scale-[1.02]"
                          : "border-border bg-surface-deep hover:border-hive/50 hover:bg-surface"
                      )}
                    >
                      <div className="relative h-28 w-full bg-black overflow-hidden">
                        {asset.thumbnail_url ? (
                          <img
                            src={asset.thumbnail_url}
                            alt={asset.filename}
                            className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                        ) : (
                          <div className="flex h-full w-full items-center justify-center bg-[#151c2c]">
                            <Clapperboard size={24} className="text-gray-500" />
                          </div>
                        )}
                        <span className="absolute top-1.5 left-1.5 rounded bg-black/70 backdrop-blur-md px-1.5 py-0.5 text-[8px] font-mono font-bold text-hive border border-white/10 uppercase">
                          VAULT
                        </span>
                        {isSelected && (
                          <div className="absolute inset-0 bg-hive/20 flex items-center justify-center">
                            <span className="rounded-full bg-hive p-1 text-[#090b10]">
                              <Check size={16} />
                            </span>
                          </div>
                        )}
                      </div>

                      <div className="p-2 flex-1 flex flex-col justify-between">
                        <div className="font-mono text-[10px] font-semibold text-gray-200 truncate">
                          {asset.filename}
                        </div>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {asset.tags.slice(0, 3).map((t, idx) => (
                            <span key={idx} className="rounded bg-black/40 px-1 py-0.2 text-[8px] text-gray-400 font-mono">
                              #{t}
                            </span>
                          ))}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between border-t border-border p-3 bg-surface">
              <span className="font-mono text-[10px] text-gray-400 truncate max-w-md">
                Selected: {selectedVaultAsset || "Dynamic AI Matcher"}
              </span>
              <button
                type="button"
                onClick={() => setIsAssetPickerOpen(false)}
                className="rounded-lg bg-hive px-4 py-1.5 font-mono text-xs font-bold text-[#090b10] hover:bg-hive-400"
              >
                DONE
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

