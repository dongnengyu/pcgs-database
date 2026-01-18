"""FastAPI application entry point"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import init_db
from .routers import coins
from .routers import tasks
from .scheduler import scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events"""
    # Startup
    logger.info("Starting PCGS Coin Database...")
    init_db()

    # Start task scheduler
    await scheduler.start()

    yield

    # Shutdown
    await scheduler.stop()
    logger.info("Shutting down PCGS Coin Database...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title="PCGS Coin Database",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Mount static files for images (data/images)
    app.mount(
        "/data/images",
        StaticFiles(directory=str(settings.IMAGES_DIR)),
        name="images",
    )

    # Mount static files (CSS, JS)
    app.mount(
        "/static",
        StaticFiles(directory=str(settings.STATIC_DIR)),
        name="static",
    )

    # Include routers
    app.include_router(coins.router)
    app.include_router(tasks.router)

    @app.get("/")
    async def index() -> FileResponse:
        """Serve the frontend page"""
        return FileResponse(str(settings.STATIC_DIR / "index.html"))

    @app.get("/tasks")
    async def tasks_page() -> FileResponse:
        """Serve the tasks management page"""
        return FileResponse(str(settings.STATIC_DIR / "tasks.html"))

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.pcgs_database.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
