import os
import re
import json
import time
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

from app.schemas.video import (
    SceneNode,
    VisualDirective,
    AudioDirective,
    EmotionalBeat,
    RetentionZone,
    GenerationTelemetry,
)
from app.workers.registry import WorkerConfig, get_worker
from app.services.llm import LLMService
from app.core.logging import get_logger

logger = get_logger("script_director")


class ScriptDirectorAgent:
    """Agentic short-form video screenwriter and viral retention architect.
    
    Researches trend angles, crafts bespoke 8-scene narrative arcs tailored to brand personas,
    and generates high-specificity stock footage search keywords for every scene.
    """

    async def craft_screenplay(
        self,
        worker: WorkerConfig,
        trend_title: str,
        trend_summary: Optional[str] = None,
        llm: Optional[LLMService] = None,
    ) -> Tuple[List[SceneNode], str, str, str, GenerationTelemetry]:
        """Orchestrates research, LLM script generation, dynamic NLP fallback, and telemetry recording."""
        start_time = time.time()
        events: List[Dict[str, str]] = []

        def log_event(phase: str, message: str):
            events.append({
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3],
                "phase": phase,
                "message": message,
            })
            logger.info("[%s] %s", phase, message)

        log_event("RESEARCH", f"Analyzing trend entities & viral hooks for topic: '{trend_title}' (Brand: {worker.name})")

        # Extract entities & concepts
        clean_title = re.sub(r"[^\w\s—:-]", "", trend_title).strip()
        words = [w for w in clean_title.split() if len(w) > 3 and w.lower() not in {"this", "that", "with", "from", "have", "what", "more"}]
        topic_core = " ".join(words[:4]) if words else clean_title[:30]
        primary_entity = words[0] if words else worker.niche

        log_event("RESEARCH", f"Identified primary entity: '{primary_entity}' | Core topic: '{topic_core}'")

        # Determine best screenplay archetype
        archetypes = ["contrarian_paradox", "exponential_breakthrough", "hidden_cost_warning", "insider_secret", "myth_buster"]
        # Hash topic to pick a stable yet varied archetype per topic
        archetype_idx = abs(hash(trend_title)) % len(archetypes)
        chosen_archetype = archetypes[archetype_idx]
        log_event("STRATEGY", f"Selected screenplay archetype: '{chosen_archetype}' targeting {worker.audience}")

        raw_script_result: Optional[dict] = None
        engine_mode = "agentic_nlp_synthesizer"
        llm_connected = False
        llm_error_reason = None

        # 1. Attempt LLM Generation with generous timeout if LLM is provided
        if llm is not None:
            log_event("LLM_DISPATCH", f"Dispatching prompt to Ollama model '{llm.model}' (concurrency guarded)")
            try:
                # 20 second timeout allows local Llama 3.1 to generate thorough, non-truncated structured prose
                raw_script_result = await asyncio.wait_for(
                    self._query_ollama_for_screenplay(llm, worker, trend_title, trend_summary, chosen_archetype),
                    timeout=22.0,
                )
                if raw_script_result and "scenes" in raw_script_result and len(raw_script_result["scenes"]) >= 5:
                    engine_mode = "ollama_llama3.1"
                    llm_connected = True
                    log_event("LLM_COMPLETE", f"Ollama generated {len(raw_script_result['scenes'])}-scene bespoke script in {round(time.time() - start_time, 2)}s")
                else:
                    llm_error_reason = "Ollama returned incomplete or invalid JSON schema"
                    log_event("LLM_WARNING", "Ollama output invalid; engaging dynamic NLP synthesizer")
            except asyncio.TimeoutError:
                llm_error_reason = "Ollama generation timed out after 22s (model cold or high queue depth)"
                log_event("LLM_TIMEOUT", llm_error_reason)
            except Exception as e:
                llm_error_reason = f"Ollama connection error: {str(e)}"
                log_event("LLM_ERROR", f"Could not reach Ollama: {e}")
        else:
            llm_error_reason = "Ollama LLM service was not attached; operating in autonomous NLP agent mode"
            log_event("NLP_AGENT", "No active LLM session attached; activating dynamic NLP script synthesizer")

        # 2. If LLM failed or wasn't provided, use bespoke Dynamic NLP Script Synthesizer
        if not raw_script_result or not raw_script_result.get("scenes"):
            log_event("NLP_SYNTHESIZER", f"Synthesizing unique 8-scene screenplay using archetype '{chosen_archetype}'")
            raw_script_result = self._synthesize_dynamic_nlp_script(
                worker=worker,
                trend_title=trend_title,
                trend_summary=trend_summary,
                primary_entity=primary_entity,
                topic_core=topic_core,
                archetype=chosen_archetype,
            )

        # 3. Assemble validated SceneNode list
        scenes: List[SceneNode] = []
        raw_scenes = raw_script_result.get("scenes", [])
        hook_text = raw_script_result.get("hook", f"Everything you thought you knew about {topic_core} is about to change.")
        cta_text = raw_script_result.get("cta", f"Follow for unfiltered {worker.niche} breakdowns that you won't hear in the mainstream.")
        description = raw_script_result.get("description", trend_summary or f"Deep investigative breakdown of {trend_title} for {worker.audience}.")

        beat_order = [
            EmotionalBeat.hook,
            EmotionalBeat.tension,
            EmotionalBeat.revelation,
            EmotionalBeat.escalation,
            EmotionalBeat.twist,
            EmotionalBeat.payoff,
            EmotionalBeat.cta,
        ]

        retention_zones = [
            RetentionZone.critical,
            RetentionZone.build,
            RetentionZone.core,
            RetentionZone.core,
            RetentionZone.core,
            RetentionZone.close,
            RetentionZone.close,
        ]

        motion_palette = ["slow_zoom_in", "pan_left", "slow_zoom_out", "pan_right", "ken_burns", "slow_zoom_in"]
        valid_motions = {"static", "slow_zoom_in", "slow_zoom_out", "pan_left", "pan_right", "ken_burns"}

        for idx, sc in enumerate(raw_scenes[:8]):
            beat = beat_order[min(idx, len(beat_order) - 1)]
            retention = retention_zones[min(idx, len(retention_zones) - 1)]
            raw_motion = sc.get("camera_motion") or motion_palette[idx % len(motion_palette)]
            motion = raw_motion if raw_motion in valid_motions else "slow_zoom_in"
            duration = float(sc.get("duration", 3.8 if idx == 0 else 4.2))

            # Clean and enrich visual keywords specifically for this scene
            kw_list = sc.get("search_keywords", [])
            if not kw_list or len(kw_list) < 2:
                kw_list = [f"{primary_entity.lower()} technology", f"{worker.niche.lower()} concept", "cinematic high contrast"]

            scene_node = SceneNode(
                scene_id=f"s{idx+1:02d}-{beat.value}",
                emotional_beat=beat,
                retention_zone=retention,
                duration_seconds=duration,
                visual=VisualDirective(
                    description=sc.get("visual_description", f"Cinematic visual illustrating: {sc.get('voiceover', topic_core)[:50]}"),
                    visual_type="b_roll" if idx % 2 == 0 else "text_overlay",
                    search_keywords=[str(k).strip() for k in kw_list[:4]],
                    camera_motion=motion,
                    color_mood="high_contrast" if idx == 0 else "warm" if idx % 2 == 0 else "cool",
                ),
                audio=AudioDirective(
                    voiceover_text=sc.get("voiceover", f"Scene {idx+1} breakdown."),
                    voiceover_emphasis=sc.get("voiceover", "").split()[:2],
                    voice_tone="urgent" if idx == 0 else "serious" if idx < 4 else "excited",
                    sfx_cue=sc.get("sfx_cue", "impact" if idx == 0 else "whoosh" if idx == 2 else None),
                    music_energy="peak" if idx == 0 else "building" if idx < 5 else "drop",
                ),
                caption_style="word_highlight",
                transition_in="glitch" if idx == 0 else "cut" if idx % 2 == 1 else "zoom_transition",
                pacing_note=f"Scene {idx+1} cadence locked. Maintain speech rhythm without pause.",
            )
            scenes.append(scene_node)

        total_latency = round(time.time() - start_time, 2)
        log_event("FINALIZED", f"Crafted {len(scenes)} bespoke scenes | Total agent latency: {total_latency}s | Mode: {engine_mode}")

        telemetry = GenerationTelemetry(
            engine_mode=engine_mode,  # type: ignore
            model_name=llm.model if llm else "agentic-nlp-engine",
            research_latency_seconds=total_latency,
            screenplay_archetype=chosen_archetype,
            llm_connected=llm_connected,
            llm_error_reason=llm_error_reason,
            target_audience=worker.audience,
            angle_discovered=chosen_archetype,
            event_trace=events,
        )

        return scenes, hook_text, cta_text, description, telemetry

    async def _query_ollama_for_screenplay(
        self,
        llm: LLMService,
        worker: WorkerConfig,
        trend_title: str,
        trend_summary: Optional[str],
        archetype: str,
    ) -> Optional[dict]:
        """Queries Ollama for a full 8-scene screenplay with per-scene visuals and narration."""
        system_prompt = (
            f"You are the Master Creative Director and Viral Screenwriter for '{worker.name}'.\n"
            f"Niche: {worker.niche} | Brand Voice: {worker.voice} | Target Audience: {worker.audience}\n\n"
            "MANDATORY SCRIPTWRITING RULES:\n"
            "1. DO NOT use generic filler phrases like 'Stop scrolling', 'Hey guys', 'Did you know', or 'In this video'.\n"
            "2. Write a gripping, investigative 8-scene screenplay. Every scene must reveal new information, data, or tension.\n"
            f"3. Narrative Archetype: '{archetype.upper()}'.\n"
            "4. Each scene must have:\n"
            "   - 'voiceover': exactly 1 punchy, high-impact sentence (10-18 words) of natural spoken dialogue.\n"
            "   - 'visual_description': concrete description of what is visible on screen.\n"
            "   - 'search_keywords': 3 specific photogenic keywords for stock video search (e.g. ['tokyo fashion runway', 'hologram dress', 'futuristic studio']).\n"
            "   - 'camera_motion': one of ['slow_zoom_in', 'pan_left', 'slow_zoom_out', 'pan_right', 'ken_burns'].\n"
            "   - 'sfx_cue': one of ['impact', 'whoosh', 'suspense_sting', 'reveal_chime'].\n"
            "5. Return ONLY a valid JSON object matching this schema without markdown fences:\n"
            "{\n"
            '  "hook": "3-second scroll stopping statement",\n'
            '  "cta": "Urgent call to follow",\n'
            '  "description": "2 sentence summary",\n'
            '  "scenes": [\n'
            '    {"scene_idx": 0, "beat": "hook", "voiceover": "...", "visual_description": "...", "search_keywords": ["k1","k2","k3"], "camera_motion": "slow_zoom_in", "sfx_cue": "impact"},\n'
            '    {"scene_idx": 1, "beat": "tension", "voiceover": "...", "visual_description": "...", "search_keywords": ["k1","k2","k3"], "camera_motion": "pan_left", "sfx_cue": "suspense_sting"},\n'
            '    {"scene_idx": 2, "beat": "revelation", "voiceover": "...", "visual_description": "...", "search_keywords": ["k1","k2","k3"], "camera_motion": "slow_zoom_in", "sfx_cue": "reveal_chime"},\n'
            '    {"scene_idx": 3, "beat": "escalation", "voiceover": "...", "visual_description": "...", "search_keywords": ["k1","k2","k3"], "camera_motion": "pan_right", "sfx_cue": "whoosh"},\n'
            '    {"scene_idx": 4, "beat": "deep_dive", "voiceover": "...", "visual_description": "...", "search_keywords": ["k1","k2","k3"], "camera_motion": "slow_zoom_out", "sfx_cue": null},\n'
            '    {"scene_idx": 5, "beat": "twist", "voiceover": "...", "visual_description": "...", "search_keywords": ["k1","k2","k3"], "camera_motion": "slow_zoom_in", "sfx_cue": "impact"},\n'
            '    {"scene_idx": 6, "beat": "payoff", "voiceover": "...", "visual_description": "...", "search_keywords": ["k1","k2","k3"], "camera_motion": "ken_burns", "sfx_cue": "reveal_chime"},\n'
            '    {"scene_idx": 7, "beat": "cta", "voiceover": "...", "visual_description": "...", "search_keywords": ["k1","k2","k3"], "camera_motion": "slow_zoom_in", "sfx_cue": "whoosh"}\n'
            "  ]\n"
            "}"
        )

        user_prompt = f"Write an investigative, highly viral 8-scene short-form video screenplay about this trending topic:\nTITLE: {trend_title}\nDETAILS: {trend_summary or trend_title}"

        raw = await llm.generate(prompt=user_prompt, temperature=0.4, system=system_prompt, format="json")

        # 1. Try direct JSON parse
        try:
            parsed = json.loads(raw.strip())
            if isinstance(parsed, dict) and "scenes" in parsed and len(parsed["scenes"]) >= 4:
                return parsed
        except Exception:
            pass

        # 2. Try substring extraction between outer brackets
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                parsed = json.loads(raw[start:end + 1])
                if isinstance(parsed, dict) and "scenes" in parsed and len(parsed["scenes"]) >= 4:
                    return parsed
        except Exception as e:
            logger.debug("Failed parsing Ollama JSON substring: %s", e)

        # 3. Regex repair for trailing commas
        try:
            import re
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                cleaned = re.sub(r',\s*([\]}])', r'\1', raw[start:end + 1])
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict) and "scenes" in parsed and len(parsed["scenes"]) >= 4:
                    return parsed
        except Exception as e:
            logger.debug("Failed regex repair of Ollama JSON: %s", e)

        return None

    def _synthesize_dynamic_nlp_script(
        self,
        worker: WorkerConfig,
        trend_title: str,
        trend_summary: Optional[str],
        primary_entity: str,
        topic_core: str,
        archetype: str,
    ) -> dict:
        """Bespoke dynamic combinatorial screenplay composer.
        
        Synthesizes 8 unique, high-retention scenes tailored to the exact topic and brand,
        ensuring scripts are NEVER identical across different trends even when Ollama is offline.
        """
        niche = worker.niche
        audience = worker.audience
        clean_title = trend_title.split(":")[0].split("—")[0].strip()

        # Condense long audience descriptions into punchy spoken colloquial terms
        aud_lower = audience.lower()
        if any(k in aud_lower for k in ["gaming", "movie", "pop-culture", "entertainment", "culture"]):
            natural_aud = "creators and gamers"
        elif any(k in aud_lower for k in ["developer", "engineer", "builder", "tech"]):
            natural_aud = "builders and engineers"
        elif any(k in aud_lower for k in ["investor", "finance", "founder", "money"]):
            natural_aud = "investors and operators"
        elif any(k in aud_lower for k in ["student", "learner", "curiosity", "education"]):
            natural_aud = "researchers and learners"
        else:
            natural_aud = "creators and builders"

        if archetype == "contrarian_paradox":
            hook = f"Everything you've been told about {clean_title} is fundamentally backwards."
            scenes = [
                {
                    "voiceover": f"Everything you've been told about {clean_title} is fundamentally backwards.",
                    "visual_description": f"Dramatic cinematic high-contrast close-up visualizing {primary_entity} disruption.",
                    "search_keywords": [f"{primary_entity} controversy", f"{niche} breakthrough", "cinematic dark studio"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "impact",
                },
                {
                    "voiceover": f"While everyone is chasing surface hype around {clean_title}, the real power shift in {niche} is happening completely under the radar.",
                    "visual_description": f"Fast-paced b-roll of behind-the-scenes decision makers analyzing {primary_entity}.",
                    "search_keywords": [f"{primary_entity} research", "data charts financial", "modern headquarters office"],
                    "camera_motion": "pan_left",
                    "sfx_cue": "suspense_sting",
                },
                {
                    "voiceover": f"Top industry insiders have quietly begun restructuring their entire operation around this one mechanism.",
                    "visual_description": f"Split-screen visualization comparing old obsolete methods with modern {primary_entity} systems.",
                    "search_keywords": [f"{niche} strategy", "technology blueprint", "server datacenter lights"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "reveal_chime",
                },
                {
                    "voiceover": f"The core reason? Legacy approaches can't compete against this speed and cost efficiency anymore.",
                    "visual_description": f"High-speed kinetic graph displaying exponential performance curves in {niche}.",
                    "search_keywords": [f"{primary_entity} performance", "exponential growth curve", "high tech engineering"],
                    "camera_motion": "pan_right",
                    "sfx_cue": "whoosh",
                },
                {
                    "voiceover": f"Here is the exact data point that caught almost every major legacy competitor by complete surprise.",
                    "visual_description": f"Macro footage highlighting real-world physical evidence of {clean_title}.",
                    "search_keywords": [f"{primary_entity} evidence", "microchip hardware", "financial terminal display"],
                    "camera_motion": "slow_zoom_out",
                    "sfx_cue": None,
                },
                {
                    "voiceover": f"If you're still relying on the 2024 playbook for {niche}, you're already fighting an uphill battle.",
                    "visual_description": f"Dynamic low-angle camera sweep showing industry transformation.",
                    "search_keywords": [f"{niche} competition", "futuristic workspace", "global network map"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "impact",
                },
                {
                    "voiceover": f"Mastering this single insight gives you an asymmetrical advantage over the next twelve months.",
                    "visual_description": f"Bright, inspirational payoff visual showing future triumph and scale.",
                    "search_keywords": [f"{primary_entity} future", "futuristic skyline sunset", "modern success creative"],
                    "camera_motion": "ken_burns",
                    "sfx_cue": "reveal_chime",
                },
                {
                    "voiceover": f"Tap follow for daily unfiltered {niche} breakdowns, and drop your prediction in the comments.",
                    "visual_description": f"Brand outro card with sleek kinetic motion graphics and follow CTA.",
                    "search_keywords": [f"{niche} community", "clean minimal typography", "neon brand glow"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "whoosh",
                },
            ]
        elif archetype == "exponential_breakthrough":
            hook = f"The biggest leap in {niche} just happened, and almost nobody noticed."
            scenes = [
                {
                    "voiceover": f"The biggest leap in {niche} just happened, and almost nobody noticed.",
                    "visual_description": f"Intense visual shockwave revealing {clean_title}.",
                    "search_keywords": [f"{primary_entity} discovery", "quantum leap technology", "breaking news studio"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "impact",
                },
                {
                    "voiceover": f"We just crossed a critical performance threshold in {clean_title} that experts predicted was still years away.",
                    "visual_description": f"Futuristic laboratory or design studio pushing {primary_entity} to limits.",
                    "search_keywords": [f"{primary_entity} innovation", "advanced laboratory science", "supercomputer racks"],
                    "camera_motion": "pan_left",
                    "sfx_cue": "suspense_sting",
                },
                {
                    "voiceover": f"What used to take months of painstaking manual effort is now being solved in micro-seconds.",
                    "visual_description": f"Time-lapse comparison showing rapid automated generation in {niche}.",
                    "search_keywords": [f"{niche} automation", "artificial intelligence code", "robotic precision arm"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "reveal_chime",
                },
                {
                    "voiceover": f"This isn't an incremental update — it fundamentally rewires the economics of how {natural_aud} create and operate.",
                    "visual_description": f"Financial visualization displaying radical cost reduction and output surge.",
                    "search_keywords": [f"{primary_entity} economics", "cryptocurrency trading dashboard", "modern venture capitalist"],
                    "camera_motion": "pan_right",
                    "sfx_cue": "whoosh",
                },
                {
                    "voiceover": f"Early adopters are already seeing a ten-fold multiplier on their output while costs plummet.",
                    "visual_description": f"Case study evidence showing real results from deploying {clean_title}.",
                    "search_keywords": [f"{primary_entity} success", "high growth startup office", "digital screen analytics"],
                    "camera_motion": "slow_zoom_out",
                    "sfx_cue": None,
                },
                {
                    "voiceover": f"The gap between those leveraging this and those ignoring it is widening at record pace.",
                    "visual_description": f"Diverging split screen showing fast innovators pulling away from slow legacy brands.",
                    "search_keywords": [f"{niche} division", "fast moving traffic blur", "modern high speed train"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "impact",
                },
                {
                    "voiceover": f"This is your chance to get positioned before this becomes common industry knowledge.",
                    "visual_description": f"Glorious sunrise over futuristic city with triumphant musical beat.",
                    "search_keywords": [f"{primary_entity} dawn", "modern architectural summit", "golden hour skyscrapers"],
                    "camera_motion": "ken_burns",
                    "sfx_cue": "reveal_chime",
                },
                {
                    "voiceover": f"Follow @{worker.name.replace(' ', '')} for daily frontline breakdowns before everyone else.",
                    "visual_description": f"Polished brand identity closing animation with call to action.",
                    "search_keywords": [f"{niche} channel", "social media verified badge", "dark luxury glow"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "whoosh",
                },
            ]
        elif archetype == "hidden_cost_warning":
            hook = f"There is a massive hidden cost in {clean_title} that nobody is warning you about."
            scenes = [
                {
                    "voiceover": f"There is a massive hidden cost in {clean_title} that nobody is warning you about.",
                    "visual_description": f"Ominous high-tension opening visual symbolizing hidden risk in {primary_entity}.",
                    "search_keywords": [f"{primary_entity} warning", "cybersecurity hazard alert", "dark corporate boardroom"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "impact",
                },
                {
                    "voiceover": f"Most creators and founders jumping into {clean_title} are walking straight into a legal and financial trap.",
                    "visual_description": f"Red alert HUD overlays scanning over {niche} documents and contracts.",
                    "search_keywords": [f"{niche} compliance", "financial audit ledger", "magnifying glass data"],
                    "camera_motion": "pan_left",
                    "sfx_cue": "suspense_sting",
                },
                {
                    "voiceover": f"When you inspect the fine print, the platform fees and hidden dependencies begin eating up your entire margin.",
                    "visual_description": f"Detailed breakdown showing invisible fees draining revenue balance.",
                    "search_keywords": [f"{primary_entity} fees", "falling red stock chart", "credit card transaction screen"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "reveal_chime",
                },
                {
                    "voiceover": f"Companies that scaled too fast without hedging are already being forced to absorb devastating losses.",
                    "visual_description": f"Stressed executive reviewing quarterly collapse on laptop display.",
                    "search_keywords": [f"{niche} collapse", "exhausted professional desk", "empty office midnight"],
                    "camera_motion": "pan_right",
                    "sfx_cue": "whoosh",
                },
                {
                    "voiceover": f"Here is the counter-measure that seasoned operators are using to protect their bottom line.",
                    "visual_description": f"Security vault door locking in place with protective green indicators.",
                    "search_keywords": [f"{primary_entity} defense", "digital fortress security", "iron clad legal agreement"],
                    "camera_motion": "slow_zoom_out",
                    "sfx_cue": None,
                },
                {
                    "voiceover": f"By isolating your core assets, you extract all the upside while eliminating the existential risk.",
                    "visual_description": f"Clean modular architecture diagram showing isolated risk containment.",
                    "search_keywords": [f"{niche} architecture", "modular building blocks", "clean glass modern server"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "impact",
                },
                {
                    "voiceover": f"Stay smart: in {niche}, defense and risk awareness create more long-term wealth than reckless hype.",
                    "visual_description": f"Confident leader standing atop high-rise looking out over modern metropolis.",
                    "search_keywords": [f"{primary_entity} mastery", "successful entrepreneur view", "cinematic blue sky glass"],
                    "camera_motion": "ken_burns",
                    "sfx_cue": "reveal_chime",
                },
                {
                    "voiceover": f"Save this video for later, and follow for more hard truths about {niche} that others won't tell you.",
                    "visual_description": f"Save bookmark icon pulsing with brand signature aesthetic.",
                    "search_keywords": [f"{niche} advice", "bookmark save icon", "ambient neon aesthetic"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "whoosh",
                },
            ]
        else:  # insider_secret
            hook = f"The top 1% in {niche} know something about {clean_title} that they aren't sharing."
            scenes = [
                {
                    "voiceover": f"The top 1% in {niche} know something about {clean_title} that they aren't sharing.",
                    "visual_description": f"Exclusive backstage door opening to reveal insider operation in {primary_entity}.",
                    "search_keywords": [f"{primary_entity} confidential", "luxury private lounge", "secret laboratory door"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "impact",
                },
                {
                    "voiceover": f"While public headlines focus on consumer features of {clean_title}, private equity is pouring millions into the infrastructure layer.",
                    "visual_description": f"High-stakes investment presentation showing capital allocation into {niche}.",
                    "search_keywords": [f"{niche} capital", "venture capital pitch deck", "silicon valley boardroom"],
                    "camera_motion": "pan_left",
                    "sfx_cue": "suspense_sting",
                },
                {
                    "voiceover": f"They discovered that owning this specific bottleneck creates an automated tollbooth on the entire industry.",
                    "visual_description": f"Flow of transactions passing through a central high-speed digital hub.",
                    "search_keywords": [f"{primary_entity} gateway", "high frequency trading stream", "blockchain digital transaction"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "reveal_chime",
                },
                {
                    "voiceover": f"Every time another company launches in this space, these infrastructure owners take a direct cut.",
                    "visual_description": f"Cash flow animation accumulating into private treasury account.",
                    "search_keywords": [f"{niche} revenue", "passive income metrics", "golden currency particle stream"],
                    "camera_motion": "pan_right",
                    "sfx_cue": "whoosh",
                },
                {
                    "voiceover": f"You don't need millions to capitalize on this — you just need to position where the capital is flowing next.",
                    "visual_description": f"Strategic chess board showing key queen move toward victory.",
                    "search_keywords": [f"{primary_entity} strategy", "crystal chess piece move", "strategic mastermind concept"],
                    "camera_motion": "slow_zoom_out",
                    "sfx_cue": None,
                },
                {
                    "voiceover": f"The window to secure your position before institutional money closes it is less than six months.",
                    "visual_description": f"Dramatic hourglass running out of sand against modern glass clock tower.",
                    "search_keywords": [f"{niche} deadline", "luxury mechanical watch movement", "countdown timer digital"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "impact",
                },
                {
                    "voiceover": f"Understand the game being played, and you turn market volatility into permanent leverage.",
                    "visual_description": f"Grand architectural marvel under blue hour sky symbolizing lasting power.",
                    "search_keywords": [f"{primary_entity} empire", "modern architectural monument", "majestic panoramic view"],
                    "camera_motion": "ken_burns",
                    "sfx_cue": "reveal_chime",
                },
                {
                    "voiceover": f"Follow for weekly insider breakdowns on {niche} and where smart money is moving next.",
                    "visual_description": f"Minimalist brand outro card with follow notification trigger.",
                    "search_keywords": [f"{niche} intelligence", "clean dark ui card", "amber gold branding"],
                    "camera_motion": "slow_zoom_in",
                    "sfx_cue": "whoosh",
                },
            ]

        cta = f"Follow @{worker.name.replace(' ', '')} for daily {niche} intelligence before the crowd catches on."
        description = trend_summary or f"Investigative breakdown of {clean_title} for {audience}."

        return {
            "hook": hook,
            "cta": cta,
            "description": description,
            "scenes": scenes,
        }


script_director_agent = ScriptDirectorAgent()
