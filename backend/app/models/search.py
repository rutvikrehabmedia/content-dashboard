from pydantic import BaseModel
from typing import Dict, Optional, Any

class SearchResult(BaseModel):
    url: str
    title: str = ""
    content: str = ""
    score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None 