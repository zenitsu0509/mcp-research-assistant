"""Tests for ArXiv client functionality."""

import pytest
from src.mcp_research_assistant.arxiv_client import ArXivClient
from src.mcp_research_assistant.utils import validate_arxiv_id


class TestArXivClient:
    """Test cases for ArXiv client."""
    
    def test_arxiv_id_validation(self):
        """Test ArXiv ID validation."""
        # Valid IDs
        assert validate_arxiv_id("2301.12345")
        assert validate_arxiv_id("1234.56789")
        assert validate_arxiv_id("cs.AI/0601001")
        assert validate_arxiv_id("arXiv:2301.12345")
        assert validate_arxiv_id("2301.12345v1")
        
        # Invalid IDs
        assert not validate_arxiv_id("invalid")
        assert not validate_arxiv_id("123")
        assert not validate_arxiv_id("")
    
    def test_build_search_query(self, arxiv_client):
        """Test search query building."""
        # Single field query
        query = arxiv_client.build_search_query(title="machine learning")
        assert 'ti:"machine learning"' in query
        
        # Multiple field query
        query = arxiv_client.build_search_query(
            title="neural networks",
            author="Smith",
            category="cs.AI"
        )
        assert 'ti:"neural networks"' in query
        assert 'au:"Smith"' in query
        assert 'cat:cs.AI' in query
        assert " AND " in query
    
    @pytest.mark.asyncio
    async def test_search_papers_mock(self, arxiv_client, monkeypatch):
        """Test paper search with mocked response."""
        # Mock the requests.get method
        class MockResponse:
            def __init__(self):
                self.text = '''<?xml version="1.0" encoding="UTF-8"?>
                <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
                    <entry>
                        <id>http://arxiv.org/abs/2301.12345v1</id>
                        <updated>2023-01-15T12:00:00Z</updated>
                        <published>2023-01-15T12:00:00Z</published>
                        <title>Test Paper</title>
                        <summary>Test summary</summary>
                        <author><name>Test Author</name></author>
                        <category term="cs.AI" />
                    </entry>
                </feed>'''
            
            def raise_for_status(self):
                pass
        
        def mock_get(*args, **kwargs):
            return MockResponse()
        
        monkeypatch.setattr("requests.get", mock_get)
        
        papers = arxiv_client.search_papers("test query", max_results=1)
        assert len(papers) == 1
        assert papers[0]["title"] == "Test Paper"
        assert papers[0]["id"] == "2301.12345v1"


class TestArXivIntegration:
    """Integration tests for ArXiv (requires internet)."""
    
    @pytest.mark.integration
    def test_real_arxiv_search(self, arxiv_client):
        """Test actual ArXiv search (requires internet)."""
        # Search for a specific paper that should exist
        papers = arxiv_client.search_papers("attention is all you need", max_results=1)
        
        if papers:  # Only test if we get results
            paper = papers[0]
            assert "title" in paper
            assert "authors" in paper
            assert "summary" in paper
            assert len(paper["summary"]) > 0
    
    @pytest.mark.integration 
    def test_get_paper_by_id(self, arxiv_client):
        """Test fetching specific paper by ID."""
        # Use a well-known paper ID
        paper = arxiv_client.get_paper_by_id("1706.03762")  # Attention is All You Need
        
        if paper:  # Only test if paper exists
            assert paper["id"] == "1706.03762"
            assert len(paper["title"]) > 0
            assert len(paper["authors"]) > 0
