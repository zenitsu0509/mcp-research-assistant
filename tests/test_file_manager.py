"""Tests for file manager functionality."""

import pytest
import json
import os
from pathlib import Path

from src.mcp_research_assistant.file_manager import FileManager


class TestFileManager:
    """Test cases for file manager."""
    
    def test_initialization(self, temp_research_dir):
        """Test file manager initialization."""
        fm = FileManager(research_dir=temp_research_dir)
        
        # Check directories are created
        assert fm.research_dir.exists()
        assert fm.notes_dir.exists()
        assert fm.summaries_dir.exists()
        assert fm.references_dir.exists()
    
    def test_save_notes(self, file_manager):
        """Test saving notes."""
        title = "Test Note"
        content = "This is a test note content."
        tags = ["test", "example"]
        metadata = {"importance": "high"}
        
        file_path = file_manager.save_notes(title, content, tags, metadata)
        
        # Check file was created
        assert os.path.exists(file_path)
        
        # Check file content
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        assert title in file_content
        assert content in file_content
        assert "test" in file_content
    
    def test_save_summary_json(self, file_manager, sample_summary_data):
        """Test saving summary in JSON format."""
        paper_id = "test_paper_123"
        
        file_path = file_manager.save_summary(paper_id, sample_summary_data, "json")
        
        # Check file was created
        assert os.path.exists(file_path)
        assert file_path.endswith(".json")
        
        # Check file content
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data["title"] == sample_summary_data["title"]
        assert "created" in saved_data
    
    def test_save_summary_markdown(self, file_manager, sample_summary_data):
        """Test saving summary in Markdown format."""
        paper_id = "test_paper_456"
        
        file_path = file_manager.save_summary(paper_id, sample_summary_data, "markdown")
        
        # Check file was created
        assert os.path.exists(file_path)
        assert file_path.endswith(".md")
        
        # Check file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert sample_summary_data["title"] in content
        assert sample_summary_data["summary"] in content
        assert "## Summary" in content
    
    def test_save_reference(self, file_manager, sample_paper_metadata):
        """Test saving reference data."""
        paper_id = "ref_test_789"
        
        file_path = file_manager.save_reference(paper_id, sample_paper_metadata)
        
        # Check file was created
        assert os.path.exists(file_path)
        
        # Check file content
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data["title"] == sample_paper_metadata["title"]
        assert saved_data["authors"] == sample_paper_metadata["authors"]
        assert "saved" in saved_data
    
    def test_search_notes(self, file_manager):
        """Test searching notes."""
        # Save some test notes
        file_manager.save_notes(
            "Machine Learning Basics",
            "This note covers machine learning fundamentals.",
            ["ml", "basics"],
            {"category": "education"}
        )
        
        file_manager.save_notes(
            "Deep Learning Advanced",
            "Advanced concepts in deep learning.",
            ["dl", "advanced"],
            {"category": "research"}
        )
        
        # Search by content
        results = file_manager.search_notes("machine learning")
        assert len(results) >= 1
        assert any("Machine Learning" in result["title"] for result in results)
        
        # Search by tags
        results = file_manager.search_notes("basics")
        assert len(results) >= 1
        
        # Search with no results
        results = file_manager.search_notes("nonexistent")
        assert len(results) == 0
    
    def test_list_files(self, file_manager):
        """Test listing files."""
        # Save some test files
        file_manager.save_notes("Test Note", "Content", ["tag1"])
        file_manager.save_summary("test123", {"title": "Test"}, "json")
        file_manager.save_reference("ref123", {"title": "Ref"})
        
        # List all files
        files = file_manager.list_files("all")
        assert "notes" in files
        assert "summaries" in files
        assert "references" in files
        assert len(files["notes"]) >= 1
        assert len(files["summaries"]) >= 1
        assert len(files["references"]) >= 1
        
        # List specific directory
        notes_files = file_manager.list_files("notes")
        assert "notes" in notes_files
        assert len(notes_files["notes"]) >= 1
    
    def test_organize_by_tags(self, file_manager):
        """Test organizing files by tags."""
        # Save notes with different tags
        file_manager.save_notes("Note 1", "Content 1", ["ai", "research"])
        file_manager.save_notes("Note 2", "Content 2", ["ml", "research"])
        file_manager.save_notes("Note 3", "Content 3", ["ai", "tutorial"])
        
        tag_map = file_manager.organize_by_tags()
        
        assert "ai" in tag_map
        assert "ml" in tag_map
        assert "research" in tag_map
        assert "tutorial" in tag_map
        
        # Check that files are properly categorized
        assert len(tag_map["research"]) >= 2
        assert len(tag_map["ai"]) >= 2
    
    def test_sanitize_filename(self, file_manager):
        """Test filename sanitization."""
        # Test with problematic characters
        original = "Test: File/Name with <invalid> chars?"
        sanitized = file_manager._sanitize_filename(original)
        
        assert "/" not in sanitized
        assert ":" not in sanitized
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert "?" not in sanitized
        
        # Should contain underscores instead
        assert "_" in sanitized
