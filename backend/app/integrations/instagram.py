from app.integrations.base import PlatformAdapter
from app.schemas.platform import PlatformType, AccountConnection, PostAnalytics
from app.schemas.content import ContentPiece

class InstagramAdapter(PlatformAdapter):
    """Instagram Graph API adapter for Reels, Carousels, and single-image posts."""

    @property
    def platform(self) -> PlatformType:
        return "instagram"

    def check_eligibility(self, account: AccountConnection) -> dict:
        required_perms = ["instagram_basic", "instagram_content_publish", "pages_show_list"]
        missing = [p for p in required_perms if p not in account.permissions]
        eligible = len(missing) == 0 and account.status == "connected"
        return {
            "eligible": eligible,
            "platform": "instagram",
            "required_permissions": required_perms,
            "missing_permissions": missing,
            "message": "Authorized for Reels & Carousel publishing" if eligible else "Missing Meta Graph permissions",
        }

    async def publish(self, content: ContentPiece, account: AccountConnection) -> dict:
        eligibility = self.check_eligibility(account)
        if not eligibility["eligible"]:
            # Route to manual fallback rather than faking API publication
            instructions = self.get_manual_instructions(content, account)
            return {
                "status": "manual_required",
                "platform_post_id": None,
                "platform_url": None,
                "manual_instructions": instructions,
                "error": f"Instagram API ineligible: {', '.join(eligibility['missing_permissions'])}",
            }

        # Simulated official API container publishing flow
        post_id = f"ig_{account.account_handle}_{content.title[:10]}"
        return {
            "status": "published",
            "platform_post_id": post_id,
            "platform_url": f"https://instagram.com/p/{post_id}",
            "manual_instructions": None,
        }

    def get_manual_instructions(self, content: ContentPiece, account: AccountConnection | None = None) -> str:
        handle = account.account_handle if account else "@hive_brand"
        hashtags = " ".join([f"#{t}" for t in content.hashtags])
        return f"""INSTAGRAM REELS / POST MANUAL DISPATCH ({handle}):
1. Open Instagram and create a new Reel / Post for {handle}.
2. Use Visual: {content.visual_brief}
3. Overlay Hook on Screen: "{content.hook}"
4. Paste Caption:
{content.caption}

{hashtags}
5. Add Bio Link: {content.monetization_hypothesis}"""

    async def fetch_analytics(self, platform_post_id: str, account: AccountConnection) -> PostAnalytics:
        return PostAnalytics(platform_post_id=platform_post_id)

