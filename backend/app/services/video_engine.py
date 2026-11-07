"""
HIVE Video Intelligence Engine — Core Production Service

This is NOT a MoneyPrinterTurbo clone. This engine thinks like a creative director:

1. STORY ARC ENGINE: Structures content as emotional beat sequences 
   (hook → tension → revelation → escalation → payoff → CTA) with 
   retention-zone-aware pacing.

2. SCENE GRAPH COMPOSER: Each scene is a node with visual directives, 
   audio directives, camera motion, transitions, and caption style.

3. BRAND IDENTITY SYSTEM: Every worker brand has its own color palette, 
   typography, voice character, watermark, and intro/outro templates.

4. A/B HOOK FACTORY: Generates 3 different hook variants per video with 
   different psychological archetypes (contrarian, curiosity gap, stat shock).

5. VIRALITY SCORER: Predicts retention and shareability before rendering.

6. MULTI-FORMAT EXPORT: Same content adapted for 9:16, 1:1, and 16:9.

The rendering pipeline (FFmpeg/moviepy) is a separate concern — this engine 
produces the BLUEPRINT that the renderer consumes.
"""

import re
import json
import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Any

from app.schemas.video import (
    VideoProductionBlueprint,
    SceneNode,
    VisualDirective,
    AudioDirective,
    EmotionalBeat,
    RetentionZone,
    BrandIdentity,
    BrandColorPalette,
    BrandTypography,
    CaptionConfig,
    HookVariant,
    ThumbnailSpec,
    MultiFormatExport,
    ExportFormat,
    ViralityScorecard,
    RenderJobStatus,
    GenerationTelemetry,
)
from app.schemas.trend import AnalyzedTrendOpportunity
from app.workers.registry import get_worker
from app.services.llm import LLMService
from app.services.script_director import script_director_agent
from app.core.logging import get_logger

logger = get_logger("video_engine")


# ---------------------------------------------------------------------------
# BRAND IDENTITY REGISTRY — Visual language per worker
# ---------------------------------------------------------------------------

BRAND_IDENTITIES: dict[str, BrandIdentity] = {
    "tech": BrandIdentity(
        worker_id="tech",
        brand_name="Signal Tech",
        colors=BrandColorPalette(
            primary="#00d4ff",
            secondary="#0a0e1a",
            accent="#7c3aed",
            caption_highlight="#00d4ff",
        ),
        typography=BrandTypography(
            heading_font="JetBrains Mono Bold",
            caption_font="JetBrains Mono Bold",
            caption_size=44,
        ),
        default_voice="en-US-GuyNeural",
        voice_speed=1.08,
    ),
    "business": BrandIdentity(
        worker_id="business",
        brand_name="Founder Brief",
        colors=BrandColorPalette(
            primary="#f5a623",
            secondary="#1a1a2e",
            accent="#10b981",
            caption_highlight="#f5a623",
        ),
        typography=BrandTypography(
            heading_font="Montserrat-Bold",
            caption_font="Inter-Bold",
            caption_size=48,
        ),
        default_voice="en-US-ChristopherNeural",
        voice_speed=1.05,
    ),
    "entertainment": BrandIdentity(
        worker_id="entertainment",
        brand_name="Culture Loop",
        colors=BrandColorPalette(
            primary="#ff4757",
            secondary="#1e1e2e",
            accent="#ffa502",
            caption_highlight="#ff4757",
        ),
        typography=BrandTypography(
            heading_font="Bebas Neue",
            caption_font="Bebas Neue",
            caption_size=56,
        ),
        default_voice="en-US-JennyNeural",
        voice_speed=1.12,
    ),
    "education": BrandIdentity(
        worker_id="education",
        brand_name="Curiosity Daily",
        colors=BrandColorPalette(
            primary="#4ecdc4",
            secondary="#0f0f23",
            accent="#ff6b6b",
            caption_highlight="#4ecdc4",
        ),
        typography=BrandTypography(
            heading_font="Poppins-Bold",
            caption_font="Poppins-Bold",
            caption_size=46,
        ),
        default_voice="en-GB-RyanNeural",
        voice_speed=1.0,
    ),
    "lifestyle": BrandIdentity(
        worker_id="lifestyle",
        brand_name="Everyday Edit",
        colors=BrandColorPalette(
            primary="#e8b4b8",
            secondary="#1a1a2e",
            accent="#a29bfe",
            caption_highlight="#e8b4b8",
        ),
        typography=BrandTypography(
            heading_font="Playfair Display Bold",
            caption_font="Inter-Medium",
            caption_size=42,
        ),
        default_voice="en-US-AriaNeural",
        voice_speed=0.98,
    ),
}


