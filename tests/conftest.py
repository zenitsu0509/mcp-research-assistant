"""Test configuration and fixtures for the research assistant."""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from typing import Dict, Any

from src.mcp_research_assistant.arxiv_client import ArXivClient
from src.mcp_research_assistant.file_manager import FileManager
from src.mcp_research_assistant.utils import setup_logging


@pytest.fixture
def temp_research_dir():
    """Create a temporary research directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def file_manager(temp_research_dir):
    """Create a file manager with temporary directory."""
    return FileManager(research_dir=temp_research_dir)


@pytest.fixture
def arxiv_client():
    """Create an ArXiv client for testing."""
    return ArXivClient(delay_seconds=0.1, max_results=5)


@pytest.fixture
def sample_paper_metadata():
    """Sample paper metadata for testing."""
    return {
        "id": "2301.12345",
        "title": "Test Paper: Advanced Research Methods",
        "authors": ["John Doe", "Jane Smith"],
        "summary": "This is a test paper summary for demonstration purposes.",
        "published": "2023-01-15",
        "categories": ["cs.AI", "cs.LG"],
        "pdf_url": "http://arxiv.org/pdf/2301.12345.pdf",
        "abs_url": "http://arxiv.org/abs/2301.12345"
    }


@pytest.fixture
def sample_summary_data():
    """Sample summary data for testing."""
    return {
        "title": "Test Paper: Advanced Research Methods",
        "summary": "This paper presents advanced research methods for AI systems.",
        "key_points": [
            "Novel methodology for data analysis",
            "Improved performance metrics", 
            "Comprehensive evaluation framework"
        ],
        "main_contribution": "A new framework for research analysis",
        "methodology": "Machine learning based approach",
        "limitations": "Limited to specific domains"
    }


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "research_dir": "./test_research_data",
        "arxiv_max_results": 5,
        "arxiv_delay_seconds": 0.1
    }


# Setup logging for tests
setup_logging("DEBUG")
