from app.integrations.base import PlatformAdapter
from app.schemas.platform import PlatformType, AccountConnection, PostAnalytics
from app.schemas.content import ContentPiece

class ManualPublishingAdapter(PlatformAdapter):
    """Sanctioned fallback workflow when platform API credentials are not yet authorized."""

    @property
    def platform(self) -> PlatformType:
        return "manual"

    def check_eligibility(self, account: AccountConnection) -> dict:
        return {
            "eligible": True,
            "mode": "manual",
            "message": "Manual publishing is always available as a verified safe fallback.",
        }

    async def publish(self, content: ContentPiece, account: AccountConnection) -> dict:
        # Never fake success: mark as manual_required with clear directions
        instructions = self.get_manual_instructions(content, account)
        return {
            "status": "manual_required",
            "platform_post_id": None,
            "platform_url": None,
            "manual_instructions": instructions,
        }

    def get_manual_instructions(self, content: ContentPiece, account: AccountConnection | None = None) -> str:
        handle = account.account_handle if account else "Official Account"
        hashtags_str = " ".join([f"#{t}" for t in content.hashtags]) if content.hashtags else ""
        return f"""MANUAL PUBLISHING DISPATCH:
Target Account: {handle} ({content.target_platform.upper()})
Title: {content.title}

1. Visual Asset:
   {content.visual_brief}

2. Retention Hook (Text Overlay / Opening 3s):
   "{content.hook}"

3. Caption (Copy & Paste):
--------------------------------------------------
{content.caption}

{hashtags_str}
--------------------------------------------------

4. Monetization Directive:
   Ensure affiliate or bio link is verified: {content.monetization_hypothesis}

5. Factual Caution:
   Double-check: {', '.join(content.factual_checks) if content.factual_checks else 'None flagged.'}"""

    async def fetch_analytics(self, platform_post_id: str, account: AccountConnection) -> PostAnalytics:
        return PostAnalytics(platform_post_id=platform_post_id or "manual-post")

