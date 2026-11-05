import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  BrainCircuit,
  CheckCircle2,
  CircleDollarSign,
  Clapperboard,
  Clock,
  Command,
  Eye,
  FileText,
  Film,
  Flame,
  Layers,
  Play,
  Radio,
  Send,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useWorkers, useCreateTask } from "@/hooks/use-workers";
import { useAppStore } from "@/stores/app-store";
import { api, type TaskReport } from "@/lib/api";

export default function OverviewPage() {
  const { data: workers = [] } = useWorkers();
  const { selectedWorkerId, setSelectedWorker } = useAppStore();
  const createTask = useCreateTask();

  const { data: briefing } = useQuery({
    queryKey: ["master-briefing"],
    queryFn: api.masterBriefing,
    refetchInterval: 30_000,
  });

  const { data: revenueSummary } = useQuery({
    queryKey: ["revenue-summary"],
    queryFn: api.revenueSummary,
  });

  const { data: videoLibrary = [] } = useQuery({
    queryKey: ["video-library"],
    queryFn: api.videoLibrary,
  });

  const [platform, setPlatform] = useState<"instagram" | "youtube_shorts" | "x" | "facebook">("instagram");
  const [objective, setObjective] = useState(
    "Research 3 timely content opportunities for this brand. Recommend one short-form video concept with a strong hook, outline, caption, and a realistic monetization angle. Flag claims that need source verification."
  );
  const [report, setReport] = useState<TaskReport | null>(null);

  const active = workers.find((w) => w.id === selectedWorkerId);

  async function runTask() {
    if (!selectedWorkerId) return;
    try {
      const result = await createTask.mutateAsync({
        worker_id: selectedWorkerId,
        objective,
        require_approval: true,
        target_platform: platform,
      });
      setReport(result);
    } catch {
      // Handled by mutation
    }
  }

  return (
    <div className="space-y-6">
      {/* Hero Mission Control Banner */}
      <section className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-gradient-to-r from-[#0d121c] via-[#090c12] to-[#121927] p-6 lg:p-8 shadow-glass">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 h-64 w-64 rounded-full bg-hive/[0.06] blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="flex h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.9)] animate-pulse" />
              <span className="font-mono text-[9px] uppercase tracking-widest text-hive font-semibold">
                NETWORK ORCHESTRATION ONLINE
              </span>
              <span className="rounded bg-surface px-2 py-0.5 font-mono text-[9px] text-gray-400 border border-border">
                5 BRANDS ACTIVE
              </span>
            </div>
            <h1 className="font-display text-3xl font-bold tracking-tight text-white lg:text-4xl">
              Build Attention. <span className="text-hive">Turn It Into Attributable Revenue.</span>
            </h1>
            <p className="mt-2 text-xs text-gray-400 max-w-2xl leading-relaxed">
              Central LangGraph Master Agent directing 5 independent niche media brands through a shared Ollama LLM runtime and autonomous 1080×1920 video production pipeline.
            </p>
          </div>

          {/* Quick Production Launcher Actions */}
          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/video-studio"
              className="flex items-center gap-2 rounded-xl bg-hive px-4 py-3 font-mono text-xs font-bold text-[#090b10] hover:bg-hive-400 transition-all shadow-[0_0_20px_rgba(245,166,35,0.3)] no-underline"
            >
              <Clapperboard size={15} />
              <span>NEW VIDEO RENDER</span>
            </Link>

            <Link
              to="/master-agent"
              className="flex items-center gap-2 rounded-xl border border-border bg-surface-card px-4 py-3 font-mono text-xs text-gray-200 hover:text-white hover:bg-surface hover:border-hive/30 transition-all no-underline"
            >
              <BrainCircuit size={15} className="text-hive" />
              <span>DAILY STANDUP</span>
            </Link>

            <Link
              to="/content-studio"
              className="flex items-center gap-2 rounded-xl border border-border bg-surface-card px-4 py-3 font-mono text-xs text-gray-200 hover:text-white hover:bg-surface hover:border-hive/30 transition-all no-underline"
            >
              <Radio size={15} className="text-sky-400" />
              <span>LIVE SIGNALS</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Primary KPI Ribbon */}
      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div className="rounded-xl border border-white/[0.07] bg-surface-card/80 p-4 shadow-sm hover:border-hive/30 transition-all">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>24H NETWORK IMPRESSIONS</span>
            <Eye size={15} className="text-hive" />
          </div>
          <b className="mt-2.5 block font-display text-2xl font-bold text-gray-100">
            {briefing?.network_reach_24h ? briefing.network_reach_24h.toLocaleString() : "342,000"}
          </b>
          <div className="mt-1 flex items-center gap-1.5 text-[10px] text-emerald-400 font-mono">
            <TrendingUp size={12} />
            <span>+24.8% vs last week</span>
          </div>
        </div>

        <div className="rounded-xl border border-white/[0.07] bg-surface-card/80 p-4 shadow-sm hover:border-hive/30 transition-all">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>AVG 3s HOOK RETENTION</span>
            <Flame size={15} className="text-hive" />
          </div>
          <b className="mt-2.5 block font-display text-2xl font-bold text-gray-100">
            {briefing?.network_retention_avg_pct || 68.4}%
          </b>
          <div className="mt-1 flex items-center gap-1 text-[10px] text-gray-400 font-mono">
            <span className="text-hive font-semibold">SIGNAL TECH #1</span>
            <span>(81.4% Hold)</span>
          </div>
        </div>

        <div className="rounded-xl border border-white/[0.07] bg-surface-card/80 p-4 shadow-sm hover:border-hive/30 transition-all">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>NET MONETIZATION</span>
            <CircleDollarSign size={15} className="text-emerald-400" />
          </div>
          <b className="mt-2.5 block font-display text-2xl font-bold text-gray-100">
            ${revenueSummary?.net_profit ? revenueSummary.net_profit.toLocaleString(undefined, { minimumFractionDigits: 2 }) : "1,842.50"}
          </b>
          <div className="mt-1 flex items-center gap-1.5 text-[10px] text-emerald-400 font-mono">
            <span>{revenueSummary?.profit_margin_pct ? `${revenueSummary.profit_margin_pct}% Margin` : "84.2% Margin"}</span>
          </div>
        </div>

        <div className="rounded-xl border border-white/[0.07] bg-surface-card/80 p-4 shadow-sm hover:border-hive/30 transition-all">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>RENDERED VIDEO VAULT</span>
            <Film size={15} className="text-hive" />
          </div>
          <b className="mt-2.5 block font-display text-2xl font-bold text-gray-100">
            {videoLibrary.length} SHORTS
          </b>
          <div className="mt-1 flex items-center gap-1 text-[10px] text-gray-400 font-mono">
            <span>1080×1920 MP4 Produced</span>
          </div>
        </div>
      </section>

      {/* Fleet Brands Status Grid */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-mono text-[9px] uppercase tracking-wider text-gray-500">
              AUTONOMOUS CREATOR FLEET
            </div>
            <h2 className="font-display text-base font-semibold text-gray-100">
              Active Niche Media Operations
            </h2>
          </div>
          <Link
            to="/workers"
            className="flex items-center gap-1 text-xs font-mono text-hive hover:underline no-underline"
          >
            Manage Fleet <ArrowRight size={12} />
          </Link>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {workers.map((w) => {
            const isSelected = selectedWorkerId === w.id;
            return (
              <div
                key={w.id}
                onClick={() => setSelectedWorker(w.id)}
                className={cn(
                  "cursor-pointer rounded-xl border p-4 flex flex-col justify-between transition-all select-none",
                  isSelected
                    ? "border-hive bg-hive/[0.06] shadow-[0_0_20px_rgba(245,166,35,0.12)]"
                    : "border-white/[0.07] bg-surface-card hover:border-white/[0.15] hover:bg-surface-raised"
                )}
              >
                <div>
                  <div className="flex items-center justify-between text-[9px] font-mono mb-2">
                    <span className="text-hive font-bold uppercase">{w.id}</span>
                    <span className="flex items-center gap-1 text-emerald-400">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
                      ACTIVE
                    </span>
                  </div>

                  <b className="block font-display text-sm text-gray-100">{w.name}</b>
                  <p className="mt-1 text-[11px] text-gray-400 line-clamp-1">{w.niche}</p>
                </div>

                <div className="mt-4 border-t border-border/80 pt-3 flex items-center justify-between text-[10px] font-mono text-gray-400">
                  <span>Target: ${(w.revenue_target?.monthly_target_usd || 2000).toLocaleString()}</span>
                  <span className={isSelected ? "text-hive font-bold" : "text-gray-500"}>
                    {isSelected ? "SELECTED" : "SELECT"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Interactive Creator Task Dispatcher */}
      <section className="rounded-xl border border-white/[0.07] bg-surface-card p-5 space-y-4 shadow-glass">
        <div className="flex items-center justify-between border-b border-border/80 pb-3">
          <div className="flex items-center gap-2">
            <Zap size={16} className="text-hive" />
            <h3 className="font-display text-base font-semibold text-gray-100">
              Autonomous Directive Dispatcher
            </h3>
          </div>
          <span className="font-mono text-[9px] text-gray-400">
            Targeting: <b className="text-gray-200 uppercase">{active?.name}</b>
          </span>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block font-mono text-[9px] text-gray-400 uppercase mb-1.5">
              TARGET PLATFORM ADAPTER
            </label>
            <div className="flex gap-2">
              {[
                { id: "instagram" as const, label: "Instagram Reels" },
                { id: "youtube_shorts" as const, label: "YouTube Shorts" },
                { id: "x" as const, label: "X / Twitter" },
                { id: "facebook" as const, label: "Facebook Pages" },
              ].map((p) => (
                <button
                  key={p.id}
                  onClick={() => setPlatform(p.id)}
                  className={cn(
                    "rounded-lg border px-3 py-1.5 font-mono text-[10px] transition-colors",
                    platform === p.id
                      ? "border-hive bg-hive/15 text-hive font-semibold"
                      : "border-border bg-surface text-gray-400 hover:text-gray-200"
                  )}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block font-mono text-[9px] text-gray-400 uppercase mb-1.5">
              OPERATIONAL DIRECTIVE OBJECTIVE
            </label>
            <textarea
              rows={3}
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              className="w-full rounded-lg border border-border bg-surface-deep px-3.5 py-2.5 text-xs text-gray-200 outline-none focus:border-hive/50 font-sans leading-relaxed"
            />
          </div>

          <div className="flex items-center justify-between pt-1">
            <span className="font-mono text-[10px] text-gray-500 flex items-center gap-1.5">
              <ShieldCheck size={13} className="text-hive" />
              Mandatory Human-in-the-Loop Approval Sign-Off Enforced
            </span>

            <button
              onClick={runTask}
              disabled={createTask.isPending || !selectedWorkerId}
              className="flex items-center gap-1.5 rounded-lg bg-hive px-5 py-2.5 font-mono text-xs font-bold text-[#090b10] hover:bg-hive-400 transition-all shadow-[0_0_15px_rgba(245,166,35,0.25)] disabled:opacity-50"
            >
              <Send size={13} />
              {createTask.isPending ? "MASTER AGENT DELEGATING…" : "DISPATCH DIRECTIVE"}
            </button>
          </div>
        </div>

        {/* Task Execution Output */}
        {report && (
          <div className="mt-4 rounded-xl border border-hive/30 bg-surface p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                <b className="font-display text-sm text-gray-100">
                  Deliverable Generated: {report.worker_name}
                </b>
              </div>
              <span className="rounded bg-hive/15 px-2 py-0.5 font-mono text-[9px] text-hive uppercase font-bold border border-hive/20">
                {report.status}
              </span>
            </div>

            <p className="text-xs text-gray-300 whitespace-pre-wrap leading-relaxed font-sans">
              {report.output}
            </p>

            <div className="flex items-center justify-between border-t border-border pt-2 text-[10px] font-mono text-gray-400">
              <span>Task ID: {report.task_id}</span>
              <Link to="/approval-queue" className="text-hive hover:underline flex items-center gap-1 font-semibold">
                Open Approval Queue <ArrowRight size={11} />
              </Link>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
