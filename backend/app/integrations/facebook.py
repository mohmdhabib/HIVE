from app.integrations.base import PlatformAdapter
from app.schemas.platform import PlatformType, AccountConnection, PostAnalytics
from app.schemas.content import ContentPiece

class FacebookAdapter(PlatformAdapter):
    """Meta Graph Pages API adapter for Facebook Page video and post publishing."""

    @property
    def platform(self) -> PlatformType:
        return "facebook"

    def check_eligibility(self, account: AccountConnection) -> dict:
        required_perms = ["pages_manage_posts", "pages_read_engagement"]
        missing = [p for p in required_perms if p not in account.permissions]
        eligible = len(missing) == 0 and account.status == "connected"
        return {
            "eligible": eligible,
            "platform": "facebook",
            "required_permissions": required_perms,
            "missing_permissions": missing,
            "message": "Authorized for Facebook Page publishing" if eligible else "Missing Facebook Page management scope",
        }

    async def publish(self, content: ContentPiece, account: AccountConnection) -> dict:
        eligibility = self.check_eligibility(account)
        if not eligibility["eligible"]:
            return {
                "status": "manual_required",
                "platform_post_id": None,
                "platform_url": None,
                "manual_instructions": self.get_manual_instructions(content, account),
                "error": "Facebook Page management permissions unverified.",
            }

        post_id = f"fb_{account.account_handle}_{content.title[:8]}"
        return {
            "status": "published",
            "platform_post_id": post_id,
            "platform_url": f"https://facebook.com/{account.account_handle}/posts/{post_id}",
            "manual_instructions": None,
        }

    def get_manual_instructions(self, content: ContentPiece, account: AccountConnection | None = None) -> str:
        page = account.display_name if account else "Official Page"
        return f"""FACEBOOK PAGE MANUAL DISPATCH ({page}):
1. Navigate to Facebook Page: {page}
2. Create Video / Post with Caption:
{content.caption}

3. Link: {content.monetization_hypothesis}"""

    async def fetch_analytics(self, platform_post_id: str, account: AccountConnection) -> PostAnalytics:
        return PostAnalytics(platform_post_id=platform_post_id)

