"""Support Copilot - production-grade Streamlit UI."""
import streamlit as st
from datetime import datetime
from agent import run_agent

st.set_page_config(
    page_title="Support Copilot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Production CSS
# ============================================================

st.markdown("""
<style>
    /* Hide Streamlit chrome */
    #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; }
    .stDeployButton { display: none; }
    
    /* Reset block container padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 920px;
    }
    
    /* App background */
    .stApp {
        background: #fafafa;
    }
    
    /* ===== Header strip ===== */
    .app-header {
        position: sticky;
        top: 0;
        z-index: 100;
        background: white;
        border-bottom: 1px solid #e5e7eb;
        padding: 1rem 1.5rem;
        margin: -1rem -1rem 1.5rem -1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .header-brand {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .header-logo {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
        font-size: 1.1rem;
    }
    .header-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827;
        margin: 0;
    }
    .header-subtitle {
        font-size: 0.75rem;
        color: #6b7280;
        margin: 0;
    }
    .header-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8rem;
        color: #059669;
        font-weight: 500;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    
    /* ===== Sidebar ===== */
    [data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e5e7eb;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
    }
    
    /* Sidebar section labels */
    .sidebar-section {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #6b7280;
        margin: 1.25rem 0 0.5rem 0;
    }
    
    /* ===== Status pill ===== */
    .status-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
    .status-high { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    .status-med  { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .status-low  { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    
    /* ===== Metric cards ===== */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.5rem;
        margin: 0.75rem 0;
    }
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        text-align: left;
    }
    .metric-label {
        font-size: 0.65rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
        font-weight: 600;
    }
    .metric-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827;
    }
    
    /* ===== Escalation banner ===== */
    .escalation-banner {
        background: linear-gradient(135deg, #fef2f2 0%, #fce7f3 100%);
        border: 1px solid #fecaca;
        border-left: 4px solid #dc2626;
        padding: 1rem 1.25rem;
        border-radius: 10px;
        margin: 0.75rem 0;
    }
    .escalation-title {
        font-weight: 700;
        color: #991b1b;
        margin-bottom: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .escalation-body {
        color: #7f1d1d;
        font-size: 0.85rem;
    }
    
    /* ===== Tool card ===== */
    .tool-name {
        font-weight: 600;
        color: #4338ca;
        font-family: 'SF Mono', Monaco, monospace;
        font-size: 0.85rem;
    }
    
    /* ===== Empty state ===== */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        max-width: 600px;
        margin: 2rem auto;
    }
    .empty-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    .empty-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.5rem;
    }
    .empty-subtitle {
        color: #6b7280;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    
    /* ===== Buttons ===== */
    .stButton > button {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        text-align: left;
        font-size: 0.85rem;
        font-weight: 500;
        color: #374151;
        padding: 0.5rem 0.85rem;
        transition: all 0.15s ease;
        white-space: normal;
        height: auto;
        line-height: 1.4;
    }
    .stButton > button:hover {
        border-color: #6366f1;
        background: #f5f3ff;
        transform: translateX(2px);
        color: #4338ca;
    }
    .stButton > button:focus {
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    }
    
    /* ===== Chat messages ===== */
    [data-testid="stChatMessage"] {
        background: transparent;
        padding: 1rem 0;
    }
    
    /* ===== Chat input ===== */
    [data-testid="stChatInput"] {
        background: white;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #6366f1;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
    }
    
    /* ===== Expanders ===== */
    [data-testid="stExpander"] {
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        background: white;
    }
    
    /* Spacing between assistant message body and metadata */
    .meta-spacer {
        height: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Header strip
# ============================================================

st.markdown("""
<div class="app-header">
    <div class="header-brand">
        <div class="header-logo">SC</div>
        <div>
            <p class="header-title">Support Copilot</p>
            <p class="header-subtitle">Self-hostable AI support agent</p>
        </div>
    </div>
    <div class="header-status">
        <span class="status-dot"></span>
        <span>All systems operational</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:
    st.markdown('<div style="font-size: 1.05rem; font-weight: 700; color: #111827;">Quick start</div>', unsafe_allow_html=True)
    st.caption("Click a question to try the agent.")
    
    st.markdown('<div class="sidebar-section">Knowledge base</div>', unsafe_allow_html=True)
    examples_kb = [
        ("🔑", "How do I create an API key?"),
        ("⚠️", "What does a 429 error mean?"),
        ("💎", "What's included in the Pro plan?"),
        ("🔐", "How do I rotate a leaked API key?"),
    ]
    for icon, text in examples_kb:
        if st.button(f"{icon}  {text}", key=f"kb_{text}", use_container_width=True):
            st.session_state["pending_question"] = text
    
    st.markdown('<div class="sidebar-section">Tool calling</div>', unsafe_allow_html=True)
    examples_tools = [
        ("📊", "What's my usage? My email is jane@acme.com"),
        ("🎫", "My email is jane@acme.com — please file a high-priority ticket: I was double-charged $199 in October."),
    ]
    for icon, text in examples_tools:
        if st.button(f"{icon}  {text}", key=f"t_{text}", use_container_width=True):
            st.session_state["pending_question"] = text
    
    st.markdown('<div class="sidebar-section">Escalation</div>', unsafe_allow_html=True)
    examples_esc = [
        ("🤔", "Can you write me a Python script to integrate your API?"),
        ("📅", "When will Acme launch v3 of the API?"),
        ("🌍", "What's the weather forecast for Paris this weekend?"),
    ]
    for icon, text in examples_esc:
        if st.button(f"{icon}  {text}", key=f"e_{text}", use_container_width=True):
            st.session_state["pending_question"] = text
    
    st.markdown('<div class="sidebar-section">Architecture</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size: 0.8rem; color: #6b7280; line-height: 1.6;">'
        '🧠 LangGraph state machine<br>'
        '⚡ Anthropic Claude<br>'
        '📚 ChromaDB retrieval<br>'
        '🔧 Native tool calling<br>'
        '🆘 Confidence escalation'
        '</div>',
        unsafe_allow_html=True,
    )
    
    st.markdown("---")
    if st.button("🔄  Reset conversation", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()
    
    st.markdown("---")
    st.caption("Open-source · MIT license · Drop in any docs.")


# ============================================================
# Main
# ============================================================

if "messages" not in st.session_state:
    st.session_state["messages"] = []


def confidence_class(conf: float) -> str:
    if conf >= 0.8: return "status-high"
    if conf >= 0.6: return "status-med"
    return "status-low"


def confidence_label(conf: float) -> str:
    if conf >= 0.8: return "High confidence"
    if conf >= 0.6: return "Medium confidence"
    return "Low confidence"


def render_meta(meta):
    cat = meta.get("category", "—")
    lat = meta.get("latency", 0)
    conf = meta.get("confidence", 0.0)
    tools = meta.get("tool_calls", [])
    sources = meta.get("sources", [])
    escalated = meta.get("escalated", False)
    
    st.markdown('<div class="meta-spacer"></div>', unsafe_allow_html=True)
    
    pill_class = confidence_class(conf)
    pill_label = confidence_label(conf)
    st.markdown(
        f'<span class="status-pill {pill_class}">● {pill_label} · {conf:.2f}</span>',
        unsafe_allow_html=True,
    )
    
    cols = st.columns(3)
    with cols[0]:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Category</div>'
            f'<div class="metric-value">{cat.title()}</div></div>',
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Latency</div>'
            f'<div class="metric-value">{lat:.2f}s</div></div>',
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Tools used</div>'
            f'<div class="metric-value">{len(tools)}</div></div>',
            unsafe_allow_html=True,
        )
    
    if escalated:
        st.markdown(
            '<div class="escalation-banner">'
            '<div class="escalation-title">⚠️ Escalated to human support</div>'
            '<div class="escalation-body">Confidence dropped below threshold. '
            'A team member will follow up shortly.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    
    if tools:
        with st.expander(f"🔧 Tool calls ({len(tools)})", expanded=False):
            for tc in tools:
                st.markdown(f'<div class="tool-name">{tc["name"]}( )</div>', unsafe_allow_html=True)
                col_in, col_out = st.columns(2)
                with col_in:
                    st.caption("Input")
                    st.json(tc["input"])
                with col_out:
                    st.caption("Result")
                    st.json(tc["result"])
    
    if sources:
        with st.expander(f"📚 Sources ({len(sources)})", expanded=False):
            for s in sources:
                st.markdown(f"- `{s}`")


# Render history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("meta"):
            render_meta(msg["meta"])

# Empty state
if not st.session_state["messages"]:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">💬</div>
        <div class="empty-title">Start a conversation</div>
        <div class="empty-subtitle">
            Ask anything about Acme API, or pick an example from the sidebar.<br>
            The agent will classify, retrieve, call tools if needed, and escalate when confidence drops.
        </div>
    </div>
    """, unsafe_allow_html=True)

# Input
pending = st.session_state.pop("pending_question", None)
if pending is None:
    pending = st.chat_input("Ask anything about Acme API...")

if pending:
    st.session_state["messages"].append({"role": "user", "content": pending})
    with st.chat_message("user"):
        st.markdown(pending)
    
    history = []
    msgs = st.session_state["messages"]
    for i, m in enumerate(msgs[:-1]):
        if m["role"] == "user" and i + 1 < len(msgs) and msgs[i + 1]["role"] == "assistant":
            history.append({"question": m["content"], "answer": msgs[i + 1]["content"]})
    
    with st.chat_message("assistant"):
        with st.spinner("Classifying, retrieving, reasoning..."):
            result = run_agent(pending, history)
        st.markdown(result["answer"])
        meta = {
            "category": result.get("category", "other"),
            "latency": result.get("metrics", {}).get("latency_seconds", 0),
            "confidence": result.get("confidence", 0.0),
            "escalated": result.get("needs_human", False),
            "tool_calls": result.get("tool_calls", []),
            "sources": result.get("sources", []),
        }
        render_meta(meta)
    
    st.session_state["messages"].append({
        "role": "assistant",
        "content": result["answer"],
        "meta": meta,
    })
