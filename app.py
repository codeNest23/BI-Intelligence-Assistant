"""
Multi-Agent PDF Intelligence Platform
Run: streamlit run app.py
"""
import os
import streamlit as st
from dotenv import load_dotenv

# STYLED: Load environment variables and set page config with custom favicon
load_dotenv()

st.set_page_config(
    page_title="PDF Intelligence Hub",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ──────────────────────────────────────────────────
def init_state():
    defaults = {
        "page": "upload",
        "pdf_text": None,
        "pdf_pages_list": [],   # list of per-page strings
        "pdf_name": None,
        "pdf_pages": 0,
        "pdf_size_kb": 0.0,
        "rag_history": [],
        "trend_results": None,
        "rag_steps": [],
        "rag_logs": [],
        "trend_logs": [],
        "pinecone_index": None,
        "pinecone_namespace": None,
        "pinecone_chunks": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── CSS (PREMIUM REDESIGN) ──────────────────────────────────────────────────
# STYLED: Injecting a comprehensive design system with modern typography and component overrides
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --primary: #6366F1;
    --primary-light: #818CF8;
    --secondary: #A855F7;
    --accent: #F43F5E;
    --bg-main: #F8FAFC;
    --sidebar-bg: #0F172A;
    --card-bg: rgba(255, 255, 255, 0.8);
    --text-main: #1E293B;
    --text-muted: #64748B;
}

*, html, body { 
    font-family: 'Outfit', sans-serif !important; 
}

/* Hide Streamlit elements */
#MainMenu, footer, header { visibility: hidden; }

/* App Background */
.stApp {
    background: radial-gradient(circle at top right, #F1F5F9, #E2E8F0);
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: var(--sidebar-bg) !important;
    background-image: radial-gradient(circle at 0% 0%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
                      radial-gradient(circle at 100% 100%, rgba(168, 85, 247, 0.1) 0%, transparent 50%) !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important;
    min-width: 300px !important;
}

section[data-testid="stSidebar"] .stMarkdown h2 {
    color: white !important;
    font-weight: 700 !important;
}

/* Navigation Buttons in Sidebar */
div[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: 12px !important;
    color: #94A3B8 !important;
    text-align: left !important;
    width: 100% !important;
    padding: 12px 16px !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    margin: 4px 0 !important;
    display: flex !important;
    align-items: center !important;
}

div[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255, 255, 255, 0.05) !important;
    color: white !important;
    transform: translateX(4px);
}

div[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"]:active,
div[data-testid="stSidebar"] .stButton > button:focus {
    background: rgba(99, 102, 241, 0.15) !important;
    border-color: rgba(99, 102, 241, 0.4) !important;
    color: #C7D2FE !important;
}

/* Main Container */
.main .block-container {
    padding: 2rem 4rem !important;
    max-width: 1200px;
}

/* Header / Hero Section */
.hero-section {
    padding: 2rem 0;
    margin-bottom: 2rem;
}

.hero-title {
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
    margin-bottom: 0.5rem;
}

.hero-subtitle {
    font-size: 1.1rem;
    color: var(--text-muted);
    font-weight: 400;
}

/* Glass Cards */
.glass-card {
    background: var(--card-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.7);
    border-radius: 24px;
    padding: 32px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
    margin-bottom: 24px;
    transition: transform 0.3s ease;
}

.glass-card:hover {
    transform: translateY(-4px);
}

/* Metric Cards */
[data-testid="stMetric"] {
    background: white !important;
    border-radius: 16px !important;
    padding: 16px !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"] {
    height: 45px;
    white-space: pre-wrap;
    background-color: white;
    border-radius: 12px 12px 0 0;
    gap: 1px;
    padding: 8px 16px;
    border: 1px solid #E2E8F0;
    color: var(--text-muted);
}

.stTabs [aria-selected="true"] {
    background-color: var(--primary) !important;
    color: white !important;
}

/* Input Styles */
.stTextInput > div > div > input {
    border-radius: 12px !important;
    padding: 12px 16px !important;
}

/* Chat Bubbles */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-bottom: 24px;
}

.user-bubble-v2 {
    background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
    color: white;
    padding: 16px 20px;
    border-radius: 20px 20px 4px 20px;
    align-self: flex-end;
    max-width: 85%;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
    font-size: 0.95rem;
    line-height: 1.6;
}

.bot-bubble-v2 {
    background: white;
    color: var(--text-main);
    padding: 16px 20px;
    border-radius: 20px 20px 20px 4px;
    align-self: flex-start;
    max-width: 85%;
    border: 1px solid #E2E8F0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
    font-size: 0.95rem;
    line-height: 1.6;
}

/* Progress and Spinner */
.stProgress > div > div > div > div {
    background-color: var(--primary) !important;
}

/* Buttons */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    border-color: var(--primary) !important;
    color: var(--primary) !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%) !important;
    border: none !important;
    color: white !important;
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
    transform: scale(1.02);
}

