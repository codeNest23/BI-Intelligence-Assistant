from fastapi import APIRouter, HTTPException
from services import cache_service
from core.config import settings
from openai import OpenAI
from pydantic import BaseModel

router = APIRouter()

class SummarizeRequest(BaseModel):
    document_id: str

class SummarizeResponse(BaseModel):
    summary: str

SYSTEM_PROMPT_TEMPLATE = (
    "You are a helpful PDF assistant. Answer questions ONLY using the content "
    "of the document provided. Do not use outside knowledge.\n\n"
    "For summaries, respond with:\n"
    "  Overview: [brief overview]\n"
    "  Key Points: [bullet list]\n"
    "  Conclusion: [final takeaway]\n\n"
    "Always cite the section or page when possible.\n\n"
    "The document content is provided below:\n\n"
    "{pdf_text}"
)

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_pdf(request: SummarizeRequest):
    doc_data = cache_service.get_document(request.document_id)
    if not doc_data:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPEN_ROUTER_API_KEY,
        )
        
        pdf_text = doc_data["full_text"]
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(pdf_text=pdf_text)
        
        response = client.chat.completions.create(
            model=settings.MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Please provide a structured summary of this document."},
            ],
        )
        
        summary = response.choices[0].message.content.strip()
        return SummarizeResponse(summary=summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
