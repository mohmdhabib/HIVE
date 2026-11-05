import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  ArrowLeft,
  Bot,
  Brain,
  CheckCircle2,
  CircleDollarSign,
  Clock,
  Compass,
  History,
  Layers,
  Pause,
  Play,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function WorkerDetailsPage() {
  const { id = "tech" } = useParams();
  const queryClient = useQueryClient();

  const { data: worker } = useQuery({
    queryKey: ["worker", id],
    queryFn: () => api.workerDetail(id),
  });

  const { data: memoryEntries = [] } = useQuery({
    queryKey: ["worker-memory", id],
    queryFn: () => api.workerMemory(id),
    refetchInterval: 15_000,
  });

  const { data: tasks = [] } = useQuery({
    queryKey: ["worker-tasks", id],
    queryFn: () => api.listTasks({ worker_id: id }),
    refetchInterval: 15_000,
  });

  const togglePauseMutation = useMutation({
    mutationFn: () => (worker?.enabled ? api.pauseWorker(id) : api.resumeWorker(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["worker", id] });
      queryClient.invalidateQueries({ queryKey: ["workers"] });
    },
  });

  if (!worker) {
    return (
      <div className="flex h-64 items-center justify-center font-mono text-xs text-gray-400">
        LOADING WORKER DATA…
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button and status header */}
      <div className="flex items-center justify-between">
        <Link
          to="/workers"
          className="flex items-center gap-1.5 font-mono text-[10px] text-gray-400 hover:text-hive"
        >
          <ArrowLeft size={13} /> BACK TO DIRECTORY
        </Link>
        <div className="flex items-center gap-3">
          <span
            className={cn(
              "flex items-center gap-1.5 rounded border px-2.5 py-1 font-mono text-[9px]",
              worker.enabled
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                : "border-amber-500/30 bg-amber-500/10 text-amber-400"
            )}
          >
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                worker.enabled ? "bg-emerald-400" : "bg-amber-400"
              )}
            />
            {worker.enabled ? "ACTIVE · LISTENING" : "PAUSED BY OPERATOR"}
          </span>
          <button
            onClick={() => togglePauseMutation.mutate()}
            disabled={togglePauseMutation.isPending}
            className="flex items-center gap-1.5 rounded border border-border bg-surface px-3 py-1 font-mono text-[9px] text-gray-300 hover:border-hive/50 hover:text-hive"
          >
            {worker.enabled ? (
              <>
                <Pause size={11} /> PAUSE WORKER
              </>
            ) : (
              <>
                <Play size={11} /> RESUME WORKER
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Identity Banner */}
      <div className="rounded-xl border border-border bg-surface p-6">
        <div className="flex items-start gap-4">
          <div className="grid h-12 w-12 place-items-center rounded-xl bg-hive/10 text-hive font-display text-xl font-bold">
            {worker.name[0]}
          </div>
          <div className="flex-1">
            <h1 className="font-display text-2xl font-semibold">{worker.name}</h1>
            <div className="font-mono text-xs text-hive capitalize mt-0.5">{worker.niche}</div>
            <p className="mt-2 text-xs text-gray-300 max-w-2xl">{worker.objective}</p>
          </div>
        </div>

        <div className="mt-6 grid gap-4 border-t border-border pt-4 sm:grid-cols-3">
          <div>
            <span className="font-mono text-[9px] text-gray-500 block">TARGET AUDIENCE</span>
            <p className="text-xs text-gray-300 mt-1">{worker.audience}</p>
          </div>
          <div>
            <span className="font-mono text-[9px] text-gray-500 block">EDITORIAL VOICE</span>
            <p className="text-xs text-gray-300 mt-1">{worker.voice}</p>
          </div>
          <div>
            <span className="font-mono text-[9px] text-gray-500 block">REVENUE STREAM</span>
            <p className="text-xs text-emerald-400 font-medium mt-1">
              ${worker.revenue_target?.monthly_target_usd.toLocaleString()}/mo ·{" "}
              <span className="capitalize">{worker.revenue_target?.primary_stream}</span>
            </p>
          </div>
        </div>
      </div>

      {/* Two Columns: Isolated Memory vs Past Tasks */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Worker Isolated Memory */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div className="flex items-center gap-2">
              <Brain size={16} className="text-hive" />
              <h2 className="font-display text-sm font-semibold">Isolated Brand Memory</h2>
            </div>
            <span className="font-mono text-[9px] text-gray-500">
              {memoryEntries.length} Stored Entries
            </span>
          </div>

          {memoryEntries.length === 0 ? (
            <div className="py-8 text-center font-mono text-[10px] text-gray-500">
              NO MEMORY ENTRIES YET. EXECUTE TASKS TO BUILD BRAND MEMORY.
            </div>
          ) : (
            <div className="space-y-2 max-h-[320px] overflow-auto pr-1">
              {memoryEntries.map((m) => (
                <div
                  key={m.id}
                  className="rounded-lg border border-border bg-surface-deep p-3 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between font-mono text-[9px]">
                    <span className="text-hive capitalize">{m.category.replace("_", " ")}</span>
                    <span className="text-gray-500">
                      {new Date(m.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <b className="block text-gray-200">{m.key}</b>
                  {m.content?.pattern && (
                    <p className="text-gray-400 text-[11px]">{m.content.pattern}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Execution History */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div className="flex items-center gap-2">
              <History size={16} className="text-hive" />
              <h2 className="font-display text-sm font-semibold">Task Execution History</h2>
            </div>
            <span className="font-mono text-[9px] text-gray-500">{tasks.length} Executions</span>
          </div>

          {tasks.length === 0 ? (
            <div className="py-8 text-center font-mono text-[10px] text-gray-500">
              NO HISTORICAL TASKS FOR THIS WORKER.
            </div>
          ) : (
            <div className="space-y-2 max-h-[320px] overflow-auto pr-1">
              {tasks.map((t) => (
                <div
                  key={t.task_id}
                  className="rounded-lg border border-border bg-surface-deep p-3 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between font-mono text-[9px]">
                    <span className="text-gray-400">ID: {t.task_id.slice(0, 8)}</span>
                    <span
                      className={cn(
                        "rounded px-1.5 py-0.5 uppercase",
                        t.status === "completed"
                          ? "text-emerald-400 bg-emerald-500/10"
                          : t.status === "needs_approval"
                          ? "text-hive bg-hive/10"
                          : "text-red-400 bg-red-500/10"
                      )}
                    >
                      {t.status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="text-gray-200 line-clamp-1">{t.content?.title || t.objective}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
