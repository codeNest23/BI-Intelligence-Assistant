"""Upload page — PDF extraction + metadata display."""
import fitz
import streamlit as st
from agents.pinecone_store import index_document, pinecone_configured


def extract_pdf(uploaded_file):
    data = uploaded_file.read()
    doc  = fitz.open(stream=data, filetype="pdf")
    pages_list = []
    for i, page in enumerate(doc, 1):
        t = page.get_text().strip()
        pages_list.append(f"--- Page {i} ---\n{t}" if t else f"--- Page {i} ---\n[no text]")
    page_count = len(doc)
    doc.close()
    full_text = "\n\n".join(pages_list)
    if not any(p for p in pages_list):
        raise ValueError("No extractable text found. PDF may be image-based.")
    return full_text, pages_list, page_count


"""Upload page — PDF extraction + metadata display."""
import fitz
import streamlit as st
from agents.pinecone_store import index_document, pinecone_configured


def extract_pdf(uploaded_file):
    data = uploaded_file.read()
    doc  = fitz.open(stream=data, filetype="pdf")
    pages_list = []
    for i, page in enumerate(doc, 1):
        t = page.get_text().strip()
        pages_list.append(f"--- Page {i} ---\n{t}" if t else f"--- Page {i} ---\n[no text]")
    page_count = len(doc)
    doc.close()
    full_text = "\n\n".join(pages_list)
    if not any(p for p in pages_list):
        raise ValueError("No extractable text found. PDF may be image-based.")
    return full_text, pages_list, page_count


def page_upload():
    # STYLED: Premium Hero Section
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">Knowledge Starts Here</h1>
        <p class="hero-subtitle">Upload your PDF documents and let our multi-agent intelligence extract insights, track trends, and answer complex queries.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("_redirect_warn"):
        st.session_state.pop("_redirect_warn", None)
        st.toast("Upload a PDF first to access other features.", icon="⚠️")

    # STYLED: Redesigned Drop zone in a glass card
    st.markdown("""
    <div class="glass-card" style="text-align: center; border: 2px dashed rgba(99, 102, 241, 0.3); background: rgba(255,255,255,0.4);">
        <div style="font-size: 4rem; margin-bottom: 1rem; filter: drop-shadow(0 10px 15px rgba(99, 102, 241, 0.2));">📂</div>
        <h3 style="color: #1E293B; margin-bottom: 0.5rem; font-weight: 700;">Drag & Drop Document</h3>
        <p style="color: #64748B; font-size: 0.9rem; max-width: 400px; margin: 0 auto 1.5rem;">
            Select a PDF file to begin. We'll automatically extract text and index it for semantic search.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Placing the file uploader slightly overlapping or below
    st.markdown("<div style='margin-top: -60px; padding: 0 100px;'>", unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Choose PDF file", type=["pdf"], label_visibility="collapsed", help="Select a PDF document (max 200MB)"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded:
        if uploaded.name != st.session_state.pdf_name:
            with st.status("🔍 Processing document...", expanded=True) as status:
                st.write("Extracting text layers...")
                try:
                    text, pages_list, pages = extract_pdf(uploaded)
                    st.write("Chunking and generating embeddings...")
                    
                    st.session_state.pdf_text       = text
                    st.session_state.pdf_pages_list = pages_list
                    st.session_state.pdf_name       = uploaded.name
                    st.session_state.pdf_pages      = pages
                    st.session_state.pdf_size_kb    = round(uploaded.size / 1024, 1)
                    st.session_state.rag_history    = []
                    st.session_state.trend_results  = None
                    st.session_state.rag_steps      = []
                    st.session_state.pinecone_index = None
                    st.session_state.pinecone_namespace = None
                    st.session_state.pinecone_chunks = 0

                    if pinecone_configured():
                        pinecone_info = index_document(text, uploaded.name)
                        st.session_state.pinecone_index = pinecone_info["index_name"]
                        st.session_state.pinecone_namespace = pinecone_info["namespace"]
                        st.session_state.pinecone_chunks = pinecone_info["chunks"]
                    else:
                        st.warning("PINECONE_API_KEY missing. PDF loaded, but RAG indexing is not available yet.")
                    
                    status.update(label="✅ Document ready!", state="complete", expanded=False)
                    st.toast(f"Successfully loaded {uploaded.name}", icon="✅")
                except Exception as e:
                    status.update(label="❌ Extraction failed", state="error")
                    st.error(f"Error: {e}")
                    return

        # STYLED: Success card with modern layout
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container():
            st.markdown(f"""
            <div class="glass-card" style="border-left: 6px solid #10B981;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                    <div>
                        <h3 style="margin: 0; color: #1E293B; font-weight: 700;">{st.session_state.pdf_name}</h3>
                        <p style="color: #64748B; font-size: 0.85rem; margin-top: 4px;">Document successfully indexed and available for analysis.</p>
                    </div>
                    <div style="background: #ECFDF5; color: #059669; padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;">
                        ACTIVE
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px;">
                    <div style="background: #F8FAFC; padding: 16px; border-radius: 16px; border: 1px solid #E2E8F0;">
                        <p style="color: #64748B; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;">Pages</p>
                        <p style="font-size: 1.25rem; font-weight: 700; color: #1E293B; margin: 0;">{st.session_state.pdf_pages}</p>
                    </div>
                    <div style="background: #F8FAFC; padding: 16px; border-radius: 16px; border: 1px solid #E2E8F0;">
                        <p style="color: #64748B; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;">File Size</p>
                        <p style="font-size: 1.25rem; font-weight: 700; color: #1E293B; margin: 0;">{st.session_state.pdf_size_kb} <small style="font-size: 0.7rem;">KB</small></p>
                    </div>
                    <div style="background: #F8FAFC; padding: 16px; border-radius: 16px; border: 1px solid #E2E8F0;">
                        <p style="color: #64748B; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;">Vectors</p>
                        <p style="font-size: 1.25rem; font-weight: 700; color: #1E293B; margin: 0;">{st.session_state.pinecone_chunks or 0}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<p style='text-align: center; color: #64748B; font-size: 0.9rem; margin: 1.5rem 0 1rem;'>What would you like to do next?</p>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🤖  Start Intelligent Chat", use_container_width=True, type="primary", help="Ask questions about this document"):
                st.session_state.page = "rag"; st.rerun()
        with c2:
            if st.button("📊  View Trend Analysis", use_container_width=True, help="See visual insights and patterns"):
                st.session_state.page = "trend"; st.rerun()
