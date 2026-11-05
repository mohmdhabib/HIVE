import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  CheckCircle2,
  ExternalLink,
  Facebook,
  Globe,
  Instagram,
  Layers,
  Lock,
  Plug,
  ShieldCheck,
  Twitter,
  Youtube,
  AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

const platformCards = [
  {
    id: "instagram",
    name: "Instagram Graph API",
    category: "Short-Form Video (Reels) & Carousels",
    icon: <Instagram size={22} className="text-pink-400" />,
    requiredScopes: ["instagram_basic", "instagram_content_publish", "pages_show_list"],
    status: "manual_fallback",
    desc: "Direct automated publishing for Instagram Reels and visual Carousels via official Meta Graph API v20.0.",
  },
  {
    id: "youtube",
    name: "YouTube Data API v3",
    category: "YouTube Shorts & Video Uploads",
    icon: <Youtube size={22} className="text-red-400" />,
    requiredScopes: ["https://www.googleapis.com/auth/youtube.upload"],
    status: "manual_fallback",
    desc: "Automated video container upload and metadata dispatch for YouTube Shorts.",
  },
  {
    id: "twitter",
    name: "X / Twitter API v2",
    category: "Threads & Social Posts",
    icon: <Twitter size={22} className="text-sky-400" />,
    requiredScopes: ["tweet.write", "tweet.read", "users.read"],
    status: "manual_fallback",
    desc: "Sequential thread publishing with 280-character boundary formatting via X Developer Portal.",
  },
  {
    id: "facebook",
    name: "Meta Graph Pages API",
    category: "Facebook Page Video & Posts",
    icon: <Facebook size={22} className="text-blue-400" />,
    requiredScopes: ["pages_manage_posts", "pages_read_engagement"],
    status: "manual_fallback",
    desc: "Longer format distribution and community posts to brand Pages.",
  },
  {
    id: "manual",
    name: "Sanctioned Manual Fallback",
    category: "Universal Safe Dispatch",
    icon: <Layers size={22} className="text-hive" />,
    requiredScopes: ["All channels supported"],
    status: "connected",
    desc: "100% compliant, copy-paste verified publishing workflow. Guaranteed safe against account bans and API limits.",
  },
];

export default function IntegrationsPage() {
  const { data: accounts = [] } = useQuery({
    queryKey: ["connected-accounts"],
    queryFn: () => api.listAccounts(),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
            OFFICIAL PLATFORM CONNECTORS
          </div>
          <h1 className="mt-1 font-display text-2xl font-semibold">Platform Integrations</h1>
          <p className="text-xs text-gray-400">
            Authorized OAuth2 APIs, permission scopes, and verified publishing adapters.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded border border-border bg-surface px-3 py-1.5 font-mono text-[10px]">
          <Plug size={13} className="text-hive" />
          <span>{accounts.length} ACTIVE ADAPTERS</span>
        </div>
      </div>

      {/* Compliance Callout */}
      <div className="rounded-xl border border-border bg-surface-deep p-4 flex items-start gap-3">
        <ShieldCheck size={20} className="text-hive flex-shrink-0 mt-0.5" />
        <div className="text-xs text-gray-300">
          <b className="text-gray-100 font-display">Zero Unauthorized Scraping Policy:</b> HIVE only communicates through official, authorized platform developer APIs. No unofficial bots, headless browser impersonation, or fake engagement tools are used. When credentials are not provisioned, HIVE automatically routes dispatches through the verified manual workflow.
        </div>
      </div>

      {/* Platform Cards Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {platformCards.map((card) => {
          const isConnected = card.status === "connected";
          return (
            <div
              key={card.id}
              className="rounded-xl border border-border bg-surface p-5 flex flex-col justify-between transition-colors hover:border-hive/30"
            >
              <div>
                <div className="flex items-start justify-between">
                  <div className="grid h-10 w-10 place-items-center rounded-lg bg-surface-deep border border-border">
                    {card.icon}
                  </div>
                  <span
                    className={cn(
                      "rounded px-2 py-0.5 font-mono text-[8px] uppercase font-semibold",
                      isConnected
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                    )}
                  >
                    {isConnected ? "ACTIVE · LIVE" : "MANUAL ROUTING"}
                  </span>
                </div>

                <div className="mt-4">
                  <h3 className="font-display text-base font-semibold text-gray-100">{card.name}</h3>
                  <div className="font-mono text-[10px] text-gray-400 mt-0.5">{card.category}</div>
                  <p className="mt-2 text-xs text-gray-400 leading-relaxed">{card.desc}</p>
                </div>

                <div className="mt-4 border-t border-border pt-3">
                  <span className="font-mono text-[9px] text-gray-500 block mb-1">REQUIRED SCOPES</span>
                  <div className="flex flex-wrap gap-1">
                    {card.requiredScopes.map((scope) => (
                      <span
                        key={scope}
                        className="rounded bg-surface-deep border border-border px-1.5 py-0.5 font-mono text-[8px] text-gray-300"
                      >
                        {scope}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-5 border-t border-border pt-4">
                <button
                  disabled={isConnected}
                  className={cn(
                    "w-full rounded-md py-2 font-mono text-[10px] font-semibold transition-colors",
                    isConnected
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 cursor-default"
                      : "bg-surface-deep border border-border text-gray-300 hover:border-hive/50 hover:text-hive"
                  )}
                >
                  {isConnected ? "VERIFIED & CONNECTED" : "CONFIGURE OAUTH CREDENTIALS →"}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Connected Accounts Directory */}
      <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <h2 className="font-display text-base font-semibold">Worker Account Mapping</h2>
          <span className="font-mono text-[10px] text-gray-500">{accounts.length} Connected Identifiers</span>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {accounts.map((acc) => (
            <div
              key={acc.id}
              className="rounded-lg border border-border bg-surface-deep p-3.5 text-xs space-y-1.5"
            >
              <div className="flex items-center justify-between font-mono text-[9px]">
                <span className="text-hive uppercase font-semibold">{acc.worker_id}</span>
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 size={10} /> {acc.status.replace("_", " ")}
                </span>
              </div>
              <b className="block text-gray-200">{acc.display_name}</b>
              <div className="font-mono text-[10px] text-gray-400">{acc.account_handle}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
