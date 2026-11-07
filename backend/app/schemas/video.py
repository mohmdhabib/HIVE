"""
HIVE Video Intelligence Engine — Production Schemas

Goes beyond MoneyPrinterTurbo's flat script model by introducing:
1. Scene-graph storytelling with emotional arc mapping
2. Retention-curve-aware pacing directives
3. Per-worker brand identity systems (colors, fonts, intros)
4. Multi-voice TTS with SFX cue points
5. Word-level animated caption configs
6. A/B hook variant generation
7. Thumbnail composition specs
8. Multi-format export (9:16, 1:1, 16:9)
9. Pre-publish virality scoring
"""

from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field
from enum import Enum


# ---------------------------------------------------------------------------
# 1. EMOTIONAL ARC & RETENTION MODELLING
# ---------------------------------------------------------------------------

class EmotionalBeat(str, Enum):
    hook = "hook"                   # 0-3s: Stop the scroll
    tension = "tension"             # 3-8s: Create curiosity gap
    revelation = "revelation"       # 8-15s: Deliver the core insight
    escalation = "escalation"       # 15-25s: Stack evidence or examples
    payoff = "payoff"               # 25-40s: Emotional reward
    twist = "twist"                 # Optional: subvert expectations
    cta = "cta"                     # Final: call-to-action

class RetentionZone(str, Enum):
    critical = "critical"           # First 3 seconds — make or break
    build = "build"                 # 3-8s — audience deciding to stay
    core = "core"                   # 8-25s — main value delivery
    close = "close"                 # 25s+ — conversion window


# ---------------------------------------------------------------------------
# 2. SCENE GRAPH — Each video is a sequence of directed scenes
# ---------------------------------------------------------------------------

class VisualDirective(BaseModel):
    """What should appear on screen for this scene."""
    description: str = Field(..., description="What the viewer sees — concrete and specific")
    visual_type: Literal["b_roll", "talking_head", "screen_recording", "text_overlay", "split_screen", "kinetic_typography", "meme_reference"] = "b_roll"
    search_keywords: List[str] = Field(default_factory=list, description="Keywords for stock footage matching")
    visual_metaphor: Optional[str] = Field(None, description="Abstract concept to visualize (e.g. 'exponential growth' → rocket launch)")
    camera_motion: Literal["static", "slow_zoom_in", "slow_zoom_out", "pan_left", "pan_right", "ken_burns"] = "slow_zoom_in"
    color_mood: Optional[str] = Field(None, description="Color grading hint: warm, cool, desaturated, high_contrast")

class AudioDirective(BaseModel):
    """Audio layer configuration for a scene."""
    voiceover_text: str = Field(..., description="Exact TTS narration text")
    voiceover_emphasis: List[str] = Field(default_factory=list, description="Words to emphasize with slower pacing or louder volume")
    voice_tone: Literal["neutral", "excited", "serious", "conspiratorial", "urgent", "calm"] = "neutral"
    sfx_cue: Optional[str] = Field(None, description="Sound effect trigger: whoosh, impact, notification, suspense_sting, reveal_chime")
    music_energy: Literal["low", "building", "peak", "drop", "silence"] = "building"
    bgm_track: Optional[str] = Field("cyber_beat", description="Background lo-fi ambient track name")

class SceneNode(BaseModel):
    """A single scene in the video's story graph."""
    scene_id: str
    emotional_beat: EmotionalBeat
    retention_zone: RetentionZone
    duration_seconds: float = Field(..., ge=0.5, le=30.0)
    visual: VisualDirective
    audio: AudioDirective
    caption_style: Literal["word_highlight", "full_sentence", "minimal", "none"] = "word_highlight"
    transition_in: Literal["cut", "fade", "zoom_transition", "swipe_left", "glitch"] = "cut"
    pacing_note: Optional[str] = Field(None, description="Director's note on rhythm and energy")


# ---------------------------------------------------------------------------
# 3. BRAND IDENTITY SYSTEM — Per-worker visual language
# ---------------------------------------------------------------------------

class BrandColorPalette(BaseModel):
    primary: str = "#f5a623"        # HIVE amber default
    secondary: str = "#1a1a2e"
    accent: str = "#e94560"
    text_primary: str = "#ffffff"
    text_secondary: str = "#a0a0a0"
    caption_highlight: str = "#f5a623"
    caption_background: str = "rgba(0,0,0,0.7)"

class BrandTypography(BaseModel):
    heading_font: str = "Montserrat-Bold"
    body_font: str = "Inter-Regular"
    caption_font: str = "Inter-Bold"
    caption_size: int = Field(default=48, ge=24, le=96)

