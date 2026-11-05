import { useLocation, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useHealth } from "@/hooks/use-workers";
import { api } from "@/lib/api";
import {
  Activity,
  AlertOctagon,
  Bot,
  BrainCircuit,
  Calendar,
  CheckCircle2,
  ChevronRight,
  CircleDollarSign,
  Clapperboard,
  Command,
  Cpu,
  HeartPulse,
  LayoutDashboard,
  Plug,
  Radio,
  Search,
  Settings2,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const pageMeta: Record<string, { title: string; category: string; icon: any }> = {
  "/": { title: "Executive Overview", category: "Operations", icon: LayoutDashboard },
  "/master-agent": { title: "Master Agent Cockpit", category: "Intelligence", icon: BrainCircuit },
  "/workers": { title: "Creator Fleets", category: "Brands", icon: Users },
  "/content-studio": { title: "Trend & Multi-Channel Studio", category: "Production", icon: Radio },
  "/video-studio": { title: "Video Intelligence Engine", category: "Rendering", icon: Clapperboard },
  "/approval-queue": { title: "Master Approval Queue", category: "Safety", icon: ShieldCheck },
  "/publishing": { title: "Publishing & Distribution", category: "Network", icon: Calendar },
  "/analytics": { title: "Cross-Platform Attention", category: "Intelligence", icon: Activity },
  "/revenue": { title: "Monetization & Ledger", category: "Finance", icon: CircleDollarSign },
  "/integrations": { title: "Platform Adapters", category: "System", icon: Plug },
  "/system": { title: "System Telemetry", category: "DevOps", icon: HeartPulse },
  "/settings": { title: "Fleet Settings", category: "System", icon: Settings2 },
};

export function Topbar() {
  const location = useLocation();
  const queryClient = useQueryClient();
  const { data: health } = useHealth();
  
  const { data: metrics } = useQuery({
    queryKey: ["system-metrics"],
    queryFn: api.systemMetrics,
    refetchInterval: 15_000,
  });

  const killSwitchMutation = useMutation({
    mutationFn: (active: boolean) => api.toggleKillSwitch(active, "Operator topbar action"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["system-metrics"] });
      queryClient.invalidateQueries({ queryKey: ["master-status"] });
    },
  });

  const meta = pageMeta[location.pathname] || {
    title: "HIVE Operations",
    category: "Workspace",
    icon: Sparkles,
  };
  const Icon = meta.icon;
  const isOnline = health?.status === "ok";
  const isHalted = metrics?.kill_switch_active ?? false;

  return (
    <header className="flex h-[68px] items-center justify-between border-b border-border/80 bg-surface-deep/80 px-4 backdrop-blur-xl">
      {/* Left: Breadcrumbs & Active Page Badge */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 rounded-lg border border-border bg-surface-card px-2.5 py-1 text-xs">
          <Icon size={14} className="text-hive" />
          <span className="font-mono text-[10px] uppercase text-gray-500 tracking-wider">
            {meta.category}
          </span>
          <ChevronRight size={12} className="text-gray-600" />
          <span className="font-display font-semibold text-gray-100">{meta.title}</span>
        </div>
      </div>

      {/* Right: Telemetry Indicators & Quick Actions */}
      <div className="flex items-center gap-3">
        {/* Quick Search trigger pill */}
        <div className="hidden sm:flex items-center gap-2 rounded-lg border border-border/80 bg-surface-card/60 px-3 py-1.5 text-xs text-gray-400 hover:border-hive/30 transition-colors cursor-pointer">
          <Search size={13} className="text-gray-500" />
          <span className="text-[11px] text-gray-400 font-sans">Quick Jump</span>
          <kbd className="rounded border border-border bg-surface px-1.5 py-0.5 font-mono text-[9px] text-gray-400">
            ⌘K
          </kbd>
        </div>

        {/* LLM Model Status Pill */}
        <div className="hidden md:flex items-center gap-2 rounded-lg border border-border bg-surface-card px-3 py-1.5 font-mono text-[10px]">
          <Cpu size={12} className="text-hive" />
          <span className="text-gray-300 font-medium">Llama 3.1</span>
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse" />
          <span className="text-gray-500">{metrics?.llm?.latency_ms ? `${metrics.llm.latency_ms}ms` : "18ms"}</span>
        </div>

        {/* Global Emergency Kill-Switch Toggle Pill */}
        <button
          onClick={() => killSwitchMutation.mutate(!isHalted)}
          disabled={killSwitchMutation.isPending}
          className={cn(
            "flex items-center gap-2 rounded-lg border px-3 py-1.5 font-mono text-[10px] font-semibold transition-all shadow-sm",
            isHalted
              ? "border-red-500/50 bg-red-500/20 text-red-300 hover:bg-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.3)] animate-pulse"
              : "border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:border-red-500/40 hover:text-red-400"
          )}
          title={isHalted ? "Click to disengage kill switch" : "Click to freeze all autonomous activity"}
        >
          {isHalted ? (
            <>
              <AlertOctagon size={13} className="text-red-400" />
              <span>KILL SWITCH ACTIVE</span>
            </>
          ) : (
            <>
              <ShieldCheck size={13} className="text-emerald-400" />
              <span>CIRCUIT NORMAL</span>
            </>
          )}
        </button>

        {/* Operator Profile */}
        <div className="flex items-center gap-2 border-l border-border pl-3">
          <div className="relative grid h-8 w-8 place-items-center rounded-lg bg-surface border border-hive/30 font-mono text-xs font-bold text-hive shadow-[0_0_12px_rgba(245,166,35,0.15)]">
            OP
            <span className="absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full bg-emerald-400 border border-surface" />
          </div>
        </div>
      </div>
    </header>
  );
}
