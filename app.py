"""
app.py
LICT Campus Assistant — a professional, animated, ChatGPT-style Streamlit chatbot for Lumbini ICT Campus.

Features:
 - API keys loaded securely from .env (never exposed in the UI)
 - User registration & login (SQLite, salted+hashed passwords)
 - Streaming chat powered by the Groq API
 - Optional live web search via Tavily, blended into the prompt
 - Local "Lumbini ICT Campus" knowledge base (data.json) auto-injected when relevant
 - Persistent multi-session chat history (SQLite) + lightweight JSON log (data.json)
 - Dark / light theme toggle, futuristic ChatGPT-style two-column layout
 - Smart greeting detection ("hii", "hello", "namaste", etc.)
 - Downloadable chat export (Markdown / JSON)
"""

import os
import uuid
import time

import streamlit as st
from dotenv import load_dotenv

import database as db
import utils
from auth import show_auth_screen
from groq_client import stream_chat_completion, AVAILABLE_MODELS, DEFAULT_MODEL
from tavily_client import tavily_search, format_search_context

# --------------------------------------------------------------------------- #
# ENV / CONFIG
# --------------------------------------------------------------------------- #
load_dotenv()
# Accept both spellings since "GROK_API_KEY" is a common typo for Groq's key
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

st.set_page_config(
    page_title="LICT Campus Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()

# --------------------------------------------------------------------------- #
# SESSION STATE DEFAULTS
# --------------------------------------------------------------------------- #
defaults = {
    "user": None,
    "theme": "dark",
    "use_web_search": False,
    "model": DEFAULT_MODEL,
    "current_session_id": None,
    "messages": [],
    "temperature": 0.7,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def load_css():
    with open("style.css") as f:
        css = f.read()

    # NOTE: Streamlit strips <script> tags from st.markdown() for security,
    # so we can't toggle theme via JS. Instead we inject the correct CSS
    # variable block directly for the active theme — guaranteed to apply.
    if st.session_state.theme == "dark":
        theme_vars = """
        :root {
            --bg-primary: #08090d; --bg-secondary: #0f1117; --bg-card: #14161e;
            --bg-elevated: #191c26; --text-primary: #eef1f8; --text-secondary: #8b93a7;
            --accent: #00f0ff; --accent-2: #8b5cf6; --accent-3: #ff3d9a;
            --user-bubble: linear-gradient(135deg, #00f0ff 0%, #8b5cf6 100%);
            --bot-bubble: #14161e; --border-color: #232634;
            --border-glow: rgba(0, 240, 255, 0.25); --success: #3fd97f; --danger: #ff4d6d;
            --shadow-glow: 0 0 30px rgba(139, 92, 246, 0.15);
        }
        """
    else:
        theme_vars = """
        :root {
            --bg-primary: #f4f6fb; --bg-secondary: #ffffff; --bg-card: #ffffff;
            --bg-elevated: #ffffff; --text-primary: #14161f; --text-secondary: #636b7e;
            --accent: #0091ff; --accent-2: #7c3aed; --accent-3: #e1147a;
            --user-bubble: linear-gradient(135deg, #0091ff 0%, #7c3aed 100%);
            --bot-bubble: #eef1f7; --border-color: #e3e7f0;
            --border-glow: rgba(0, 145, 255, 0.18); --success: #1a9e57; --danger: #d4304f;
            --shadow-glow: 0 0 24px rgba(124, 58, 237, 0.08);
        }
        """
    st.markdown(f"<style>{theme_vars}\n{css}</style>", unsafe_allow_html=True)


load_css()

# --------------------------------------------------------------------------- #
# AUTH GATE
# --------------------------------------------------------------------------- #
if st.session_state.user is None:
    show_auth_screen()
    st.stop()

user = st.session_state.user

# --------------------------------------------------------------------------- #
# SIDEBAR — ChatGPT-style navigation rail
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown(
        """
        <div class="brand-row">
            <div class="brand-mark">🎓</div>
            <div class="brand-name">LICT Campus <span>Assistant</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("✦ New chat", use_container_width=True, key="new_chat_btn"):
        st.session_state.current_session_id = str(uuid.uuid4())
        st.session_state.messages = []
        if user["id"] != 0:
            db.create_session(user["id"], st.session_state.current_session_id, "New Chat")
        st.rerun()

    st.markdown("<div class='sidebar-section-label'>Recent chats</div>", unsafe_allow_html=True)

    if user["id"] != 0:
        sessions = db.list_sessions(user["id"])
        if not sessions:
            st.caption("No chats yet — start one above ✨")
        for s in sessions:
            label = s["title"] or "Untitled chat"
            is_active = s["session_id"] == st.session_state.current_session_id
            col1, col2 = st.columns([5, 1])
            with col1:
                if st.button(
                    f"{'🟢' if is_active else '💬'} {label[:26]}",
                    key=f"sess_{s['session_id']}",
                    use_container_width=True,
                ):
                    st.session_state.current_session_id = s["session_id"]
                    history = db.get_session_messages(s["session_id"], user["id"])
                    st.session_state.messages = [{"role": h["role"], "content": h["content"]} for h in history]
                    st.rerun()
            with col2:
                if st.button("✕", key=f"del_{s['session_id']}"):
                    db.delete_session(s["session_id"], user["id"])
                    if st.session_state.current_session_id == s["session_id"]:
                        st.session_state.current_session_id = None
                        st.session_state.messages = []
                    st.rerun()
    else:
        st.caption("Guest mode — chat history isn't saved between visits.")

    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-section-label'>Settings</div>", unsafe_allow_html=True)

    theme_choice = st.toggle("🌙 Dark mode", value=(st.session_state.theme == "dark"))
    st.session_state.theme = "dark" if theme_choice else "light"

    st.session_state.model = st.selectbox(
        "Model", AVAILABLE_MODELS, index=AVAILABLE_MODELS.index(st.session_state.model)
    )
    st.session_state.temperature = st.slider("Creativity", 0.0, 1.5, st.session_state.temperature, 0.1)
    st.session_state.use_web_search = st.toggle(
        "🌐 Live web search", value=st.session_state.use_web_search,
        disabled=not bool(TAVILY_API_KEY),
        help="Requires TAVILY_API_KEY in your .env file" if not TAVILY_API_KEY else "Powered by Tavily",
    )

    if not GROQ_API_KEY:
        st.error("⚠️ GROQ_API_KEY not found in .env", icon="⚠️")
    if st.session_state.use_web_search and not TAVILY_API_KEY:
        st.warning("⚠️ TAVILY_API_KEY not found in .env")

    if st.session_state.messages:
        st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-section-label'>Export</div>", unsafe_allow_html=True)
        md_export = utils.export_chat_as_markdown(st.session_state.messages, title="LICT Campus Assistant Chat Export")
        json_export = utils.export_chat_as_json(st.session_state.messages)
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📄 .md", md_export, file_name="chat_export.md", use_container_width=True)
        with col2:
            st.download_button("🧾 .json", json_export, file_name="chat_export.json", use_container_width=True)

    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="user-card">
            <div class="user-avatar">{(user.get('full_name') or user['username'])[0].upper()}</div>
            <div class="user-meta">
                <div class="user-name">{user.get('full_name') or user['username']}</div>
                <div class="user-handle">@{user['username']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        st.session_state.messages = []
        st.session_state.current_session_id = None
        st.rerun()

# --------------------------------------------------------------------------- #
# MAIN — futuristic centered chat column
# --------------------------------------------------------------------------- #
if st.session_state.current_session_id is None:
    st.session_state.current_session_id = str(uuid.uuid4())
    if user["id"] != 0:
        db.create_session(user["id"], st.session_state.current_session_id, "New Chat")

top_l, top_r = st.columns([5, 1])
with top_l:
    st.markdown(
        """
        <div class="topbar">
            <div class="topbar-title">LICT Campus <span class="accent-text">Assistant</span></div>
            <div class="topbar-sub">Your AI guide to Lumbini ICT Campus · powered by Groq</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with top_r:
    st.markdown(
        f"<div class='ws-badge'>{st.session_state.model.split('-')[0].upper()}</div>",
        unsafe_allow_html=True,
    )

clicked_suggestion = None
if not st.session_state.messages:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-glow"></div>
            <h2>What can I help with today?</h2>
            <p>Ask me anything, try a greeting like <b>"hii"</b>, or ask about <b>Lumbini ICT Campus</b>.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    suggestion_cols = st.columns(3)
    suggestions = [
        ("🎓", "Tell me about Lumbini ICT Campus courses"),
        ("💡", "Explain quantum computing simply"),
        ("🌐", "What's trending in tech today?"),
    ]
    for col, (icon, text) in zip(suggestion_cols, suggestions):
        with col:
            if st.button(f"{icon}  {text}", use_container_width=True, key=f"sugg_{text}"):
                clicked_suggestion = text

# --------------------------------------------------------------------------- #
# RENDER EXISTING MESSAGES
# --------------------------------------------------------------------------- #
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        is_user = msg["role"] == "user"
        avatar = "🧑" if is_user else "🎓"
        row_class = "msg-row user-row" if is_user else "msg-row bot-row"
        bubble_class = "user-bubble" if is_user else "bot-bubble"
        st.markdown(
            f"""
            <div class="{row_class}">
                <div class="msg-avatar">{avatar}</div>
                <div class="chat-bubble {bubble_class}">{msg['content']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# --------------------------------------------------------------------------- #
# CHAT INPUT
# --------------------------------------------------------------------------- #
prompt = st.chat_input("Message LICT Campus Assistant...")
if clicked_suggestion and not prompt:
    prompt = clicked_suggestion

if prompt:
    if not GROQ_API_KEY:
        st.error("GROQ_API_KEY is missing from your .env file. Add it and restart the app.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_container:
        st.markdown(
            f"""<div class="msg-row user-row">
                    <div class="msg-avatar">🧑</div>
                    <div class="chat-bubble user-bubble">{prompt}</div>
                </div>""",
            unsafe_allow_html=True,
        )

    if user["id"] != 0:
        db.save_message(user["id"], st.session_state.current_session_id, "user", prompt)
        if len(st.session_state.messages) == 1:
            db.update_session_title(st.session_state.current_session_id, prompt[:40])
    utils.log_interaction_to_json(user["username"], "user", prompt)

    greeting_key = utils.detect_greeting(prompt)
    response_placeholder = st.empty()
    full_response = ""

    def render_bot(content, cursor=False):
        response_placeholder.markdown(
            f"""<div class="msg-row bot-row">
                    <div class="msg-avatar">🎓</div>
                    <div class="chat-bubble bot-bubble">{content}{'▌' if cursor else ''}</div>
                </div>""",
            unsafe_allow_html=True,
        )

    if greeting_key:
        full_response = utils.get_greeting_response(greeting_key)
        displayed = ""
        for ch in full_response:
            displayed += ch
            render_bot(displayed, cursor=True)
            time.sleep(0.01)
        render_bot(full_response)
    else:
        render_bot(
            '<span class="typing-dots"><span></span><span></span><span></span></span>'
        )

        context_chunks = []
        lict_context = utils.search_lict_knowledge(prompt)
        if lict_context:
            context_chunks.append(f"Lumbini ICT Campus knowledge base:\n{lict_context}")

        if st.session_state.use_web_search and TAVILY_API_KEY:
            try:
                results = tavily_search(TAVILY_API_KEY, prompt)
                context_chunks.append(f"Live web search results:\n{format_search_context(results)}")
            except Exception as e:
                context_chunks.append(f"(Web search failed: {e})")

        system_prompt = (
            "You are LICT Campus Assistant, a friendly, professional, and highly capable AI assistant for Lumbini ICT Campus. "
            "Be clear, concise, and helpful. Use markdown formatting where useful. "
            "If campus knowledge or web search context is provided below, ground your answer in it "
            "and mention it naturally without sounding robotic."
        )
        if context_chunks:
            system_prompt += "\n\nContext:\n" + "\n\n".join(context_chunks)

        api_messages = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.messages[-12:]:
            api_messages.append({"role": m["role"], "content": m["content"]})

        try:
            for chunk in stream_chat_completion(
                api_key=GROQ_API_KEY,
                messages=api_messages,
                model=st.session_state.model,
                temperature=st.session_state.temperature,
            ):
                full_response += chunk
                render_bot(full_response, cursor=True)
            render_bot(full_response)
        except Exception as e:
            full_response = f"⚠️ Error talking to Groq: {e}"
            render_bot(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    if user["id"] != 0:
        db.save_message(user["id"], st.session_state.current_session_id, "assistant", full_response)
    utils.log_interaction_to_json(user["username"], "assistant", full_response)

    st.rerun()
