from fastapi import APIRouter, HTTPException
from services import cache_service
from agents.trend_agent import TrendAgent
from core.config import settings
from models.trend import TrendAnalyzeRequest, TrendAnalyzeResponse

router = APIRouter()

@router.post("/trend/analyze", response_model=TrendAnalyzeResponse)
async def trend_analyze(request: TrendAnalyzeRequest):
    doc_data = cache_service.get_document(request.document_id)
    if not doc_data:
        raise HTTPException(status_code=404, detail="Document not found or session expired.")
    
    try:
        agent = TrendAgent(
            pdf_pages=doc_data["pages_list"],
            api_key=settings.OPEN_ROUTER_API_KEY
        )
        
        query = "Perform a comprehensive trend analysis."
        if request.keywords:
            query += f" Focus on: {', '.join(request.keywords)}."
            
        results = agent.analyse(query)
        
        return TrendAnalyzeResponse(
            charts=results["charts"],
            insights=results["insights"],
            steps=results["steps"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
