from pydantic import BaseModel, Field
from app.schemas.content import (
    TopicOpportunity,
    SlideItem,
    ThreadPost,
    CreativeAssetBrief,
    MultiFormatDeliverable,
    ContentPiece,
)
from app.workers.registry import get_worker
from app.services.memory import memory_service
from app.services.llm import LLMService
from app.core.logging import get_logger

logger = get_logger("content_pipeline")

class TopicListSchema(BaseModel):
    topics: list[TopicOpportunity] = Field(min_length=1)

class MultiFormatResponseSchema(BaseModel):
    short_video_hook: str
    short_video_script: str
    short_video_caption: str
    thread_posts: list[str]
    carousel_slides: list[SlideItem]
    thumbnail_prompt: str
    broll_prompt: str

class ContentPipelineService:
    """Multi-format content generation, research, and creative asset brief service."""

    async def research_topics(
        self,
        worker_id: str,
        llm: LLMService,
        keyword: str | None = None,
    ) -> list[TopicOpportunity]:
        """Perform automated topic discovery based on worker pillars and audience signals."""
        worker = get_worker(worker_id)
        mem_ctx = memory_service.get_worker_context(worker.id)
        recent_topics_str = ", ".join(mem_ctx.recent_topics) if mem_ctx.recent_topics else "None"

        prompt = f"""You are the research director for media brand '{worker.name}'.
Niche: {worker.niche}
Audience: {worker.audience}
Content Pillars: {', '.join(worker.content_pillars)}
Monetization Stream: {worker.revenue_target.primary_stream}
Keyword Focus: {keyword or 'Timely high-engagement ideas'}
Recent Covered Topics (Avoid duplicating): {recent_topics_str}

Identify 3 high-leverage content topic opportunities.
For each opportunity, detail:
- title: Strong headline
- hook_angle: Unconventional premise or curiosity gap
- timeliness_factor: Why this needs to be published now
- target_audience_segment: Exact demographic/sub-community
- estimated_reach_potential: 'standard', 'high', or 'viral'
- monetization_angle: How this converts to affiliate sales, leads, or sponsorships."""

        try:
            result = await llm.generate_structured(
                prompt=prompt,
                schema=TopicListSchema,
                temperature=0.4,
                system=f"You are the research strategist for {worker.name}. Maximize attention and monetization potential."
            )
            return result.topics
        except Exception as exc:
            logger.warning("Research topics structured generation fallback: %s", exc)
            return self._fallback_topics(worker)

    async def generate_multi_format_package(
        self,
        worker_id: str,
        topic: TopicOpportunity,
        llm: LLMService,
    ) -> MultiFormatDeliverable:
        """Generate a complete multi-channel content deliverable: Short-Form Video, X Thread, Carousel, and Creative Brief."""
        worker = get_worker(worker_id)

        prompt = f"""Brand: {worker.name} ({worker.niche})
Audience: {worker.audience}
Voice: {worker.voice}
Topic Title: {topic.title}
Hook Angle: {topic.hook_angle}
Monetization Focus: {topic.monetization_angle}

Produce a complete multi-format package:
1. Short Video: 3-second hook, body script, and engaging caption.
2. Twitter/X Thread: 4-5 consecutive tweet texts.
3. Carousel: 4-5 educational slides (each with slide_number, headline, body_text, visual_direction).
4. Generative AI Prompts: One thumbnail visual prompt (1:1) and one video B-roll prompt (9:16)."""

        try:
            res = await llm.generate_structured(
                prompt=prompt,
                schema=MultiFormatResponseSchema,
                temperature=0.3,
                system=f"Generate multi-format content in the voice of {worker.name}."
            )

            # Build Short Video ContentPiece
            short_video = ContentPiece(
                title=topic.title,
                hook=res.short_video_hook,
                body_script=res.short_video_script,
                caption=res.short_video_caption,
                hashtags=[worker.id, "media", "trending"],
                visual_brief="Fast-paced talking head with dynamic B-roll cutaways.",
                target_platform="instagram",
                monetization_hypothesis=topic.monetization_angle,
                factual_checks=[],
                estimated_risk_level="low",
                risks_and_caveats=["Ensure audio level is normalized."]
            )

            # Build Thread Posts
            thread_posts = [
                ThreadPost(post_number=i + 1, text=p[:280], suggested_media="Infographic or clip")
                for i, p in enumerate(res.thread_posts)
            ]

            # Build Creative Assets
            creative_assets = [
                CreativeAssetBrief(
                    asset_type="thumbnail",
                    prompt=res.thumbnail_prompt,
                    aspect_ratio="1:1",
                    overlay_text=topic.title[:40],
                    color_palette=["#090b10", "#f5a623", "#ffffff"]
                ),
                CreativeAssetBrief(
                    asset_type="broll_video",
                    prompt=res.broll_prompt,
                    aspect_ratio="9:16",
                    overlay_text="",
                    color_palette=["#10151d", "#222d39"]
                ),
            ]

            return MultiFormatDeliverable(
                topic=topic,
                worker_id=worker.id,
                worker_name=worker.name,
                short_video=short_video,
                thread_posts=thread_posts,
                carousel_slides=res.carousel_slides,
                creative_assets=creative_assets,
            )

        except Exception as exc:
            logger.warning("Multi-format package fallback triggered: %s", exc)
            return self._fallback_package(worker, topic)

    def _fallback_topics(self, worker) -> list[TopicOpportunity]:
        return [
            TopicOpportunity(
                title=f"The Truth About {worker.content_pillars[0] if worker.content_pillars else worker.niche}",
                hook_angle="Most people are looking at this completely backwards.",
                timeliness_factor="Recent developments have disrupted conventional thinking.",
                target_audience_segment=worker.audience,
                estimated_reach_potential="viral",
                monetization_angle=f"Primary {worker.revenue_target.primary_stream} link in bio."
            ),
            TopicOpportunity(
                title=f"3 Costly Mistakes in {worker.niche}",
                hook_angle="If you are doing this in 2026, you are wasting time and money.",
                timeliness_factor="New tools make older workflows obsolete.",
                target_audience_segment="Pragmatic practitioners",
                estimated_reach_potential="high",
                monetization_angle="Affiliate tool recommendation in caption."
            ),
            TopicOpportunity(
                title=f"The 10-Minute Playbook: Mastering {worker.content_pillars[-1] if worker.content_pillars else 'Strategy'}",
                hook_angle="Steal this framework before everyone else catches on.",
                timeliness_factor="High demand for condensed actionable insights.",
                target_audience_segment="Aspiring builders and operators",
                estimated_reach_potential="high",
                monetization_angle="Free lead-magnet newsletter signup."
            ),
        ]

    def _fallback_package(self, worker, topic: TopicOpportunity) -> MultiFormatDeliverable:
        short_video = ContentPiece(
            title=topic.title,
            hook=topic.hook_angle,
            body_script=f"Here is why {topic.title} matters right now...\n1. Core insight breakdown.\n2. Key tactical shift.\n3. Actionable next step.",
            caption=f"Breaking down {topic.title}. What is your take? #content #hive",
            hashtags=[worker.id, "insights", "strategy"],
            visual_brief="Direct-to-camera with split screen graphics.",
            target_platform="instagram",
            monetization_hypothesis=topic.monetization_angle,
            factual_checks=[],
            estimated_risk_level="low",
            risks_and_caveats=["Editorial review recommended."]
        )

        thread_posts = [
            ThreadPost(post_number=1, text=f"1/ {topic.title}: {topic.hook_angle} (A quick breakdown) 🧵", suggested_media="Header graphic"),
            ThreadPost(post_number=2, text="2/ First, here is the fundamental problem most people overlook...", suggested_media="Chart"),
            ThreadPost(post_number=3, text="3/ The solution comes down to three non-negotiables...", suggested_media="Diagram"),
            ThreadPost(post_number=4, text=f"4/ Summary: If you enjoyed this, check the link in bio for more {worker.niche} breakdowns.", suggested_media="Brand card"),
        ]

        carousel_slides = [
            SlideItem(slide_number=1, headline=topic.title, body_text=topic.hook_angle, visual_direction="Bold dark theme with gold accent typography"),
            SlideItem(slide_number=2, headline="The Core Problem", body_text="Why conventional approaches are failing right now.", visual_direction="Side-by-side comparison diagram"),
            SlideItem(slide_number=3, headline="The Framework", body_text="Step-by-step strategy to capitalize on this trend.", visual_direction="3-step flowchart"),
            SlideItem(slide_number=4, headline="Key Takeaway", body_text="Save this post and follow for daily actionable teardowns.", visual_direction="Call to action card"),
        ]

        creative_assets = [
            CreativeAssetBrief(
                asset_type="thumbnail",
                prompt=f"Cinematic dark aesthetic visual representing {topic.title}, amber accent lighting, minimalist studio, high resolution 8k",
                aspect_ratio="1:1",
                overlay_text=topic.title[:35],
                color_palette=["#090b10", "#f5a623", "#ffffff"]
            ),
            CreativeAssetBrief(
                asset_type="broll_video",
                prompt=f"Moody atmospheric footage of clean modern workspace, slow camera pan, ambient studio lighting, vertical 9:16 format",
                aspect_ratio="9:16",
                overlay_text="",
                color_palette=["#10151d", "#222d39"]
            ),
        ]

        return MultiFormatDeliverable(
            topic=topic,
            worker_id=worker.id,
            worker_name=worker.name,
            short_video=short_video,
            thread_posts=thread_posts,
            carousel_slides=carousel_slides,
            creative_assets=creative_assets,
        )

content_pipeline = ContentPipelineService()