/* Monospace text */
code {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    background: #F1F5F9 !important;
    color: #475569 !important;
    padding: 2px 4px !important;
    border-radius: 4px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
# STYLED: Improved sidebar with a professional logo and status widget
def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 2rem 1rem 1.5rem; text-align: center;">
            <div style="display: flex; justify-content: center; margin-bottom: 1rem;">
                <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%); 
                            border-radius: 20px; display: flex; align-items: center; justify-content: center;
                            box-shadow: 0 10px 20px rgba(99, 102, 241, 0.3);">
                    <span style="font-size: 40px;">🧠</span>
                </div>
            </div>
            <h2 style="font-size: 1.25rem; margin-bottom: 0;">PDF Intelligence</h2>
            <p style="color: #64748B; font-size: 0.75rem; font-weight: 500; letter-spacing: 1px; text-transform: uppercase; margin-top: 4px;">
                v2.0 • Multi-Agent AI
            </p>
        </div>
        """, unsafe_allow_html=True)

        has_pdf = st.session_state.pdf_text is not None
        tick = " (Ready)" if has_pdf else ""
        
        st.markdown('<p style="color: #475569; font-size: 0.7rem; font-weight: 700; margin-left: 1rem; text-transform: uppercase;">Main Navigation</p>', unsafe_allow_html=True)

        nav_items = [
            ("📂", "Upload PDF", "upload"),
            ("🤖", "RAG Agent", "rag"),
            ("📊", "Trend Analysis", "trend"),
        ]
        
        for icon, label, key in nav_items:
            # Active state simulation
            is_active = st.session_state.page == key
            label_text = f"{icon}  {label}{tick if key=='upload' and has_pdf else ''}"
            
            clicked = st.button(label_text, key=f"nav_{key}", use_container_width=True)
            if clicked:
                if key in ("rag", "trend") and not has_pdf:
                    st.session_state.page = "upload"
                    st.session_state["_warn"] = True
                else:
                    st.session_state.page = key
                    st.session_state.pop("_warn", None)
                st.rerun()

        if has_pdf:
            st.markdown(f"""
            <div style="margin-top: 2rem; padding: 16px; background: rgba(255,255,255,0.03); 
                        border-radius: 16px; border: 1px solid rgba(255,255,255,0.05);">
                <p style="color: #64748B; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; margin-bottom: 12px;">Active Document</p>
                <div style="display: flex; align-items: flex-start; gap: 12px;">
                    <div style="font-size: 1.5rem;">📄</div>
                    <div style="flex: 1; overflow: hidden;">
                        <div style="font-size: 0.85rem; color: #E2E8F0; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            {st.session_state.pdf_name}
                        </div>
                        <div style="font-size: 0.7rem; color: #94A3B8; margin-top: 2px;">
                            {st.session_state.pdf_pages} pages • {st.session_state.pdf_size_kb} KB
                        </div>
                    </div>
                </div>
                <div style="margin-top: 12px; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px;">
                    <div style="width: 100%; height: 100%; background: #10B981; border-radius: 2px;"></div>
                </div>
                <p style="color: #10B981; font-size: 0.65rem; margin-top: 6px; font-weight: 600;">Status: Indexed & Ready</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="position: fixed; bottom: 24px; left: 0; width: 300px; text-align: center; padding: 0 20px;">
            <div style="padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.05);">
                <p style="font-size: 0.75rem; color: #475569;">Powered by <span style="color: #818CF8; font-weight: 600;">OpenRouter & Pinecone</span></p>
            </div>
        </div>
        """, unsafe_allow_html=True)

render_sidebar()

# ── Import pages ─────────────────────────────────────────────────────────────
from pages_impl.upload_page   import page_upload
from pages_impl.rag_page      import page_rag
from pages_impl.trend_page    import page_trend

# ── Router ───────────────────────────────────────────────────────────────────
# STYLED: Use st.toast for warnings
if st.session_state.get("_warn"):
    st.session_state.pop("_warn", None)
    st.toast("⚠️ Please upload a PDF first.", icon="⚠️")

page = st.session_state.page
if page == "upload":
    page_upload()
elif page == "rag":
    page_rag()
elif page == "trend":
    page_trend()
