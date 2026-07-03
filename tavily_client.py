"""
tavily_client.py
Thin wrapper around the Tavily Search API, used to give the chatbot
live web-search / "real-time knowledge" abilities.
"""

import requests

TAVILY_API_URL = "https://api.tavily.com/search"


def tavily_search(api_key: str, query: str, max_results: int = 5, search_depth: str = "basic"):
    """
    Run a Tavily web search and return a list of result dicts:
    [{"title": ..., "url": ..., "content": ...}, ...]
    """
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "include_answer": True,
    }
    resp = requests.post(TAVILY_API_URL, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Tavily API error {resp.status_code}: {resp.text}")
    data = resp.json()
    return data


def format_search_context(tavily_response: dict) -> str:
    """Turn a Tavily response into a compact context string for the LLM prompt."""
    parts = []
    if tavily_response.get("answer"):
        parts.append(f"Quick answer: {tavily_response['answer']}")
    for r in tavily_response.get("results", []):
        parts.append(f"- {r.get('title')}: {r.get('content', '')[:300]} (source: {r.get('url')})")
    return "\n".join(parts)