# ---------------------------------------------------------------------------
# KEYWORD EXTRACTION & RETENTION-OPTIMIZED SCENE TEMPLATES
# ---------------------------------------------------------------------------

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
    "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves",
    "officially", "actually", "basically", "literally", "simply", "really", "heres", "today",
    "versus", "vs", "new", "dont", "cant", "wont", "everyone", "wrong", "everything"
}


def extract_visual_keywords(text: str, fallback_niche: str = "", max_keywords: int = 3) -> List[str]:
    """Extract clean, stopword-free visual search keywords suitable for stock media lookups."""
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    tokens = [w.lower().strip() for w in cleaned.split()]
    meaningful = [w for w in tokens if len(w) > 2 and w not in STOPWORDS]

    niche_fallbacks = {
        "lifestyle": ["fashion", "runway", "model", "streetwear"],
        "tech": ["technology", "coding", "software", "future"],
        "business": ["business", "finance", "startup", "office"],
        "entertainment": ["entertainment", "cinema", "music", "celebrity"],
        "education": ["science", "learning", "books", "research"],
        "curiosity": ["space", "astronomy", "universe", "nature"],
    }
    fallback = niche_fallbacks.get(fallback_niche, ["fashion", "modern", "aesthetic", "creative"])
    combined = meaningful + [w for w in fallback if w not in meaningful]
    return combined[:max_keywords]


