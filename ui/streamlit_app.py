import streamlit as st
import requests

API_BASE = "http://localhost:8000/api"

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DoQA",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    .main { background-color: #0f0f0f; }

    .stApp {
        background-color: #0f0f0f;
        color: #e8e8e8;
    }

    h1, h2, h3 {
        font-family: 'IBM Plex Mono', monospace !important;
        color: #e8e8e8 !important;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .chat-bubble-user {
        background: #1e1e1e;
        border: 1px solid #333;
        border-radius: 12px 12px 2px 12px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 14px;
        color: #e8e8e8;
        text-align: right;
    }

    .chat-bubble-ai {
        background: #141414;
        border: 1px solid #2a2a2a;
        border-left: 3px solid #7EB8F7;
        border-radius: 2px 12px 12px 12px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 14px;
        color: #e8e8e8;
        line-height: 1.7;
    }

    .source-chip {
        display: inline-block;
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 11px;
        font-family: 'IBM Plex Mono', monospace;
        color: #7EB8F7;
        margin: 3px 3px 3px 0;
    }

    .status-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-family: 'IBM Plex Mono', monospace;
    }

    .pill-success { background: #0d2b1a; color: #4ade80; border: 1px solid #166534; }
    .pill-waiting { background: #1a1a0d; color: #facc15; border: 1px solid #854d0e; }

    .stButton > button {
        background: #7EB8F7;
        color: #0f0f0f;
        border: none;
        border-radius: 6px;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 500;
        font-size: 13px;
        padding: 8px 20px;
        width: 100%;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background: #a8cffa;
        color: #0f0f0f;
    }

    .stTextInput > div > div > input {
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        color: #e8e8e8;
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 14px;
    }

    .sidebar-section {
        background: #141414;
        border: 1px solid #222;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }

    .sidebar-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 10px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 8px;
    }

    div[data-testid="stFileUploader"] {
        background: #141414;
        border: 1px dashed #333;
        border-radius: 8px;
    }

    .stSpinner > div { border-top-color: #7EB8F7 !important; }

    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "doc_loaded" not in st.session_state:
    st.session_state.doc_loaded = False
if "doc_name" not in st.session_state:
    st.session_state.doc_name = ""

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📄 DoQA")
    st.markdown("<p style='color:#666; font-size:13px; font-family:IBM Plex Mono, monospace;'>document intelligence</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("<div class='sidebar-label'>Upload Document</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["pdf"], label_visibility="collapsed")

    if uploaded_file:
        if st.button("⬆ Ingest PDF"):
            with st.spinner("Parsing and indexing..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/upload",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.doc_loaded = True
                        st.session_state.doc_name = uploaded_file.name
                        st.session_state.messages = []
                        st.success(f"✓ {data['chunks_indexed']} chunks indexed")
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to API. Is the FastAPI server running?")

    st.divider()

    if st.session_state.doc_loaded:
        st.markdown(f"""
        <div class='sidebar-section'>
            <div class='sidebar-label'>Active Document</div>
            <div style='font-size:13px; color:#e8e8e8; word-break:break-all;'>{st.session_state.doc_name}</div>
            <div style='margin-top:8px;'><span class='status-pill pill-success'>● ready</span></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='sidebar-section'>
            <div class='sidebar-label'>Status</div>
            <span class='status-pill pill-waiting'>○ no document loaded</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("<div class='sidebar-label'>Settings</div>", unsafe_allow_html=True)
    top_k = st.slider("Chunks to retrieve (top-k)", min_value=1, max_value=10, value=5)

    if st.session_state.messages:
        if st.button("🗑 Clear Chat"):
            st.session_state.messages = []
            st.rerun()

# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown("# DoQA")
st.markdown("<p style='color:#555; font-family:IBM Plex Mono,monospace; font-size:13px; margin-top:-12px;'>Ask anything about your document</p>", unsafe_allow_html=True)
st.divider()

# Chat history
chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        <div style='text-align:center; padding: 60px 20px; color:#444;'>
            <div style='font-size:40px; margin-bottom:16px;'>📄</div>
            <div style='font-family:IBM Plex Mono,monospace; font-size:14px;'>Upload a PDF in the sidebar to get started</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"<div class='chat-bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-bubble-ai'>{msg['content']}</div>", unsafe_allow_html=True)
                if msg.get("sources"):
                    source_html = "".join([
                        f"<span class='source-chip'>pg {s['page']} · {s['score']}</span>"
                        for s in msg["sources"]
                    ])
                    st.markdown(f"<div style='margin-top:4px;'>{source_html}</div>", unsafe_allow_html=True)

st.divider()

# Input area
col1, col2 = st.columns([5, 1])
with col1:
    question = st.text_input("", placeholder="Ask a question about your document...", label_visibility="collapsed", key="question_input")
with col2:
    ask = st.button("Ask →")

if ask and question.strip():
    if not st.session_state.doc_loaded:
        st.warning("Please upload and ingest a PDF first.")
    else:
        st.session_state.messages.append({"role": "user", "content": question})

        with st.spinner("Retrieving and generating..."):
            try:
                response = requests.post(
                    f"{API_BASE}/query",
                    json={"question": question, "top_k": top_k}
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": data["answer"],
                        "sources": data.get("sources", [])
                    })
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Error: {response.json().get('detail', 'Something went wrong.')}",
                        "sources": []
                    })
            except requests.exceptions.ConnectionError:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Cannot connect to the API server. Make sure FastAPI is running on port 8000.",
                    "sources": []
                })

        st.rerun()