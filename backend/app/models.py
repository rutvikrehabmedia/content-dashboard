from datetime import datetime
from typing import Optional, Dict, List
from sqlmodel import SQLModel, Field, JSON
import uuid

class ScrapedContent(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    url: str
    original_url: Optional[str] = None
    process_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    content: Optional[str] = None
    meta_data: Dict = Field(default={}, sa_type=JSON)
    scraped_data: Dict = Field(default={}, sa_type=JSON)

class SearchLog(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    query: str
    urls: List[str] = Field(default=[], sa_type=JSON)
    whitelist: List[str] = Field(default=[], sa_type=JSON)
    blacklist: List[str] = Field(default=[], sa_type=JSON)
    scraped_data: Dict = Field(default={}, sa_type=JSON)
    process_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Whitelist(SQLModel, table=True):
    url: str = Field(primary_key=True)
    added_at: datetime = Field(default_factory=datetime.utcnow)

class Blacklist(SQLModel, table=True):
    url: str = Field(primary_key=True)
    added_at: datetime = Field(default_factory=datetime.utcnow) 