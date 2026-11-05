import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type ScheduledPublication } from "@/lib/api";
import { useWorkers } from "@/hooks/use-workers";
import {
  Calendar as CalendarIcon,
  CheckCircle2,
  Clock,
  ExternalLink,
  Flame,
  Globe,
  Instagram,
  Layers,
  Play,
  Send,
  Share2,
  Twitter,
  Youtube,
  AlertCircle,
  Copy,
} from "lucide-react";
import { cn } from "@/lib/utils";

const platformIcons: Record<string, React.ReactNode> = {
  instagram: <Instagram size={15} className="text-pink-400" />,
  youtube: <Youtube size={15} className="text-red-400" />,
  twitter: <Twitter size={15} className="text-sky-400" />,
  facebook: <Globe size={15} className="text-blue-400" />,
  manual: <Layers size={15} className="text-hive" />,
};

export default function PublishingPage() {
  const queryClient = useQueryClient();
  const { data: workers = [] } = useWorkers();

  const [selectedWorker, setSelectedWorker] = useState<string>("all");
  const [activePub, setActivePub] = useState<ScheduledPublication | null>(null);
  const [manualUrl, setManualUrl] = useState("");
  const [copied, setCopied] = useState(false);

  // Queries
  const { data: schedule = [] } = useQuery({
    queryKey: ["schedule", selectedWorker],
    queryFn: () =>
      api.listSchedule({
        worker_id: selectedWorker !== "all" ? selectedWorker : undefined,
      }),
    refetchInterval: 10_000,
  });

  const { data: approvedTasks = [] } = useQuery({
    queryKey: ["approved-tasks"],
    queryFn: () => api.listTasks({ status: "completed" }),
  });

  // Mutations
  const publishNowMutation = useMutation({
    mutationFn: (id: string) => api.publishNow(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
    },
  });

  const completeManualMutation = useMutation({
    mutationFn: ({ id, url }: { id: string; url: string }) => api.completeManual(id, url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
      setManualUrl("");
    },
  });

  const scheduleMutation = useMutation({
    mutationFn: ({ taskId, platform }: { taskId: string; platform: string }) =>
      api.schedulePublication({
        task_id: taskId,
        platform,
        scheduled_at: new Date(Date.now() + 3600_000).toISOString(),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
    },
  });

  const scheduledCount = schedule.filter((s) => s.status === "scheduled").length;
  const manualCount = schedule.filter((s) => s.status === "manual_required").length;
  const publishedCount = schedule.filter((s) => s.status === "published").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
            DISTRIBUTION OPERATIONS
          </div>
          <h1 className="mt-1 font-display text-2xl font-semibold">Publishing Calendar</h1>
          <p className="text-xs text-gray-400">
            Cross-platform delivery queues, scheduled releases, and verified manual publishing dispatches.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded border border-border bg-surface px-3 py-1.5 font-mono text-[10px]">
          <CalendarIcon size={13} className="text-hive" />
          <span>AUTONOMOUS PUBLISHING QUEUE</span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>QUEUED RELEASES</span>
            <Clock size={14} className="text-hive" />
          </div>
          <b className="mt-2 block font-display text-2xl">{scheduledCount}</b>
          <small className="text-[10px] text-gray-500">Awaiting release window</small>
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>MANUAL DISPATCHES</span>
            <Layers size={14} className="text-amber-400" />
          </div>
          <b className="mt-2 block font-display text-2xl text-amber-400">{manualCount}</b>
          <small className="text-[10px] text-gray-500">Requires operator paste</small>
        </div>

        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>LIVE RELEASES</span>
            <CheckCircle2 size={14} className="text-emerald-400" />
          </div>
          <b className="mt-2 block font-display text-2xl text-emerald-400">{publishedCount}</b>
          <small className="text-[10px] text-gray-500">Verified published posts</small>
        </div>
      </div>

      {/* Main Grid: Queue & Quick Schedule */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Left: Schedule List */}
        <div className="lg:col-span-8 space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h2 className="font-display text-base font-semibold">Distribution Queue</h2>
            <div className="flex items-center gap-1.5 font-mono text-xs">
              <button
                onClick={() => setSelectedWorker("all")}
                className={cn(
                  "rounded px-2.5 py-1 text-[10px] transition-colors",
                  selectedWorker === "all" ? "bg-hive/10 text-hive font-semibold" : "text-gray-400 hover:text-gray-200"
                )}
              >
                ALL
              </button>
              {workers.map((w) => (
                <button
                  key={w.id}
                  onClick={() => setSelectedWorker(w.id)}
                  className={cn(
                    "rounded px-2.5 py-1 text-[10px] transition-colors",
                    selectedWorker === w.id ? "bg-hive/10 text-hive font-semibold" : "text-gray-400 hover:text-gray-200"
                  )}
                >
                  {w.name}
                </button>
              ))}
            </div>
          </div>

          {schedule.length === 0 ? (
            <div className="rounded-xl border border-border bg-surface p-12 text-center">
              <CalendarIcon size={32} className="mx-auto text-gray-500 mb-3" />
              <h3 className="font-display text-sm font-semibold text-gray-200">No Scheduled Publications</h3>
              <p className="mt-1 text-xs text-gray-500 max-w-sm mx-auto">
                Authorize deliverables in the Approval Queue or select an approved content item on the right to schedule a release.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {schedule.map((item) => (
                <div
                  key={item.id}
                  className="rounded-xl border border-border bg-surface p-4 flex flex-col justify-between transition-colors hover:border-border-strong"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="grid h-8 w-8 place-items-center rounded bg-surface-deep border border-border">
                        {platformIcons[item.platform] || <Globe size={15} />}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[9px] text-hive uppercase font-semibold">
                            {item.worker_id}
                          </span>
                          <span className="text-gray-600">·</span>
                          <span className="font-mono text-[9px] text-gray-400 capitalize">
                            {item.platform}
                          </span>
                        </div>
                        <h4 className="font-display text-sm font-semibold text-gray-200 mt-0.5">
                          Scheduled Task #{item.task_id.slice(0, 8)}
                        </h4>
                      </div>
                    </div>

                    <span
                      className={cn(
                        "rounded px-2 py-0.5 font-mono text-[8px] uppercase font-semibold",
                        item.status === "published"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : item.status === "manual_required"
                          ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          : "bg-surface-deep text-gray-400 border border-border"
                      )}
                    >
                      {item.status.replace("_", " ")}
                    </span>
                  </div>

                  {/* Manual Instructions Display */}
                  {item.status === "manual_required" && item.manual_instructions && (
                    <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 text-xs space-y-2">
                      <div className="flex items-center justify-between font-mono text-[9px] text-amber-400 font-semibold">
                        <span>MANUAL OPERATOR ACTION REQUIRED</span>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(item.manual_instructions || "");
                            setCopied(true);
                            setTimeout(() => setCopied(false), 2000);
                          }}
                          className="flex items-center gap-1 text-[9px] text-gray-300 hover:text-white"
                        >
                          <Copy size={11} /> {copied ? "COPIED" : "COPY TEXT"}
                        </button>
                      </div>
                      <pre className="whitespace-pre-wrap font-sans text-gray-300 leading-relaxed text-[11px] max-h-[120px] overflow-auto">
                        {item.manual_instructions}
                      </pre>
                      <div className="flex items-center gap-2 pt-2 border-t border-border">
                        <input
                          type="text"
                          placeholder="Paste public post URL once posted..."
                          value={manualUrl}
                          onChange={(e) => setManualUrl(e.target.value)}
                          className="flex-1 rounded border border-border bg-surface-deep px-2.5 py-1.5 text-xs text-gray-200 outline-none"
                        />
                        <button
                          onClick={() => completeManualMutation.mutate({ id: item.id, url: manualUrl })}
                          disabled={!manualUrl}
                          className="rounded bg-emerald-500 px-3 py-1.5 font-mono text-[9px] font-semibold text-[#090b10] disabled:opacity-50"
                        >
                          CONFIRM PUBLISHED
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="mt-3 flex items-center justify-between border-t border-border pt-3 text-xs text-gray-400">
                    <span className="font-mono text-[9px]">
                      Scheduled: {new Date(item.scheduled_at).toLocaleString()}
                    </span>

                    {item.status === "scheduled" && (
                      <button
                        onClick={() => publishNowMutation.mutate(item.id)}
                        disabled={publishNowMutation.isPending}
                        className="flex items-center gap-1 rounded bg-surface-deep border border-border px-2.5 py-1 font-mono text-[9px] text-gray-300 hover:border-hive/50 hover:text-hive"
                      >
                        <Play size={10} fill="currentColor" /> PUBLISH NOW
                      </button>
                    )}

                    {item.platform_url && (
                      <a
                        href={item.platform_url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 font-mono text-[9px] text-hive hover:underline"
                      >
                        VIEW POST <ExternalLink size={10} />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Quick Schedule Approved Content */}
        <div className="lg:col-span-4 rounded-xl border border-border bg-surface p-5 space-y-4">
          <div className="border-b border-border pb-3">
            <h3 className="font-display text-sm font-semibold">Approved Content Ready to Schedule</h3>
            <p className="text-[11px] text-gray-400 mt-0.5">
              Only deliverables with operator approval can enter the distribution pipeline.
            </p>
          </div>

          {approvedTasks.length === 0 ? (
            <div className="py-8 text-center font-mono text-[10px] text-gray-500">
              NO APPROVED DELIVERABLES. APPROVE TASKS IN THE APPROVAL QUEUE FIRST.
            </div>
          ) : (
            <div className="space-y-3 max-h-[460px] overflow-auto pr-1">
              {approvedTasks.map((t) => (
                <div
                  key={t.task_id}
                  className="rounded-lg border border-border bg-surface-deep p-3 text-xs space-y-2"
                >
                  <div className="flex items-center justify-between font-mono text-[9px]">
                    <span className="text-hive uppercase font-semibold">{t.worker_name}</span>
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 size={11} /> APPROVED
                    </span>
                  </div>
                  <h4 className="font-display font-medium text-gray-200 line-clamp-1">
                    {t.content?.title || t.objective}
                  </h4>
                  <div className="flex items-center gap-2 pt-1">
                    <button
                      onClick={() => scheduleMutation.mutate({ taskId: t.task_id, platform: "instagram" })}
                      className="flex-1 rounded bg-surface border border-border py-1 text-center font-mono text-[9px] text-gray-300 hover:text-hive hover:border-hive/40"
                    >
                      + Instagram
                    </button>
                    <button
                      onClick={() => scheduleMutation.mutate({ taskId: t.task_id, platform: "manual" })}
                      className="flex-1 rounded bg-hive/10 border border-hive/30 py-1 text-center font-mono text-[9px] text-hive font-semibold hover:bg-hive/20"
                    >
                      + Manual
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
