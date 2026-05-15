# FastAPI Migration Plan: PDF Intelligence Hub

This plan details how to refactor the current Streamlit-based logic into a FastAPI backend to support the React frontend.

## 1. Project Structure (Backend)

The backend will be refactored into a structured FastAPI application:

```text
.
├── main.py                 # FastAPI entry point
├── api/                    # API route definitions
│   ├── upload.py           # /api/upload
│   ├── rag.py              # /api/rag
│   └── trend.py            # /api/trend
├── core/                   # Configuration and constants
│   └── config.py           # Env vars, model settings
├── models/                 # Pydantic schemas for requests/responses
│   ├── upload.py
│   ├── rag.py
│   └── trend.py
├── services/               # Shared logic extracted from pages_impl/
│   ├── pdf_service.py      # PDF extraction and processing
│   └── cache_service.py    # Temporary in-memory storage for doc text
└── agents/                 # (Existing) Agent logic (RAGAgent, TrendAgent)
```

## 2. Refactoring Logic from `pages_impl/`

### `upload_page.py` -> `POST /api/upload`
*   **Source Logic:** `extract_pdf` and `index_document` calls.
*   **API Implementation:**
    *   **Endpoint:** `POST /api/upload`
    *   **Input:** `file: UploadFile`
    *   **Action:**
        1.  Extract text and pages using `fitz` (moved to `services/pdf_service.py`).
        2.  Generate a Pinecone namespace via `pinecone_store.namespace_for_document`.
        3.  Upsert chunks to Pinecone via `pinecone_store.index_document`.
        4.  Cache the `full_text` and `pages_list` in `cache_service.py` using the namespace as the key.
    *   **Response:**
        ```json
        {
          "document_id": "namespace-string",
          "metadata": {
            "name": "filename.pdf",
            "pages": 10,
            "size_kb": 150.5,
            "pinecone_chunks": 45
          }
        }
        ```

### `rag_page.py` -> `POST /api/rag/chat`
*   **Source Logic:** `RAGAgent` instantiation and `.chat()` method.
*   **API Implementation:**
    *   **Endpoint:** `POST /api/rag/chat`
    *   **Input:** `{ "document_id": "string", "message": "string", "history": [] }`
    *   **Action:**
        1.  Retrieve cached text for `document_id`.
        2.  Initialize `RAGAgent` with the `document_id` (namespace).
        3.  Call `agent.chat(message, history)`.
        4.  Capture steps (tool calls) from the `status_callback`.
    *   **Response:**
        ```json
        {
          "answer": "Grounded answer text",
          "steps": ["🔧 search_chunks(...)", "🔧 extract_entities(...)"],
          "history": [ ...updated history ]
        }
        ```

### `trend_page.py` -> `POST /api/trend/analyze`
*   **Source Logic:** `TrendAgent` instantiation and `.analyse()` method.
*   **API Implementation:**
    *   **Endpoint:** `POST /api/trend/analyze`
    *   **Input:** `{ "document_id": "string", "keywords": ["optional", "list"] }`
    *   **Action:**
        1.  Retrieve cached `pages_list` for `document_id`.
        2.  Initialize `TrendAgent`.
        3.  Call `agent.analyse(query_with_keywords)`.
    *   **Response:**
        ```json
        {
          "charts": [ ...chart objects ],
          "insights": "Bullet pointed summary",
          "steps": ["📊 keyword_frequency(...)", ...]
        }
        ```

## 3. Refactoring `chatbot.py`

*   **CLI Logic:** `extract_pdf_text` and `ask_ai`.
*   **Migration:**
    *   Standardize `extract_pdf` logic in `services/pdf_service.py`.
    *   Implement a `POST /api/summarize` endpoint that uses the `SYSTEM_PROMPT_TEMPLATE` from `chatbot.py` to provide a structured summary of the cached document.

## 4. State Management (Statelessness)

FastAPI endpoints will rely on the `document_id` (Pinecone namespace) passed from the frontend.
*   **In-Memory Cache:** For this migration, we will use a simple Python dictionary in `services/cache_service.py` to store mapping: `namespace -> { text, pages_list }`.
*   **Persistence:** For production, this would move to Redis or a database.

## 5. Next Steps

1.  **Install FastAPI & Uvicorn**: `pip install fastapi uvicorn python-multipart`.
2.  **Create `main.py`**: Set up basic app and CORS.
3.  **Implement `services/`**: Migrate extraction logic.
4.  **Implement `api/` routes**: Build endpoints one by one (Upload -> RAG -> Trend).
5.  **Connect Frontend**: Update React components to use `fetch` calls to these new endpoints.
