from abc import ABC, abstractmethod
from app.schemas.platform import PlatformType, AccountConnection, PostAnalytics
from app.schemas.content import ContentPiece

class PlatformAdapter(ABC):
    """Abstract Base Class for social media platform integrations."""

    @property
    @abstractmethod
    def platform(self) -> PlatformType:
        pass

    @abstractmethod
    def check_eligibility(self, account: AccountConnection) -> dict:
        """Verify API permission scopes and eligibility for the account."""
        pass

    @abstractmethod
    async def publish(self, content: ContentPiece, account: AccountConnection) -> dict:
        """Publish content via official platform API. Returns platform post id and URL."""
        pass

    @abstractmethod
    def get_manual_instructions(self, content: ContentPiece, account: AccountConnection | None = None) -> str:
        """Provide detailed, copy-paste manual publishing instructions if API is unconfigured or restricted."""
        pass

    @abstractmethod
    async def fetch_analytics(self, platform_post_id: str, account: AccountConnection) -> PostAnalytics:
        """Fetch verified platform performance metrics."""
        pass

