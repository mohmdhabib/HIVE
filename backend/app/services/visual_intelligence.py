import re
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
from app.core.logging import get_logger

logger = get_logger("visual_intelligence")


class SemanticDomain(str, Enum):
    GAMING_ESPORTS = "gaming_esports"
    AI_TECH = "ai_tech"
    BUSINESS_FINANCE = "business_finance"
    ENTERTAINMENT_CINEMA = "entertainment_cinema"
    LIFESTYLE_FASHION = "lifestyle_fashion"
    CURIOSITY_SCIENCE = "curiosity_science"
    NATURE_ENVIRONMENT = "nature_environment"
    GENERAL = "general"


class VisualIntelligenceService:
    """Intelligent visual asset classification, query transmutation, and negative keyword filtering.
    Guarantees that video topics (like Fortnite, AI, or Finance) match accurate, high-affinity B-roll
    and prevents irrelevant stock footage (such as tree/nature photos for gaming) from ever appearing."""

    # 1. ENTITY & KEYWORD DICTIONARIES FOR DOMAIN DETECTION
    GAMING_KEYWORDS = {
        "fortnite", "roblox", "minecraft", "gta", "grand theft auto", "call of duty", "cod",
        "warzone", "valorant", "league of legends", "lol", "apex legends", "overwatch",
        "csgo", "counter-strike", "counter strike", "playstation", "ps5", "ps4", "xbox",
        "nintendo", "switch", "steam", "esports", "e-sports", "gaming", "gamer", "gamers",
        "twitch", "streamer", "streaming", "gameplay", "video game", "videogame", "rpg",
        "mmo", "battle royale", "speedrun", "unreal engine", "unity", "zelda", "pokemon",
        "cyberpunk 2077", "elden ring", "dark souls", "dota", "pubg", "genshin", "discord",
        "controller", "joystick", "battlestation", "rig", "gpu", "rtx", "clutch", "respawn",
        "boss fight", "multiplayer", "fps game", "co-op", "epic games", "riot games",
        "blizzard", "valve", "ea sports", "ubisoft", "sega", "capcom", "konami"
    }

    AI_TECH_KEYWORDS = {
        "ai", "artificial intelligence", "chatgpt", "openai", "gemini", "claude", "anthropic",
        "llm", "deep learning", "machine learning", "neural network", "robotics", "robot",
        "humanoid", "cybersecurity", "cyber", "hacker", "hacking", "malware", "code",
        "coding", "programmer", "programming", "software", "developer", "python", "algorithm",
        "hardware", "semiconductor", "microchip", "silicon", "gpu", "nvidia", "quantum computing",
        "supercomputer", "server room", "cloud computing", "datacenter", "api", "automation"
    }

    FINANCE_KEYWORDS = {
        "stock", "stocks", "wall street", "investor", "investing", "crypto", "cryptocurrency",
        "bitcoin", "btc", "ethereum", "eth", "solana", "trading", "trader", "fed", "federal reserve",
        "economy", "economic", "startup", "venture capital", "vc", "funding", "revenue",
        "profit", "valuation", "recession", "inflation", "banking", "bank", "fintech",
        "wealth", "hedge fund", "nasdaq", "dow jones", "s&p 500", "portfolio", "dividend",
        "dividend", "ipo", "monetization", "acquisition", "cash flow", "market cap"
    }

    CINEMA_KEYWORDS = {
        "movie", "film", "cinema", "hollywood", "actor", "actress", "box office", "netflix",
        "disney", "marvel", "mcu", "dc comics", "batman", "superman", "star wars", "trailer",
        "director", "oscar", "academy award", "soundtrack", "pop star", "concert", "billboard",
        "album", "recording studio", "producer", "tv show", "series", "screenplay"
    }

    FASHION_KEYWORDS = {
        "fashion", "outfit", "sneakers", "streetwear", "couture", "luxury", "aesthetic",
        "model", "runway", "skincare", "beauty", "cosmetics", "apparel", "designer",
        "drip", "wardrobe", "jewelry", "watches", "accessories", "styling", "vogue"
    }

    SCIENCE_KEYWORDS = {
        "space", "nasa", "planet", "astronomy", "galaxy", "mars", "moon", "physics",
        "quantum", "biology", "evolution", "history", "ancient", "archaeology", "ocean",
        "deep sea", "brain", "neuroscience", "universe", "telescope", "james webb"
    }

    NATURE_KEYWORDS = {
        "forest", "trees", "wildlife", "nature", "climate", "jungle", "ocean conservation",
        "gardening", "animals", "biodiversity", "safari", "national park", "plants", "botany",
        "rainforest", "woodland", "ecosystem", "ecology"
    }

    # 2. NEGATIVE REJECTION FILTERS BY DOMAIN
    # These terms represent irrelevant visual content that must NEVER appear for that domain.
    DOMAIN_NEGATIVE_TERMS: Dict[SemanticDomain, set] = {
        SemanticDomain.GAMING_ESPORTS: {
            "tree", "trees", "forest", "woodland", "plant", "plants", "nature", "leaves", "leaf",
            "foliage", "garden", "flower", "flowers", "meadow", "grass", "wilderness", "park",
            "mountain", "countryside", "agriculture", "farm", "crop", "hiking", "lake",
            "corporate boardroom", "handshake", "suit", "audit", "medical", "hospital", "clinic"
        },
        SemanticDomain.AI_TECH: {
            "tree", "trees", "forest", "woodland", "plant", "plants", "nature", "leaves", "leaf",
            "foliage", "garden", "flower", "flowers", "meadow", "farm", "cow", "horse", "wildlife"
        },
        SemanticDomain.BUSINESS_FINANCE: {
            "forest", "jungle", "wildlife", "flowers", "video game controller", "arcade", "playground"
        },
        SemanticDomain.ENTERTAINMENT_CINEMA: {
            "tree", "forest", "leaves", "wildlife", "farm", "garden", "plant", "agriculture"
        },
        SemanticDomain.LIFESTYLE_FASHION: {
            "tree", "forest", "hardware", "server rack", "motherboard", "code", "terminal"
        },
        SemanticDomain.CURIOSITY_SCIENCE: {
            "corporate boardroom", "handshake", "shopping mall", "fashion runway"
        },
        SemanticDomain.NATURE_ENVIRONMENT: set(),
        SemanticDomain.GENERAL: set(),
    }

    # 3. HIGH-AFFINITY B-ROLL TRANSMUTATION FOR GAMING
    # Stock photo sites (Unsplash/Pexels) have 0 results for "Fortnite warning" or trademarked games.
    # We transmute to concrete cinematic physical descriptions that stock photography banks actually possess.
    GAMING_BEAT_TRANSMUTATIONS = {
        "hook": [
            "cinematic neon rgb gaming setup battlestation",
            "cyberpunk glowing gaming controller in hands",
            "intense esports gamer focused at dark computer monitor",
            "futuristic gaming desk with purple led lighting",
        ],
        "tension": [
            "focused pro esports player at tournament tournament",
            "close up hands on mechanical rgb gaming keyboard",
            "dark neon esports gaming arena stage lights",
            "high tech gaming headset with microphone in dark studio",
        ],
        "revelation": [
            "futuristic virtual reality headset gamer cyber space",
            "high end liquid cooled gaming pc chassis internal lighting",
            "holographic cyber grid digital interface glow",
            "macro shot of mechanical gaming switches and rgb keys",
        ],
        "escalation": [
            "massive esports tournament arena stadium cheering crowd",
            "fast paced competitive gaming tournament stage screens",
            "pro gamer team communicating in headsets intense match",
            "cyberpunk arcade cabinet neon lights glowing",
        ],
        "deep_dive": [
            "dual curved ultra wide gaming monitors with glowing wallpaper",
            "minimalist dark gaming battlestation with neon ambient lighting",
            "cyberpunk hacker terminal neon data stream dark room",
            "gamer streaming room with led light bars and microphone",
        ],
        "twist": [
            "dramatic silhouette of gamer holding wireless controller",
            "cyberpunk neon city reflection on dark glass screen",
            "glowing neon gaming logo badge dark texture",
            "intense screen glare reflecting in esports gamer eyes",
        ],
        "payoff": [
            "esports tournament champion trophy celebration stage",
            "cinematic neon purple gaming battlestation clean aesthetic",
            "excited pro gamer victory celebration at tournament",
            "futuristic golden trophy cup under arena spotlights",
        ],
        "cta": [
            "content creator streaming studio with neon light and professional mic",
            "sleek minimalist dark gamer setup clean aesthetic",
            "cyberpunk glowing neon sign dark wall studio",
            "modern gaming room with dual monitors and led backlight",
        ],
    }

    # Quick selection chips for the Frontend StockPickerModal
    DOMAIN_UI_SUGGESTIONS: Dict[SemanticDomain, List[Dict[str, str]]] = {
        SemanticDomain.GAMING_ESPORTS: [
            {"label": "RGB Battlestation", "query": "rgb gaming setup neon battlestation", "icon": "🎮"},
            {"label": "Cyber Controller", "query": "cyberpunk gaming controller neon glow", "icon": "🕹️"},
            {"label": "Esports Streamer", "query": "gamer streaming headset neon studio", "icon": "🎧"},
            {"label": "Esports Arena", "query": "esports tournament arena crowd", "icon": "🏟️"},
            {"label": "VR Cyberspace", "query": "virtual reality gamer headset cyber", "icon": "🥽"},
            {"label": "Mechanical RGB", "query": "mechanical gaming keyboard rgb macro", "icon": "⌨️"},
        ],
        SemanticDomain.AI_TECH: [
            {"label": "Neural Network", "query": "futuristic neural network data server", "icon": "🧠"},
            {"label": "Cyber Terminal", "query": "cyberpunk dark code screen terminal", "icon": "💻"},
            {"label": "AI Robotics", "query": "futuristic humanoid robot technology", "icon": "🤖"},
            {"label": "Server Datacenter", "query": "modern blue led server racks datacenter", "icon": "🏢"},
            {"label": "Quantum Microchip", "query": "macro glowing semiconductor processor", "icon": "⚡"},
        ],
        SemanticDomain.BUSINESS_FINANCE: [
            {"label": "Market Charts", "query": "financial trading charts screen dark", "icon": "📈"},
            {"label": "Crypto Currency", "query": "golden bitcoin cryptocurrency dark neon", "icon": "🪙"},
            {"label": "Executive Summit", "query": "modern skyline financial district", "icon": "🏙️"},
            {"label": "Venture Startup", "query": "modern tech startup collaboration desk", "icon": "🚀"},
        ],
        SemanticDomain.ENTERTAINMENT_CINEMA: [
            {"label": "Cinema Spotlight", "query": "cinematic movie theater projector beam", "icon": "🎬"},
            {"label": "Concert Stage", "query": "concert stage lights performance crowd", "icon": "🎤"},
            {"label": "Film Camera", "query": "cinematographer 35mm film camera rig", "icon": "🎥"},
            {"label": "Red Carpet", "query": "hollywood red carpet premiere spotlights", "icon": "✨"},
        ],
        SemanticDomain.LIFESTYLE_FASHION: [
            {"label": "Cyber Streetwear", "query": "futuristic cyberpunk streetwear model", "icon": "👟"},
            {"label": "Fashion Runway", "query": "high fashion runway couture model", "icon": "👗"},
            {"label": "Luxury Aesthetic", "query": "luxury perfume aesthetic minimal", "icon": "💎"},
            {"label": "Urban Lifestyle", "query": "cinematic urban streetwear golden hour", "icon": "🏙️"},
        ],
    }

    def classify_topic_domain(
        self,
        topic: str,
        context: Optional[str] = None,
        worker_id: Optional[str] = None,
    ) -> SemanticDomain:
        """Classifies any trend title, summary, or worker context into a primary visual domain."""
        combined_text = f"{topic or ''} {context or ''}".lower()
        tokens = set(re.findall(r"\b[a-z0-9\-_]{2,}\b", combined_text))

        # 1. Exact match on gaming entities (highest precision)
        if any(g in combined_text for g in self.GAMING_KEYWORDS):
            return SemanticDomain.GAMING_ESPORTS

        # 2. Worker Niche Hint: Culture Loop (entertainment) + gaming hints
        if worker_id and worker_id.lower() in ("entertainment", "culture"):
            if any(t in tokens for t in {"game", "games", "gaming", "play", "player", "stream", "streamer", "console", "skin", "battle", "royale", "vbucks", "patch"}):
                return SemanticDomain.GAMING_ESPORTS

        # 3. AI / Tech check
        if any(t in combined_text for t in self.AI_TECH_KEYWORDS):
            return SemanticDomain.AI_TECH

        # 4. Finance / Business check
        if any(f in combined_text for f in self.FINANCE_KEYWORDS):
            return SemanticDomain.BUSINESS_FINANCE

        # 5. Cinema / Entertainment
        if any(c in combined_text for c in self.CINEMA_KEYWORDS):
            return SemanticDomain.ENTERTAINMENT_CINEMA

        # 6. Fashion / Lifestyle
        if any(fa in combined_text for fa in self.FASHION_KEYWORDS):
            return SemanticDomain.LIFESTYLE_FASHION

        # 7. Science / Curiosity
        if any(s in combined_text for s in self.SCIENCE_KEYWORDS):
            return SemanticDomain.CURIOSITY_SCIENCE

        # 8. Nature check
        if any(n in combined_text for n in self.NATURE_KEYWORDS):
            return SemanticDomain.NATURE_ENVIRONMENT

        # Fallback to worker niche
        if worker_id:
            w_norm = worker_id.lower()
            if w_norm in ("tech", "technology"):
                return SemanticDomain.AI_TECH
            elif w_norm in ("business", "finance"):
                return SemanticDomain.BUSINESS_FINANCE
            elif w_norm in ("entertainment", "culture"):
                return SemanticDomain.ENTERTAINMENT_CINEMA
            elif w_norm in ("lifestyle", "fashion"):
                return SemanticDomain.LIFESTYLE_FASHION
            elif w_norm in ("curiosity", "education"):
                return SemanticDomain.CURIOSITY_SCIENCE

        return SemanticDomain.GENERAL

    def transmute_search_queries(
        self,
        domain: SemanticDomain,
        scene_beat: str,
        original_keywords: List[str],
        scene_idx: int = 0,
    ) -> List[str]:
        """Transmutes abstract or brand-locked queries into concrete, high-affinity visual queries
        that stock photography libraries (Unsplash, Pexels) successfully return."""
        clean_kws = [k.replace('"', '').replace("'", '').replace("#", "").strip() for k in original_keywords if len(k.strip()) > 1]
        
        # If domain is GAMING_ESPORTS, brand names like 'fortnite' cannot be queried directly
        if domain == SemanticDomain.GAMING_ESPORTS:
            beat_transmutes = self.GAMING_BEAT_TRANSMUTATIONS.get(
                scene_beat.lower(),
                self.GAMING_BEAT_TRANSMUTATIONS["hook"]
            )
            # Pick primary transmutation based on scene beat & index
            primary_transmuted = beat_transmutes[scene_idx % len(beat_transmutes)]
            
            # Combine with safe sub-intent from clean_kws if present
            sub_candidates = [primary_transmuted]
            for kw in clean_kws:
                kw_low = kw.lower()
                # If keyword has specific gaming intent like 'controller', 'headset', 'tournament', 'neon'
                if any(w in kw_low for w in ("controller", "headset", "keyboard", "arena", "stream", "pc", "neon", "battle")):
                    sub_candidates.append(f"gaming {kw}")
                elif not any(b in kw_low for b in ("fortnite", "warning", "compliance", "boardroom", "ledger", "sky", "view")):
                    sub_candidates.append(f"gaming setup {kw}")

            # Add fallback beat transmutation
            sub_candidates.append(beat_transmutes[(scene_idx + 1) % len(beat_transmutes)])
            return sub_candidates

        # For AI / Tech:
        elif domain == SemanticDomain.AI_TECH:
            tech_candidates = []
            for kw in clean_kws:
                kw_low = kw.lower()
                if not any(neg in kw_low for kw in ("tree", "nature", "foliage", "farm")):
                    tech_candidates.append(f"high tech {kw}")
            tech_candidates.extend([
                "futuristic blue neon server room",
                "cyberpunk coding data screen",
                "modern artificial intelligence lab",
            ])
            return tech_candidates

        # For Business:
        elif domain == SemanticDomain.BUSINESS_FINANCE:
            fin_candidates = []
            for kw in clean_kws:
                fin_candidates.append(f"business finance {kw}")
            fin_candidates.extend([
                "stock market trading terminal dark",
                "modern financial skyscraper architecture",
                "fintech crypto digital dashboard",
            ])
            return fin_candidates

        # Default fallback: preserve clean original keywords
        return clean_kws or ["cinematic 4k vertical aesthetic"]

    def validate_photo_relevance(
        self,
        domain: SemanticDomain,
        photo_meta: Dict[str, Any],
        query: str,
    ) -> Tuple[bool, float, str]:
        """Validates an Unsplash or Commons photo item against domain rules and negative filters.
        Returns (is_valid, relevance_score, reason).
        Directly detects and rejects nature/tree photos for gaming topics."""
        # Extract all textual tags and descriptions from the stock metadata
        tags = [t.get("title", "").lower() for t in photo_meta.get("tags", []) if isinstance(t, dict)]
        alt_desc = (photo_meta.get("alt_description") or "").lower()
        desc = (photo_meta.get("description") or "").lower()
        title = (photo_meta.get("title") or "").lower()

        combined_text = f"{alt_desc} {desc} {title} {' '.join(tags)}".lower()
        photo_tokens = set(re.findall(r"\b[a-z]{3,}\b", combined_text))

        # 1. CHECK NEGATIVE FILTERS FOR THIS DOMAIN
        negative_set = self.DOMAIN_NEGATIVE_TERMS.get(domain, set())
        for neg in negative_set:
            if neg in photo_tokens or neg in combined_text:
                logger.warning(
                    "Rejecting stock photo '%s' for domain '%s' — matched negative filter '%s' in metadata: %s",
                    photo_meta.get("id"), domain.value, neg, alt_desc or desc
                )
                return False, 0.0, f"Rejected: matched negative domain term '{neg}'"

        # 2. DOMAIN POSITIVE AFFINITY SCORING
        score = 0.5  # Base neutral score
        if domain == SemanticDomain.GAMING_ESPORTS:
            gaming_anchors = {"gaming", "game", "gamer", "esports", "controller", "headset", "keyboard", "neon", "pc", "console", "rig", "screen", "rgb"}
            match_count = len(photo_tokens.intersection(gaming_anchors))
            if match_count >= 2:
                score = 0.95
            elif match_count == 1:
                score = 0.80
            else:
                # If neither the photo description nor tags mention gaming/controller/neon/screen,
                # check if it's completely generic
                if any(w in combined_text for w in ("computer", "electronics", "technology", "display")):
                    score = 0.65
                else:
                    return False, 0.2, "Rejected: lacks gaming visual anchors"

        elif domain == SemanticDomain.AI_TECH:
            tech_anchors = {"server", "code", "coding", "software", "screen", "terminal", "cyber", "robot", "robotics", "data", "circuit", "hardware"}
            match_count = len(photo_tokens.intersection(tech_anchors))
            if match_count >= 1:
                score = 0.90
            else:
                score = 0.60

        return True, score, "Photo relevance verified"

    def get_ui_suggestions(self, domain: SemanticDomain) -> List[Dict[str, str]]:
        """Returns rapid-select visual chips for the frontend scene editor."""
        return self.DOMAIN_UI_SUGGESTIONS.get(domain, self.DOMAIN_UI_SUGGESTIONS[SemanticDomain.GAMING_ESPORTS])


visual_intelligence = VisualIntelligenceService()

