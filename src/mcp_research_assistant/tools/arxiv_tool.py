from __future__ import annotations

import arxiv
from typing import List, Dict
from ..jsonrpc import rpc_method


def search_arxiv(query: str, max_results: int = 5) -> List[Dict]:
    search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
    results: List[Dict] = []
    try:
        # Newer API pattern (v2+): use Client
        client = arxiv.Client(page_size=max_results)
        itr = client.results(search)
    except Exception:
        # Fallback: older API had search.results()
        itr = search.results()

    for result in itr:
        authors = ", ".join(getattr(a, 'name', str(a)) for a in result.authors)
        results.append({
            "title": result.title,
            "authors": authors,
            "published": getattr(result.published, 'strftime', lambda _fmt: str(result.published))("%Y-%m-%d"),
            "summary": result.summary,
            "pdf_url": getattr(result, 'pdf_url', None),
            "entry_id": getattr(result, 'entry_id', None),
        })
    return results


def register_arxiv_methods():
    rpc_method("arxiv.search")(search_arxiv)
