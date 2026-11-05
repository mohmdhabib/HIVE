import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type TopicOpportunity, type MultiFormatDeliverable } from "@/lib/api";
import { useWorkers } from "@/hooks/use-workers";
import { useAppStore } from "@/stores/app-store";
import {
  Bot,
  Brain,
  CheckCircle2,
  CircleDollarSign,
  Compass,
  Copy,
  Eye,
  FileText,
  Flame,
  Image as ImageIcon,
  Layers,
  MessageSquare,
  Play,
  Radio,
  Search,
  Send,
  Share2,
  Sparkles,
  Video,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function ContentStudioPage() {
  const queryClient = useQueryClient();
  const { data: workers = [] } = useWorkers();
  const { selectedWorkerId, setSelectedWorker } = useAppStore();

  const [keyword, setKeyword] = useState("");
  const [selectedTopic, setSelectedTopic] = useState<TopicOpportunity | null>(null);
  const [deliverable, setDeliverable] = useState<MultiFormatDeliverable | null>(null);
  const [activeTab, setActiveTab] = useState<"video" | "thread" | "carousel" | "creative">("video");
  const [dispatched, setDispatched] = useState(false);

  const activeWorker = workers.find((w) => w.id === selectedWorkerId) || workers[0];

  // Topic Research Mutation
  const researchMutation = useMutation({
    mutationFn: () =>
      api.researchTopics({
        worker_id: selectedWorkerId || "tech",
        keyword: keyword.trim() || undefined,
      }),
  });

  // Multi-Format Generation Mutation
  const generateMutation = useMutation({
    mutationFn: (topic: TopicOpportunity) =>
      api.generateMultiFormat({
        worker_id: selectedWorkerId || "tech",
        topic,
      }),
    onSuccess: (data) => {
      setDeliverable(data);
      setDispatched(false);
    },
  });

  // Dispatch to Master Agent Approval Queue Mutation
  const dispatchMutation = useMutation({
    mutationFn: () => {
      if (!deliverable || !selectedWorkerId) return Promise.reject("No deliverable");
      return api.createTask({
        worker_id: selectedWorkerId,
        objective: `Produce multi-format campaign for: "${deliverable.topic.title}". Angle: ${deliverable.topic.hook_angle}`,
        require_approval: true,
        target_platform: "instagram",
      });
    },
    onSuccess: () => {
      setDispatched(true);
      queryClient.invalidateQueries({ queryKey: ["pending-tasks"] });
    },
  });

  const topics = researchMutation.data || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-[9px] tracking-[1.8px] text-gray-400">
            CONTENT PRODUCTION ENGINE
          </div>
          <h1 className="mt-1 font-display text-2xl font-semibold">Content Studio</h1>
          <p className="text-xs text-gray-400">
            Autonomous trend research, multi-format scripting (Video, Threads, Carousels), and generative asset briefs.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded border border-border bg-surface px-3 py-1.5 font-mono text-[10px]">
          <Sparkles size={13} className="text-hive" />
          <span>MULTI-CHANNEL WORKFLOW</span>
        </div>
      </div>

      {/* Worker Selector Bar */}
      <div className="rounded-xl border border-border bg-surface p-4">
        <label className="block font-mono text-[9px] tracking-[1.1px] text-gray-400 mb-2">
          OPERATIONAL WORKER BRAND
        </label>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          {workers.map((w) => (
            <button
              key={w.id}
              onClick={() => {
                setSelectedWorker(w.id);
                setSelectedTopic(null);
                setDeliverable(null);
              }}
              className={cn(
                "flex items-center gap-2 rounded-lg border p-2.5 text-left text-xs transition-colors",
                selectedWorkerId === w.id
                  ? "border-hive/50 bg-hive/10 text-gray-100 font-medium"
                  : "border-border bg-surface-deep text-gray-400 hover:text-gray-200"
              )}
            >
              <Bot size={15} className={selectedWorkerId === w.id ? "text-hive" : "text-gray-500"} />
              <div className="truncate">
                <div className="truncate font-medium">{w.name}</div>
                <div className="text-[9px] text-gray-500 capitalize truncate">{w.niche}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Stage 1: Topic Discovery & Research */}
      <div className="rounded-xl border border-border bg-surface p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div className="flex items-center gap-2">
            <Search size={16} className="text-hive" />
            <h2 className="font-display text-base font-semibold">
              1. Automated Topic Discovery & Trend Research
            </h2>
          </div>
          <span className="font-mono text-[9px] text-gray-400">
            Targeting: {activeWorker?.audience || "Curious audience"}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Filter by keyword (e.g. AI benchmarks, unit economics, daily habits) or leave empty for timely trends..."
              className="w-full rounded-lg border border-border bg-surface-deep px-3.5 py-2.5 text-xs text-gray-200 outline-none focus:border-hive/50"
            />
          </div>
          <button
            onClick={() => researchMutation.mutate()}
            disabled={researchMutation.isPending}
            className="flex items-center gap-1.5 rounded-lg bg-hive px-4 py-2.5 font-mono text-xs font-semibold text-[#090b10] hover:bg-hive-400 transition-colors disabled:opacity-50"
          >
            <Compass size={14} />
            {researchMutation.isPending ? "SCANNING SIGNALS…" : "DISCOVER TOPICS"}
          </button>
        </div>

        {/* Discovered Opportunities Grid */}
        {topics.length > 0 && (
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {topics.map((t, idx) => {
              const isSelected = selectedTopic?.title === t.title;
              return (
                <div
                  key={idx}
                  onClick={() => setSelectedTopic(t)}
                  className={cn(
                    "cursor-pointer rounded-lg border p-4 flex flex-col justify-between transition-colors",
                    isSelected
                      ? "border-hive bg-hive/5 shadow-[0_0_15px_rgba(245,166,35,0.08)]"
                      : "border-border bg-surface-deep hover:border-border-strong"
                  )}
                >
                  <div>
                    <div className="flex items-center justify-between text-[9px] font-mono mb-2">
                      <span className="rounded bg-surface px-1.5 py-0.5 uppercase border border-border text-gray-400">
                        {t.estimated_reach_potential} Reach
                      </span>
                      {isSelected && <span className="text-hive font-bold">SELECTED</span>}
                    </div>
                    <h3 className="font-display text-sm font-semibold text-gray-100">{t.title}</h3>
                    <p className="mt-2 text-xs text-gray-400 italic">"{t.hook_angle}"</p>
                    <div className="mt-3 text-[11px] text-gray-400 space-y-1">
                      <div>
                        <span className="font-mono text-[9px] text-gray-500 block">TIMELINESS</span>
                        {t.timeliness_factor}
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 border-t border-border pt-3">
                    <span className="flex items-center gap-1 font-mono text-[9px] text-emerald-400">
                      <CircleDollarSign size={12} />
                      {t.monetization_angle}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Stage 2 & 3: Multi-Format Package Preview */}
      {selectedTopic && (
        <div className="rounded-xl border border-border bg-surface p-5 space-y-5">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
            <div>
              <div className="font-mono text-[9px] tracking-wide text-gray-400">
                2. MULTI-FORMAT GENERATION FOR:
              </div>
              <h2 className="font-display text-lg font-semibold text-gray-100 mt-0.5">
                {selectedTopic.title}
              </h2>
            </div>
            <button
              onClick={() => generateMutation.mutate(selectedTopic)}
              disabled={generateMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg bg-hive px-4 py-2 font-mono text-xs font-semibold text-[#090b10] hover:bg-hive-400 transition-colors disabled:opacity-50"
            >
              <Layers size={14} />
              {generateMutation.isPending ? "GENERATING PACKAGE…" : "GENERATE ALL FORMATS"}
            </button>
          </div>

          {deliverable && (
            <div className="space-y-4">
              {/* Format Navigation Tabs */}
              <div className="flex border-b border-border font-mono text-xs">
                <button
                  onClick={() => setActiveTab("video")}
                  className={cn(
                    "flex items-center gap-2 border-b-2 px-4 py-2.5 transition-colors",
                    activeTab === "video"
                      ? "border-hive text-hive font-semibold"
                      : "border-transparent text-gray-400 hover:text-gray-200"
                  )}
                >
                  <Video size={14} /> Short Video (9:16)
                </button>
                <button
                  onClick={() => setActiveTab("thread")}
                  className={cn(
                    "flex items-center gap-2 border-b-2 px-4 py-2.5 transition-colors",
                    activeTab === "thread"
                      ? "border-hive text-hive font-semibold"
                      : "border-transparent text-gray-400 hover:text-gray-200"
                  )}
                >
                  <MessageSquare size={14} /> X / Twitter Thread ({deliverable.thread_posts.length})
                </button>
                <button
                  onClick={() => setActiveTab("carousel")}
                  className={cn(
                    "flex items-center gap-2 border-b-2 px-4 py-2.5 transition-colors",
                    activeTab === "carousel"
                      ? "border-hive text-hive font-semibold"
                      : "border-transparent text-gray-400 hover:text-gray-200"
                  )}
                >
                  <Layers size={14} /> Carousel Slides ({deliverable.carousel_slides.length})
                </button>
                <button
                  onClick={() => setActiveTab("creative")}
                  className={cn(
                    "flex items-center gap-2 border-b-2 px-4 py-2.5 transition-colors",
                    activeTab === "creative"
                      ? "border-hive text-hive font-semibold"
                      : "border-transparent text-gray-400 hover:text-gray-200"
                  )}
                >
                  <ImageIcon size={14} /> Generative AI Prompts ({deliverable.creative_assets.length})
                </button>
              </div>

              {/* Tab 1: Short Video */}
              {activeTab === "video" && deliverable.short_video && (
                <div className="space-y-3 text-xs">
                  <div className="rounded-lg border border-hive/30 bg-hive/5 p-4">
                    <div className="font-mono text-[9px] font-semibold text-hive mb-1">
                      3-SECOND RETENTION HOOK
                    </div>
                    <p className="font-display text-sm font-semibold text-gray-100">
                      "{deliverable.short_video.hook}"
                    </p>
                  </div>

                  <div className="rounded-lg border border-border bg-surface-deep p-4 space-y-1.5">
                    <div className="font-mono text-[9px] text-gray-400">NARRATION & ACTING SCRIPT</div>
                    <pre className="whitespace-pre-wrap font-sans text-gray-300 leading-relaxed text-xs">
                      {deliverable.short_video.body_script}
                    </pre>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-lg border border-border bg-surface-deep p-3.5">
                      <div className="font-mono text-[9px] text-gray-400 mb-1">SOCIAL CAPTION</div>
                      <p className="text-gray-300">{deliverable.short_video.caption}</p>
                    </div>
                    <div className="rounded-lg border border-border bg-surface-deep p-3.5">
                      <div className="font-mono text-[9px] text-gray-400 mb-1">VISUAL BRIEF</div>
                      <p className="text-gray-300">{deliverable.short_video.visual_brief}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: X Thread */}
              {activeTab === "thread" && (
                <div className="space-y-2.5">
                  {deliverable.thread_posts.map((post) => (
                    <div
                      key={post.post_number}
                      className="rounded-lg border border-border bg-surface-deep p-3.5 text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between font-mono text-[9px] text-gray-500">
                        <span>POST #{post.post_number}</span>
                        <span>{post.text.length} / 280 CHARACTERS</span>
                      </div>
                      <p className="text-gray-200 leading-relaxed">{post.text}</p>
                      {post.suggested_media && (
                        <div className="font-mono text-[9px] text-hive pt-1">
                          Media Suggestion: {post.suggested_media}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Tab 3: Carousel */}
              {activeTab === "carousel" && (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  {deliverable.carousel_slides.map((slide) => (
                    <div
                      key={slide.slide_number}
                      className="rounded-xl border border-border bg-surface-deep p-4 flex flex-col justify-between"
                    >
                      <div>
                        <div className="font-mono text-[9px] text-hive font-semibold mb-2">
                          SLIDE {slide.slide_number}
                        </div>
                        <h4 className="font-display text-sm font-semibold text-gray-100">
                          {slide.headline}
                        </h4>
                        <p className="mt-2 text-xs text-gray-300 leading-relaxed">
                          {slide.body_text}
                        </p>
                      </div>
                      <div className="mt-4 border-t border-border pt-2 text-[9px] font-mono text-gray-500">
                        {slide.visual_direction}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Tab 4: Creative Assets */}
              {activeTab === "creative" && (
                <div className="grid gap-3 sm:grid-cols-2">
                  {deliverable.creative_assets.map((asset, idx) => (
                    <div
                      key={idx}
                      className="rounded-xl border border-border bg-surface-deep p-4 space-y-2.5"
                    >
                      <div className="flex items-center justify-between font-mono text-[9px]">
                        <span className="text-hive uppercase font-semibold">
                          {asset.asset_type.replace("_", " ")}
                        </span>
                        <span className="rounded bg-surface px-1.5 py-0.5 border border-border text-gray-400">
                          Ratio: {asset.aspect_ratio}
                        </span>
                      </div>
                      <div>
                        <span className="font-mono text-[9px] text-gray-500 block mb-1">
                          GENERATION PROMPT (MIDJOURNEY / FLUX / SDXL)
                        </span>
                        <p className="text-xs text-gray-200 bg-surface p-2.5 rounded border border-border font-mono">
                          {asset.prompt}
                        </p>
                      </div>
                      {asset.overlay_text && (
                        <div className="text-[10px] text-gray-400">
                          <span className="font-mono text-[9px] text-gray-500 block">OVERLAY COPY</span>
                          "{asset.overlay_text}"
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Dispatch to Approval Queue Action */}
              <div className="mt-6 flex items-center justify-between border-t border-border pt-4">
                <span className="text-xs text-gray-400">
                  Ready to queue this deliverable for human sign-off?
                </span>
                {dispatched ? (
                  <div className="flex items-center gap-1.5 font-mono text-xs text-emerald-400">
                    <CheckCircle2 size={16} /> DISPATCHED TO APPROVAL QUEUE
                  </div>
                ) : (
                  <button
                    onClick={() => dispatchMutation.mutate()}
                    disabled={dispatchMutation.isPending}
                    className="flex items-center gap-1.5 rounded-lg bg-emerald-500 px-4 py-2 font-mono text-xs font-semibold text-[#090b10] hover:bg-emerald-400 transition-colors disabled:opacity-50"
                  >
                    <Send size={13} />
                    {dispatchMutation.isPending ? "QUEUEING…" : "QUEUE FOR APPROVAL"}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
