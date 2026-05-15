"""Trend Analysis Page — charts + AI insights."""
import os
import json
import logging
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

log = logging.getLogger("trend_page")

PALETTE = ["#7C6FFF", "#FF6B9D", "#00D2AA", "#FFB347", "#4ECDC4", "#45B7D1"]


def render_chart(chart: dict):
    ctype  = chart.get("type", "bar")
    title  = chart.get("title", "")
    labels = chart.get("labels", [])
    dsets  = chart.get("datasets", [])

    if not dsets:
        return

    if ctype == "line":
        fig = go.Figure()
        for i, ds in enumerate(dsets):
            fig.add_trace(go.Scatter(
                x=labels, y=ds["data"], name=ds["label"],
                mode="lines+markers",
                line=dict(color=PALETTE[i % len(PALETTE)], width=2.5),
                marker=dict(size=6),
                fill="tozeroy" if len(dsets) == 1 else "none",
                fillcolor=f"rgba(124,111,255,0.08)",
            ))
        y_min = chart.get("yMin", None)
        y_max = chart.get("yMax", None)
        yaxis = dict(range=[y_min, y_max]) if y_min is not None else {}
        fig.update_layout(
            title=dict(text=title, font=dict(size=15, family="Inter", color="#1A1A3E")),
            paper_bgcolor="white", plot_bgcolor="#FAFAFF",
            font=dict(family="Inter", color="#3A3A6E"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=48, b=20),
            xaxis=dict(gridcolor="#F0EFF8"),
            yaxis=dict(gridcolor="#F0EFF8", **yaxis),
            height=300,
        )

    elif ctype == "bar":
        fig = go.Figure()
        for i, ds in enumerate(dsets):
            fig.add_trace(go.Bar(
                x=labels, y=ds["data"], name=ds["label"],
                marker_color=PALETTE[i % len(PALETTE)],
                marker_line_width=0,
                opacity=0.88,
            ))
        fig.update_layout(
            title=dict(text=title, font=dict(size=15, family="Inter", color="#1A1A3E")),
            paper_bgcolor="white", plot_bgcolor="#FAFAFF",
            font=dict(family="Inter", color="#3A3A6E"),
            barmode="group",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=48, b=40),
            xaxis=dict(gridcolor="#F0EFF8", tickangle=-30 if len(labels) > 10 else 0),
            yaxis=dict(gridcolor="#F0EFF8"),
            height=320,
        )

    st.plotly_chart(fig, use_container_width=True)


