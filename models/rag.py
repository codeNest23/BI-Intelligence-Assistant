from pydantic import BaseModel
from typing import List, Dict, Optional

class RagChatRequest(BaseModel):
    document_id: str
    message: str
    history: Optional[List[Dict[str, str]]] = []

class RagChatResponse(BaseModel):
    answer: str
    steps: List[str]
    history: List[Dict[str, str]]
