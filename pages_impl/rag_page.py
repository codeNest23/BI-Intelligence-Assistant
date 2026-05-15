"""RAG Agent Chat Page — multi-step query decomposition + tool calling."""
import os
import logging
import streamlit as st
from datetime import datetime

log = logging.getLogger("rag_page")


def page_rag():
    # STYLED: Premium Hero Section for Agent
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">RAG Intelligence Agent</h1>
        <p class="hero-subtitle">Ask complex, multi-step questions. Our agent will decompose your query and find grounded answers from your document.</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.pdf_text:
        st.toast("No PDF loaded. Redirecting to Upload...", icon="⚠️")
        st.session_state.page = "upload"
        st.rerun()

    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        st.error("OPEN_ROUTER_API_KEY missing from .env")
        return
    if not os.getenv("PINECONE_API_KEY"):
        st.error("PINECONE_API_KEY missing from .env. Add it to use Pinecone retrieval.")
        return

    # STYLED: Improved info banner using glass card
    with st.container():
        st.markdown("""
        <div class="glass-card" style="padding: 20px; border-left: 4px solid var(--primary);">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <div style="background: var(--primary); color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 18px;">💡</span>
                </div>
                <h4 style="margin: 0; color: #1E293B;">Agent Capabilities</h4>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; font-size: 0.85rem; color: #64748B;">
                <div>🔍 <b>Decomposition:</b> Breaks down complex queries.</div>
                <div>📚 <b>Retrieval:</b> Semantic search across chunks.</div>
                <div>🔧 <b>Tool Use:</b> Entity extraction & counting.</div>
                <div>💡 <b>Synthesis:</b> Grounded, cited answers.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # STYLED: Control row with better layout
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 1rem;">
                <span style="background: #EEF2FF; color: #6366F1; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">DOCUMENT</span>
                <span style="color: #475569; font-size: 0.85rem; font-weight: 600;">{st.session_state.pdf_name}</span>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        if st.button("🗑 Clear Session", use_container_width=True, help="Wipe chat history and logs"):
            st.session_state.rag_history = []
            st.session_state.rag_steps   = []
            st.session_state.rag_logs    = []
            st.rerun()

    # STYLED: Render chat history with new bubbles
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.rag_history:
        role    = msg["role"]
        content = msg["content"]
        ts      = msg.get("ts", "")
        safe    = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

        if role == "user":
            st.markdown(
                f'<div class="user-bubble-v2">{safe}<div style="font-size: 0.65rem; opacity: 0.7; margin-top: 8px; text-align: right;">{ts} • YOU</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="bot-bubble-v2">{safe}<div style="font-size: 0.65rem; color: #94A3B8; margin-top: 8px;">{ts} • RAG AGENT</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)

    # STYLED: Improved Reasoning Trace
    if st.session_state.rag_steps:
        with st.expander("🔬 View Agent Thinking Process", expanded=False):
            for step in st.session_state.rag_steps:
                st.markdown(f"""
                    <div style="background: #F8FAFC; border-left: 3px solid #6366F1; padding: 8px 12px; margin-bottom: 6px; border-radius: 0 8px 8px 0;">
                        <code style="background: transparent !important; color: #475569 !important;">{step}</code>
                    </div>
                """, unsafe_allow_html=True)

    # STYLED: Suggested queries as chips
    if not st.session_state.rag_history:
        st.markdown("<p style='color: #64748B; font-size: 0.9rem; font-weight: 600; margin-bottom: 12px;'>💡 Try a suggested query:</p>", unsafe_allow_html=True)
        examples = [
            "What are the main findings?",
            "Summarize recommendations",
            "What risks are discussed?",
        ]
        cols = st.columns(len(examples))
        for col, ex in zip(cols, examples):
            with col:
                if st.button(ex, use_container_width=True, help="Click to run this query"):
                    st.session_state["_prefill"] = ex
                    st.rerun()

    # Chat input
    prefill = st.session_state.pop("_prefill", "")
    user_input = st.chat_input("Ask a complex question about your PDF…")

    query = user_input or prefill
    if query:
        from agents.rag_agent import RAGAgent
        ts_now = datetime.now().strftime("%H:%M")
        log.info("User query: %r", query[:100])

        st.session_state.rag_history.append({"role": "user", "content": query, "ts": ts_now})

        # STYLED: Premium status indicator
        with st.status("🤖 Agent is thinking...", expanded=True) as status:
            steps_collected = []
            log_lines = []

            def step_cb(s):
                st.write(f"⚙️ {s}")
                steps_collected.append(s)
                log_lines.append(s)

            try:
                agent = RAGAgent(
                    pdf_text=st.session_state.pdf_text,
                    api_key=api_key,
                    pdf_name=st.session_state.pdf_name,
                    pinecone_namespace=st.session_state.get("pinecone_namespace"),
                )
                answer, new_history, steps = agent.chat(
                    user_message=query,
                    history=None,
                    status_callback=step_cb,
                )
                status.update(label="✅ Answer generated!", state="complete", expanded=False)
            except Exception as e:
                log.error("RAGAgent crashed: %s", e, exc_info=True)
                answer = f"❌ Agent error: {e}"
                steps = steps_collected
                status.update(label="❌ Error occurred", state="error")

        ts_reply = datetime.now().strftime("%H:%M")
        st.session_state.rag_history.append({"role": "assistant", "content": answer, "ts": ts_reply})
        st.session_state.rag_steps = steps_collected
        st.session_state.setdefault("rag_logs", []).extend(log_lines)
        st.rerun()

    # STYLED: Improved Log Panel
    if st.session_state.get("rag_logs"):
        with st.expander("📜 Activity Logs", expanded=False):
            for line in st.session_state["rag_logs"][-20:]:
                st.markdown(f"<div style='font-family: monospace; font-size: 0.75rem; color: #64748B; border-bottom: 1px solid #F1F5F9; padding: 4px 0;'>{line}</div>", unsafe_allow_html=True)
            if st.button("Clear logs", key="clear_rag_logs"):
                st.session_state["rag_logs"] = []
                st.rerun()
