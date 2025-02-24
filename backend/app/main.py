from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import router as api_router
from app.db import db
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    """Initialize MongoDB connection on startup"""
    try:
        await db.connect()
        logger.info("MongoDB initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Don't exit, allow for retries

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connections"""
    await db.close()

app.include_router(api_router, prefix="/api")