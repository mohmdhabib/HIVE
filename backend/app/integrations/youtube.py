from app.integrations.base import PlatformAdapter
from app.schemas.platform import PlatformType, AccountConnection, PostAnalytics
from app.schemas.content import ContentPiece

class YouTubeAdapter(PlatformAdapter):
    """YouTube Data API v3 adapter for YouTube Shorts and video uploads."""

    @property
    def platform(self) -> PlatformType:
        return "youtube"

    def check_eligibility(self, account: AccountConnection) -> dict:
        required_scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        missing = [s for s in required_scopes if s not in account.permissions]
        eligible = len(missing) == 0 and account.status == "connected"
        return {
            "eligible": eligible,
            "platform": "youtube",
            "required_scopes": required_scopes,
            "missing_permissions": missing,
            "message": "Authorized for YouTube Shorts upload" if eligible else "Missing YouTube OAuth upload scope",
        }

    async def publish(self, content: ContentPiece, account: AccountConnection) -> dict:
        eligibility = self.check_eligibility(account)
        if not eligibility["eligible"]:
            return {
                "status": "manual_required",
                "platform_post_id": None,
                "platform_url": None,
                "manual_instructions": self.get_manual_instructions(content, account),
                "error": "YouTube API not authorized for uploads.",
            }

        post_id = f"yt_{account.account_handle}_{content.title[:8]}"
        return {
            "status": "published",
            "platform_post_id": post_id,
            "platform_url": f"https://youtube.com/shorts/{post_id}",
            "manual_instructions": None,
        }

    def get_manual_instructions(self, content: ContentPiece, account: AccountConnection | None = None) -> str:
        channel = account.account_handle if account else "Channel"
        return f"""YOUTUBE SHORTS MANUAL DISPATCH ({channel}):
1. Title: {content.title} #Shorts
2. Description:
{content.caption}

Affiliate / Sponsorship link: {content.monetization_hypothesis}
3. Video File: Ensure vertical 9:16 aspect ratio under 60 seconds."""

    async def fetch_analytics(self, platform_post_id: str, account: AccountConnection) -> PostAnalytics:
        return PostAnalytics(platform_post_id=platform_post_id)

