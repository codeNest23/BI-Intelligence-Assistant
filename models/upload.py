from pydantic import BaseModel
from typing import Dict, Any

class UploadResponse(BaseModel):
    document_id: str
    metadata: Dict[str, Any]
