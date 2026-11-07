import pytest
from app.services.visual_intelligence import visual_intelligence, SemanticDomain
from app.services.material_service import material_service


def test_domain_classification_for_gaming():
    # Test popular gaming entities
    for topic in ["fortnite", "Roblox update", "GTA 6 trailer", "Minecraft speedrun", "Apex Legends patch", "esports championship"]:
        domain = visual_intelligence.classify_topic_domain(topic, worker_id="entertainment")
        assert domain == SemanticDomain.GAMING_ESPORTS, f"Failed for topic: {topic}"


def test_domain_classification_for_tech():
    for topic in ["ChatGPT 5 launch", "Quantum computing breakthrough", "NVIDIA AI chip", "Cybersecurity zero-day exploit"]:
        domain = visual_intelligence.classify_topic_domain(topic, worker_id="tech")
        assert domain == SemanticDomain.AI_TECH, f"Failed for topic: {topic}"


def test_domain_classification_for_finance():
    for topic in ["Federal reserve interest rate cut", "Bitcoin crosses 100k", "Wall Street tech stocks rally", "Startup seed funding"]:
        domain = visual_intelligence.classify_topic_domain(topic, worker_id="business")
        assert domain == SemanticDomain.BUSINESS_FINANCE, f"Failed for topic: {topic}"


def test_query_transmutation_for_gaming():
    domain = SemanticDomain.GAMING_ESPORTS
    queries = visual_intelligence.transmute_search_queries(
        domain=domain,
        scene_beat="hook",
        original_keywords=["fortnite warning", "legal compliance", "dark boardroom"],
        scene_idx=0,
    )
    assert len(queries) > 0
    # None of the transmuted queries should contain forbidden corporate/nature terms
    for q in queries:
        assert "boardroom" not in q.lower()
        assert "compliance" not in q.lower()
    # At least one query must contain high-affinity gaming terms
    assert any("gaming" in q.lower() or "controller" in q.lower() or "battlestation" in q.lower() for q in queries)


def test_negative_photo_rejection_for_gaming():
    domain = SemanticDomain.GAMING_ESPORTS

    # Tree image test
    tree_meta = {
        "id": "tree_photo_01",
        "alt_description": "A tall pine tree in the green forest outdoors",
        "tags": [{"title": "nature"}, {"title": "forest"}, {"title": "tree"}],
    }
    is_valid, score, reason = visual_intelligence.validate_photo_relevance(domain, tree_meta, "fortnite")
    assert not is_valid
    assert score == 0.0
    assert "negative domain term" in reason

    # Flower / plant test
    flower_meta = {
        "id": "flower_photo_02",
        "alt_description": "Botanical garden with blooming flowers and plants",
        "tags": [{"title": "botany"}, {"title": "plant"}, {"title": "garden"}],
    }
    is_valid_f, _, _ = visual_intelligence.validate_photo_relevance(domain, flower_meta, "fortnite")
    assert not is_valid_f

    # Valid Gaming photo
    gaming_meta = {
        "id": "gaming_photo_03",
        "alt_description": "Neon RGB gaming PC setup with illuminated mechanical keyboard and headset",
        "tags": [{"title": "gaming"}, {"title": "esports"}, {"title": "keyboard"}, {"title": "neon"}],
    }
    is_valid_g, score_g, _ = visual_intelligence.validate_photo_relevance(domain, gaming_meta, "fortnite")
    assert is_valid_g
    assert score_g >= 0.8


def test_local_stock_matching_guarantees_gaming_asset():
    # When querying for fortnite with the entertainment worker, local matching must pick a gaming asset
    chosen, asset_type = material_service.find_best_local_stock_asset(
        keywords=["fortnite warning", "cybersecurity hazard alert"],
        worker_id="entertainment",
        scene_idx=0,
    )
    assert "gaming" in chosen.lower(), f"Expected gaming stock photo, got {chosen}"
    assert asset_type == "image"


def test_ui_suggestions_for_domains():
    gaming_sug = visual_intelligence.get_ui_suggestions(SemanticDomain.GAMING_ESPORTS)
    assert len(gaming_sug) >= 4
    assert any("Battlestation" in s["label"] for s in gaming_sug)

    tech_sug = visual_intelligence.get_ui_suggestions(SemanticDomain.AI_TECH)
    assert len(tech_sug) >= 3
    assert any("Neural" in s["label"] or "Terminal" in s["label"] for s in tech_sug)

