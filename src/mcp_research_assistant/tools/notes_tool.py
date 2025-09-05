from __future__ import annotations

from pathlib import Path
from typing import List, Dict
from ..config import settings
from ..jsonrpc import rpc_method


def save_note(title: str, content: str, subdir: str | None = None) -> dict:
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_"))
    folder = settings.notes_dir / (subdir or "")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{safe_title}.md"
    path.write_text(content, encoding="utf-8")
    return {"path": str(path)}


def list_notes(subdir: str | None = None) -> List[Dict]:
    folder = settings.notes_dir / (subdir or "")
    if not folder.exists():
        return []
    items = []
    for p in folder.rglob("*.md"):
        items.append({"path": str(p), "name": p.stem, "size": p.stat().st_size})
    return items


def read_note(path: str) -> dict:
    p = Path(path)
    content = p.read_text(encoding="utf-8")
    return {"path": str(p), "content": content}


def register_notes_methods():
    rpc_method("notes.save")(save_note)
    rpc_method("notes.list")(list_notes)
    rpc_method("notes.read")(read_note)