class BrandIdentity(BaseModel):
    """Complete visual identity for a worker brand."""
    worker_id: str
    brand_name: str
    logo_path: Optional[str] = None
    watermark_position: Literal["top_left", "top_right", "bottom_left", "bottom_right"] = "bottom_right"
    watermark_opacity: float = Field(default=0.3, ge=0.0, le=1.0)
    colors: BrandColorPalette = Field(default_factory=BrandColorPalette)
    typography: BrandTypography = Field(default_factory=BrandTypography)
    intro_template: Optional[str] = Field(None, description="Path to intro animation template")
    outro_template: Optional[str] = Field(None, description="Path to outro/CTA animation template")
    default_voice: str = Field(default="en-US-ChristopherNeural", description="Edge-TTS voice identifier")
    voice_speed: float = Field(default=1.05, ge=0.5, le=2.0, description="TTS speed multiplier")


# ---------------------------------------------------------------------------
# 4. CAPTION ENGINE CONFIGURATION
# ---------------------------------------------------------------------------

class CaptionConfig(BaseModel):
    style: Literal["word_highlight", "karaoke", "typewriter", "bounce", "none"] = "word_highlight"
    position: Literal["bottom_center", "center", "top_center"] = "bottom_center"
    max_words_per_line: int = Field(default=5, ge=2, le=12)
    highlight_color: str = "#f5a623"
    base_color: str = "#ffffff"
    shadow_color: str = "#000000"
    font_size: int = Field(default=48, ge=24, le=96)
    stroke_width: int = Field(default=3, ge=0, le=8)
    animation: Literal["pop", "fade", "slide_up", "none"] = "pop"


# ---------------------------------------------------------------------------
# 5. A/B HOOK VARIANTS
# ---------------------------------------------------------------------------

class HookVariant(BaseModel):
    variant_id: str
    variant_label: str = Field(..., description="e.g. 'Contrarian Warning', 'Curiosity Gap', 'Stat Shock'")
    hook_text: str = Field(..., description="The spoken hook in the first 3 seconds")
    hook_visual_description: str = Field(..., description="What appears on screen during the hook")
    predicted_retention_3s: float = Field(default=0.65, ge=0.0, le=1.0, description="Predicted % of viewers still watching at 3s")
    hook_archetype: Literal["contrarian", "curiosity_gap", "urgent_warning", "stat_paradox", "behind_the_scenes", "negative_framing"] = "curiosity_gap"


# ---------------------------------------------------------------------------
# 6. THUMBNAIL COMPOSITION
# ---------------------------------------------------------------------------

class ThumbnailSpec(BaseModel):
    headline_text: str = Field(..., max_length=60, description="Bold text overlay — max 5-6 words")
    subtext: Optional[str] = Field(None, max_length=40)
    emotion: Literal["shock", "curiosity", "excitement", "fear", "satisfaction"] = "curiosity"
    layout: Literal["text_left_image_right", "centered_text", "split_diagonal", "full_bleed_text"] = "centered_text"
    background_image_keywords: List[str] = Field(default_factory=list)
    use_brand_colors: bool = True
    face_overlay: bool = Field(default=False, description="Whether to composite a reaction face")
    arrow_or_circle: bool = Field(default=False, description="Visual attention director element")


# ---------------------------------------------------------------------------
# 7. EXPORT FORMAT SPECIFICATION
# ---------------------------------------------------------------------------

class ExportFormat(BaseModel):
    aspect_ratio: Literal["9:16", "1:1", "16:9"] = "9:16"
    resolution: str = "1080x1920"   # Derived from aspect ratio
    fps: int = Field(default=30, ge=24, le=60)
    codec: str = "libx264"
    audio_codec: str = "aac"
    bitrate: str = "8M"
    format: str = "mp4"

class MultiFormatExport(BaseModel):
    primary: ExportFormat = Field(default_factory=lambda: ExportFormat(aspect_ratio="9:16", resolution="1080x1920"))
    square: Optional[ExportFormat] = Field(default_factory=lambda: ExportFormat(aspect_ratio="1:1", resolution="1080x1080"))
    landscape: Optional[ExportFormat] = None


# ---------------------------------------------------------------------------
# 8. VIRALITY SCORING — Pre-publish quality prediction
# ---------------------------------------------------------------------------

