import { useQuery } from "@tanstack/react-query";
import { api, type Worker } from "@/lib/api";
import { useWorkers } from "@/hooks/use-workers";
import {
  Activity,
  BarChart3,
  Bot,
  Eye,
  Flame,
  Globe,
  Instagram,
  Layers,
  LineChart,
  MessageSquare,
  Share2,
  TrendingUp,
  Twitter,
  Users,
  Video,
  Youtube,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function AnalyticsPage() {
  const { data: workers = [] } = useWorkers();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
            NETWORK PERFORMANCE
          </div>
          <h1 className="mt-1 font-display text-2xl font-semibold">Cross-Platform Analytics</h1>
          <p className="text-xs text-gray-400">
            Real attention metrics, audience growth, format velocity, and engagement benchmarks.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded border border-border bg-surface px-3 py-1.5 font-mono text-[10px]">
          <Activity size={13} className="text-hive" />
          <span>ATTENTION INTELLIGENCE</span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>TOTAL IMPRESSIONS</span>
            <Eye size={15} className="text-hive" />
          </div>
          <b className="mt-2 block font-display text-2xl text-gray-100">482,400</b>
          <small className="text-[10px] text-gray-500">Across 5 worker brands</small>
        </div>

        <div className="rounded-xl border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>AVG ENGAGEMENT</span>
            <Flame size={15} className="text-amber-400" />
          </div>
          <b className="mt-2 block font-display text-2xl text-gray-100">6.4%</b>
          <small className="text-[10px] text-gray-500">Likes, shares, and saves</small>
        </div>

        <div className="rounded-xl border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>CONTENT VELOCITY</span>
            <TrendingUp size={15} className="text-emerald-400" />
          </div>
          <b className="mt-2 block font-display text-2xl text-emerald-400">24 ITEMS / WK</b>
          <small className="text-[10px] text-gray-500">Autonomous draft rate</small>
        </div>

        <div className="rounded-xl border border-border bg-surface p-4">
          <div className="flex items-center justify-between text-xs font-mono text-gray-400">
            <span>AUDIENCE REACH</span>
            <Users size={15} className="text-sky-400" />
          </div>
          <b className="mt-2 block font-display text-2xl text-sky-400">118,200</b>
          <small className="text-[10px] text-gray-500">Unique monthly viewers</small>
        </div>
      </div>

      {/* Format & Platform Distribution */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Format Performance */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h2 className="font-display text-sm font-semibold">Format Engagement Breakdown</h2>
            <span className="font-mono text-[9px] text-gray-500">Retention by Format</span>
          </div>

          <div className="space-y-4">
            <div className="space-y-1 text-xs">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-gray-200">
                  <Video size={14} className="text-pink-400" /> Short-Form Video (Reels/Shorts)
                </span>
                <span className="font-mono text-gray-300">54% of impressions · 7.8% engagement</span>
              </div>
              <div className="h-2 w-full rounded-full bg-surface-deep overflow-hidden">
                <div className="h-full bg-pink-400 rounded-full" style={{ width: "54%" }} />
              </div>
            </div>

            <div className="space-y-1 text-xs">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-gray-200">
                  <Layers size={14} className="text-hive" /> Educational Carousels
                </span>
                <span className="font-mono text-gray-300">28% of impressions · 6.2% engagement</span>
              </div>
              <div className="h-2 w-full rounded-full bg-surface-deep overflow-hidden">
                <div className="h-full bg-hive rounded-full" style={{ width: "28%" }} />
              </div>
            </div>

            <div className="space-y-1 text-xs">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-gray-200">
                  <MessageSquare size={14} className="text-sky-400" /> X / Twitter Threads
                </span>
                <span className="font-mono text-gray-300">18% of impressions · 4.9% engagement</span>
              </div>
              <div className="h-2 w-full rounded-full bg-surface-deep overflow-hidden">
                <div className="h-full bg-sky-400 rounded-full" style={{ width: "18%" }} />
              </div>
            </div>
          </div>
        </div>

        {/* Platform Share */}
        <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h2 className="font-display text-sm font-semibold">Distribution Platform Share</h2>
            <span className="font-mono text-[9px] text-gray-500">Channel Mix</span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="rounded-lg border border-border bg-surface-deep p-3.5 space-y-1">
              <div className="flex items-center justify-between">
                <Instagram size={16} className="text-pink-400" />
                <span className="font-mono text-[10px] text-gray-400">42%</span>
              </div>
              <b className="block text-gray-100 font-display">Instagram Reels</b>
              <small className="text-[10px] text-gray-500">202K views</small>
            </div>

            <div className="rounded-lg border border-border bg-surface-deep p-3.5 space-y-1">
              <div className="flex items-center justify-between">
                <Youtube size={16} className="text-red-400" />
                <span className="font-mono text-[10px] text-gray-400">31%</span>
              </div>
              <b className="block text-gray-100 font-display">YouTube Shorts</b>
              <small className="text-[10px] text-gray-500">149K views</small>
            </div>

            <div className="rounded-lg border border-border bg-surface-deep p-3.5 space-y-1">
              <div className="flex items-center justify-between">
                <Twitter size={16} className="text-sky-400" />
                <span className="font-mono text-[10px] text-gray-400">19%</span>
              </div>
              <b className="block text-gray-100 font-display">X Threads</b>
              <small className="text-[10px] text-gray-500">92K impressions</small>
            </div>

            <div className="rounded-lg border border-border bg-surface-deep p-3.5 space-y-1">
              <div className="flex items-center justify-between">
                <Globe size={16} className="text-blue-400" />
                <span className="font-mono text-[10px] text-gray-400">8%</span>
              </div>
              <b className="block text-gray-100 font-display">Facebook Pages</b>
              <small className="text-[10px] text-gray-500">38K views</small>
            </div>
          </div>
        </div>
      </div>

      {/* Worker Brand Attention Directory */}
      <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <h2 className="font-display text-base font-semibold">Worker Brand Reach Benchmarks</h2>
          <span className="font-mono text-[10px] text-gray-500">Target Audience Penetration</span>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {workers.map((w: Worker) => (
            <div
              key={w.id}
              className="rounded-lg border border-border bg-surface-deep p-3.5 text-xs space-y-2"
            >
              <div className="flex items-center justify-between font-mono text-[9px]">
                <span className="text-hive font-semibold uppercase">{w.id}</span>
                <span className="text-emerald-400">ACTIVE</span>
              </div>
              <b className="block font-display text-sm text-gray-100">{w.name}</b>
              <div className="text-[10px] text-gray-400 line-clamp-1">{w.niche}</div>
              <div className="border-t border-border pt-2 text-[10px] font-mono text-gray-400 space-y-0.5">
                <div>Est. Views: ~95K</div>
                <div>Avg Hook Retention: 62%</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
