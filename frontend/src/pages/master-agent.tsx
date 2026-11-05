import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type MasterExecutiveBriefing, type WorkerPerformanceDigest } from "@/lib/api";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  BrainCircuit,
  CheckCircle2,
  Clock,
  Cpu,
  Flame,
  GitBranch,
  Layers,
  MessageSquare,
  Play,
  Power,
  RefreshCw,
  Send,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const masterSteps = [
  {
    step: "01",
    title: "Circuit Breaker & Kill Switch",
    desc: "Enforces global operational lock. Any active kill switch immediately suspends execution across all workers.",
    status: "PASS",
  },
  {
    step: "02",
    title: "Priority & Token Budgeting",
    desc: "Analyzes directive urgency, target platform, and calculates token allocation and required approval gates.",
    status: "ACTIVE",
  },
  {
    step: "03",
    title: "Assignment & Brand Validation",
    desc: "Validates worker identity, active operational state, and brand voice alignment.",
    status: "ACTIVE",
  },
  {
    step: "04",
    title: "Worker Pipeline Execution",
    desc: "Delegates to the reusable 4-stage worker pipeline (Research → Scripting → Factuality → Packaging).",
    status: "ACTIVE",
  },
  {
    step: "05",
    title: "Editorial & Safety Evaluator",
    desc: "Audits unverified factual claims and risk scores; strictly enforces human approval on sensitive outputs.",
    status: "ACTIVE",
  },
];

