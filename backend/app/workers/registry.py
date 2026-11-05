from app.schemas.worker import WorkerConfig, WorkerRevenueTarget

WORKERS: dict[str, WorkerConfig] = {
    "tech": WorkerConfig(
        id="tech",
        name="Signal Tech",
        niche="AI and technology",
        audience="Curious professionals, developers, and builders",
        voice="Clear, useful, curious, evidence-led, technical yet accessible",
        objective="Grow a trusted AI and technology audience monetized through dev tool sponsorships and SaaS affiliate referrals",
        content_pillars=["LLM breakthroughs", "Developer tools", "AI productivity workflows", "Hardware benchmarks"],
        revenue_target=WorkerRevenueTarget(
            monthly_target_usd=2500.0,
            primary_stream="affiliate",
            target_rpm=22.0
        ),
    ),
    "business": WorkerConfig(
        id="business",
        name="Founder Brief",
        niche="Business and startups",
        audience="Founders, operators, and aspiring entrepreneurs",
        voice="Practical, analytical, direct, metrics-focused, anti-fluff",
        objective="Build an engaged audience around venture creation, B2B playbooks, and business breakdowns",
        content_pillars=["Unit economics", "Bootstrapping stories", "B2B sales tactics", "Pricing teardowns"],
        revenue_target=WorkerRevenueTarget(
            monthly_target_usd=3000.0,
            primary_stream="sponsorships",
            target_rpm=28.0
        ),
    ),
    "entertainment": WorkerConfig(
        id="entertainment",
        name="Culture Loop",
        niche="Entertainment",
        audience="Pop-culture fans, movie/gaming enthusiasts, and internet culture trackers",
        voice="Energetic, concise, playful, punchy, visually descriptive",
        objective="Create high-velocity short-form entertainment formats that drive viral reach and platform creator rewards",
        content_pillars=["Film breakdown", "Gaming lore", "Streaming highlights", "Cultural moments"],
        revenue_target=WorkerRevenueTarget(
            monthly_target_usd=1500.0,
            primary_stream="digital_products",
            target_rpm=12.0
        ),
    ),
    "education": WorkerConfig(
        id="education",
        name="Curiosity Daily",
        niche="Education and facts",
        audience="Lifelong learners, students, and curious generalists",
        voice="Simple, engaging, impeccably accurate, wonder-driven",
        objective="Make complex scientific, historical, and economic facts intuitive and memorable",
        content_pillars=["Science explained", "History deep dives", "Cognitive psychology", "Everyday economics"],
        revenue_target=WorkerRevenueTarget(
            monthly_target_usd=1800.0,
            primary_stream="affiliate",
            target_rpm=16.0
        ),
    ),
    "lifestyle": WorkerConfig(
        id="lifestyle",
        name="Everyday Edit",
        niche="Lifestyle and trends",
        audience="Urban professionals and young adults interested in intentional living and smart consumer choices",
        voice="Approachable, modern, aesthetic, candid, quality-focused",
        objective="Curate practical trends, workspace setups, and mindful habits with transparent affiliate monetization",
        content_pillars=["Desk setups", "Minimalist gear", "Daily routines", "Habit optimization"],
        revenue_target=WorkerRevenueTarget(
            monthly_target_usd=2200.0,
            primary_stream="affiliate",
            target_rpm=20.0
        ),
    ),
}

def list_workers() -> list[WorkerConfig]:
    return list(WORKERS.values())

def get_worker(worker_id: str) -> WorkerConfig:
    worker = WORKERS.get(worker_id)
    if not worker:
        raise KeyError(worker_id)
    return worker
