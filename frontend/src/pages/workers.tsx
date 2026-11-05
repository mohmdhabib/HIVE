import { useWorkers } from "@/hooks/use-workers";
import { useAppStore } from "@/stores/app-store";
import { useNavigate, Link } from "react-router-dom";
import { Bot, CircleDollarSign, Compass, Layers, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

const workerColors = [
  "text-hive bg-hive/10",
  "text-sky-400 bg-sky-400/10",
  "text-pink-400 bg-pink-400/10",
  "text-purple-400 bg-purple-400/10",
  "text-amber-300 bg-amber-300/10",
];

export default function WorkersPage() {
  const { data: workers = [] } = useWorkers();
  const { setSelectedWorker } = useAppStore();
  const navigate = useNavigate();

  function handleSelect(id: string) {
    setSelectedWorker(id);
    navigate("/");
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
            NETWORK DIRECTORY
          </div>
          <h1 className="mt-1 font-display text-2xl font-semibold">Worker Brands</h1>
          <p className="text-xs text-gray-400">
            5 autonomous niche media operations coordinated under the central Master Agent.
          </p>
        </div>
        <div className="rounded border border-border bg-surface px-3 py-1.5 font-mono text-[10px] text-gray-300">
          5 / 5 OPERATIONAL
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {workers.map((w, i) => (
          <div
            key={w.id}
            className="flex flex-col justify-between rounded-xl border border-border bg-surface p-5 transition-colors hover:border-hive/40"
          >
            <div>
              <div className="flex items-start justify-between">
                <div
                  className={cn(
                    "grid h-10 w-10 place-items-center rounded-lg",
                    workerColors[i % workerColors.length]
                  )}
                >
                  <Bot size={22} />
                </div>
                <span
                  className={cn(
                    "flex items-center gap-1 font-mono text-[9px]",
                    w.enabled ? "text-emerald-400" : "text-amber-400"
                  )}
                >
                  <span
                    className={cn(
                      "inline-block h-1.5 w-1.5 rounded-full",
                      w.enabled ? "bg-emerald-400" : "bg-amber-400"
                    )}
                  />
                  {w.enabled ? "IDLE · READY" : "PAUSED"}
                </span>
              </div>

              <div className="mt-4">
                <Link
                  to={`/workers/${w.id}`}
                  className="font-display text-base font-semibold hover:text-hive transition-colors"
                >
                  {w.name}
                </Link>
                <div className="font-mono text-[10px] text-hive capitalize">{w.niche}</div>
              </div>

              <div className="mt-3 space-y-2 text-[11px] text-gray-300">
                <div>
                  <span className="font-mono text-[9px] text-gray-500 block">AUDIENCE</span>
                  <p className="text-gray-400">{w.audience}</p>
                </div>
                <div>
                  <span className="font-mono text-[9px] text-gray-500 block">EDITORIAL VOICE</span>
                  <p className="text-gray-400">{w.voice}</p>
                </div>
                {w.content_pillars && w.content_pillars.length > 0 && (
                  <div>
                    <span className="font-mono text-[9px] text-gray-500 block mb-1">CONTENT PILLARS</span>
                    <div className="flex flex-wrap gap-1">
                      {w.content_pillars.map((pillar) => (
                        <span
                          key={pillar}
                          className="rounded bg-surface-raised border border-border px-1.5 py-0.5 font-mono text-[8px] text-gray-300"
                        >
                          {pillar}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-5 border-t border-border pt-4 space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="flex items-center gap-1 font-mono text-[10px] text-gray-400">
                  <CircleDollarSign size={13} className="text-emerald-400" />
                  Target: ${w.revenue_target?.monthly_target_usd.toLocaleString()}/mo
                </span>
                <span className="font-mono text-[9px] text-gray-500 uppercase">
                  {w.revenue_target?.primary_stream}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 pt-1">
                <Link
                  to={`/workers/${w.id}`}
                  className="rounded-md bg-surface-raised border border-border py-1.5 text-center font-mono text-[9px] text-gray-300 hover:text-gray-100"
                >
                  MEMORY & LOGS
                </Link>
                <button
                  onClick={() => handleSelect(w.id)}
                  className="rounded-md bg-hive/10 border border-hive/30 py-1.5 text-center font-mono text-[9px] font-semibold text-hive hover:bg-hive/20"
                >
                  DELEGATE →
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
