from pydantic import BaseModel
from typing import List, Optional, Any

class TrendAnalyzeRequest(BaseModel):
    document_id: str
    keywords: Optional[List[str]] = []

class TrendAnalyzeResponse(BaseModel):
    charts: List[Any]
    insights: str
    steps: List[str]
