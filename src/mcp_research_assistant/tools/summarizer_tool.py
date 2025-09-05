from __future__ import annotations

from typing import List, Dict
import textwrap
import os

from ..jsonrpc import rpc_method
from ..config import settings

# LLM SDKs (optional)
try:
    from groq import Groq
    _groq_available = True
except Exception:
    _groq_available = False

try:
    from openai import OpenAI
    _openai_available = True
except Exception:
    _openai_available = False


def _summarize_with_groq(text: str, max_words: int, model: str) -> str:
    if not settings.groq_api_key or not _groq_available:
        raise RuntimeError("GROQ not available or GROQ_API_KEY not set")
    client = Groq(api_key=settings.groq_api_key)
    prompt = (
        f"Summarize the following text in up to {max_words} words focusing on key contributions, findings, and limitations.\n\n{text}"
    )
    # For Groq, a good default model is 'llama-3.1-70b-versatile' or 'mixtral-8x7b-32768'
    chosen = model or "llama-3.1-70b-versatile"
    resp = client.chat.completions.create(
        model=chosen,
        messages=[
            {"role": "system", "content": "You are a concise research assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


def _summarize_with_openai(text: str, max_words: int, model: str) -> str:
    if not settings.openai_api_key or not _openai_available:
        raise RuntimeError("OpenAI not available or OPENAI_API_KEY not set")
    client = OpenAI(api_key=settings.openai_api_key)
    prompt = (
        f"Summarize the following text in up to {max_words} words focusing on key contributions, findings, and limitations.\n\n{text}"
    )
    chosen = model or "gpt-4o-mini"
    resp = client.chat.completions.create(
        model=chosen,
        messages=[
            {"role": "system", "content": "You are a concise research assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


def summarize_text(text: str, max_words: int = 150, model: str = "") -> Dict:
    # Prefer Groq if configured; fallback to OpenAI; final fallback is truncation
    try:
        if settings.groq_api_key and _groq_available:
            out = _summarize_with_groq(text, max_words, model)
        elif settings.openai_api_key and _openai_available:
            out = _summarize_with_openai(text, max_words, model)
        else:
            raise RuntimeError("No LLM configured")
    except Exception:
        out = textwrap.shorten(text, width=max_words * 6, placeholder="…")
    return {"summary": out}


def summarize_arxiv_items(items: List[Dict], max_words: int = 150, model: str = "") -> List[Dict]:
    out = []
    for it in items:
        content = f"Title: {it.get('title')}\nAuthors: {it.get('authors')}\nAbstract: {it.get('summary')}"
        out.append({
            "entry_id": it.get("entry_id"),
            "title": it.get("title"),
            "summary": summarize_text(content, max_words=max_words, model=model)["summary"],
        })
    return out


def register_summarizer_methods():
    rpc_method("summarize.text")(summarize_text)
    rpc_method("summarize.arxiv_items")(summarize_arxiv_items)
