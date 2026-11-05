import { useState } from "react";
import {
  Activity,
  AlertTriangle,
  Bot,
  BrainCircuit,
  CheckCircle2,
  CircleDollarSign,
  Command,
  Eye,
  FileText,
  Flame,
  Layers,
  Play,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useWorkers, useCreateTask } from "@/hooks/use-workers";
import { useAppStore } from "@/stores/app-store";
import type { TaskReport } from "@/lib/api";

function Metric({
  label,
  value,
  note,
  icon,
}: {
  label: string;
  value: string;
  note: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4 min-h-[106px]">
      <div className="flex items-center justify-between font-mono text-[9px] tracking-wide text-gray-500">
        <span>{label}</span>
        <span className="text-gray-400">{icon}</span>
      </div>
      <b className="mt-2.5 block font-display text-[23px] font-semibold">{value}</b>
      <small className="text-[10px] text-gray-500">{note}</small>
    </div>
  );
}

const workerColors = [
  "text-hive bg-hive/10",
  "text-sky-400 bg-sky-400/10",
  "text-pink-400 bg-pink-400/10",
  "text-purple-400 bg-purple-400/10",
  "text-amber-300 bg-amber-300/10",
];

export default function OverviewPage() {
  const { data: workers = [], isError } = useWorkers();
  const { selectedWorkerId, setSelectedWorker } = useAppStore();
  const createTask = useCreateTask();

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
      // Handled by mutation state
    }
  }

  return (
    <>
      {/* Welcome */}
      <section className="flex items-center justify-between py-8">
        <div>
          <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
            <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-hive shadow-[0_0_9px_rgba(245,166,35,0.6)]" />
            COMMAND CENTER
          </div>
          <h1 className="mt-3 font-display text-4xl font-semibold leading-tight tracking-tight lg:text-5xl">
            Build attention.
            <br />
            <em className="not-italic text-hive">Turn it into revenue.</em>
          </h1>
          <p className="mt-3 text-xs text-gray-400">
            One intelligence layer. Independent media brands. Measurable growth.
          </p>
        </div>
        <div className="hidden min-w-[260px] items-center gap-3 rounded-xl border border-border bg-gradient-to-br from-surface-overlay to-surface p-4 lg:flex">
          <div className="grid h-10 w-10 place-items-center rounded-lg bg-hive/10 text-hive">
            <BrainCircuit size={22} />
          </div>
          <div>
            <span className="block font-mono text-[9px] tracking-[1px] text-gray-400">
              MASTER AGENT
            </span>
            <b className="block text-[12px]">
              Autonomous Orchestrator{" "}
              <span className="ml-1 inline-block h-1.5 w-1.5 rounded-full bg-hive" />
            </b>
            <small className="text-[10px] text-gray-500">LangGraph Pipeline Active</small>
          </div>
          <div className="ml-auto self-start rounded border border-border px-1.5 py-1 font-mono text-[9px] text-gray-400">
            V 0.2
          </div>
        </div>
      </section>

      {/* Metrics */}
      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Metric
          label="WORKER BRANDS"
          value={String(workers.length || 5).padStart(2, "0")}
          note="Configured identities"
          icon={<Bot size={15} />}
        />
        <Metric
          label="ACTIVE PIPELINE"
          value="5 NODES"
          note="LangGraph stateful workflow"
          icon={<CheckCircle2 size={15} />}
        />
        <Metric
          label="MONTHLY TARGET"
          value="$11,000"
          note="Combined worker goals"
          icon={<CircleDollarSign size={15} />}
        />
        <Metric
          label="SYSTEM HEALTH"
          value={isError ? "OFFLINE" : "READY"}
          note="Ollama shared runtime"
          icon={<Activity size={15} />}
        />
      </section>

      {/* Worker brands */}
      <section className="mt-8">
        <div className="flex items-end justify-between">
          <div>
            <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
              THE NETWORK
            </div>
            <h2 className="mt-1.5 font-display text-lg font-semibold">Worker brands</h2>
          </div>
          <span className="text-[10px] text-gray-500">
            Independent identities · Shared intelligence
          </span>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2.5 lg:grid-cols-5">
          {workers.map((w, i) => (
            <button
              key={w.id}
              onClick={() => setSelectedWorker(w.id)}
              className={cn(
                "rounded-lg border border-border bg-surface p-3.5 text-left transition-colors",
                selectedWorkerId === w.id && "border-hive/50 bg-hive/5"
              )}
            >
              <div
                className={cn(
                  "grid h-[34px] w-[34px] place-items-center rounded-lg",
                  workerColors[i % workerColors.length]
                )}
              >
                <Bot size={19} />
              </div>
              <div className="mt-3">
                <b className="block text-[11px]">{w.name}</b>
                <small className="block text-[9px] text-gray-500">{w.niche}</small>
              </div>
              <span className="mt-2 block font-mono text-[8px] text-gray-500">
                <span className="mr-1 inline-block h-1 w-1 rounded-full bg-emerald-400" />
                IDLE
              </span>
              <p className="mt-1 h-[31px] text-[9px] leading-relaxed text-gray-500 line-clamp-2">
                {w.objective}
              </p>
              <div className="mt-3 flex items-center justify-between border-t border-border pt-2 font-mono text-[8px] tracking-wide text-gray-500">
                <span>SELECT WORKER</span>
                <span>↗</span>
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* Task delegation */}
      <section className="mt-8">
        <div className="flex items-end justify-between">
          <div>
            <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
              MASTER → WORKER ENGINE
            </div>
            <h2 className="mt-1.5 font-display text-lg font-semibold">Delegate a task</h2>
          </div>
          <span className="text-[10px] text-gray-500">
            Structured Pydantic validation & quality gates enabled
          </span>
        </div>
        <div className="mt-3 grid gap-3 lg:grid-cols-2">
          {/* Task input panel */}
          <div className="rounded-lg border border-border bg-surface p-4 flex flex-col justify-between">
            <div>
              <label className="mb-2 block font-mono text-[9px] tracking-[1.1px] text-gray-400">
                SELECTED WORKER
              </label>
              <div className="mb-4 flex items-center gap-2.5">
                <div className="grid h-[34px] w-[34px] place-items-center rounded-lg bg-hive/10 text-hive">
                  <Bot size={18} />
                </div>
                <div>
                  <b className="block text-[11px]">{active?.name || "Loading workers…"}</b>
                  <small className="block text-[9px] text-gray-500">
                    {active?.niche || "Worker configuration"}
                  </small>
                </div>
                <span className="ml-auto font-mono text-[9px] text-hive">READY</span>
              </div>

              {/* Distribution Channel */}
              <div className="mb-3">
                <label className="mb-1.5 block font-mono text-[9px] tracking-[1.1px] text-gray-400">
                  TARGET DISTRIBUTION PLATFORM
                </label>
                <div className="grid grid-cols-4 gap-1.5 font-mono text-[10px]">
                  {(["instagram", "youtube_shorts", "x", "facebook"] as const).map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setPlatform(p)}
                      className={cn(
                        "rounded border border-border py-1.5 capitalize transition-colors",
                        platform === p ? "border-hive bg-hive/10 text-hive font-semibold" : "text-gray-400 hover:text-gray-200"
                      )}
                    >
                      {p.replace("_", " ")}
                    </button>
                  ))}
                </div>
              </div>

              <label
                htmlFor="objective"
                className="mb-2 block font-mono text-[9px] tracking-[1.1px] text-gray-400"
              >
                TASK OBJECTIVE / DIRECTIVE
              </label>
              <textarea
                id="objective"
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
                rows={4}
                className="w-full resize-y rounded-md border border-border bg-surface-deep p-3 text-[11px] leading-relaxed text-gray-300 outline-none focus:border-hive/50"
              />
            </div>

            <div className="mt-4">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-[9px] text-gray-400">
                  <ShieldCheck size={14} className="text-hive" />
                  Mandatory human approval gate
                </span>
                <button
                  onClick={runTask}
                  disabled={createTask.isPending || !workers.length || objective.length < 8}
                  className="flex items-center gap-1.5 rounded-md bg-hive px-4 py-2.5 font-mono text-[9px] font-semibold tracking-wide text-[#11170b] transition-opacity disabled:opacity-50"
                >
                  <Play size={15} fill="currentColor" />
                  {createTask.isPending ? "EXECUTING PIPELINE…" : "RUN TASK"}
                </button>
              </div>
              {createTask.isError && (
                <div className="mt-2 text-[10px] text-red-300">
                  {createTask.error instanceof Error ? createTask.error.message : "Unexpected error"}
                </div>
              )}
            </div>
          </div>

          {/* Output panel */}
          <div className="rounded-lg border border-border bg-surface p-4">
            <div className="flex items-start justify-between border-b border-border pb-3">
              <div>
                <label className="mb-0.5 block font-mono text-[9px] tracking-[1.1px] text-gray-400">
                  STRUCTURED EXECUTION REPORT
                </label>
                <div className="flex items-center gap-2 mt-1">
                  <b className="font-mono text-[10px] text-hive">
                    {report ? report.status.replace("_", " ").toUpperCase() : "AWAITING TASK"}
                  </b>
                  {report?.priority && (
                    <span className="rounded bg-surface-raised border border-border px-1.5 py-0.5 font-mono text-[8px] uppercase text-gray-300">
                      Priority: {report.priority}
                    </span>
                  )}
                  {report?.quality_check && (
                    <span className="rounded bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 font-mono text-[8px] text-emerald-400">
                      Score: {Math.round(report.quality_check.score * 100)}%
                    </span>
                  )}
                </div>
              </div>
              <Command size={17} className="text-gray-500" />
            </div>

            {report ? (
              <div className="mt-3 max-h-[380px] overflow-auto space-y-3 pr-1 text-[11px]">
                {report.content ? (
                  <>
                    {/* Title */}
                    <div>
                      <span className="font-mono text-[9px] text-gray-500">CONTENT TITLE</span>
                      <h3 className="font-display text-base font-semibold text-gray-100">
                        {report.content.title}
                      </h3>
                    </div>

                    {/* 3s Hook */}
                    <div className="rounded-md border border-hive/30 bg-hive/5 p-3">
                      <div className="flex items-center gap-1.5 font-mono text-[9px] font-semibold text-hive">
                        <Sparkles size={13} />
                        3-SECOND RETENTION HOOK
                      </div>
                      <p className="mt-1 font-medium text-gray-200">
                        "{report.content.hook}"
                      </p>
                    </div>

                    {/* Body script */}
                    <div className="rounded-md border border-border bg-surface-deep p-3">
                      <div className="flex items-center gap-1.5 font-mono text-[9px] text-gray-400 mb-1">
                        <FileText size={13} />
                        NARRATION / SCRIPT
                      </div>
                      <pre className="whitespace-pre-wrap font-sans text-gray-300 leading-relaxed text-[11px]">
                        {report.content.body_script}
                      </pre>
                    </div>

                    {/* Caption & Hashtags */}
                    <div className="rounded-md border border-border bg-surface-deep p-3">
                      <div className="font-mono text-[9px] text-gray-400 mb-1">CAPTION & TAGS</div>
                      <p className="text-gray-300">{report.content.caption}</p>
                      {report.content.hashtags?.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {report.content.hashtags.map((tag) => (
                            <span key={tag} className="font-mono text-[9px] text-hive">
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Visual Brief */}
                    <div className="rounded-md border border-border bg-surface-deep p-3">
                      <div className="flex items-center gap-1.5 font-mono text-[9px] text-gray-400 mb-1">
                        <Eye size={13} />
                        VISUAL BRIEF & DIRECTION
                      </div>
                      <p className="text-gray-300">{report.content.visual_brief}</p>
                    </div>

                    {/* Monetization Hypothesis */}
                    <div className="rounded-md border border-emerald-500/30 bg-emerald-500/5 p-3">
                      <div className="flex items-center gap-1.5 font-mono text-[9px] font-semibold text-emerald-400 mb-1">
                        <CircleDollarSign size={13} />
                        MONETIZATION ATTRIBUTION HYPOTHESIS
                      </div>
                      <p className="text-gray-300">{report.content.monetization_hypothesis}</p>
                    </div>

                    {/* Factual Checks & Risks */}
                    {(report.content.factual_checks?.length > 0 || report.content.estimated_risk_level !== "low") && (
                      <div className="rounded-md border border-amber-500/30 bg-amber-500/5 p-3">
                        <div className="flex items-center gap-1.5 font-mono text-[9px] font-semibold text-amber-400 mb-1">
                          <AlertTriangle size={13} />
                          FACTUAL CHECKS & RISK FACTORS ({report.content.estimated_risk_level.toUpperCase()})
                        </div>
                        <ul className="list-disc pl-4 space-y-1 text-gray-300 text-[10px]">
                          {report.content.factual_checks.map((fc, i) => (
                            <li key={i}>Fact check needed: {fc}</li>
                          ))}
                          {report.content.risks_and_caveats.map((rc, i) => (
                            <li key={i}>Risk note: {rc}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </>
                ) : (
                  <pre className="whitespace-pre-wrap rounded-md border border-border bg-surface-deep p-3 text-[11px] leading-relaxed text-gray-300">
                    {report.output}
                  </pre>
                )}

                <div className="flex items-center gap-1.5 border-t border-border pt-2 text-[10px] text-hive">
                  <ShieldCheck size={15} />
                  Draft verified by LangGraph quality gate. Awaiting human publication sign-off.
                </div>
              </div>
            ) : (
              <div className="flex h-[260px] flex-col items-center justify-center text-center">
                <div className="mb-3 grid h-[52px] w-[52px] place-items-center rounded-full border border-hive/20 bg-hive/5 text-hive">
                  <BrainCircuit size={27} />
                </div>
                <b className="text-[11px]">Structured agent deliverables appear here</b>
                <p className="mt-1 max-w-[280px] text-[10px] leading-relaxed text-gray-500">
                  Select a worker, set a target platform and directive, and execute through the LangGraph Master Agent.
                </p>
              </div>
            )}
          </div>
        </div>
      </section>
    </>
  );
}
