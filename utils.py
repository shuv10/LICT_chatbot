"""
utils.py
Helper functions: data.json read/write, greeting detection,
Lumbini ICT Campus knowledge lookups, and chat export helpers.
"""

import json
import os
import re
import datetime

DATA_FILE = "data.json"


def load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"knowledge_base": {}, "faq": [], "greetings": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def log_interaction_to_json(username: str, role: str, content: str):
    """Append a lightweight log of every message into data.json under 'interaction_log'."""
    data = load_data()
    log = data.setdefault("interaction_log", [])
    log.append({
        "user": username,
        "role": role,
        "content": content,
        "timestamp": datetime.datetime.now().isoformat(),
    })
    # Keep the log from growing forever
    data["interaction_log"] = log[-500:]
    save_data(data)


_GREETING_PATTERNS = {
    "hii": "hii", "hi": "hi", "hiya": "hi", "hello": "hello", "helo": "hello",
    "hey": "hey", "heyy": "hey", "yo": "hey",
    "good morning": "good morning", "good afternoon": "good afternoon",
    "good evening": "good evening", "good night": "good evening",
    "namaste": "namaste", "namaskar": "namaste",
    "bye": "bye", "goodbye": "bye", "see you": "bye",
    "thanks": "thanks", "thank you": "thanks", "thx": "thanks",
}


def detect_greeting(text: str):
    """
    Return a greeting key (e.g. 'hello') if the message is essentially just
    a greeting, else None. Handles typos like 'hii', 'helo', etc.
    """
    cleaned = re.sub(r"[^a-z\s]", "", text.lower().strip())
    cleaned = cleaned.strip()
    if not cleaned:
        return None
    # Direct match
    if cleaned in _GREETING_PATTERNS:
        return _GREETING_PATTERNS[cleaned]
    # Match if message is short (<=4 words) and starts with a known greeting word
    words = cleaned.split()
    if len(words) <= 4:
        for pattern, key in _GREETING_PATTERNS.items():
            if cleaned.startswith(pattern):
                return key
    return None


def get_greeting_response(key: str) -> str:
    import random
    data = load_data()
    greetings = data.get("greetings", {})
    options = greetings.get(key, ["Hello! How can I help you today?"])
    return random.choice(options)


def search_lict_knowledge(query: str) -> str | None:
    """
    Very simple keyword search across the locally stored Lumbini ICT Campus
    knowledge base (data.json). Returns a context string to feed the LLM,
    or None if nothing relevant is found.
    """
    data = load_data()
    kb = data.get("knowledge_base", {})
    faq = data.get("faq", [])
    q = query.lower()

    if not any(k in q for k in ["lict", "lumbini ict", "campus", "gaindakot", "csit", "bca", "bim", "bhm", "kaligandaki"]):
        return None

    context_parts = []
    institute = kb.get("institute", {})
    if institute:
        context_parts.append(
            f"Institute: {institute.get('name')} located at {institute.get('address')}. "
            f"Phone: {', '.join(institute.get('phone', []))}. Website: {institute.get('website')}."
        )
    if kb.get("about"):
        context_parts.append(f"About: {kb['about']}")
    if "vision" in q and kb.get("vision"):
        context_parts.append(f"Vision: {kb['vision']}")
    if "mission" in q and kb.get("mission"):
        context_parts.append(f"Mission: {kb['mission']}")
    if any(k in q for k in ["course", "program", "csit", "bca", "bim", "bhm"]):
        courses = kb.get("courses_offered", [])
        context_parts.append("Courses offered: " + "; ".join(
            f"{c['code']} ({c['full_name']})" for c in courses
        ))
    if any(k in q for k in ["principal", "chairman", "leadership", "head"]):
        leadership = kb.get("leadership", {})
        for role, info in leadership.items():
            context_parts.append(f"{info.get('title')}: {info.get('name')}")
    for item in faq:
        if any(word in item["question"].lower() for word in q.split()):
            context_parts.append(f"Q: {item['question']} A: {item['answer']}")

    return "\n".join(context_parts) if context_parts else None


def export_chat_as_markdown(messages: list, title: str = "Chat Export") -> str:
    lines = [f"# {title}", f"_Exported on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}_", ""]
    for m in messages:
        role = "🧑 You" if m["role"] == "user" else "🤖 Assistant"
        lines.append(f"**{role}:**\n\n{m['content']}\n")
    return "\n".join(lines)


def export_chat_as_json(messages: list) -> str:
    return json.dumps(messages, indent=2, ensure_ascii=False)
