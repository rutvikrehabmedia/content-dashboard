from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class LogType(str, Enum):
    SEARCH = "search"
    SCRAPE = "scrape"


class LogStatus(str, Enum):
    STARTED = "started"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"


class BaseLog(BaseModel):
    process_id: str = Field(..., description="Unique identifier for the process")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: LogStatus
    error: Optional[str] = None
    metadata: Optional[Dict] = None


class SearchLog(BaseLog):
    query: str
    results: Optional[List[Dict]] = None
    type: LogType = LogType.SEARCH
    parent_process_id: Optional[str] = None  # For bulk search child processes
    whitelist: Optional[List[str]] = None
    blacklist: Optional[List[str]] = None


class ScrapeLog(BaseLog):
    urls: List[str]
    type: LogType = LogType.SCRAPE
    results: Optional[List[Dict]] = None
    parent_process_id: Optional[str] = None  # For bulk scrape child processes
