from fastapi import Depends
from app.config import Settings, get_settings
from app.services.llm import LLMService

_llm_service: LLMService | None = None

def get_llm_service(settings: Settings = Depends(get_settings)) -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(settings)
    return _llm_service