def build_scene_graph_template(
    title: str,
    hook_text: str,
    body_points: List[str],
    cta_text: str,
    worker_id: str = "",
) -> List[SceneNode]:
    """Generate a retention-optimized scene graph from structured content points.
    
    This implements the proven short-form retention curve:
    - Scenes 1-2 (0-3s): CRITICAL zone — aggressive hook with fast cuts
    - Scene 3 (3-8s): BUILD zone — create curiosity gap  
    - Scenes 4-6 (8-25s): CORE zone — value delivery with visual variety
    - Scene 7-8 (25s+): CLOSE zone — payoff + conversion CTA
    """
    scenes: List[SceneNode] = []
    hook_keywords = extract_visual_keywords(f"{title} {hook_text}", fallback_niche=worker_id, max_keywords=3)

    # SCENE 1: THE HOOK (0-2.5s) — Critical retention zone
    scenes.append(SceneNode(
        scene_id="s01-hook",
        emotional_beat=EmotionalBeat.hook,
        retention_zone=RetentionZone.critical,
        duration_seconds=2.5,
        visual=VisualDirective(
            description="Rapid kinetic text animation of the core claim, zooming into frame",
            visual_type="b_roll",
            search_keywords=hook_keywords,
            camera_motion="slow_zoom_in",
            color_mood="high_contrast",
        ),
        audio=AudioDirective(
            voiceover_text=hook_text,
            voiceover_emphasis=hook_text.split()[:3],
            voice_tone="urgent",
            sfx_cue="impact",
            music_energy="peak",
        ),
        caption_style="word_highlight",
        transition_in="glitch",
        pacing_note="MAXIMUM ENERGY. No dead frames. Text must appear within 0.3s.",
    ))

    # SCENE 2: TENSION BUILDER (2.5-5s) — Still critical
    tension_text = f"And most people have no idea what's actually happening with {title.split(':')[0].split('—')[0].strip()[:30]}."
    scenes.append(SceneNode(
        scene_id="s02-tension",
        emotional_beat=EmotionalBeat.tension,
        retention_zone=RetentionZone.build,
        duration_seconds=3.0,
        visual=VisualDirective(
            description="Dramatic b-roll establishing the topic context with subtle camera movement",
            visual_type="b_roll",
            search_keywords=extract_visual_keywords(title, fallback_niche=worker_id, max_keywords=3),
            visual_metaphor="unveiling hidden truth",
            camera_motion="pan_left",
            color_mood="desaturated",
        ),
        audio=AudioDirective(
            voiceover_text=tension_text,
            voice_tone="conspiratorial",
            sfx_cue="suspense_sting",
            music_energy="building",
        ),
        caption_style="word_highlight",
        transition_in="cut",
        pacing_note="Lower energy but maintain intrigue. Lean into the curiosity gap.",
    ))

    # SCENES 3-N: CORE VALUE DELIVERY — Each body point becomes a scene
    core_motions = ["slow_zoom_out", "pan_right", "ken_burns", "slow_zoom_in"]
    for i, point in enumerate(body_points[:4]):
        beat = EmotionalBeat.revelation if i == 0 else EmotionalBeat.escalation
        motion = core_motions[i % len(core_motions)]
        scenes.append(SceneNode(
            scene_id=f"s{i+3:02d}-core-{i+1}",
            emotional_beat=beat,
            retention_zone=RetentionZone.core,
            duration_seconds=4.5,
            visual=VisualDirective(
                description=f"Visual evidence or example illustrating: {point[:60]}",
                visual_type="b_roll" if i % 2 == 0 else "split_screen",
                search_keywords=extract_visual_keywords(f"{point} {title}", fallback_niche=worker_id, max_keywords=3),
                camera_motion=motion,
                color_mood="warm" if i % 2 == 0 else "cool",
            ),
            audio=AudioDirective(
                voiceover_text=point,
                voice_tone="excited" if beat == EmotionalBeat.revelation else "serious",
                sfx_cue="reveal_chime" if i == 0 else None,
                music_energy="building" if i < 2 else "peak",
            ),
            caption_style="word_highlight",
            transition_in="zoom_transition" if i == 0 else "cut",
            pacing_note=f"Evidence delivery scene {i+1}. Vary visual type from previous scene.",
        ))

    # PAYOFF SCENE
    scenes.append(SceneNode(
        scene_id=f"s{len(scenes)+1:02d}-payoff",
        emotional_beat=EmotionalBeat.payoff,
        retention_zone=RetentionZone.close,
        duration_seconds=3.5,
        visual=VisualDirective(
            description="Satisfying summary visual — chart, transformation, or before/after",
            visual_type="text_overlay",
            search_keywords=extract_visual_keywords(f"{title} success transformation", fallback_niche=worker_id, max_keywords=3),
            camera_motion="slow_zoom_out",
            color_mood="warm",
        ),
        audio=AudioDirective(
            voiceover_text=f"And that changes everything about how we think about {title.split()[0].lower()}.",
            voice_tone="calm",
            music_energy="drop",
        ),
        caption_style="full_sentence",
        transition_in="fade",
        pacing_note="Breathing room. Let the insight land.",
    ))

    # CTA SCENE
    scenes.append(SceneNode(
        scene_id=f"s{len(scenes)+1:02d}-cta",
        emotional_beat=EmotionalBeat.cta,
        retention_zone=RetentionZone.close,
        duration_seconds=3.0,
        visual=VisualDirective(
            description="Brand outro card with follow CTA and next-video tease",
            visual_type="text_overlay",
            search_keywords=extract_visual_keywords(f"{title} community follow", fallback_niche=worker_id, max_keywords=3),
            camera_motion="ken_burns",
        ),
        audio=AudioDirective(
            voiceover_text=cta_text,
            voice_tone="excited",
            sfx_cue="notification",
            music_energy="peak",
        ),
        caption_style="minimal",
        transition_in="zoom_transition",
        pacing_note="Energy spike for CTA. Make the follow feel urgent.",
    ))

    return scenes


# ---------------------------------------------------------------------------
# A/B HOOK VARIANT FACTORY
# ---------------------------------------------------------------------------

