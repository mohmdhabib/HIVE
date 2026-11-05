import { useLocation } from "react-router-dom";
import { useHealth } from "@/hooks/use-workers";
import { cn } from "@/lib/utils";

const pageTitles: Record<string, string> = {
  "/": "Overview",
  "/master-agent": "Master Agent",
  "/workers": "Workers",
  "/content-studio": "Content Studio",
  "/approval-queue": "Approval Queue",
  "/publishing": "Publishing Calendar",
  "/analytics": "Analytics",
  "/revenue": "Revenue",
  "/integrations": "Integrations",
  "/system": "System Health",
  "/settings": "Settings",
};

export function Topbar() {
  const location = useLocation();
  const { data: health } = useHealth();
  const title = pageTitles[location.pathname] || "HIVE";
  const isOnline = health?.status === "ok";

  return (
    <header className="flex h-[66px] items-center justify-between border-b border-border px-1">
      <div className="text-[11px]">
        <span className="mr-3 text-gray-500">Workspace</span>
        <span className="mr-3 text-gray-600">/</span>
        <b>{title}</b>
      </div>
      <div className="flex items-center gap-4">
        <span className="font-mono text-[9px] tracking-wide text-gray-400">
          <span
            className={cn(
              "mr-1.5 inline-block h-1.5 w-1.5 rounded-full",
              isOnline ? "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.5)]" : "bg-red-400"
            )}
          />
          {isOnline ? "SYSTEM ONLINE" : "CONNECTING…"}
        </span>
        <span className="font-mono text-[9px] tracking-wide text-gray-600">
          LOCAL DEVELOPMENT
        </span>
        <div className="grid h-[27px] w-[27px] place-items-center rounded-full bg-[#283447] font-mono text-[10px] text-blue-100">
          MH
        </div>
      </div>
    </header>
  );
}
