from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    app_name: str = "HIVE Agent Network"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Ollama
    ollama_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3.1"
    ollama_timeout: float = 180.0
    ollama_max_concurrent: int = 2
    
    # Supabase (optional for now)
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    
    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]
    
    # Security
    global_kill_switch: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

@lru_cache
def get_settings() -> Settings:
    return Settings()
