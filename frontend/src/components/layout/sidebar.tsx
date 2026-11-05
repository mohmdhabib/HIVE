import { Link, useLocation } from "react-router-dom";
import {
  Activity,
  Bot,
  BrainCircuit,
  Calendar,
  CircleDollarSign,
  LayoutDashboard,
  Radio,
  Settings2,
  ShieldCheck,
  Users,
  Plug,
  HeartPulse,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/stores/app-store";

const mainNav = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/master-agent", label: "Master Agent", icon: BrainCircuit },
  { to: "/workers", label: "Workers", icon: Users },
  { to: "/content-studio", label: "Content Studio", icon: Radio },
  { to: "/approval-queue", label: "Approvals", icon: ShieldCheck },
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
  const { sidebarCollapsed, systemOnline } = useAppStore();

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-border bg-[#0b0e14] transition-all duration-200",
        sidebarCollapsed ? "w-[60px]" : "w-[238px]"
      )}
    >
      {/* Brand */}
      <div className="flex items-center gap-3 px-4 pt-6 pb-7">
        <div className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-[10px] bg-hive font-display text-[21px] font-bold text-[#10150b] shadow-[0_0_25px_rgba(245,166,35,0.15)]">
          H
        </div>
        {!sidebarCollapsed && (
          <div>
            <b className="block font-display text-[17px] tracking-[2px]">HIVE</b>
            <small className="block font-mono text-[9px] tracking-[1.1px] text-gray-500">
              MEDIA NETWORK OS
            </small>
          </div>
        )}
      </div>

      {/* Workspace indicator */}
      {!sidebarCollapsed && (
        <div className="mx-3 mb-7 rounded-lg border border-border p-3 font-mono text-[10px] tracking-wide text-gray-400">
          <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-hive shadow-[0_0_9px_rgba(245,166,35,0.6)]" />
          LOCAL WORKSPACE
        </div>
      )}

      {/* Main navigation */}
      {!sidebarCollapsed && (
        <div className="px-3 pb-2 font-mono text-[9px] tracking-[1.5px] text-gray-600">
          WORKSPACE
        </div>
      )}
      <nav className="grid gap-1 px-2">
        {mainNav.map((item) => {
          const isActive = location.pathname === item.to;
          return (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                "flex h-[39px] items-center gap-3 rounded-[7px] px-3 text-[12px] text-gray-500 no-underline transition-colors hover:text-gray-300",
                isActive && "border border-border-strong bg-surface-overlay text-gray-200",
                sidebarCollapsed && "justify-center px-0"
              )}
            >
              <item.icon
                size={17}
                className={cn(isActive && "text-hive")}
              />
              {!sidebarCollapsed && item.label}
            </Link>
          );
        })}
      </nav>

      {/* System navigation */}
      {!sidebarCollapsed && (
        <div className="mt-7 px-3 pb-2 font-mono text-[9px] tracking-[1.5px] text-gray-600">
          SYSTEM
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
                "flex h-[39px] items-center gap-3 rounded-[7px] px-3 text-[12px] text-gray-500 no-underline transition-colors hover:text-gray-300",
                isActive && "border border-border-strong bg-surface-overlay text-gray-200",
                sidebarCollapsed && "justify-center px-0"
              )}
            >
              <item.icon size={17} className={cn(isActive && "text-hive")} />
              {!sidebarCollapsed && item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="mt-auto border-t border-border px-3 pt-4 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="grid h-[30px] w-[30px] place-items-center rounded-full bg-[#283447] font-mono text-[10px] text-blue-100">
            MH
          </div>
          {!sidebarCollapsed && (
            <>
              <div>
                <b className="block text-[11px]">Operator</b>
                <small className="block font-mono text-[9px] text-gray-500">
                  Founder workspace
                </small>
              </div>
              <span className="ml-auto h-1.5 w-1.5 rounded-full bg-hive" />
            </>
          )}
        </div>
      </div>
    </aside>
  );
}