def generate_hook_variants(title: str, audience: str) -> List[HookVariant]:
    """Generate 3 psychologically distinct hook variants for A/B testing."""
    subject = title.split(":")[0].split("—")[0].strip()
    if len(subject) > 35:
        subject = subject[:33] + "…"

    return [
        HookVariant(
            variant_id="hook-contrarian",
            variant_label="Contrarian Warning",
            hook_text=f"Everyone is wrong about {subject}. Here's the proof.",
            hook_visual_description="Red warning text flash with camera shake effect",
            predicted_retention_3s=0.72,
            hook_archetype="contrarian",
        ),
        HookVariant(
            variant_id="hook-curiosity",
            variant_label="Curiosity Gap",
            hook_text=f"I spent 48 hours testing {subject} and what I found changes everything.",
            hook_visual_description="Personal POV shot transitioning to evidence montage",
            predicted_retention_3s=0.68,
            hook_archetype="curiosity_gap",
        ),
        HookVariant(
            variant_id="hook-stat-shock",
            variant_label="Statistical Shock",
            hook_text=f"97% of people don't know this about {subject}. Number 3 will surprise you.",
            hook_visual_description="Large animated percentage counter with dramatic reveal",
            predicted_retention_3s=0.65,
            hook_archetype="stat_paradox",
        ),
    ]


# ---------------------------------------------------------------------------
# VIRALITY SCORER
# ---------------------------------------------------------------------------

def score_virality(blueprint: VideoProductionBlueprint) -> ViralityScorecard:
    """Pre-publish quality prediction based on production blueprint analysis."""
    
    # Hook strength: First scene duration < 3s and has SFX
    first_scene = blueprint.scenes[0] if blueprint.scenes else None
    hook_score = 70
    if first_scene:
        if first_scene.duration_seconds <= 3.0:
            hook_score += 10
        if first_scene.audio.sfx_cue:
            hook_score += 8
        if first_scene.audio.voice_tone in ("urgent", "excited"):
            hook_score += 7
        if first_scene.transition_in in ("glitch", "zoom_transition"):
            hook_score += 5

    # Pacing: Check scene duration variance and total duration
    durations = [s.duration_seconds for s in blueprint.scenes]
    avg_duration = sum(durations) / len(durations) if durations else 5.0
    pacing_score = 75
    if 2.5 <= avg_duration <= 5.0:
        pacing_score += 15
    if blueprint.total_duration_seconds <= 45:
        pacing_score += 5
    if len(blueprint.scenes) >= 5:
        pacing_score += 5

    # Visual variety: Count unique visual types
    visual_types = set(s.visual.visual_type for s in blueprint.scenes)
    variety_score = min(100, 50 + len(visual_types) * 12)

    # Audio energy: Check for SFX and voice tone variety
    sfx_count = sum(1 for s in blueprint.scenes if s.audio.sfx_cue)
    tone_variety = len(set(s.audio.voice_tone for s in blueprint.scenes))
    audio_score = min(100, 55 + sfx_count * 8 + tone_variety * 6)

    # CTA clarity
    cta_scenes = [s for s in blueprint.scenes if s.emotional_beat == EmotionalBeat.cta]
    cta_score = 85 if cta_scenes else 40

    # Shareability: Based on hook variants and thumbnail quality
    share_score = 65
    if len(blueprint.hook_variants) >= 2:
        share_score += 10
    if blueprint.thumbnail.headline_text:
        share_score += 10
    if blueprint.thumbnail.arrow_or_circle:
        share_score += 5

    overall = int((hook_score + pacing_score + variety_score + audio_score + cta_score + share_score) / 6)

    risk_flags = []
    if blueprint.total_duration_seconds > 60:
        risk_flags.append("Duration exceeds optimal 45s window for shorts")
    if not first_scene or first_scene.duration_seconds > 3.0:
        risk_flags.append("Hook exceeds 3-second critical retention window")

    recommendation = "publish"
    if overall < 60:
        recommendation = "revise_hook"
    elif hook_score < 65:
        recommendation = "revise_hook"
    elif pacing_score < 60:
        recommendation = "revise_pacing"
    elif variety_score < 55:
        recommendation = "revise_visuals"

    return ViralityScorecard(
        overall_score=min(100, overall),
        hook_strength=min(100, hook_score),
        pacing_quality=min(100, pacing_score),
        visual_variety=min(100, variety_score),
        audio_energy=min(100, audio_score),
        cta_clarity=min(100, cta_score),
        shareability=min(100, share_score),
        risk_flags=risk_flags,
        recommendation=recommendation,
    )


