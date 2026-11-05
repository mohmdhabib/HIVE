import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  CheckCircle2,
  Cpu,
  Database,
  Globe,
  HardDrive,
  Lock,
  Power,
  Save,
  Server,
  Settings2,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const queryClient = useQueryClient();

  const { data: metrics } = useQuery({
    queryKey: ["system-metrics"],
    queryFn: api.systemMetrics,
  });

  const [savedMessage, setSavedMessage] = useState(false);

  const killSwitchMutation = useMutation({
    mutationFn: (active: boolean) => api.toggleKillSwitch(active),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["system-metrics"] });
      queryClient.invalidateQueries({ queryKey: ["master-status"] });
    },
  });

  const isHalted = metrics?.kill_switch_active;

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
            SYSTEM PREFERENCES
          </div>
          <h1 className="mt-1 font-display text-2xl font-semibold">Settings & Configuration</h1>
          <p className="text-xs text-gray-400">
            Global operational boundaries, runtime inference quotas, database credentials, and security gates.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded border border-border bg-surface px-3 py-1.5 font-mono text-[10px]">
          <Settings2 size={13} className="text-hive" />
          <span>PRODUCTION DEPLOYMENT</span>
        </div>
      </div>

      {/* Emergency Control Card */}
      <div
        className={cn(
          "rounded-xl border p-5 flex items-center justify-between transition-colors",
          isHalted ? "border-red-500/50 bg-red-500/10" : "border-border bg-surface"
        )}
      >
        <div>
          <b className="block font-display text-sm text-gray-100">Global Operations Kill Switch</b>
          <p className="text-xs text-gray-400 mt-0.5">
            Emergency master cutoff. Halts all active LangGraph worker delegations immediately.
          </p>
        </div>
        <button
          onClick={() => killSwitchMutation.mutate(!isHalted)}
          disabled={killSwitchMutation.isPending}
          className={cn(
            "rounded-lg px-4 py-2 font-mono text-xs font-semibold tracking-wide transition-colors",
            isHalted
              ? "bg-emerald-500 text-[#090b10] hover:bg-emerald-400"
              : "bg-red-500 text-white hover:bg-red-600"
          )}
        >
          {isHalted ? "DISENGAGE KILL SWITCH" : "ENGAGE KILL SWITCH"}
        </button>
      </div>

      {/* AI & Model Inference Runtime */}
      <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
        <div className="flex items-center gap-2 border-b border-border pb-3">
          <Cpu size={16} className="text-hive" />
          <h2 className="font-display text-base font-semibold">Shared Ollama Model Runtime</h2>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 text-xs">
          <div>
            <label className="block font-mono text-[9px] text-gray-500 mb-1">OLLAMA HOST URL</label>
            <input
              type="text"
              readOnly
              value={metrics?.llm.endpoint || "http://host.docker.internal:11434"}
              className="w-full rounded border border-border bg-surface-deep px-3 py-2 font-mono text-gray-300 outline-none"
            />
          </div>

          <div>
            <label className="block font-mono text-[9px] text-gray-500 mb-1">LOCAL INFERENCE MODEL</label>
            <input
              type="text"
              readOnly
              value={metrics?.llm.model || "llama3.1"}
              className="w-full rounded border border-border bg-surface-deep px-3 py-2 font-mono text-gray-300 outline-none"
            />
          </div>

          <div>
            <label className="block font-mono text-[9px] text-gray-500 mb-1">CONCURRENCY SEMAPHORE</label>
            <input
              type="text"
              readOnly
              value={`${metrics?.llm.max_concurrency || 2} concurrent worker execution slots`}
              className="w-full rounded border border-border bg-surface-deep px-3 py-2 font-mono text-gray-300 outline-none"
            />
          </div>

          <div>
            <label className="block font-mono text-[9px] text-gray-500 mb-1">INFERENCE TIMEOUT</label>
            <input
              type="text"
              readOnly
              value="180 seconds"
              className="w-full rounded border border-border bg-surface-deep px-3 py-2 font-mono text-gray-300 outline-none"
            />
          </div>
        </div>
      </div>

      {/* Supabase & Cloud Persistence */}
      <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
        <div className="flex items-center gap-2 border-b border-border pb-3">
          <Database size={16} className="text-emerald-400" />
          <h2 className="font-display text-base font-semibold">Supabase PostgreSQL & Auth</h2>
        </div>

        <div className="space-y-3 text-xs">
          <div>
            <label className="block font-mono text-[9px] text-gray-500 mb-1">SUPABASE URL</label>
            <input
              type="text"
              readOnly
              value="https://bksoqxewamrqnqjqborx.supabase.co"
              className="w-full rounded border border-border bg-surface-deep px-3 py-2 font-mono text-gray-300 outline-none"
            />
          </div>

          <div>
            <label className="block font-mono text-[9px] text-gray-500 mb-1">PUBLISHABLE KEY (ANON)</label>
            <input
              type="password"
              readOnly
              value="sb_publishable_Pw1yZskOS_4B15_fFkrhBA_5TryJ-9L"
              className="w-full rounded border border-border bg-surface-deep px-3 py-2 font-mono text-gray-300 outline-none"
            />
          </div>

          <div className="flex items-center gap-2 text-[11px] text-emerald-400 pt-1">
            <CheckCircle2 size={13} />
            <span>Connected & Schema Migrations Active (RLS Enforced)</span>
          </div>
        </div>
      </div>

      {/* Safety & Compliance Gates */}
      <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
        <div className="flex items-center gap-2 border-b border-border pb-3">
          <ShieldCheck size={16} className="text-hive" />
          <h2 className="font-display text-base font-semibold">Editorial & Safety Controls</h2>
        </div>

        <div className="space-y-3 text-xs">
          <div className="flex items-center justify-between rounded-lg border border-border bg-surface-deep p-3">
            <div>
              <b className="block text-gray-200">Mandatory Human-in-the-Loop Sign-off</b>
              <p className="text-[11px] text-gray-400">Require operator approval before any deliverable is scheduled or published.</p>
            </div>
            <span className="font-mono text-[10px] text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">
              ALWAYS ENFORCED
            </span>
          </div>

          <div className="flex items-center justify-between rounded-lg border border-border bg-surface-deep p-3">
            <div>
              <b className="block text-gray-200">Zero-Scraping / Official API Mode</b>
              <p className="text-[11px] text-gray-400">Strictly prohibits automated engagement, fake views, and unverified scraping.</p>
            </div>
            <span className="font-mono text-[10px] text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">
              ACTIVE
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
