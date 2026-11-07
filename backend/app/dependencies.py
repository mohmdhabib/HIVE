from fastapi import Depends
from app.config import Settings, get_settings
from app.services.llm import LLMService

_llm_service: LLMService | None = None

def get_llm_service(settings: Settings = Depends(get_settings)) -> LLMService:
    global _llm_service
    if _llm_service is None:
        s = settings if isinstance(settings, Settings) else get_settings()
        _llm_service = LLMService(s)
    return _llm_service
