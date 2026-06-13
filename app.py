"""
Streamlit frontend — light theme, clean layout.
Run: streamlit run app.py
Backend must be running: uvicorn main:app --reload --port 8000
"""

import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="AskFirst AI", page_icon="✦", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
    background: #f9f9fb;
    color: #1a1a1a;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #ebebeb;
}
[data-testid="stSidebar"] > div:first-child { padding: 0; }

.sb-header {
    padding: 20px 18px 16px;
    border-bottom: 1px solid #f2f2f2;
    display: flex;
    align-items: center;
    gap: 8px;
}
.sb-logo { font-size: 1rem; font-weight: 600; color: #1a1a1a; }
.sb-logo em { font-style: normal; color: #5b5bd6; }

.sb-section { font-size: 0.67rem; font-weight: 600; letter-spacing: .07em;
    text-transform: uppercase; color: #bbb; padding: 14px 18px 4px; }

[data-testid="stSidebar"] .stButton button {
    background: transparent !important;
    border: none !important; color: #555 !important;
    text-align: left !important; padding: 7px 12px !important;
    font-size: 0.83rem !important; border-radius: 8px !important;
    box-shadow: none !important; font-family: 'Inter', sans-serif !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: #f4f4f7 !important; color: #1a1a1a !important;
}
[data-testid="stSidebar"] .stButton button[kind="primary"] {
    background: #5b5bd6 !important; color: #fff !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] .stButton button[kind="primary"]:hover {
    background: #4a4ac4 !important;
}

.sb-foot { position: absolute; bottom: 14px; left: 0; right: 0;
    text-align: center; font-size: 0.69rem; color: #d0d0d0; }

/* Main */
[data-testid="stMain"] { background: #f9f9fb; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: 100% !important; }

/* Header bar */
.chat-hdr {
    background: #fff;
    border-bottom: 1px solid #ebebeb;
    padding: 13px 36px;
    display: flex; align-items: center; gap: 10px;
    position: sticky; top: 0; z-index: 50;
}
.chat-hdr-title { font-size: 0.9rem; font-weight: 500; color: #1a1a1a;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chat-hdr-pill { font-size: 0.67rem; background: #eeeeff; color: #5b5bd6;
    padding: 2px 9px; border-radius: 20px; font-weight: 500; flex-shrink: 0; }

/* Message list */
.msgs { padding: 28px 36px 150px; max-width: 800px;
    margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }

.row { display: flex; gap: 10px; align-items: flex-start; }
.row.usr { flex-direction: row-reverse; }

.av { width: 28px; height: 28px; border-radius: 50%; font-size: 0.7rem;
    font-weight: 600; display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 3px; }
.av.ai-av  { background: #eeeeff; color: #5b5bd6; }
.av.usr-av { background: #e9f5eb; color: #2e7d32; }

.bbl { max-width: 72%; padding: 10px 14px; font-size: 0.875rem;
    line-height: 1.7; word-break: break-word; }
.bbl.u {
    background: #fff; color: #1a1a1a;
    border: 1px solid #e4e4e7;
    border-radius: 16px 16px 4px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.bbl.a {
    background: #eeeeff; color: #1a1a1a;
    border-radius: 16px 16px 16px 4px;
}

/* Input */
.inp-wrap { position: fixed; bottom: 0; left: 0; right: 0;
    background: linear-gradient(to top, #f9f9fb 72%, transparent);
    padding: 10px 36px 22px; z-index: 100; }
.inp-box { max-width: 800px; margin: 0 auto; background: #fff;
    border: 1px solid #e0e0e0; border-radius: 12px;
    display: flex; align-items: center; padding: 4px 4px 4px 14px; gap: 6px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    transition: border-color .2s, box-shadow .2s; }
.inp-box:focus-within { border-color: #5b5bd6; box-shadow: 0 2px 14px rgba(91,91,214,.1); }

.inp-box .stTextInput input {
    background: transparent !important; border: none !important;
    color: #1a1a1a !important; font-size: 0.875rem !important;
    padding: 6px 0 !important; box-shadow: none !important;
    font-family: 'Inter', sans-serif !important;
}
.inp-box .stTextInput input::placeholder { color: #bbb !important; }
.inp-box .stTextInput { flex: 1; }
.inp-box .stFormSubmitButton button {
    background: #5b5bd6 !important; color: #fff !important;
    border: none !important; border-radius: 9px !important;
    padding: 8px 18px !important; font-size: 0.83rem !important;
    font-weight: 500 !important; box-shadow: none !important;
    font-family: 'Inter', sans-serif !important;
}
.inp-box .stFormSubmitButton button:hover { background: #4a4ac4 !important; }

/* Landing */
.land { display: flex; flex-direction: column; align-items: center;
    justify-content: center; min-height: 76vh; text-align: center; gap: 8px; }
.land-icon { width: 50px; height: 50px; border-radius: 14px;
    background: #eeeeff; color: #5b5bd6; font-size: 1.3rem;
    display: flex; align-items: center; justify-content: center; margin-bottom: 4px; }
.land-title { font-size: 1.25rem; font-weight: 600; color: #1a1a1a; }
.land-sub { font-size: 0.83rem; color: #aaa; }
.chips { display: flex; gap: 8px; margin-top: 16px; flex-wrap: wrap; justify-content: center; }
.chip { background: #fff; border: 1px solid #e4e4e7; border-radius: 20px;
    padding: 7px 14px; font-size: 0.78rem; color: #555;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04); }

/* Hide chrome */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
.stSpinner > div { border-top-color: #5b5bd6 !important; }
</style>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────────────────────
for k, v in [("active_thread_id", None), ("messages", []), ("threads", [])]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── API helpers ────────────────────────────────────────────────────────────────
def fetch_threads():
    try:
        r = requests.get(f"{API_URL}/threads", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.sidebar.error(f"Backend unreachable: {e}")
        return []

def create_thread():
    try:
        r = requests.post(f"{API_URL}/threads", json={"title": "New Chat"}, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Failed to create thread: {e}")
        return None

def fetch_messages(thread_id):
    try:
        r = requests.get(f"{API_URL}/threads/{thread_id}", timeout=5)
        r.raise_for_status()
        return r.json().get("messages", [])
    except Exception:
        return []

def delete_thread_api(thread_id):
    try:
        r = requests.delete(f"{API_URL}/threads/{thread_id}", timeout=5)
        r.raise_for_status()
        return True
    except Exception:
        return False

def stream_chat(thread_id, message):
    try:
        with requests.post(
            f"{API_URL}/chat",
            json={"thread_id": thread_id, "message": message},
            stream=True, timeout=60,
        ) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    yield chunk
    except Exception as e:
        yield f"\n\n[Error: {e}]"


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div class="sb-header">
            <div class="sb-logo"><em>✦</em> AskFirst AI</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='padding:12px 12px 4px;'>", unsafe_allow_html=True)
    if st.button("＋  New Chat", use_container_width=True, type="primary"):
        t = create_thread()
        if t:
            st.session_state.active_thread_id = t["id"]
            st.session_state.messages = []
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="sb-section">Conversations</div>', unsafe_allow_html=True)

    threads = fetch_threads()
    st.session_state.threads = threads

    if not threads:
        st.markdown(
            "<div style='padding:6px 18px;font-size:0.8rem;color:#ccc;'>No conversations yet.</div>",
            unsafe_allow_html=True,
        )

    for thread in threads:
        tid = thread["id"]
        title = (thread["title"] or "New Chat")[:36]
        is_active = tid == st.session_state.active_thread_id
        c1, c2 = st.columns([7, 1])
        with c1:
            lbl = f"**{title}**" if is_active else title
            if st.button(lbl, key=f"t_{tid}", use_container_width=True):
                st.session_state.active_thread_id = tid
                st.session_state.messages = fetch_messages(tid)
                st.rerun()
        with c2:
            if st.button("✕", key=f"d_{tid}", help="Delete"):
                if delete_thread_api(tid):
                    if st.session_state.active_thread_id == tid:
                        st.session_state.active_thread_id = None
                        st.session_state.messages = []
                    st.rerun()

    st.markdown('<div class="sb-foot">Memory persists across all chats</div>', unsafe_allow_html=True)


# ── Main ───────────────────────────────────────────────────────────────────────
if st.session_state.active_thread_id is None:
    st.markdown("""
        <div class="land">
            <div class="land-icon">✦</div>
            <div class="land-title">How can I help you today?</div>
            <div class="land-sub">Pick a conversation or start a new one from the sidebar.</div>
            <div class="chips">
                <div class="chip">✍️ Draft an email</div>
                <div class="chip">🔍 Research a topic</div>
                <div class="chip">💡 Brainstorm ideas</div>
                <div class="chip">🐛 Debug my code</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

else:
    thread_id = st.session_state.active_thread_id
    active = next((t for t in threads if t["id"] == thread_id), None)
    title = (active["title"] if active else "Chat")[:55]

    # Header
    st.markdown(f"""
        <div class="chat-hdr">
            <div class="chat-hdr-title">{title}</div>
            <div class="chat-hdr-pill">✦ AI</div>
        </div>
    """, unsafe_allow_html=True)

    # Messages
    st.markdown('<div class="msgs">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        role = msg["role"]
        content = (
            msg["content"]
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )
        if role == "user":
            st.markdown(f"""
                <div class="row usr">
                    <div class="av usr-av">You</div>
                    <div class="bbl u">{content}</div>
                </div>
            """, unsafe_allow_html=True)
        elif role == "assistant":
            st.markdown(f"""
                <div class="row">
                    <div class="av ai-av">✦</div>
                    <div class="bbl a">{content}</div>
                </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Input bar
    st.markdown('<div class="inp-wrap"><div class="inp-box">', unsafe_allow_html=True)
    with st.form(key="chat_form", clear_on_submit=True):
        c1, c2 = st.columns([9, 1])
        with c1:
            user_input = st.text_input(
                "msg", placeholder="Ask anything…", label_visibility="collapsed"
            )
        with c2:
            submitted = st.form_submit_button("Send", use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    if submitted and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner(""):
            chunks = [c for c in stream_chat(thread_id, user_input)]
        st.session_state.messages.append({"role": "assistant", "content": "".join(chunks)})
        st.rerun()
