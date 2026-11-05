import { Link, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  Activity,
  Bot,
  BrainCircuit,
  Calendar,
  CircleDollarSign,
  Clapperboard,
  LayoutDashboard,
  Radio,
  Settings2,
  ShieldCheck,
  Users,
  Plug,
  HeartPulse,
  Flame,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/stores/app-store";

const mainNav = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/master-agent", label: "Master Agent", icon: BrainCircuit, badge: "LIVE" },
  { to: "/workers", label: "Workers", icon: Users },
  { to: "/content-studio", label: "Content Studio", icon: Radio },
  { to: "/video-studio", label: "Video Engine", icon: Clapperboard, badge: "9:16 HD" },
  { to: "/approval-queue", label: "Approvals", icon: ShieldCheck, hasCounter: true },
  { to: "/publishing", label: "Publishing", icon: Calendar },
  { to: "/analytics", label: "Analytics", icon: Activity },
  { to: "/revenue", label: "Revenue", icon: CircleDollarSign },
];

const systemNav = [
  { to: "/integrations", label: "Integrations", icon: Plug },
  { to: "/system", label: "System Health", icon: HeartPulse },
  { to: "/settings", label: "Settings", icon: Settings2 },
];

export function Sidebar() {
  const location = useLocation();
  const { sidebarCollapsed, toggleSidebar } = useAppStore();

  const { data: pendingTasks = [] } = useQuery({
    queryKey: ["pending-tasks"],
    queryFn: api.pendingTasks,
    refetchInterval: 12_000,
  });

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-border/80 bg-[#07090e] transition-all duration-300 relative select-none",
        sidebarCollapsed ? "w-[68px]" : "w-[244px]"
      )}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between px-4 pt-5 pb-6">
        <Link to="/" className="flex items-center gap-3 no-underline">
          <div className="relative grid h-9 w-9 flex-shrink-0 place-items-center rounded-xl bg-hive font-display text-[20px] font-bold text-[#090b10] shadow-[0_0_20px_rgba(245,166,35,0.35)]">
            H
            <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-emerald-400 border border-surface shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
          </div>
          {!sidebarCollapsed && (
            <div>
              <div className="flex items-center gap-1.5">
                <b className="font-display text-[16px] tracking-[1.5px] text-gray-100">HIVE</b>
                <span className="rounded bg-hive/15 px-1.5 py-0.2 font-mono text-[8px] font-bold text-hive border border-hive/20">
                  AI OS
                </span>
              </div>
              <small className="block font-mono text-[9px] tracking-[1.1px] text-gray-500">
                MEDIA NETWORK
              </small>
            </div>
          )}
        </Link>
        <button
          onClick={toggleSidebar}
          className="text-gray-500 hover:text-gray-300 p-1 rounded hover:bg-surface"
          title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {sidebarCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>

      {/* Workspace Indicator Badge */}
      {!sidebarCollapsed && (
        <div className="mx-3 mb-5 rounded-lg border border-border/80 bg-surface-card/60 p-2.5 font-mono text-[10px] text-gray-400 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-hive shadow-[0_0_8px_rgba(245,166,35,0.7)] animate-pulse" />
            <span className="font-medium text-gray-300">AUTONOMOUS RUNTIME</span>
          </div>
          <span className="text-[9px] text-emerald-400 font-bold">5/5 FLEET</span>
        </div>
      )}

      {/* Main Workspace Navigation */}
      {!sidebarCollapsed && (
        <div className="px-3 pb-2 font-mono text-[9px] tracking-[1.8px] text-gray-500">
          WORKSPACE
        </div>
      )}
      <nav className="grid gap-1 px-2">
        {mainNav.map((item) => {
          const isActive = location.pathname === item.to;
          const pendingCount = item.hasCounter ? pendingTasks.length : 0;
          return (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                "group flex h-[40px] items-center justify-between rounded-lg px-3 text-[12px] no-underline transition-all",
                isActive
                  ? "border border-hive/30 bg-hive/10 text-gray-100 shadow-[0_0_15px_rgba(245,166,35,0.08)] font-medium"
                  : "text-gray-400 hover:text-gray-200 hover:bg-surface-card/50",
                sidebarCollapsed && "justify-center px-0"
              )}
            >
              <div className="flex items-center gap-3">
                <item.icon
                  size={16}
                  className={cn(
                    "transition-colors",
                    isActive ? "text-hive" : "text-gray-500 group-hover:text-gray-300"
                  )}
                />
                {!sidebarCollapsed && <span>{item.label}</span>}
              </div>

              {!sidebarCollapsed && (
                <>
                  {pendingCount > 0 && (
                    <span className="rounded-full bg-hive px-2 py-0.5 font-mono text-[10px] font-bold text-[#090b10] shadow-[0_0_8px_rgba(245,166,35,0.4)] animate-pulse">
                      {pendingCount}
                    </span>
                  )}
                  {!pendingCount && item.badge && (
                    <span
                      className={cn(
                        "rounded px-1.5 py-0.5 font-mono text-[8px] font-semibold border",
                        item.badge === "LIVE"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : "bg-surface border-border text-gray-400"
                      )}
                    >
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </Link>
          );
        })}
      </nav>

      {/* System Navigation */}
      {!sidebarCollapsed && (
        <div className="mt-6 px-3 pb-2 font-mono text-[9px] tracking-[1.8px] text-gray-500">
          INFRASTRUCTURE
        </div>
      )}
      <nav className="grid gap-1 px-2">
        {systemNav.map((item) => {
          const isActive = location.pathname === item.to;
          return (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                "group flex h-[38px] items-center gap-3 rounded-lg px-3 text-[12px] no-underline transition-colors",
                isActive
                  ? "border border-hive/30 bg-hive/10 text-gray-100 font-medium"
                  : "text-gray-400 hover:text-gray-200 hover:bg-surface-card/50",
                sidebarCollapsed && "justify-center px-0"
              )}
            >
              <item.icon
                size={16}
                className={cn(
                  isActive ? "text-hive" : "text-gray-500 group-hover:text-gray-300"
                )}
              />
              {!sidebarCollapsed && item.label}
            </Link>
          );
        })}
      </nav>

      {/* Operator Footer Profile */}
      <div className="mt-auto border-t border-border/70 p-3 bg-surface-card/30">
        <div className="flex items-center gap-2.5">
          <div className="relative grid h-8 w-8 place-items-center rounded-lg bg-surface border border-hive/30 font-mono text-[11px] font-bold text-hive shadow-[0_0_10px_rgba(245,166,35,0.15)]">
            MH
            <span className="absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full bg-emerald-400 border border-surface shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
          </div>
          {!sidebarCollapsed && (
            <div className="truncate flex-1">
              <div className="flex items-center justify-between">
                <b className="block text-[11px] text-gray-200">Operator</b>
                <span className="font-mono text-[8px] text-emerald-400 font-semibold">ROOT</span>
              </div>
              <small className="block font-mono text-[9px] text-gray-500 truncate">
                hive.local/workspace
              </small>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
