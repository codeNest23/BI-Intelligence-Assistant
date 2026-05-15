# PDF Intelligence Hub - GEMINI Project Documentation

## Project Overview
The **PDF Intelligence Hub** is a multi-agent PDF intelligence platform built with Python and Streamlit. It leverages Large Language Models (LLMs) via OpenRouter and vector databases (Pinecone) to provide deep insights into PDF documents.

### Key Features
- **Multi-Agent RAG:** An agentic Retrieval-Augmented Generation system that uses tool-calling to decompose queries, search document chunks, and verify claims.
- **Trend Analysis:** A specialized agent that performs keyword frequency tracking, sentiment analysis, topic modeling (TF-IDF), and entity timeline extraction.
- **Interactive UI:** A polished Streamlit dashboard with dedicated pages for uploading documents, chatting with the RAG agent, and visualizing trends.
- **CLI Chatbot:** A standalone command-line tool for basic PDF Q&A and summarization.

## Architecture
The project follows a modular architecture:
- `app.py`: Main Streamlit entry point, handling session state, navigation, and custom CSS styling.
- `agents/`: Contains the logic for the platform's intelligence:
    - `rag_agent.py`: Implements the `RAGAgent` using OpenAI's tool-calling for document interaction.
    - `trend_agent.py`: Implements the `TrendAgent` for statistical and semantic document analysis.
    - `pinecone_store.py`: Manages document chunking and upserting to Pinecone using integrated text embeddings.
- `pages_impl/`: UI implementation for individual platform features (Upload, RAG, Trend).
- `chatbot.py`: A simplified, CLI-based PDF interaction tool using OpenRouter.

## Tech Stack
- **Framework:** Streamlit
- **LLM Provider:** OpenAI / OpenRouter (default: `gpt-oss-120b:free`)
- **Vector Database:** Pinecone (Serverless with integrated embeddings)
- **PDF Processing:** PyMuPDF (`fitz`)
- **Data & Viz:** Plotly, NumPy, scikit-learn
- **Environment:** `python-dotenv` for configuration

## Building and Running

### Prerequisites
- Python 3.10+
- A `.env` file with the following keys:
  ```env
  OPEN_ROUTER_API_KEY=your_key_here
  PINECONE_API_KEY=your_key_here
  PINECONE_INDEX_NAME=pdf-intelligence (optional)
  ```

### Installation
```powershell
# Create and activate virtual environment
python -m venv myenv
.\myenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```powershell
# Launch the Streamlit web interface
streamlit run app.py

# Launch the CLI chatbot
python chatbot.py
```

## Development Conventions

### Coding Style
- **Type Hints:** Use type hints for function signatures where possible (e.g., `def search(query: str, top_k: int = 3) -> list[str]`).
- **Logging:** Use the standard `logging` module for tracking agent actions and tool calls.
- **Tool-Calling:** Agents are designed around JSON tool schemas and specialized execution methods (`_execute_tool`).

### Agent Workflow
- **Research -> Strategy -> Execution:** Agents first analyze the user intent, decide which tools to call (e.g., `decompose_query`, `search_chunks`), and finally synthesize the findings.
- **Stateless Design:** Agent classes (like `RAGAgent`) are initialized with document context but maintain minimal internal state between chats.

### UI Guidelines
- Custom CSS is injected in `app.py` to provide a "Premium Redesign" look.
- Use `st.session_state` extensively for cross-page persistence of document text and analysis results.

## Key Files
- `app.py`: UI entry point and layout.
- `chatbot.py`: CLI interaction script.
- `agents/rag_agent.py`: Core logic for agentic Q&A.
- `agents/trend_agent.py`: Core logic for document analytics.
- `agents/pinecone_store.py`: Vector search abstraction.
- `requirements.txt`: Project dependencies.
