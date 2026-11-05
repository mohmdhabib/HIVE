import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  BrainCircuit,
  CheckCircle2,
  Cpu,
  Flame,
  GitBranch,
  Layers,
  Power,
  ShieldAlert,
  ShieldCheck,
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

export default function MasterAgentPage() {
  const { data: status } = useQuery({
    queryKey: ["master-status"],
    queryFn: api.masterStatus,
    refetchInterval: 10_000,
  });

  const isHalted = status?.kill_switch_active;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
            CENTRAL INTELLIGENCE
          </div>
          <h1 className="mt-1 font-display text-2xl font-semibold">Master Agent Orchestrator</h1>
          <p className="text-xs text-gray-400">
            Stateful LangGraph coordination layer controlling task prioritization, allocation, and quality safety gates.
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
            <span>MODEL RUNTIME</span>
            <Cpu size={15} className="text-hive" />
          </div>
          <b className="mt-2 block font-display text-xl">{status?.model || "llama3.1"}</b>
          <small className="text-[10px] text-gray-500">Shared Ollama Server</small>
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs font-mono">
            <span>CONCURRENCY LIMIT</span>
            <Layers size={15} className="text-hive" />
          </div>
          <b className="mt-2 block font-display text-xl">{status?.max_concurrent || 2} WORKERS</b>
          <small className="text-[10px] text-gray-500">Semaphore Controlled</small>
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs font-mono">
            <span>ACTIVE FLEET</span>
            <GitBranch size={15} className="text-hive" />
          </div>
          <b className="mt-2 block font-display text-xl">{status?.workers_enabled || 5} OF {status?.worker_count || 5}</b>
          <small className="text-[10px] text-gray-500">Brands Available</small>
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-gray-400 text-xs font-mono">
            <span>HUMAN GATES</span>
            <ShieldCheck size={15} className="text-hive" />
          </div>
          <b className="mt-2 block font-display text-xl">MANDATORY</b>
          <small className="text-[10px] text-gray-500">100% External Sign-off</small>
        </div>
      </div>

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
          {masterSteps.map((step, idx) => (
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