# ---------------------------------------------------------------------------
# VIDEO INTELLIGENCE ENGINE — Main orchestration class
# ---------------------------------------------------------------------------

class VideoIntelligenceEngine:
    """Autonomous video production blueprint generator.
    
    Produces complete VideoProductionBlueprint artifacts that can be:
    1. Reviewed and approved by the human operator
    2. Rendered by the FFmpeg pipeline
    3. A/B tested with multiple hook variants
    4. Exported to multiple aspect ratios
    """

    def assemble_blueprint(
        self,
        worker_id: str,
        trend_title: str,
        hook_text: str,
        body_points: List[str],
        cta_text: str,
        description: str,
        source_trend_id: Optional[str] = None,
    ) -> VideoProductionBlueprint:
        worker = get_worker(worker_id)
        brand = BRAND_IDENTITIES.get(worker_id, BRAND_IDENTITIES["business"])
        blueprint_id = f"vbp-{uuid.uuid4().hex[:12]}"

        # Build scene graph
        scenes = build_scene_graph_template(
            title=trend_title,
            hook_text=hook_text,
            body_points=body_points,
            cta_text=cta_text,
            worker_id=worker_id,
        )
        total_duration = sum(s.duration_seconds for s in scenes)

        # Hook variants
        hook_variants = generate_hook_variants(trend_title, worker.audience)

        # Thumbnail spec
        thumbnail_words = trend_title.split()
        thumbnail = ThumbnailSpec(
            headline_text=" ".join(thumbnail_words[:5]).upper() if len(thumbnail_words) >= 5 else trend_title[:40].upper(),
            subtext=f"by {brand.brand_name}",
            emotion="shock" if "wrong" in hook_text.lower() or "stop" in hook_text.lower() else "curiosity",
            layout="split_diagonal",
            background_image_keywords=extract_visual_keywords(trend_title, fallback_niche=worker_id, max_keywords=3),
            arrow_or_circle=True,
        )

        # Captions
        captions = CaptionConfig(
            style="word_highlight",
            highlight_color=brand.colors.caption_highlight,
            base_color=brand.colors.text_primary,
            font_size=brand.typography.caption_size,
            animation="pop",
        )

        # Multi-format export
        export = MultiFormatExport(
            primary=ExportFormat(aspect_ratio="9:16", resolution="1080x1920"),
            square=ExportFormat(aspect_ratio="1:1", resolution="1080x1080"),
            landscape=None,
        )

        # Assemble blueprint
        blueprint = VideoProductionBlueprint(
            blueprint_id=blueprint_id,
            worker_id=worker_id,
            source_trend_id=source_trend_id,
            title=trend_title,
            description=description,
            scenes=scenes,
            total_duration_seconds=total_duration,
            brand=brand,
            captions=captions,
            hook_variants=hook_variants,
            selected_hook_variant="hook-contrarian",
            thumbnail=thumbnail,
            export=export,
            hashtags=self._generate_hashtags(worker, trend_title),
            target_platforms=["youtube_shorts", "instagram_reels", "tiktok"],
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        blueprint.virality_score = score_virality(blueprint)
        return blueprint

    async def generate_blueprint_from_trend(
        self,
        worker_id: str,
        trend_title: str,
        trend_summary: Optional[str] = None,
        source_trend_id: Optional[str] = None,
        llm: Optional[LLMService] = None,
        step_callback: Optional[Any] = None,
        token_callback: Optional[Any] = None,
    ) -> VideoProductionBlueprint:
        """Generate a complete video production blueprint from a trending topic with agentic scriptwriting."""
        worker = get_worker(worker_id)
        brand = BRAND_IDENTITIES.get(worker_id, BRAND_IDENTITIES["business"])

        # Auto-resolve LLM service if not explicitly passed
        active_llm = llm
        if active_llm is None:
            try:
                from app.dependencies import get_llm_service
                active_llm = get_llm_service()
            except Exception as ex:
                logger.debug("Could not resolve default LLM service: %s", ex)

        # 1. Agentic Screenplay Crafting & Research
        scenes, hook_text, cta_text, description, telemetry = await script_director_agent.craft_screenplay(
            worker=worker,
            trend_title=trend_title,
            trend_summary=trend_summary,
            llm=active_llm,
            step_callback=step_callback,
            token_callback=token_callback,
        )

        blueprint_id = f"vbp-{uuid.uuid4().hex[:12]}"
        total_duration = sum(s.duration_seconds for s in scenes)
        hook_variants = generate_hook_variants(trend_title, worker.audience)

        # Thumbnail spec
        thumbnail_words = trend_title.split()
        thumbnail = ThumbnailSpec(
            headline_text=" ".join(thumbnail_words[:5]).upper() if len(thumbnail_words) >= 5 else trend_title[:40].upper(),
            subtext=f"by {brand.brand_name}",
            emotion="shock" if "wrong" in hook_text.lower() or "cost" in hook_text.lower() else "curiosity",
            layout="split_diagonal",
            background_image_keywords=scenes[0].visual.search_keywords if scenes else extract_visual_keywords(trend_title, fallback_niche=worker_id, max_keywords=3),
            arrow_or_circle=True,
        )

        # Captions
        captions = CaptionConfig(
            style="word_highlight",
            highlight_color=brand.colors.caption_highlight,
            base_color=brand.colors.text_primary,
            font_size=brand.typography.caption_size,
            animation="pop",
        )

        # Multi-format export
        export = MultiFormatExport(
            primary=ExportFormat(aspect_ratio="9:16", resolution="1080x1920"),
            square=ExportFormat(aspect_ratio="1:1", resolution="1080x1080"),
            landscape=None,
        )

        blueprint = VideoProductionBlueprint(
            blueprint_id=blueprint_id,
            worker_id=worker_id,
            source_trend_id=source_trend_id,
            title=trend_title,
            description=description,
            scenes=scenes,
            total_duration_seconds=total_duration,
            brand=brand,
            captions=captions,
            hook_variants=hook_variants,
            selected_hook_variant=hook_variants[0].variant_id if hook_variants else "hook-contrarian",
            thumbnail=thumbnail,
            export=export,
            virality_score=None,
            telemetry=telemetry,
            hashtags=self._generate_hashtags(worker, trend_title),
            target_platforms=["youtube_shorts", "instagram_reels", "tiktok"],
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        blueprint.virality_score = score_virality(blueprint)

        logger.info(
            "Blueprint '%s' generated for %s | Scenes: %d | Duration: %.1fs | Mode: %s | Virality: %d/100",
            blueprint.blueprint_id,
            blueprint.brand.brand_name,
            len(blueprint.scenes),
            blueprint.total_duration_seconds,
            telemetry.engine_mode,
            blueprint.virality_score.overall_score if blueprint.virality_score else 0,
        )

        return blueprint

    async def _generate_script_with_llm(
        self, llm: LLMService, worker, trend_title: str, trend_summary: Optional[str]
    ) -> Optional[dict]:
        """Use Ollama to generate a structured scene-by-scene script."""
        system_prompt = (
            f"You are the Lead Creative Director for '{worker.name}', producing viral short-form video content.\n"
            f"Brand voice: {worker.voice}\n"
            f"Target audience: {worker.audience}\n"
            f"Content pillars: {', '.join(worker.content_pillars or [])}\n\n"
            "RULES:\n"
            "1. The 'hook' MUST be a 3-second scroll-stopping statement. No 'Hey guys' or 'In today's video'.\n"
            "2. Use high-retention formulas: Contrarian Warning, Stat Paradox, Curiosity Gap, or Negative Framing.\n"
            "3. Each 'body_point' should be a single sentence narration for one visual scene (4-5 seconds of speech).\n"
            "4. The 'cta' must create urgency to follow, not just say 'like and subscribe'.\n"
            "5. Total script should be 30-45 seconds of spoken audio.\n\n"
            "Return ONLY valid JSON:\n"
            '{"hook": "...", "body_points": ["point 1", "point 2", "point 3", "point 4"], "cta": "...", "description": "..."}'
        )

        context = trend_summary or trend_title
        user_prompt = f"Create a viral short-form video script about: {trend_title}\n\nContext: {context}"

        raw = await llm.generate(prompt=user_prompt, system=system_prompt)

        try:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                parsed = json.loads(raw[start:end + 1])
                if isinstance(parsed, dict) and "hook" in parsed and "body_points" in parsed:
                    return parsed
        except Exception as e:
            logger.debug("LLM script JSON parse failed: %s", e)

        return None

    def _generate_hashtags(self, worker, title: str) -> List[str]:
        """Generate platform-optimized hashtags."""
        base = ["shorts", "viral", worker.niche.replace(" ", "").lower()]
        words = [w.lower().replace(",", "").replace(".", "") for w in title.split() if len(w) > 3]
        return ["#" + tag for tag in (base + words[:4])]

    def get_render_job_status(self, blueprint_id: str) -> RenderJobStatus:
        """Check the status of a render job (placeholder for actual rendering pipeline)."""
        return RenderJobStatus(
            job_id=f"rj-{uuid.uuid4().hex[:8]}",
            blueprint_id=blueprint_id,
            worker_id="tech",
            status="queued",
            progress_pct=0.0,
        )

    async def enhance_scene_script(
        self,
        current_text: str,
        emotional_beat: str,
        style: str = "punchy",
        llm: Optional[LLMService] = None,
    ) -> str:
        """Uses LLM or algorithmic viral copywriting formulas to rewrite a scene script for maximum viewer retention."""
        if llm:
            try:
                system_prompt = (
                    "You are an elite short-form video copywriter (MrBeast, Alex Hormozi style).\n"
                    "Your task is to rewrite a single scene's spoken narration line.\n"
                    "RULES:\n"
                    "1. Maximum 1-2 punchy sentences (10-20 words total).\n"
                    "2. Remove all filler, passive voice, and throat-clearing.\n"
                    f"3. Style target: {style} (e.g. punchy = direct & urgent, curiosity_gap = cliffhanger intrigue, controversial = bold claim).\n"
                    "4. Return ONLY the rewritten spoken line, nothing else."
                )
                user_prompt = f"Original line: '{current_text}' (Beat: {emotional_beat})"
                enhanced = await asyncio.wait_for(
                    llm.generate(prompt=user_prompt, system=system_prompt),
                    timeout=3.0,
                )
                enhanced = enhanced.strip().strip('"').strip("'")
                if len(enhanced) > 5 and len(enhanced.split()) <= 30:
                    return enhanced
            except Exception as e:
                logger.debug("LLM script enhancement failed or timed out: %s", e)

        # Algorithmic fallback
        return self.enhance_script_sync(current_text=current_text, emotional_beat=emotional_beat, style=style)

    def enhance_script_sync(
        self,
        current_text: str,
        emotional_beat: str,
        style: str = "punchy",
    ) -> str:
        """Algorithmic high-retention copywriting formulas to rewrite a scene script."""
        clean = current_text.strip().rstrip(".")
        if style == "punchy":
            if not clean.startswith(("Stop", "Look", "Notice", "Here's")):
                return f"Here is the truth: {clean.lower()}."
            return f"{clean} Right now."
        elif style == "curiosity_gap":
            return f"Almost nobody realizes this, but {clean.lower()}."
        elif style == "controversial":
            return f"Most experts got this completely wrong: {clean.lower()}."
        else:
            return f"{clean}—and it changes everything."


video_engine = VideoIntelligenceEngine()

