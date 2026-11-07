import React, { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Loader2,
  AlertTriangle,
  XCircle,
  Terminal,
  Zap,
  Search,
  Target,
  Sparkles,
  Film,
  Volume2,
  Clock,
  RotateCw,
} from "lucide-react";
import { TraceStep } from "@/lib/api";
import { cn } from "@/lib/utils";

interface LiveTraceabilityBoxProps {
  title?: string;
  isGenerating?: boolean;
  currentTaskTitle?: string;
  traceSteps?: TraceStep[];
  liveTokens?: string;
  elapsedSeconds?: number;
  error?: string | null;
  archetype?: string;
  engineMode?: string;
  onRetry?: () => void;
  defaultExpanded?: boolean;
  className?: string;
}

const PHASE_ICONS: Record<string, React.ReactNode> = {
  init: <Sparkles size={13} className="text-hive" />,
  research: <Search size={13} className="text-blue-400" />,
  strategy: <Target size={13} className="text-violet-400" />,
  llm_dispatch: <Zap size={13} className="text-amber-400" />,
  llm_complete: <Zap size={13} className="text-emerald-400" />,
  llm_retry: <RotateCw size={13} className="text-amber-300 animate-spin" />,
  llm_warning: <AlertTriangle size={13} className="text-amber-400" />,
  llm_timeout: <AlertTriangle size={13} className="text-red-400" />,
  llm_error: <XCircle size={13} className="text-red-400" />,
  visuals: <Film size={13} className="text-cyan-400" />,
  audio: <Volume2 size={13} className="text-emerald-400" />,
  complete: <CheckCircle2 size={13} className="text-emerald-400" />,
};

