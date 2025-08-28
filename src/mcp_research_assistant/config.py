from __future__ import annotations

import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))
    notes_dir: Path = Path(os.getenv("NOTES_DIR", "data/notes"))
    github_token: str | None = os.getenv("GITHUB_TOKEN")
    github_repo: str | None = os.getenv("GITHUB_REPO")  # e.g. "owner/repo"
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")

    class Config:
        arbitrary_types_allowed = True

settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.notes_dir.mkdir(parents=True, exist_ok=True)
