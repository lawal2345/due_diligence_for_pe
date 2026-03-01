import streamlit as st
import os
import tempfile
from agent import run_agent

st.set_page_config(
    page_title="Due Diligence Agent",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=DM+Sans:wght@300;400;500&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #FAFAF8;
    color: #1a1a1a;
}

/* Hide Streamlit branding */
#MainMenu, footer, header {visibility: hidden;}

/* Main container */
.block-container {
    padding: 3rem 4rem;
    max-width: 1200px;
}

/* Headings */
h1 {
    font-family: 'Playfair Display', serif !important;
    font-size: 2.4rem !important;
    font-weight: 600 !important;
    color: #0a0a0a !important;
    letter-spacing: -0.02em !important;
    margin-bottom: 0.2rem !important;
}

h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: #0a0a0a !important;
}

/* Subtitle */
.subtitle {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    color: #888;
    font-weight: 300;
    margin-bottom: 3rem;
    letter-spacing: 0.01em;
}

/* Divider */
.divider {
    height: 1px;
    background: #e8e4de;
    margin: 2rem 0;
}

/* Upload box */
[data-testid="stFileUploader"] {
    background: #ffffff;
    border: 1.5px dashed #d0ccc4;
    border-radius: 8px;
    padding: 1.5rem;
}

[data-testid="stFileUploader"]:hover {
    border-color: #1a3a5c;
}

/* Primary button */
[data-testid="baseButton-primary"] {
    background-color: #1a3a5c !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 2rem !important;
    transition: all 0.2s !important;
}

[data-testid="baseButton-primary"]:hover {
    background-color: #0f2440 !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e8e4de;
    border-radius: 6px;
    padding: 1.2rem 1.5rem !important;
}

[data-testid="stMetricLabel"] {
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: #888 !important;
    font-weight: 500 !important;
}

[data-testid="stMetricValue"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1.4rem !important;
    font-weight: 500 !important;
    color: #0a0a0a !important;
}

/* Risk tags */
.risk-tag {
    display: inline-block;
    background: #fff5f5;
    border: 1px solid #fcc;
    color: #c00;
    font-size: 0.8rem;
    padding: 0.2rem 0.7rem;
    border-radius: 3px;
    margin: 0.2rem 0.2rem 0.2rem 0;
    font-family: 'DM Sans', sans-serif;
}

/* News item */
.news-item {
    border-left: 3px solid #1a3a5c;
    padding: 0.6rem 1rem;
    margin-bottom: 1rem;
    background: #ffffff;
}

.news-headline {
    font-weight: 500;
    font-size: 0.9rem;
    color: #0a0a0a;
    margin-bottom: 0.3rem;
}

.news-summary {
    font-size: 0.82rem;
    color: #666;
    line-height: 1.5;
}

/* Memo output */
.memo-container {
    background: #ffffff;
    border: 1px solid #e8e4de;
    border-radius: 6px;
    padding: 2.5rem 3rem;
    line-height: 1.8;
    font-size: 0.93rem;
}

/* Section label */
.section-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #aaa;
    font-weight: 500;
    margin-bottom: 1rem;
}

/* Download button */
[data-testid="baseButton-secondary"] {
    border: 1.5px solid #1a3a5c !important;
    color: #1a3a5c !important;
    background: transparent !important;
    border-radius: 4px !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
}
</style>
""", unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────
st.markdown("<h1>Due Diligence Agent</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Upload documents and receive a structured analysis memo in under 60 seconds.</p>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Upload ─────────────────────────────────────────────────────
st.markdown('<p class="section-label">Documents</p>', unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Drop up to 3 PDF files — 10-K, CIM, financial statements",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="visible"
)

if uploaded_files and len(uploaded_files) > 3:
    st.error("Maximum 3 documents allowed.")
    st.stop()

st.markdown("<br>", unsafe_allow_html=True)
run_button = st.button("Run Analysis", type="primary")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ── Agent Run ──────────────────────────────────────────────────
if run_button and uploaded_files:

    temp_paths = []
    temp_dir = tempfile.mkdtemp()

    for f in uploaded_files:
        temp_path = os.path.join(temp_dir, f.name)
        with open(temp_path, "wb") as out:
            out.write(f.read())
        temp_paths.append(temp_path)

    with st.spinner("Analysing documents..."):
        try:
            final_state = run_agent(temp_paths)
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
            st.stop()

    # ── Results ────────────────────────────────────────────────
    if final_state.get("errors"):
        with st.expander("Warnings"):
            for err in final_state["errors"]:
                st.warning(err)

    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        st.markdown('<p class="section-label">Memo</p>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="memo-container">{final_state["final_memo"]}</div>',
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="Download Memo",
            data=final_state["final_memo"],
            file_name=f"{final_state.get('company_name', 'company')}_DD_memo.txt",
            mime="text/plain"
        )

    with col2:
        # Financials
        st.markdown('<p class="section-label">Key Financials</p>', unsafe_allow_html=True)
        if final_state.get("financials"):
            fin = final_state["financials"]
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Revenue", f"${fin.revenue/1e9:.2f}B" if fin.revenue else "N/A")
                st.metric("Net Income", f"${fin.net_income/1e9:.2f}B" if fin.net_income else "N/A")
            with m2:
                st.metric("Gross Margin", f"{fin.gross_margin:.1f}%" if fin.gross_margin else "N/A")
                st.metric("Op. Margin", f"{fin.operating_margin:.1f}%" if fin.operating_margin else "N/A")
        else:
            st.info("Financials unavailable")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # Risks
        st.markdown('<p class="section-label">Risk Flags</p>', unsafe_allow_html=True)
        if final_state.get("risk_flags"):
            risks = final_state["risk_flags"]
            all_risks = (
                (risks.financial_risks or []) +
                (risks.regulatory_risks or []) +
                (risks.market_risks or []) +
                (risks.operational_risks or [])
            )
            if all_risks:
                tags_html = "".join([f'<span class="risk-tag">{r}</span>' for r in all_risks[:8]])
                st.markdown(tags_html, unsafe_allow_html=True)
            if risks.severity_summary:
                st.markdown(f"<br><small style='color:#888'>{risks.severity_summary}</small>", unsafe_allow_html=True)
        else:
            st.info("No risk flags found")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # News
        st.markdown('<p class="section-label">Recent News</p>', unsafe_allow_html=True)
        if final_state.get("news_items"):
            for item in final_state["news_items"][:4]:
                st.markdown(f"""
                <div class="news-item">
                    <div class="news-headline">{item.headline}</div>
                    <div class="news-summary">{item.summary}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent news found")

elif run_button and not uploaded_files:
    st.warning("Please upload at least one document to begin.")