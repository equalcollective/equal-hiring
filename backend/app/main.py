"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import init_db
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: (add cleanup if needed)


app = FastAPI(
    title="X-Ray API",
    description="Decision Observability API for Multi-Step Algorithmic Systems",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "X-Ray API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "ingest": "/ingest",
            "analyze": "/analyze/{run_id}",
            "runs": "/runs",
        },
    }
