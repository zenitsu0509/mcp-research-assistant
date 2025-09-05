from __future__ import annotations

from typing import List
from pathlib import Path
from github import Github, InputGitTreeElement
from ..config import settings
from ..jsonrpc import rpc_method


def publish_notes(commit_message: str = "Update research notes", paths: List[str] | None = None) -> dict:
    if not settings.github_token or not settings.github_repo:
        raise ValueError("GITHUB_TOKEN and GITHUB_REPO must be set")
    g = Github(settings.github_token)
    repo = g.get_repo(settings.github_repo)

    # Collect files
    base = Path.cwd()
    files = [Path(p) for p in (paths or [])]
    if not files:
        files = list(settings.notes_dir.rglob("*.md"))

    if not files:
        return {"committed": 0, "commit_sha": None}

    branch = repo.default_branch
    ref = repo.get_git_ref(f"heads/{branch}")
    latest_commit = repo.get_commit(ref.object.sha)
    base_tree = repo.get_git_tree(sha=latest_commit.sha, recursive=True)

    elements: list[InputGitTreeElement] = []
    for file_path in files:
        repo_path = str(file_path.relative_to(base))
        content = file_path.read_text(encoding="utf-8")
        element = InputGitTreeElement(path=repo_path, mode='100644', type='blob', content=content)
        elements.append(element)

    tree = repo.create_git_tree(elements, base_tree)
    parent = repo.get_git_commit(latest_commit.sha)
    commit = repo.create_git_commit(commit_message, tree, [parent])
    ref.edit(commit.sha)

    return {"committed": len(elements), "commit_sha": commit.sha}


def register_github_methods():
    rpc_method("github.publish")(publish_notes)
