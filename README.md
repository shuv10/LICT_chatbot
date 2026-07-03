# 🎓 LICT Campus Assistant — Professional Streamlit Chatbot

A full-stack, animated, ChatGPT-style chatbot built with **Streamlit**, powered by the **Groq API** (LLM) and **Tavily API** (live web search), with user accounts, persistent chat history, and a built-in Lumbini ICT Campus knowledge base.

## ✨ Features

- 🔐 **User Login & Registration** — SQLite-backed, salted + hashed passwords (PBKDF2-SHA256)
- 💬 **ChatGPT-style chat UI** with animated message bubbles, typing indicator, and streaming responses
- ⚡ **Groq API** integration (Llama 3.3 70B, Llama 3.1 8B Instant, Mixtral, Gemma2)
- 🌐 **Tavily live web search** blended into answers when enabled
- 🎓 **Lumbini ICT Campus knowledge base** (`data.json`) — courses, leadership, contact info, FAQs, auto-fetched from [lict.edu.np](https://lict.edu.np/)
- 👋 **Smart greeting detection** — "hii", "hello", "namaste", "good morning", etc. get warm, varied responses instead of going to the LLM
- 🗂️ **Multi-session chat history** stored in SQLite, switchable from the sidebar
- 🌗 **Dark / Light theme toggle**
- ⬇️ **Downloadable chat exports** (Markdown & JSON)
- 📝 Lightweight interaction log also mirrored into `data.json`
- 👤 **Guest mode** for trying it out without registering

## 📁 Project Structure

```
groqbot/
├── app.py                 # Main Streamlit app
├── auth.py                 # Login / Register UI
├── database.py              # SQLite layer (users, sessions, chats)
├── groq_client.py            # Groq API wrapper (streaming + non-streaming)
├── tavily_client.py           # Tavily web search wrapper
├── utils.py                 # data.json helpers, greeting detection, exports
├── data.json                # Knowledge base + greetings + interaction log
├── style.css                # Dark/Light theme + animations
├── requirements.txt
├── .streamlit/config.toml     # Streamlit theme config
└── README.md
```

## 🚀 Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Add your API keys**

   Copy `.env.example` to `.env` and fill in your real keys:

   ```bash
   cp .env.example .env
   ```

   ```env
   GROQ_API_KEY=gsk_your_real_key
   TAVILY_API_KEY=tvly_your_real_key
   ```

   Keys are loaded automatically via `python-dotenv` — they are never shown or entered in the UI. Never commit your real `.env` file.

3. **Run the app**

   ```bash
   streamlit run app.py
   ```

4. **Register an account** (or click "Continue as Guest") and start chatting!

## 🗄️ Database

On first run, `database.py` auto-creates `users.db` (SQLite) with three tables:

- `users` — account info, salted password hash, theme preference
- `sessions` — one row per chat session (title, timestamps)
- `chats` — every message, linked to a session and user

## 🎓 Lumbini ICT Campus Data

`data.json` ships pre-loaded with real data fetched from https://lict.edu.np/ — institute info, vision/mission, courses (BSc. CSIT, BCA, BIM, BHM), leadership messages, and FAQs. Ask the bot things like:

- "What courses does Lumbini ICT Campus offer?"
- "Who is the principal of LICT?"
- "How do I contact Lumbini ICT Campus?"

The bot automatically detects campus-related questions and grounds its answer in this data.

## 🔒 Security Notes

This is a learning/demo project. For production use you'd want to:
- Move API keys to environment variables / secrets manager instead of sidebar input
- Add rate limiting & HTTPS
- Add email verification for registration
- Add CSRF protection if exposing publicly

## 📦 Downloadable

This entire project is packaged as a zip — extract it, `pip install -r requirements.txt`, and run `streamlit run app.py`.

Enjoy! ⚡
"# LICT_chatbot" 