class ViralityScorecard(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    hook_strength: int = Field(..., ge=0, le=100, description="How compelling is the first 3 seconds")
    pacing_quality: int = Field(..., ge=0, le=100, description="Is the cut rhythm retention-optimized")
    visual_variety: int = Field(..., ge=0, le=100, description="Enough visual changes to prevent scroll-away")
    audio_energy: int = Field(..., ge=0, le=100, description="Voice + music + SFX energy match")
    cta_clarity: int = Field(..., ge=0, le=100, description="Is the call-to-action clear and compelling")
    shareability: int = Field(..., ge=0, le=100, description="Would viewers share/save this")
    risk_flags: List[str] = Field(default_factory=list, description="Content risks: factual, legal, platform policy")
    recommendation: Literal["publish", "revise_hook", "revise_pacing", "revise_visuals", "reject"] = "publish"


# ---------------------------------------------------------------------------
# 9. COMPLETE VIDEO PRODUCTION BLUEPRINT
# ---------------------------------------------------------------------------

class VideoProductionBlueprint(BaseModel):
    """The complete production specification for a single video — the central artifact
    that the Video Intelligence Engine produces and the rendering pipeline consumes."""

    blueprint_id: str
    worker_id: str
    source_trend_id: Optional[str] = None
    title: str
    description: str
    
    # Story structure
    scenes: List[SceneNode] = Field(..., min_length=3, description="Ordered scene graph")
    total_duration_seconds: float = Field(..., ge=5.0, le=180.0)
    
    # Brand identity
    brand: BrandIdentity
    
    # Captions
    captions: CaptionConfig = Field(default_factory=CaptionConfig)
    
    # A/B testing
    hook_variants: List[HookVariant] = Field(default_factory=list, min_length=1)
    selected_hook_variant: str = Field(..., description="variant_id of the chosen hook")
    
    # Thumbnail
    thumbnail: ThumbnailSpec
    
    # Export
    export: MultiFormatExport = Field(default_factory=MultiFormatExport)
    
    # Quality prediction
    virality_score: Optional[ViralityScorecard] = None

    # AI Engine & Agent Telemetry Trace
    telemetry: Optional["GenerationTelemetry"] = None
    
    # Metadata
    hashtags: List[str] = Field(default_factory=list)
    target_platforms: List[str] = Field(default_factory=lambda: ["youtube_shorts", "instagram_reels", "tiktok"])
    monetization_links: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None


# ---------------------------------------------------------------------------
# 10. AI GENERATION TELEMETRY & LOG TRACE
# ---------------------------------------------------------------------------

class GenerationTelemetry(BaseModel):
    engine_mode: Literal["ollama_llama3.1", "agentic_nlp_synthesizer"] = "agentic_nlp_synthesizer"
    model_name: str = "llama3.1:latest"
    research_latency_seconds: float = 0.0
    screenplay_archetype: str = "contrarian_paradox"
    llm_connected: bool = True
    llm_error_reason: Optional[str] = None
    target_audience: str = "general"
    angle_discovered: str = "contrarian"
    event_trace: List[Dict[str, str]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 11. SCENE CLIPS & RENDER JOB STATUS
# ---------------------------------------------------------------------------

class SceneClipArtifact(BaseModel):
    """Visual asset artifacts for an individual scene clip in the video editor."""
    scene_idx: int
    scene_id: str
    emotional_beat: str
    duration_seconds: float
    clip_path: str
    thumbnail_path: Optional[str] = None
    overlay_path: Optional[str] = None
    voice_path: Optional[str] = None
    voiceover_text: str
    camera_motion: str
    search_keywords: List[str] = Field(default_factory=list)
    source_asset: Optional[str] = None
    resolved_footage_type: Optional[str] = None
    resolved_footage_query: Optional[str] = None
    status: str = "ready"
    status: Literal["ready", "rendering", "failed"] = "ready"


class SceneUpdateRequest(BaseModel):
    """Payload for editing and regenerating an individual scene clip in the advanced editor."""
    voiceover_text: Optional[str] = None
    search_keywords: Optional[List[str]] = None
    camera_motion: Optional[str] = None
    visual_description: Optional[str] = None
    custom_asset_path: Optional[str] = None
    caption_position: Optional[Literal["bottom", "center", "top", "bottom_center", "top_center"]] = None
    caption_font_size: Optional[int] = None
    caption_highlight_color: Optional[str] = None
    caption_style: Optional[Literal["pill", "outline", "minimal"]] = None
    sfx_cue: Optional[str] = None
    voice_speed: Optional[float] = None
    bgm_track: Optional[str] = None
    visual_filter: Optional[Literal["none", "vibrant", "cinematic", "cyberpunk"]] = None
    aspect_ratio: Optional[Literal["9:16", "1:1", "16:9"]] = None


class SceneReorderRequest(BaseModel):
    from_idx: int
    to_idx: int


class SceneAddRequest(BaseModel):
    scene_idx: Optional[int] = None
    voiceover_text: str
    search_keywords: List[str] = Field(default_factory=list)
    camera_motion: str = "slow_zoom_in"
    emotional_beat: str = "escalation"


class EnhanceScriptRequest(BaseModel):
    style: Literal["punchy", "curiosity_gap", "controversial", "conversational"] = "punchy"


class StockMaterialItem(BaseModel):
    """Stock photo/video asset available in the editor's visual library."""
    filename: str
    asset_type: Literal["image", "video"]
    file_path: str
    relative_url: str
    thumbnail_url: str
    niche: str
    tags: List[str] = Field(default_factory=list)


class RenderJobStatus(BaseModel):
    job_id: str
    blueprint_id: str
    worker_id: str
    status: Literal["queued", "downloading_assets", "generating_tts", "compositing", "encoding", "complete", "failed"] = "queued"
    progress_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    current_step: Optional[str] = None
    output_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_size_mb: Optional[float] = None
    scene_clips: List[SceneClipArtifact] = Field(default_factory=list)

VideoProductionBlueprint.model_rebuild()


