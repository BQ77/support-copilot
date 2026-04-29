"""Support Copilot - polished Streamlit UI."""
import streamlit as st
from agent import run_agent

st.set_page_config(
    page_title="Support Copilot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Custom CSS
# ============================================================

st.markdown("""
<style>
    /* Hide Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Hero title */
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem;
    }
    .hero-subtitle {
        font-size: 1rem;
        color: #6b7280;
        margin-bottom: 1.5rem;
    }
    
    /* Status pill */
    .status-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .status-high { background: #dcfce7; color: #166534; }
    .status-med  { background: #fef3c7; color: #92400e; }
    .status-low  { background: #fee2e2; color: #991b1b; }
    
    /* Metric card */
    .metric-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        text-align: center;
    }
    .metric-label {
        font-size: 0.7rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        font-size: 1.25rem;
        font-weight: 600;
        color: #111827;
    }
    
    /* Escalation banner */
    .escalation-banner {
        background: linear-gradient(135deg, #fef2f2 0%, #fce7f3 100%);
        border-left: 4px solid #dc2626;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .escalation-title {
        font-weight: 700;
        color: #991b1b;
        margin-bottom: 0.25rem;
    }
    .escalation-body {
        color: #7f1d1d;
        font-size: 0.9rem;
    }
    
    /* Tool call card */
    .tool-card {
        background: #eef2ff;
        border: 1px solid #c7d2fe;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
    }
    .tool-name {
        font-weight: 600;
        color: #4338ca;
        font-family: 'SF Mono', Monaco, monospace;
    }
    
    /* Sidebar tweaks */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fafafa 0%, #f4f4f5 100%);
    }
    
    /* Example chips */
    .stButton > button {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 999px;
        text-align: left;
        font-size: 0.85rem;
        font-weight: 500;
        transition: all 0.15s;
    }
    .stButton > button:hover {
        border-color: #6366f1;
        background: #f5f3ff;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:
    st.markdown("### 🤖 Support Copilot")
    st.caption("Open-source AI support agent")
    
    st.markdown("---")
    st.markdown("**Tech stack**")
    st.markdown(
        "- 🧠 LangGraph state machine\n"
        "- ⚡ Anthropic Claude\n"
        "- 📚 ChromaDB vector retrieval\n"
        "- 🔧 Native tool calling (MCP-ready)\n"
        "- 🆘 Confidence-based escalation"
    )
    
    st.markdown("---")
    st.markdown("**How it works**")
    st.markdown(
        "1. **Classify** the question\n"
        "2. **Retrieve** relevant docs\n"
        "3. **Generate** grounded answer\n"
        "4. **Call tools** if needed\n"
        "5. **Escalate** if confidence < 0.6"
    )
    
    st.markdown("---")
    st.markdown("**Try asking:**")
    examples = [
        ("🔑", "How do I create an API key?"),
        ("⚠️", "What does a 429 error mean?"),
        ("💎", "What's included in the Pro plan?"),
        ("📊", "What's my account usage? My email is jane@acme.com"),
        ("🎫", "I want to dispute my last invoice — please help."),
    ]
    for icon, text in examples:
        if st.button(f"{icon}  {text}", key=f"ex_{text}", use_container_width=True):
            st.session_state["pending_question"] = text
    
    st.markdown("---")
    if st.button("🔄 Reset conversation", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()
    
    st.markdown("---")
    st.caption("Built with ❤️ for SMBs who can't afford $50K/yr support tools.")


# ============================================================
# Main
# ============================================================

st.markdown('<div class="hero-title">Support Copilot</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Self-hostable AI support agent. Drop in your docs, ship in an afternoon.</div>',
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state["messages"] = []


def confidence_class(conf: float) -> str:
    if conf >= 0.8:
        return "status-high"
    if conf >= 0.6:
        return "status-med"
    return "status-low"


def confidence_label(conf: float) -> str:
    if conf >= 0.8:
        return "High confidence"
    if conf >= 0.6:
        return "Medium confidence"
    return "Low confidence"


def render_meta(meta):
    """Render the metric strip + tool calls + sources for an answer."""
    cat = meta.get("category", "—")
    lat = meta.get("latency", 0)
    conf = meta.get("confidence", 0.0)
    tools = meta.get("tool_calls", [])
    sources = meta.get("sources", [])
    escalated = meta.get("escalated", False)
    
    # Status pill
    pill_class = confidence_class(conf)
    pill_label = confidence_label(conf)
    st.markdown(
        f'<span class="status-pill {pill_class}">{pill_label} · {conf:.2f}</span>',
        unsafe_allow_html=True,
    )
    
    # Metric strip
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
    
    # Escalation banner
    if escalated:
        st.markdown(
            '<div class="escalation-banner">'
            '<div class="escalation-title">⚠️ Escalated to human support</div>'
            '<div class="escalation-body">Confidence dropped below threshold. '
            'A team member will follow up shortly.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    
    # Tool calls
    if tools:
        with st.expander(f"🔧 Tool calls ({len(tools)})", expanded=False):
            for tc in tools:
                st.markdown(
                    f'<div class="tool-card">'
                    f'<div class="tool-name">{tc["name"]}( )</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                col_in, col_out = st.columns(2)
                with col_in:
                    st.caption("Input")
                    st.json(tc["input"])
                with col_out:
                    st.caption("Result")
                    st.json(tc["result"])
    
    # Sources
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
        with st.spinner("🤔 Classifying, retrieving, and reasoning..."):
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

# Empty state
if not st.session_state["messages"] and not pending:
    st.markdown("---")
    st.markdown(
        "### 👋 Welcome\n"
        "Click an example in the sidebar, or type a question below to start. "
        "The agent classifies your question, retrieves relevant docs, calls tools "
        "if needed, and escalates to a human when it's not confident enough."
    )
