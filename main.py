from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PDF Intelligence Hub API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "PDF Intelligence Hub API is running"}

# Include routers
from api import upload, rag, trend, summarize
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(rag.router, prefix="/api", tags=["RAG"])
app.include_router(trend.router, prefix="/api", tags=["Trend"])
app.include_router(summarize.router, prefix="/api", tags=["Summarize"])
