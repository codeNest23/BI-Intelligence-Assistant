from fastapi import APIRouter, HTTPException
from services import cache_service
from agents.rag_agent import RAGAgent
from core.config import settings
from models.rag import RagChatRequest, RagChatResponse

router = APIRouter()

@router.post("/rag/chat", response_model=RagChatResponse)
async def rag_chat(request: RagChatRequest):
    doc_data = cache_service.get_document(request.document_id)
    if not doc_data:
        raise HTTPException(status_code=404, detail="Document not found or session expired.")
    
    try:
        agent = RAGAgent(
            pdf_text=doc_data["full_text"],
            api_key=settings.OPEN_ROUTER_API_KEY,
            pdf_name=doc_data["metadata"]["name"],
            pinecone_namespace=request.document_id
        )
        
        steps_collected = []
        def step_cb(s):
            steps_collected.append(s)
            
        answer, new_history, _ = agent.chat(
            user_message=request.message,
            history=request.history,
            status_callback=step_cb
        )
        
        return RagChatResponse(
            answer=answer,
            steps=steps_collected,
            history=new_history
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
