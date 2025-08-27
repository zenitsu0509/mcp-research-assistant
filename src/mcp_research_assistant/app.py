from __future__ import annotations

import json
from typing import Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .jsonrpc import router as jsonrpc_router
from .tools.arxiv_tool import register_arxiv_methods
from .tools.notes_tool import register_notes_methods
from .tools.github_tool import register_github_methods
from .tools.summarizer_tool import register_summarizer_methods

app = FastAPI(title="MCP Research Assistant", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
    ,allow_headers=["*"]
)

app.include_router(jsonrpc_router)

# Register tool methods
register_arxiv_methods()
register_notes_methods()
register_github_methods()
register_summarizer_methods()

def main():
    import uvicorn
    uvicorn.run("mcp_research_assistant.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
