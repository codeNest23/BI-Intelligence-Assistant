from fastapi import APIRouter, UploadFile, File, HTTPException
from services import pdf_service, cache_service
from agents import pinecone_store
from models.upload import UploadResponse

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    try:
        content = await file.read()
        full_text, pages_list, page_count = pdf_service.extract_pdf_content(content)
        
        # Pinecone indexing
        namespace = pinecone_store.namespace_for_document(file.filename, full_text)
        
        indexing_info = {"chunks": 0}
        if pinecone_store.pinecone_configured():
            indexing_info = pinecone_store.index_document(full_text, file.filename)
        
        metadata = {
            "name": file.filename,
            "pages": page_count,
            "size_kb": round(len(content) / 1024, 2),
            "pinecone_chunks": indexing_info.get("chunks", 0)
        }
        
        # Cache the document data
        cache_service.set_document(namespace, {
            "full_text": full_text,
            "pages_list": pages_list,
            "metadata": metadata
        })
        
        return UploadResponse(document_id=namespace, metadata=metadata)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