def page_trend():
    # STYLED: Premium Hero Section
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">Visual Trend Analysis</h1>
        <p class="hero-subtitle">The agent autonomously runs analytical tools to discover patterns, keyword frequencies, and sentiment arcs within your document.</p>
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

    # STYLED: Info banner as glass card
    st.markdown("""
    <div class="glass-card" style="padding: 20px; border-left: 4px solid var(--secondary);">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
            <div style="background: var(--secondary); color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 18px;">📊</span>
            </div>
            <h4 style="margin: 0; color: #1E293B;">Agentic Intelligence</h4>
        </div>
        <p style="font-size: 0.85rem; color: #64748B; margin: 0; line-height: 1.6;">
            The agent runs <b>5 specialized tools</b>: keyword frequency, sentiment mapping, TF-IDF topics, word statistics, and entity timelines to generate comprehensive insights.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # STYLED: Better keyword input layout
    with st.container():
        st.markdown("<p style='color: #475569; font-size: 0.9rem; font-weight: 700; margin-bottom: 8px;'>🔍 Track Specific Keywords (Optional)</p>", unsafe_allow_html=True)
        kw_col, btn_col = st.columns([4, 1.2])
        with kw_col:
            kw_input = st.text_input(
                "Keywords", value="", placeholder="e.g. risk, growth, revenue, innovation",
                label_visibility="collapsed", help="Enter keywords separated by commas"
            )
        with btn_col:
            run_btn = st.button("▶ Run Full Analysis", type="primary", use_container_width=True)

    # Auto-run logic
    if st.session_state.trend_results is None and not run_btn:
        run_btn = True

    if run_btn:
        pages_list = st.session_state.pdf_pages_list
        if not pages_list:
            import re
            parts = re.split(r'--- Page \d+ ---', st.session_state.pdf_text)
            pages_list = [p.strip() for p in parts if p.strip()]

        with st.status("🤖 Agent is analyzing document trends...", expanded=True) as status:
            from agents.trend_agent import TrendAgent
            agent = TrendAgent(pdf_pages=pages_list, api_key=api_key)
            
            keywords = [k.strip() for k in kw_input.split(",") if k.strip()]
            query = "Perform a comprehensive trend analysis."
            if keywords:
                query += f" Focus on: {', '.join(keywords)}."
            
            try:
                results = agent.analyse(query)
                status.update(label="✅ Analysis complete!", state="complete", expanded=False)
            except Exception as e:
                log.error("TrendAgent crashed: %s", e, exc_info=True)
                st.error(f"❌ Analysis error: {e}")
                results = {"charts": [], "insights": f"Error: {e}", "steps": []}

            if keywords and pages_list:
                series = {kw.lower(): [p.lower().count(kw.lower()) for p in pages_list] for kw in keywords[:5]}
                custom_chart = {
                    "type": "line",
                    "title": f"Custom Keyword Tracking",
                    "labels": [f"P{i+1}" for i in range(len(pages_list))],
                    "datasets": [{"label": kw, "data": counts} for kw, counts in series.items()],
                }
                results["charts"].insert(0, custom_chart)

            st.session_state.trend_results = results
            st.session_state.setdefault("trend_logs", []).extend(results.get("steps", []))
            st.rerun()

    results = st.session_state.trend_results
    if not results:
        return

    # STYLED: Improved Insights Section
    if results.get("insights"):
        with st.container():
            st.markdown("""
                <div class="glass-card" style="border-top: 4px solid #10B981;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
                        <div style="background: #D1FAE5; color: #059669; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                            <span style="font-size: 18px;">💡</span>
                        </div>
                        <h3 style="margin: 0; color: #1E293B; font-weight: 700;">AI-Generated Insights</h3>
                    </div>
            """, unsafe_allow_html=True)
            
            insight_text = results["insights"]
            for line in insight_text.split("\n"):
                line = line.strip()
                if line.startswith(("•", "-", "*", "·")):
                    st.markdown(f"<div style='margin-left: 1rem; color: #334155; margin-bottom: 8px;'><b>•</b> {line[1:].strip()}</div>", unsafe_allow_html=True)
                elif line:
                    st.markdown(f"<p style='color: #475569; margin-bottom: 12px;'>{line}</p>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

    # STYLED: Charts in professional grid
    charts = results.get("charts", [])
    if charts:
        st.markdown("<h3 style='color: #1E293B; margin: 2rem 0 1rem; font-weight: 700;'>📈 Visual Analytics</h3>", unsafe_allow_html=True)
        
        for i in range(0, len(charts), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(charts):
                    with col:
                        st.markdown('<div class="glass-card" style="padding: 16px; min-height: 400px;">', unsafe_allow_html=True)
                        render_chart(charts[i + j])
                        st.markdown('</div>', unsafe_allow_html=True)

    # STYLED: Footer controls
    st.markdown("<div style='display: flex; justify-content: center; margin-top: 2rem;'>", unsafe_allow_html=True)
    if st.button("🔄 Refresh Data & Re-run", use_container_width=False, help="Start analysis from scratch"):
        st.session_state.trend_results = None
        st.session_state["trend_logs"] = []
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # STYLED: Log Panel
    if st.session_state.get("trend_logs"):
        with st.expander("📜 Process History & Tool Logs", expanded=False):
            for line in st.session_state["trend_logs"][-20:]:
                st.markdown(f"<div style='font-family: monospace; font-size: 0.75rem; color: #64748B; border-bottom: 1px solid #F1F5F9; padding: 4px 0;'>{line}</div>", unsafe_allow_html=True)
            if st.button("Clear logs", key="clear_trend_logs"):
                st.session_state["trend_logs"] = []
                st.rerun()
