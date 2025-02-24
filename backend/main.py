import sys
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import os

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import router as api_router
from app.db import db
from app.services.search import process_search_results

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        # Console handler
        logging.StreamHandler(),
        # File handler
        RotatingFileHandler(
            logs_dir / "app.log",
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding="utf-8",
        ),
    ],
)

logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_db_client():
    """Initialize MongoDB connection on startup."""
    try:
        # Initialize MongoDB
        await db.connect()

        # Test connection
        stats = await db.get_db_stats()
        print("MongoDB connected successfully:", stats)

    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)


@app.on_event("shutdown")
async def shutdown_db_client():
    """Close MongoDB connection on shutdown."""
    await db.close()


# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        stats = await db.get_db_stats()
        return {
            "status": "healthy",
            "database": "connected",
            "stats": stats,
            "version": settings.VERSION,
        }
    except Exception as e:
        return {"status": "unhealthy", "database": str(e), "version": settings.VERSION}


@app.get("/")
async def root():
    return {
        "message": "Welcome to Search and Scraping API",
        "version": settings.VERSION,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["app"])
