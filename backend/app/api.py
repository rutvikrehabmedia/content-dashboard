from typing import List, Dict, Optional
from sqlmodel import SQLModel


class SearchRequest(SQLModel):
    """Search request model."""

    query: str
    whitelist: List[str] = []
    blacklist: List[str] = []
    process_id: Optional[str] = None


class SearchResponse(SQLModel):
    """Search response model."""

    results: List[Dict]
    process_id: str
    total_results: int = 0
    scraped_results: int = 0


class ListResponse(SQLModel):
    """Response model for list operations."""

    urls: List[str]


class UpdateListRequest(SQLModel):
    """Request model for updating lists."""

    urls: List[str]


class BatchRequest(SQLModel):
    """Batch request model."""

    queries: List[str]
    whitelist: List[str] = []
    blacklist: List[str] = []
