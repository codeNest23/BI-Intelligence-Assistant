import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "pdf-intelligence")
    MODEL = os.getenv("MODEL", "openai/gpt-oss-120b:free")

settings = Config()
