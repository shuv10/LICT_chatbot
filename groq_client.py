"""
groq_client.py
Thin wrapper around the Groq Chat Completions API.
"""

import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Good general-purpose default; user can change in the sidebar.
DEFAULT_MODEL = "llama-3.3-70b-versatile"

AVAILABLE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]


def stream_chat_completion(api_key: str, messages: list, model: str = DEFAULT_MODEL,
                            temperature: float = 0.7, max_tokens: int = 1024):
    """
    Generator that yields content chunks (str) as they stream from Groq.
    `messages` must be a list of {"role": ..., "content": ...} dicts.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    with requests.post(GROQ_API_URL, headers=headers, json=payload, stream=True, timeout=60) as resp:
        if resp.status_code != 200:
            raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text}")

        for line in resp.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8")
            if not decoded.startswith("data: "):
                continue
            data = decoded[len("data: "):]
            if data.strip() == "[DONE]":
                break
            try:
                import json
                chunk = json.loads(data)
                delta = chunk["choices"][0]["delta"]
                content = delta.get("content")
                if content:
                    yield content
            except Exception:
                continue


def chat_completion(api_key: str, messages: list, model: str = DEFAULT_MODEL,
                     temperature: float = 0.7, max_tokens: int = 1024) -> str:
    """Non-streaming convenience call. Returns the full text response."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text}")
    data = resp.json()
    return data["choices"][0]["message"]["content"]
