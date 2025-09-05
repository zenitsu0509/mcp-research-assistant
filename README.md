# MCP Research Assistant

A custom MCP-like server (FastAPI + JSON-RPC) that lets an LLM act as a research assistant:

- Search Arxiv for papers and fetch metadata/abstracts
- Summarize papers or arbitrary text
- Save organized notes locally in Markdown
- Publish notes to a GitHub repository

## Features

- Search Papers – query Arxiv with keywords, fetch abstracts & metadata
- Summarize Papers – LLM-backed (Groq preferred, OpenAI fallback) or simple fallback
- Organize Notes – store as Markdown in `data/notes/`
- Publish Reports – commit & push notes to a GitHub repo via API
- Conversational Interface – call tools via JSON-RPC; suitable for MCP clients

## Tech Stack

- Python 3.9+
- FastAPI (HTTP server) + simple JSON-RPC handler
- Arxiv API (python `arxiv` lib)
- PyGitHub for publishing notes to GitHub
- Optional LLMs: Groq (preferred) and OpenAI for summaries

## Setup

1. Create and activate a virtual environment, then install:

    ```bash
    python -m venv .venv
    source .venv/Scripts/activate
    pip install -e .
    ```

2. Create a `.env` file based on `.env.example`:

    ```properties
    DATA_DIR=data
    NOTES_DIR=data/notes
    GITHUB_TOKEN=ghp_...   # with repo access
    GITHUB_REPO=owner/repo
    # Choose either GROQ or OpenAI (Groq preferred)
    GROQ_API_KEY=gsk_...
    OPENAI_API_KEY=sk_...
    ```

## Run

```bash
python -m mcp_research_assistant.app
# or installed script
mcp-research-assistant
```

Server listens on <http://localhost:8000>

## JSON-RPC Endpoints

POST to `/json-rpc` with a body like:

- Search arxiv

    ```json
    {"jsonrpc":"2.0","method":"arxiv.search","params":{"query":"LLM agents","max_results":3},"id":1}
    ```

- Summarize text (Groq by default; override model if desired)

    ```json
    {"jsonrpc":"2.0","method":"summarize.text","params":{"text":"...","max_words":120,"model":"llama-3.1-70b-versatile"},"id":2}
    ```

- Save a note

    ```json
    {"jsonrpc":"2.0","method":"notes.save","params":{"title":"Paper X","content":"..."},"id":3}
    ```

- Publish notes to GitHub

    ```json
    {"jsonrpc":"2.0","method":"github.publish","params":{"commit_message":"Add notes"},"id":4}
    ```

## MCP Integration

This server exposes tool-like JSON-RPC methods compatible with MCP clients. Point your client/tooling to call POST http(s)://localhost:8000/json-rpc and wire the methods above as tools.

## Notes

- If GROQ_API_KEY is set, Groq is used first. If not, OpenAI is used when OPENAI_API_KEY is set. Otherwise a simple truncation fallback is used.
- GitHub publishing writes files based on paths relative to the current working dir. By default it includes all Markdown notes under `data/notes`.
