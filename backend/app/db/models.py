import logging

logger = logging.getLogger(__name__)

async def init_db():
    """Initialize the database"""
    # This function is now empty as the database is no longer initialized
    pass

async def get_db():
    """Get database session"""
    # This function is now empty as the database session is no longer available
    raise HTTPException(
        status_code=500,
        detail="Database connection not available"
    ) 