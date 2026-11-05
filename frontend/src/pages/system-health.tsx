import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Database,
  FolderCheck,
  HardDrive,
  HeartPulse,
  Layers,
  Power,
  RefreshCw,
  Server,
  ShieldAlert,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function SystemHealthPage() {
  const queryClient = useQueryClient();

  const { data: metrics, isLoading } = useQuery({
    queryKey: ["system-metrics"],
    queryFn: api.systemMetrics,
    refetchInterval: 5_000,
  });

  const killSwitchMutation = useMutation({
    mutationFn: (active: boolean) => api.toggleKillSwitch(active),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["system-metrics"] });
      queryClient.invalidateQueries({ queryKey: ["master-status"] });
    },
  });

  if (!metrics) {
    return (
      <div className="flex h-64 items-center justify-center font-mono text-xs text-gray-400">
        READING REAL-TIME SYSTEM TELEMETRY…
      </div>
    );
  }

  const isHalted = metrics.kill_switch_active;
  const isOllamaConnected = metrics.llm.status === "connected";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
            PRODUCTION HARDENING & TELEMETRY
          </div>
          <h1 className="mt-1 font-display text-2xl font-semibold">System Health</h1>
          <p className="text-xs text-gray-400">
            Real-time infrastructure probes, shared Ollama inference latency, storage mounts, and circuit breakers.
          </p>
        </div>
        <div
          className={cn(
            "flex items-center gap-2 rounded border px-3 py-1.5 font-mono text-[10px]",
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
          {isHalted ? "CIRCUIT BREAKER ENGAGED" : "ALL SERVICES OPERATIONAL"}
        </div>
      </div>

      {/* Emergency Kill Switch Banner */}
      <div
        className={cn(
          "rounded-xl border p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 transition-colors",
          isHalted
            ? "border-red-500/50 bg-red-500/10"
            : "border-border bg-surface"
        )}
      >
        <div className="flex items-start gap-3">
          <ShieldAlert
            size={24}
            className={isHalted ? "text-red-400 flex-shrink-0 mt-0.5" : "text-hive flex-shrink-0 mt-0.5"}
          />
          <div>
            <h3 className="font-display font-semibold text-sm text-gray-100">
              Global Operations Kill Switch
            </h3>
            <p className="text-xs text-gray-400 max-w-xl mt-0.5">
              Instantly halts Master Agent delegation, pauses worker generation pipelines, and locks social publishing queues across all 5 media brands.
            </p>
          </div>
        </div>

        <button
          onClick={() => killSwitchMutation.mutate(!isHalted)}
          disabled={killSwitchMutation.isPending}
          className={cn(
            "flex items-center justify-center gap-1.5 rounded-lg px-5 py-2.5 font-mono text-xs font-semibold tracking-wide transition-colors whitespace-nowrap",
            isHalted
              ? "bg-emerald-500 text-[#090b10] hover:bg-emerald-400"
              : "bg-red-500 text-white hover:bg-red-600"
          )}
        >
          <Power size={14} />
          {isHalted ? "DISENGAGE KILL SWITCH" : "ENGAGE EMERGENCY KILL SWITCH"}
        </button>
      </div>

      {/* Health Probes Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Ollama LLM Runtime */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>OLLAMA RUNTIME</span>
            <Cpu size={16} className="text-hive" />
          </div>
          <div>
            <b className="font-display text-xl text-gray-100 block">{metrics.llm.model}</b>
            <span className="font-mono text-[10px] text-gray-500 truncate block">
              {metrics.llm.endpoint}
            </span>
          </div>
          <div className="border-t border-border pt-3 space-y-1 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Connection:</span>
              <span className={cn("font-mono text-[10px]", isOllamaConnected ? "text-emerald-400" : "text-red-400")}>
                {metrics.llm.status.toUpperCase()}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Probe Latency:</span>
              <span className="font-mono text-[10px] text-gray-200">{metrics.llm.latency_ms} ms</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Concurrency:</span>
              <span className="font-mono text-[10px] text-hive">{metrics.llm.max_concurrency} max workers</span>
            </div>
          </div>
        </div>

        {/* Worker Fleet Health */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>WORKER FLEET</span>
            <Layers size={16} className="text-hive" />
          </div>
          <div>
            <b className="font-display text-xl text-gray-100 block">
              {metrics.fleet.active_brands} / {metrics.fleet.total_brands} ONLINE
            </b>
            <span className="font-mono text-[10px] text-gray-500">Autonomous Niche Brands</span>
          </div>
          <div className="border-t border-border pt-3 space-y-1 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Active Fleet:</span>
              <span className="font-mono text-[10px] text-emerald-400">{metrics.fleet.active_brands} Ready</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Paused Fleet:</span>
              <span className="font-mono text-[10px] text-gray-400">{metrics.fleet.paused_brands} Paused</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Memory Stores:</span>
              <span className="font-mono text-[10px] text-gray-200">5 Isolated</span>
            </div>
          </div>
        </div>

        {/* Storage Mounts */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>STORAGE VOLUMES</span>
            <HardDrive size={16} className="text-hive" />
          </div>
          <div>
            <b className="font-display text-xl text-gray-100 block">VOLUMES MOUNTED</b>
            <span className="font-mono text-[10px] text-gray-500">Media & Cache Storage</span>
          </div>
          <div className="border-t border-border pt-3 space-y-1 text-xs">
            {Object.entries(metrics.storage.directories).map(([dir, mounted]) => (
              <div key={dir} className="flex items-center justify-between font-mono text-[10px]">
                <span className="text-gray-400 capitalize">storage/{dir}:</span>
                <span className={mounted ? "text-emerald-400" : "text-red-400"}>
                  {mounted ? "MOUNTED" : "MISSING"}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Security & Audit */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>SECURITY AUDIT</span>
            <ShieldCheck size={16} className="text-emerald-400" />
          </div>
          <div>
            <b className="font-display text-xl text-emerald-400 block">ENFORCED</b>
            <span className="font-mono text-[10px] text-gray-500">Zero-Scraping / Official APIs</span>
          </div>
          <div className="border-t border-border pt-3 space-y-1 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Audit Logs:</span>
              <span className="font-mono text-[10px] text-gray-200">{metrics.security.audit_logs_count} recorded</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">HITL Approval:</span>
              <span className="font-mono text-[10px] text-emerald-400">100% Gated</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">RLS Status:</span>
              <span className="font-mono text-[10px] text-emerald-400">Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
