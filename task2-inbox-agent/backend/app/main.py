"""Intelligent Inbox Agent FastAPI Application."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routes import router as inbox_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("inbox_agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("Initializing Inbox Agent database...")
    try:
        await init_db()
        logger.info("Inbox Agent database ready.")
    except Exception as e:
        logger.error(f"Inbox Agent db init error: {e}", exc_info=True)

    yield

    logger.info("Inbox Agent shutting down...")


app = FastAPI(
    title="AI Tech Consultant - Intelligent Inbox Agent",
    description="Email classification, grounded draft generation, and human-in-the-loop review interface.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inbox_router)

# Mount frontend UI if built
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/")
    async def index_redirect():
        return FileResponse(str(frontend_dist / "index.html"))

    @app.get("/ui")
    async def ui_page():
        return FileResponse(str(frontend_dist / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