const SIGNAL_BADGES: Record<string, { label: string; className: string }> = {
  viral: { label: "VIRAL VELOCITY", className: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
  high_performing: { label: "HIGH PERFORMING", className: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  average: { label: "STEADY REACH", className: "bg-gray-500/20 text-gray-400 border-border" },
  underperforming: { label: "UNDERPERFORMING", className: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
  hook_fatigue: { label: "HOOK FATIGUE DETECTED", className: "bg-red-500/20 text-red-400 border-red-500/30" },
};

export default function MasterAgentPage() {
  const queryClient = useQueryClient();

  const { data: status } = useQuery({
    queryKey: ["master-status"],
    queryFn: api.masterStatus,
    refetchInterval: 10_000,
  });

  const { data: briefing, isLoading: isLoadingBriefing } = useQuery({
    queryKey: ["master-briefing"],
    queryFn: api.masterBriefing,
    refetchInterval: 30_000,
  });

  const approveMutation = useMutation({
    mutationFn: api.approveMasterBriefing,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["master-briefing"] });
    },
  });

  const generateMutation = useMutation({
    mutationFn: api.generateMasterBriefing,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["master-briefing"] });
    },
  });

  const isHalted = status?.kill_switch_active;
  const isExecuting = briefing?.status === "executing";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
            CENTRAL INTELLIGENCE & OPERATIONS
          </div>
          <h1 className="mt-1 font-display text-2xl font-semibold">Master Agent Executive Briefing</h1>
          <p className="text-xs text-gray-400">
            Chief Content Officer layer: evaluates daily creator performance, detects virality vs hook fatigue, and orders strategic pivots.
          </p>
        </div>
        <div
          className={cn(
            "flex items-center gap-2 rounded-lg border px-3 py-1.5 font-mono text-[10px]",
            isHalted
              ? "border-red-500/30 bg-red-500/10 text-red-400"
              : "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
          )}
        >
          <span
            className={cn(
              "h-2 w-2 rounded-full",
              isHalted ? "bg-red-400" : "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"
            )}
          />
          {isHalted ? "KILL SWITCH ENGAGED" : "ORCHESTRATOR ONLINE"}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs font-mono">
            <span>24H NETWORK REACH</span>
            <Activity size={15} className="text-hive" />
          </div>
          <b className="mt-2 block font-display text-xl">
            {briefing?.network_reach_24h ? briefing.network_reach_24h.toLocaleString() : "342,000"}
          </b>
          <small className="text-[10px] text-gray-500">Verified Impressions</small>
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs font-mono">
            <span>AVG 3s RETENTION</span>
            <Flame size={15} className="text-hive" />
          </div>
          <b className="mt-2 block font-display text-xl">
            {briefing?.network_retention_avg_pct || 68.4}%
          </b>
          <small className="text-[10px] text-gray-500">Hook Hold Benchmark</small>
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs font-mono">
            <span>ACTIVE FLEET</span>
            <GitBranch size={15} className="text-hive" />
          </div>
          <b className="mt-2 block font-display text-xl">
            {status?.workers_enabled || 5} OF {status?.worker_count || 5}
          </b>
          <small className="text-[10px] text-gray-500">Autonomous Brands</small>
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs font-mono">
            <span>DIRECTIVE STATUS</span>
            <ShieldCheck size={15} className="text-hive" />
          </div>
          <b className={cn("mt-2 block font-display text-xl", isExecuting ? "text-emerald-400" : "text-hive")}>
            {isExecuting ? "EXECUTING" : "PENDING REVIEW"}
          </b>
          <small className="text-[10px] text-gray-500">Operator Sign-Off Required</small>
        </div>
      </div>

      {/* DAILY EXECUTIVE STANDUP CARD */}
      {briefing && (
        <div className="rounded-xl border border-hive/30 bg-surface p-6 shadow-[0_0_25px_rgba(245,166,35,0.06)] space-y-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-hive text-[#090b10] font-bold font-display text-lg shadow-[0_0_15px_rgba(245,166,35,0.3)]">
                M
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[9px] tracking-widest text-hive uppercase font-semibold">
                    DAILY STANDUP REPORT • {briefing.date}
                  </span>
                  <span className="rounded bg-hive/10 px-2 py-0.5 font-mono text-[9px] text-hive border border-hive/20">
                    MASTER AI DIRECTOR
                  </span>
                </div>
                <h2 className="font-display text-lg font-semibold text-gray-100 mt-0.5">
                  {briefing.headline}
                </h2>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => generateMutation.mutate()}
                disabled={generateMutation.isPending}
                className="flex items-center gap-1.5 rounded-lg border border-border bg-surface-deep px-3 py-2 font-mono text-xs text-gray-300 hover:text-gray-100 hover:bg-surface transition-colors disabled:opacity-50"
              >
                <RefreshCw size={12} className={generateMutation.isPending ? "animate-spin" : ""} />
                {generateMutation.isPending ? "ANALYZING…" : "RE-ANALYZE SIGNALS"}
              </button>

              <button
                onClick={() => approveMutation.mutate()}
                disabled={approveMutation.isPending || isExecuting}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-4 py-2 font-mono text-xs font-semibold transition-all",
                  isExecuting
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 cursor-default"
                    : "bg-hive text-[#090b10] hover:bg-hive-400 shadow-[0_0_15px_rgba(245,166,35,0.2)]"
                )}
              >
                <CheckCircle2 size={14} />
                {isExecuting ? "DIRECTIVES DISPATCHED" : "APPROVE DAILY DIRECTIVES"}
              </button>
            </div>
          </div>

          {/* Master Agent's Voice / Executive Summary */}
          <div className="rounded-lg border border-hive/20 bg-hive/5 p-4">
            <div className="font-mono text-[9px] text-hive font-semibold tracking-wide mb-1.5 flex items-center gap-1.5">
              <BrainCircuit size={13} />
              EXECUTIVE BRIEFING TO OPERATOR
            </div>
            <p className="text-sm text-gray-200 leading-relaxed font-sans italic">
              "{briefing.executive_summary}"
            </p>
          </div>

          {/* Worker Brand Directives & Hook Pivot Matrix */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-display text-sm font-semibold text-gray-200">
                Creator Agent Daily Directives & Hook Pivots
              </h3>
              <span className="font-mono text-[9px] text-gray-500">
                5 Niche Media Brands Evaluated
              </span>
            </div>

            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {briefing.worker_directives.map((w: WorkerPerformanceDigest) => {
                const badge = SIGNAL_BADGES[w.status_signal] || SIGNAL_BADGES["average"];
                return (
                  <div
                    key={w.worker_id}
                    className="rounded-lg border border-border bg-surface-deep p-4 flex flex-col justify-between space-y-3 transition-colors hover:border-border-strong"
                  >
                    <div>
                      {/* Brand Header */}
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <b className="block font-display text-sm text-gray-100">{w.worker_name}</b>
                          <small className="text-[10px] text-gray-400 capitalize">{w.niche}</small>
                        </div>
                        <span className={cn("rounded px-2 py-0.5 text-[8px] font-mono font-bold border", badge.className)}>
                          {badge.label}
                        </span>
                      </div>

                      {/* Performance Bar */}
                      <div className="grid grid-cols-2 gap-2 border-y border-border py-2 text-[10px] font-mono my-2.5">
                        <div>
                          <span className="text-gray-500 block text-[8px]">24H REACH</span>
                          <span className="text-gray-200 font-semibold">{w.yesterday_reach.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 block text-[8px]">3s HOOK RETENTION</span>
                          <span
                            className={cn(
                              "font-semibold",
                              w.avg_3s_retention_pct >= 75
                                ? "text-emerald-400"
                                : w.avg_3s_retention_pct >= 55
                                ? "text-hive"
                                : "text-red-400"
                            )}
                          >
                            {w.avg_3s_retention_pct}%
                          </span>
                        </div>
                      </div>

                      {/* Diagnosis */}
                      <div className="text-[11px] text-gray-400 space-y-1 mb-2">
                        <span className="font-mono text-[8px] text-gray-500 block uppercase">
                          AI DIAGNOSIS
                        </span>
                        <p className="text-gray-300 leading-snug">{w.diagnosis}</p>
                      </div>

                      {/* Recommended Strategy Pivot */}
                      <div className="text-[11px] space-y-1">
                        <span className="font-mono text-[8px] text-hive block uppercase font-semibold">
                          STRATEGY PIVOT FOR TODAY
                        </span>
                        <p className="text-hive/90 text-xs font-medium leading-snug">{w.recommended_pivot}</p>
                      </div>
                    </div>

                    {/* Today's Proposed Hook */}
                    <div className="rounded border border-border bg-surface p-2.5 space-y-1">
                      <div className="flex items-center justify-between text-[8px] font-mono text-gray-500">
                        <span>TODAY'S PROPOSED HOOK</span>
                        <span className="text-emerald-400">{w.virality_probability}% VIRALITY PROB</span>
                      </div>
                      <p className="text-[11px] text-gray-100 italic line-clamp-2">
                        "{w.proposed_daily_hook}"
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* State Machine Workflow */}
      <div className="rounded-xl border border-border bg-surface p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="font-mono text-[9px] tracking-[1.5px] text-gray-400">
              STATE MACHINE ARCHITECTURE
            </div>
            <h2 className="font-display text-lg font-semibold mt-1">Master Agent LangGraph Pipeline</h2>
          </div>
          <span className="font-mono text-[10px] text-gray-500">5 Stateful Graph Nodes</span>
        </div>

        <div className="space-y-4">
          {masterSteps.map((step) => (
            <div
              key={step.step}
              className="relative flex items-start gap-4 rounded-lg border border-border bg-surface-deep p-4 transition-colors hover:border-hive/30"
            >
              <div className="grid h-8 w-8 flex-shrink-0 place-items-center rounded bg-hive/10 font-mono text-xs font-bold text-hive">
                {step.step}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-sm text-gray-200">{step.title}</h3>
                  <span className="font-mono text-[9px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    {step.status}
                  </span>
                </div>
                <p className="mt-1 text-xs text-gray-400 leading-relaxed">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
