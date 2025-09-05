from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from .tools.arxiv_tool import search_arxiv
from .tools.summarizer_tool import summarize_text, summarize_arxiv_items
from .tools.notes_tool import save_note, list_notes, read_note
from .tools.github_tool import publish_notes


server = Server("mcp-research-assistant")


def _text_payload(obj: Any) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps(obj, ensure_ascii=False, indent=2))]


@server.tool("arxiv.search")
async def _tool_arxiv_search(query: str, max_results: int = 5) -> list[types.TextContent]:
    results = search_arxiv(query=query, max_results=max_results)
    return _text_payload(results)


@server.tool("summarize.text")
async def _tool_summarize_text(text: str, max_words: int = 150, model: str = "") -> list[types.TextContent]:
    res = summarize_text(text=text, max_words=max_words, model=model)
    return _text_payload(res)


@server.tool("summarize.arxiv_items")
async def _tool_summarize_items(items: list[dict], max_words: int = 150, model: str = "") -> list[types.TextContent]:
    res = summarize_arxiv_items(items=items, max_words=max_words, model=model)
    return _text_payload(res)


@server.tool("notes.save")
async def _tool_notes_save(title: str, content: str, subdir: str | None = None) -> list[types.TextContent]:
    res = save_note(title=title, content=content, subdir=subdir)
    return _text_payload(res)


@server.tool("notes.list")
async def _tool_notes_list(subdir: str | None = None) -> list[types.TextContent]:
    res = list_notes(subdir=subdir)
    return _text_payload(res)


@server.tool("notes.read")
async def _tool_notes_read(path: str) -> list[types.TextContent]:
    res = read_note(path=path)
    return _text_payload(res)


@server.tool("github.publish")
async def _tool_github_publish(commit_message: str = "Update research notes", paths: list[str] | None = None) -> list[types.TextContent]:
    res = publish_notes(commit_message=commit_message, paths=paths)
    return _text_payload(res)


async def amain():
    async with stdio_server() as (read, write):
        await server.run(read, write)


def main():
    asyncio.run(amain())


if __name__ == "__main__":
    main()
