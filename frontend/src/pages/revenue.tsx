import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  ArrowUpRight,
  Bot,
  CheckCircle2,
  CircleDollarSign,
  DollarSign,
  Download,
  Flame,
  Percent,
  PieChart,
  ShieldCheck,
  TrendingUp,
  Wallet,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function RevenuePage() {
  const { data: summary, isLoading } = useQuery({
    queryKey: ["financial-summary"],
    queryFn: api.financialSummary,
    refetchInterval: 15_000,
  });

  if (!summary) {
    return (
      <div className="flex h-64 items-center justify-center font-mono text-xs text-gray-400">
        LOADING FINANCIAL ATTRIBUTION LEDGER…
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
            FINANCIAL INTELLIGENCE
          </div>
          <h1 className="mt-1 font-display text-2xl font-semibold">Revenue & Profitability Engine</h1>
          <p className="text-xs text-gray-400">
            First-class attribution across affiliate conversions, brand sponsorships, lead gen, and digital sales.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded border border-border bg-surface px-3 py-1.5 font-mono text-[10px]">
          <ShieldCheck size={13} className="text-emerald-400" />
          <span>VERIFIED LEDGER ATTRIBUTION</span>
        </div>
      </div>

      {/* Primary KPI Metrics Row */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>NET PROFIT</span>
            <CircleDollarSign size={15} className="text-emerald-400" />
          </div>
          <b className="mt-2 block font-display text-2xl text-emerald-400">
            ${summary.net_profit.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </b>
          <small className="text-[10px] text-gray-500">Gross minus production costs</small>
        </div>

        <div className="rounded-xl border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>GROSS REVENUE</span>
            <TrendingUp size={15} className="text-hive" />
          </div>
          <b className="mt-2 block font-display text-2xl text-gray-100">
            ${summary.total_gross_revenue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </b>
          <small className="text-[10px] text-gray-500">Total attributed volume</small>
        </div>

        <div className="rounded-xl border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>PROFIT MARGIN</span>
            <Percent size={15} className="text-hive" />
          </div>
          <b className="mt-2 block font-display text-2xl text-gray-100">
            {summary.profit_margin_pct}%
          </b>
          <small className="text-[10px] text-gray-500">Lean AI agent economics</small>
        </div>

        <div className="rounded-xl border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>TOTAL COSTS</span>
            <Wallet size={15} className="text-gray-400" />
          </div>
          <b className="mt-2 block font-display text-2xl text-gray-400">
            ${summary.total_costs.toFixed(2)}
          </b>
          <small className="text-[10px] text-gray-500">Local compute + infra allocation</small>
        </div>
      </div>

      {/* Stream Distribution & Attribution Rigor */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Stream Breakdown */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h2 className="font-display text-sm font-semibold">Attributed Streams</h2>
            <span className="font-mono text-[9px] text-gray-500">By Channel Type</span>
          </div>

          <div className="space-y-3">
            {Object.entries(summary.stream_breakdown).map(([stream, amount]) => {
              const pct = Math.round((amount / summary.total_gross_revenue) * 100);
              return (
                <div key={stream} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="capitalize font-mono text-gray-300">{stream.replace("_", " ")}</span>
                    <span className="font-mono font-medium text-gray-100">${amount.toFixed(2)} ({pct}%)</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-surface-deep overflow-hidden">
                    <div className="h-full bg-hive rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Attribution Rigor Breakdown */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h2 className="font-display text-sm font-semibold">Attribution Classification</h2>
            <span className="font-mono text-[9px] text-gray-500">Measured vs Estimated</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3 flex items-center justify-between">
              <div>
                <b className="block text-emerald-400 font-mono text-xs">MEASURED ATTRIBUTION</b>
                <p className="text-[11px] text-gray-400">Directly verified webhooks, affiliate IDs, or sponsor wire contracts.</p>
              </div>
              <span className="font-display text-base font-semibold text-emerald-400">
                ${(summary.attribution_breakdown["measured"] || 0).toFixed(2)}
              </span>
            </div>

            <div className="rounded-lg border border-sky-500/30 bg-sky-500/5 p-3 flex items-center justify-between">
              <div>
                <b className="block text-sky-400 font-mono text-xs">IMPORTED ATTRIBUTION</b>
                <p className="text-[11px] text-gray-400">Imported from affiliate dashboards or platform creator fund payouts.</p>
              </div>
              <span className="font-display text-base font-semibold text-sky-400">
                ${(summary.attribution_breakdown["imported"] || 0).toFixed(2)}
              </span>
            </div>

            <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 flex items-center justify-between">
              <div>
                <b className="block text-amber-400 font-mono text-xs">ESTIMATED ATTRIBUTION</b>
                <p className="text-[11px] text-gray-400">Estimated based on verified impressions and benchmark conversion RPMs.</p>
              </div>
              <span className="font-display text-base font-semibold text-amber-400">
                ${(summary.attribution_breakdown["estimated"] || 0).toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Worker Brand Profitability Leaderboard */}
      <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <h2 className="font-display text-base font-semibold">Worker Brand Profitability Leaderboard</h2>
          <span className="font-mono text-[10px] text-gray-500">Ranked by Net Profit</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border text-[9px] font-mono text-gray-500 uppercase">
                <th className="py-2.5">Worker Brand</th>
                <th className="py-2.5">Primary Stream</th>
                <th className="py-2.5">Gross Revenue</th>
                <th className="py-2.5">Total Costs</th>
                <th className="py-2.5">Net Profit</th>
                <th className="py-2.5">Profit Margin</th>
                <th className="py-2.5">Target Progress</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {summary.worker_rankings.map((w, idx) => (
                <tr key={w.worker_id} className="hover:bg-surface-deep/50 transition-colors">
                  <td className="py-3 font-medium text-gray-100 flex items-center gap-2">
                    <span className="font-mono text-[10px] text-hive font-bold">#{idx + 1}</span>
                    {w.worker_name}
                  </td>
                  <td className="py-3 font-mono text-[10px] text-gray-400 capitalize">
                    {w.primary_stream.replace("_", " ")}
                  </td>
                  <td className="py-3 font-mono text-gray-200">${w.gross_revenue.toFixed(2)}</td>
                  <td className="py-3 font-mono text-gray-400">${w.total_costs.toFixed(2)}</td>
                  <td className="py-3 font-mono font-semibold text-emerald-400">${w.net_profit.toFixed(2)}</td>
                  <td className="py-3 font-mono text-gray-300">{w.profit_margin_pct}%</td>
                  <td className="py-3">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-20 rounded-full bg-surface-deep overflow-hidden">
                        <div
                          className="h-full bg-hive rounded-full"
                          style={{ width: `${Math.min(100, w.target_progress_pct)}%` }}
                        />
                      </div>
                      <span className="font-mono text-[9px] text-gray-400">
                        {w.target_progress_pct}% of ${w.monthly_target_usd}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Attribution Ledger */}
      <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <h2 className="font-display text-base font-semibold">Attribution Ledger</h2>
          <span className="font-mono text-[10px] text-gray-500">Recent Conversion & Payment Events</span>
        </div>

        <div className="space-y-2 max-h-[360px] overflow-auto pr-1">
          {summary.recent_events.map((event) => (
            <div
              key={event.id}
              className="rounded-lg border border-border bg-surface-deep p-3 flex items-center justify-between text-xs"
            >
              <div className="space-y-0.5">
                <div className="flex items-center gap-2 font-mono text-[9px]">
                  <span className="text-hive font-semibold uppercase">{event.worker_id}</span>
                  <span className="text-gray-600">·</span>
                  <span className="text-gray-400 uppercase">{event.platform}</span>
                  <span className="text-gray-600">·</span>
                  <span
                    className={cn(
                      "rounded px-1.5 py-0.5 uppercase",
                      event.attribution_type === "measured"
                        ? "bg-emerald-500/10 text-emerald-400"
                        : event.attribution_type === "imported"
                        ? "bg-sky-500/10 text-sky-400"
                        : "bg-amber-500/10 text-amber-400"
                    )}
                  >
                    {event.attribution_type}
                  </span>
                </div>
                <div className="text-gray-300">
                  {event.conversion_metadata.sponsor ||
                    event.conversion_metadata.source ||
                    event.conversion_metadata.product ||
                    event.conversion_metadata.network ||
                    event.stream.replace("_", " ").toUpperCase()}
                </div>
              </div>

              <div className="text-right">
                <b className="font-display text-base font-semibold text-emerald-400">
                  +${event.gross_amount.toFixed(2)}
                </b>
                <span className="block font-mono text-[9px] text-gray-500">
                  {new Date(event.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
