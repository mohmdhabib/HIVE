import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.config import get_settings
from app.core.logging import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = setup_logging()
    settings = get_settings()
    logger.info("HIVE API starting (version=%s, model=%s)", settings.app_version, settings.ollama_model)
    yield
    logger.info("HIVE API shutting down")

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

# Mount local media storage for direct browser video and thumbnail playback
storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
if not os.path.exists(storage_dir):
    storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage"))
if not os.path.exists(storage_dir) and os.path.exists("/app/storage"):
    storage_dir = "/app/storage"
if os.path.exists(storage_dir):
    app.mount("/storage", StaticFiles(directory=storage_dir), name="storage")
    app.mount("/api/storage", StaticFiles(directory=storage_dir), name="api_storage")