export function LiveTraceabilityBox({
  title = "Agentic Traceability & Execution Log",
  isGenerating = false,
  currentTaskTitle,
  traceSteps = [],
  liveTokens = "",
  elapsedSeconds = 0,
  error,
  archetype,
  engineMode,
  onRetry,
  defaultExpanded,
  className,
}: LiveTraceabilityBoxProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(defaultExpanded ?? isGenerating);

  // Auto-expand during live generation if user hasn't explicitly toggled
  const expanded = defaultExpanded !== undefined ? isExpanded : (isGenerating || isExpanded);

  const completedCount = traceSteps.filter((s) => s.status === "completed").length;
  const isComplete = !isGenerating && completedCount > 0 && !error;

  return (
    <div
      className={cn(
        "rounded-2xl border transition-all duration-300 overflow-hidden shadow-lg",
        isGenerating
          ? "border-hive/50 bg-black/90 ring-1 ring-hive/20 shadow-[0_0_25px_rgba(245,166,35,0.12)]"
          : error
          ? "border-red-500/40 bg-[#0d090a]"
          : "border-border/80 bg-[#090c12]/95",
        className
      )}
    >
      {/* Header Bar: Status Indicator, Live Timer & Expand Toggle */}
      <div
        onClick={() => setIsExpanded(!expanded)}
        className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 cursor-pointer select-none border-b border-white/[0.06] hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-2.5">
          {/* Animated Status Pill */}
          {isGenerating ? (
            <div className="flex items-center gap-1.5 rounded-full bg-hive/15 border border-hive/30 px-2.5 py-0.5 font-mono text-[10px] font-bold text-hive animate-pulse">
              <Loader2 size={11} className="animate-spin text-hive" />
              <span>NEURAL AGENT ACTIVE</span>
            </div>
          ) : error ? (
            <div className="flex items-center gap-1.5 rounded-full bg-red-500/15 border border-red-500/30 px-2.5 py-0.5 font-mono text-[10px] font-bold text-red-400">
              <XCircle size={11} />
              <span>GENERATION HALTED</span>
            </div>
          ) : isComplete ? (
            <div className="flex items-center gap-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2.5 py-0.5 font-mono text-[10px] font-bold text-emerald-400">
              <CheckCircle2 size={11} />
              <span>TRACE VERIFIED</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 rounded-full bg-white/[0.08] border border-white/10 px-2.5 py-0.5 font-mono text-[10px] font-medium text-gray-400">
              <Terminal size={11} />
              <span>OBSERVABILITY</span>
            </div>
          )}

          <div className="flex items-center gap-2">
            <span className="font-sans text-xs font-semibold text-gray-200">
              {currentTaskTitle || title}
            </span>
            {archetype && (
              <span className="hidden sm:inline-block rounded bg-surface border border-border px-1.5 py-0.5 font-mono text-[9px] uppercase text-gray-400">
                {archetype.replace(/_/g, " ")}
              </span>
            )}
          </div>
        </div>

        {/* Right side telemetry metrics & toggle */}
        <div className="flex items-center gap-3 font-mono text-[10px] text-gray-400">
          {(isGenerating || elapsedSeconds > 0) && (
            <span className="flex items-center gap-1 text-gray-300">
              <Clock size={11} className="text-hive" />
              <span>{elapsedSeconds > 0 ? `${elapsedSeconds.toFixed(1)}s` : "active"}</span>
            </span>
          )}

          <span className="text-gray-400">
            {completedCount}/{Math.max(traceSteps.length, 6)} steps
          </span>

          <div className="flex items-center gap-1 text-gray-300 hover:text-white transition-colors">
            <span className="text-[9px] uppercase tracking-wider">
              {expanded ? "HIDE TRACE" : "VIEW TRACE"}
            </span>
            {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </div>
        </div>
      </div>

      {/* Expanded Drawer: Timeline Progression, Live Tokens & Diagnostics */}
      {expanded && (
        <div className="p-4 space-y-4">
          {/* Step Timeline */}
          <div className="relative pl-6 space-y-3.5 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-[1.5px] before:bg-white/[0.08]">
            {traceSteps.map((step, idx) => {
              const isRunning = step.status === "running";
              const isFailed = step.status === "error";
              const isWarning = step.status === "warning";
              const isDone = step.status === "completed";

              return (
                <div key={step.step_id || idx} className="relative group text-xs">
                  {/* Step Node Marker */}
                  <div
                    className={cn(
                      "absolute -left-[23px] top-0.5 flex h-4 w-4 items-center justify-center rounded-full border text-[9px] transition-all",
                      isRunning
                        ? "border-hive bg-black text-hive ring-2 ring-hive/30 shadow-[0_0_8px_rgba(245,166,35,0.5)]"
                        : isFailed
                        ? "border-red-500 bg-red-500/20 text-red-400"
                        : isWarning
                        ? "border-amber-400 bg-amber-400/20 text-amber-300"
                        : isDone
                        ? "border-emerald-500/60 bg-emerald-500/20 text-emerald-400"
                        : "border-gray-700 bg-black text-gray-500"
                    )}
                  >
                    {isRunning ? (
                      <Loader2 size={10} className="animate-spin" />
                    ) : isDone ? (
                      <CheckCircle2 size={10} />
                    ) : (
                      idx + 1
                    )}
                  </div>

                  {/* Step Content */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-200 text-xs">
                          {step.title}
                        </span>
                        <span className="rounded bg-surface-deep border border-border/80 px-1.5 py-0.2 font-mono text-[9px] uppercase tracking-wider text-gray-400">
                          {step.phase}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 font-mono text-[9px] text-gray-500">
                        {step.elapsed_ms !== undefined && step.elapsed_ms !== null && (
                          <span>
                            {step.elapsed_ms > 1000
                              ? `${(step.elapsed_ms / 1000).toFixed(1)}s`
                              : `${step.elapsed_ms}ms`}
                          </span>
                        )}
                        <span>{step.timestamp}</span>
                      </div>
                    </div>

                    <p className="text-[11px] text-gray-400 font-mono leading-relaxed">
                      {step.detail}
                    </p>

                    {/* Optional snippet quote */}
                    {step.snippet && (
                      <div className="mt-1.5 rounded-lg border border-hive/20 bg-hive/5 p-2 font-mono text-[10px] text-hive-300/90 leading-normal">
                        {step.snippet}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Live Streaming LLM Output Terminal */}
          {liveTokens && isGenerating && (
            <div className="rounded-xl border border-hive/30 bg-black/80 p-3 space-y-1.5 font-mono text-xs shadow-inner">
              <div className="flex items-center justify-between border-b border-white/[0.08] pb-1.5 text-[10px] text-gray-400">
                <div className="flex items-center gap-1.5 text-hive font-semibold">
                  <Zap size={11} className="animate-pulse" />
                  <span>OLLAMA LLAMA 3.1 8B REAL-TIME TOKEN STREAM</span>
                </div>
                <span className="text-[9px] text-gray-500">Live synthesis in progress</span>
              </div>
              <p className="font-mono text-[11px] text-gray-300 leading-relaxed max-h-32 overflow-y-auto whitespace-pre-wrap select-text">
                {liveTokens}
                <span className="inline-block h-3.5 w-1.5 bg-hive ml-1 animate-pulse align-middle" />
              </p>
            </div>
          )}

          {/* Error Banner with 1-Click Retry */}
          {error && (
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-3.5 text-xs text-red-300 font-mono">
              <div className="flex items-start gap-2">
                <AlertTriangle size={15} className="text-red-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-red-200 block">Agent Execution Stopped</span>
                  <span className="text-[11px] text-red-300/90">{error}</span>
                </div>
              </div>
              {onRetry && (
                <button
                  type="button"
                  onClick={onRetry}
                  className="flex items-center justify-center gap-1.5 rounded-lg bg-red-500 px-3.5 py-1.5 font-mono text-[10px] font-bold text-white hover:bg-red-400 transition-all shrink-0 shadow"
                >
                  <RotateCw size={11} />
                  <span>RETRY GENERATION</span>
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

