import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type TaskReport } from "@/lib/api";
import {
  AlertTriangle,
  CheckCircle2,
  CircleDollarSign,
  Clapperboard,
  Clock,
  Eye,
  FileText,
  Film,
  Play,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function ApprovalQueuePage() {
  const queryClient = useQueryClient();
  const [selectedTask, setSelectedTask] = useState<TaskReport | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [isRejecting, setIsRejecting] = useState(false);

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ["pending-tasks"],
    queryFn: () => api.listTasks({ status: "needs_approval" }),
    refetchInterval: 10_000,
  });

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

  const activeTask = selectedTask || tasks[0] || null;

  const videoUrl = (() => {
    if (!activeTask) return null;
    const combined = `${activeTask.objective} ${activeTask.output || ""}`;
    const match = combined.match(/(\/storage\/videos\/[^\s'"]+\.mp4)/);
    return match ? match[1] : null;
  })();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
            HUMAN-IN-THE-LOOP CONTROL
          </div>
          <h1 className="mt-1 font-display text-2xl font-semibold">Approval Queue</h1>
          <p className="text-xs text-gray-400">
            Review, verify factual claims, and authorize worker deliverables prior to public distribution.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded border border-border bg-surface px-3 py-1.5 font-mono text-[10px]">
          <Clock size={13} className="text-hive" />
          <span>{tasks.length} PENDING REVIEW</span>
        </div>
      </div>

      {tasks.length === 0 ? (
        <div className="flex min-h-[50vh] flex-col items-center justify-center rounded-xl border border-border bg-surface p-8 text-center">
          <div className="mb-4 grid h-14 w-14 place-items-center rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400">
            <CheckCircle2 size={28} />
          </div>
          <h2 className="font-display text-lg font-semibold">Queue is Clear</h2>
          <p className="mt-1 max-w-sm text-xs text-gray-400">
            No worker deliverables are currently awaiting authorization. New tasks requiring review will appear here automatically.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-12">
          {/* Left: Pending Task List */}
          <div className="lg:col-span-5 space-y-2">
            <div className="font-mono text-[9px] tracking-wide text-gray-500 mb-1">
              AWAITING OPERATOR SIGN-OFF
            </div>
            {tasks.map((task) => {
              const isSelected = activeTask?.task_id === task.task_id;
              return (
                <button
                  key={task.task_id}
                  onClick={() => setSelectedTask(task)}
                  className={cn(
                    "w-full text-left rounded-lg border p-4 transition-colors",
                    isSelected
                      ? "border-hive/50 bg-hive/5 shadow-[0_0_15px_rgba(245,166,35,0.05)]"
                      : "border-border bg-surface hover:border-border-strong"
                  )}
                >
                  <div className="flex items-center justify-between text-[10px] font-mono">
                    <span className="text-hive font-semibold uppercase">{task.worker_name}</span>
                    <span className="text-gray-500">{new Date(task.created_at).toLocaleTimeString()}</span>
                  </div>
                  <h3 className="mt-1.5 font-display text-sm font-medium text-gray-100 line-clamp-1">
                    {task.content?.title || task.objective}
                  </h3>
                  <div className="mt-2.5 flex items-center gap-2">
                    {task.priority && (
                      <span className="rounded bg-surface-raised border border-border px-1.5 py-0.5 font-mono text-[8px] uppercase text-gray-400">
                        {task.priority}
                      </span>
                    )}
                    {task.content?.estimated_risk_level && (
                      <span
                        className={cn(
                          "rounded px-1.5 py-0.5 font-mono text-[8px] uppercase",
                          task.content.estimated_risk_level === "high"
                            ? "bg-red-500/10 text-red-400 border border-red-500/20"
                            : "bg-surface-raised text-gray-400 border border-border"
                        )}
                      >
                        Risk: {task.content.estimated_risk_level}
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
            <div className="lg:col-span-7 rounded-xl border border-border bg-surface p-6 flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex items-start justify-between border-b border-border pb-4">
                  <div>
                    <div className="font-mono text-[9px] text-gray-500 uppercase">
                      {activeTask.worker_name} · TASK #{activeTask.task_id.slice(0, 8)}
                    </div>
                    <h2 className="mt-1 font-display text-lg font-semibold text-gray-100">
                      {activeTask.content?.title || "Content Deliverable"}
                    </h2>
                  </div>
                  <span className="rounded border border-hive/30 bg-hive/10 px-2 py-0.5 font-mono text-[9px] text-hive font-semibold">
                    NEEDS APPROVAL
                  </span>
                </div>

                {videoUrl && (
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
                )}

                {activeTask.content ? (
                  <div className="space-y-3 text-[11px]">
                    {/* Hook */}
                    <div className="rounded-lg border border-hive/30 bg-hive/5 p-3">
                      <div className="flex items-center gap-1.5 font-mono text-[9px] font-semibold text-hive mb-1">
                        <Sparkles size={13} />
                        3-SECOND HOOK
                      </div>
                      <p className="font-medium text-gray-200">"{activeTask.content.hook}"</p>
                    </div>

                    {/* Script */}
                    <div className="rounded-lg border border-border bg-surface-deep p-3">
                      <div className="flex items-center gap-1.5 font-mono text-[9px] text-gray-400 mb-1">
                        <FileText size={13} />
                        BODY SCRIPT / NARRATION
                      </div>
                      <pre className="whitespace-pre-wrap font-sans text-gray-300 leading-relaxed text-[11px] max-h-[140px] overflow-auto">
                        {activeTask.content.body_script}
                      </pre>
                    </div>

                    {/* Caption */}
                    <div className="rounded-lg border border-border bg-surface-deep p-3">
                      <div className="font-mono text-[9px] text-gray-400 mb-1">CAPTION & HASHTAGS</div>
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
                        VISUAL BRIEF
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
              <div className="mt-6 border-t border-border pt-4">
                {isRejecting ? (
                  <div className="space-y-2">
                    <label className="block font-mono text-[9px] text-gray-400">REJECTION FEEDBACK / INSTRUCTIONS</label>
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
                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => setIsRejecting(true)}
                      className="flex items-center gap-1.5 rounded border border-red-500/30 bg-red-500/5 px-4 py-2 font-mono text-[10px] text-red-400 hover:bg-red-500/10"
                    >
                      <XCircle size={15} />
                      REJECT / REVISE
                    </button>

                    <button
                      onClick={() => approveMutation.mutate(activeTask.task_id)}
                      disabled={approveMutation.isPending}
                      className="flex items-center gap-1.5 rounded bg-emerald-500 px-5 py-2 font-mono text-[10px] font-semibold text-[#090b10] hover:bg-emerald-400 transition-colors"
                    >
                      <CheckCircle2 size={15} />
                      {approveMutation.isPending ? "AUTHORIZING…" : "AUTHORIZE FOR PUBLISHING"}
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
