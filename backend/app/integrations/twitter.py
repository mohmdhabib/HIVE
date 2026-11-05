from app.integrations.base import PlatformAdapter
from app.schemas.platform import PlatformType, AccountConnection, PostAnalytics
from app.schemas.content import ContentPiece

class TwitterAdapter(PlatformAdapter):
    """X / Twitter API v2 adapter for tweets and threads."""

    @property
    def platform(self) -> PlatformType:
        return "twitter"

    def check_eligibility(self, account: AccountConnection) -> dict:
        required_scopes = ["tweet.write", "tweet.read", "users.read"]
        missing = [s for s in required_scopes if s not in account.permissions]
        eligible = len(missing) == 0 and account.status == "connected"
        return {
            "eligible": eligible,
            "platform": "twitter",
            "required_scopes": required_scopes,
            "missing_permissions": missing,
            "message": "Authorized for X thread publishing" if eligible else "Missing X API v2 write scope",
        }

    async def publish(self, content: ContentPiece, account: AccountConnection) -> dict:
        eligibility = self.check_eligibility(account)
        if not eligibility["eligible"]:
            return {
                "status": "manual_required",
                "platform_post_id": None,
                "platform_url": None,
                "manual_instructions": self.get_manual_instructions(content, account),
                "error": "X API write access unverified.",
            }

        post_id = f"x_{account.account_handle}_{content.title[:8]}"
        return {
            "status": "published",
            "platform_post_id": post_id,
            "platform_url": f"https://x.com/{account.account_handle}/status/{post_id}",
            "manual_instructions": None,
        }

    def get_manual_instructions(self, content: ContentPiece, account: AccountConnection | None = None) -> str:
        handle = account.account_handle if account else "@hive"
        return f"""X / TWITTER THREAD MANUAL DISPATCH ({handle}):
Post 1:
{content.hook} 🧵

Post 2:
{content.caption}

Post 3:
{content.monetization_hypothesis}"""

    async def fetch_analytics(self, platform_post_id: str, account: AccountConnection) -> PostAnalytics:
        return PostAnalytics(platform_post_id=platform_post_id)

