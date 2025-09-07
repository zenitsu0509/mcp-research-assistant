"""File system management for research data organization."""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import shutil
import glob

logger = logging.getLogger(__name__)


class FileManager:
    """Manages local file system operations for research data."""
    
    def __init__(
        self,
        research_dir: str = "./research_data",
        notes_dir: Optional[str] = None,
        summaries_dir: Optional[str] = None,
        references_dir: Optional[str] = None
    ):
        """Initialize file manager.
        
        Args:
            research_dir: Base directory for research data
            notes_dir: Directory for notes (defaults to research_dir/notes)
            summaries_dir: Directory for summaries (defaults to research_dir/summaries)
            references_dir: Directory for references (defaults to research_dir/references)
        """
        self.research_dir = Path(research_dir)
        self.notes_dir = Path(notes_dir) if notes_dir else self.research_dir / "notes"
        self.summaries_dir = Path(summaries_dir) if summaries_dir else self.research_dir / "summaries"
        self.references_dir = Path(references_dir) if references_dir else self.research_dir / "references"
        
        # Create directories if they don't exist
        self._create_directories()
    
    def _create_directories(self) -> None:
        """Create necessary directories."""
        for directory in [self.research_dir, self.notes_dir, self.summaries_dir, self.references_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")
    
    def save_notes(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save research notes to file.
        
        Args:
            title: Note title
            content: Note content
            tags: List of tags for categorization
            metadata: Additional metadata
            
        Returns:
            Path to saved file
        """
        if tags is None:
            tags = []
        if metadata is None:
            metadata = {}
        
        # Create filename from title
        filename = self._sanitize_filename(title) + ".md"
        file_path = self.notes_dir / filename
        
        # Prepare note data
        note_data = {
            "title": title,
            "created": datetime.now().isoformat(),
            "tags": tags,
            "metadata": metadata
        }
        
        # Create markdown content with frontmatter
        frontmatter = "---\n"
        for key, value in note_data.items():
            if isinstance(value, list):
                frontmatter += f"{key}: {json.dumps(value)}\n"
            else:
                frontmatter += f"{key}: {json.dumps(value)}\n"
        frontmatter += "---\n\n"
        
        full_content = frontmatter + content
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            logger.info(f"Saved notes to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save notes: {e}")
            raise
    
    def save_summary(
        self,
        paper_id: str,
        summary_data: Dict[str, Any],
        format_type: str = "json"
    ) -> str:
        """Save paper summary to file.
        
        Args:
            paper_id: Paper identifier (e.g., ArXiv ID)
            summary_data: Summary data dictionary
            format_type: Output format (json, markdown)
            
        Returns:
            Path to saved file
        """
        # Sanitize paper ID for filename
        safe_id = self._sanitize_filename(paper_id)
        
        if format_type == "json":
            filename = f"{safe_id}_summary.json"
            file_path = self.summaries_dir / filename
            
            # Add timestamp
            summary_data["created"] = datetime.now().isoformat()
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(summary_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Saved JSON summary to: {file_path}")
                return str(file_path)
                
            except Exception as e:
                logger.error(f"Failed to save JSON summary: {e}")
                raise
                
        elif format_type == "markdown":
            filename = f"{safe_id}_summary.md"
            file_path = self.summaries_dir / filename
            
            try:
                md_content = self._summary_to_markdown(summary_data)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                
                logger.info(f"Saved Markdown summary to: {file_path}")
                return str(file_path)
                
            except Exception as e:
                logger.error(f"Failed to save Markdown summary: {e}")
                raise
        
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def save_reference(
        self,
        paper_id: str,
        reference_data: Dict[str, Any]
    ) -> str:
        """Save paper reference data.
        
        Args:
            paper_id: Paper identifier
            reference_data: Reference metadata
            
        Returns:
            Path to saved file
        """
        safe_id = self._sanitize_filename(paper_id)
        filename = f"{safe_id}_reference.json"
        file_path = self.references_dir / filename
        
        # Add timestamp
        reference_data["saved"] = datetime.now().isoformat()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(reference_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved reference to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save reference: {e}")
            raise
    
    def search_notes(
        self,
        query: str,
        search_content: bool = True,
        search_tags: bool = True
    ) -> List[Dict[str, Any]]:
        """Search through saved notes.
        
        Args:
            query: Search query
            search_content: Whether to search in content
            search_tags: Whether to search in tags
            
        Returns:
            List of matching notes with metadata
        """
        results = []
        query_lower = query.lower()
        
        for note_file in self.notes_dir.glob("*.md"):
            try:
                with open(note_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse frontmatter and content
                note_data = self._parse_note_file(content)
                
                # Check for matches
                match_found = False
                
                if search_content and query_lower in note_data.get('content', '').lower():
                    match_found = True
                
                if search_tags and note_data.get('tags'):
                    for tag in note_data['tags']:
                        if query_lower in tag.lower():
                            match_found = True
                            break
                
                if query_lower in note_data.get('title', '').lower():
                    match_found = True
                
                if match_found:
                    note_data['file_path'] = str(note_file)
                    results.append(note_data)
                    
            except Exception as e:
                logger.error(f"Error reading note file {note_file}: {e}")
        
        return results
    
    def list_files(self, directory: str = "all") -> Dict[str, List[str]]:
        """List files in research directories.
        
        Args:
            directory: Which directory to list (all, notes, summaries, references)
            
        Returns:
            Dictionary mapping directory names to file lists
        """
        result = {}
        
        directories_map = {
            "notes": self.notes_dir,
            "summaries": self.summaries_dir,
            "references": self.references_dir
        }
        
        if directory == "all":
            dirs_to_list = directories_map
        elif directory in directories_map:
            dirs_to_list = {directory: directories_map[directory]}
        else:
            raise ValueError(f"Unknown directory: {directory}")
        
        for dir_name, dir_path in dirs_to_list.items():
            if dir_path.exists():
                files = [f.name for f in dir_path.iterdir() if f.is_file()]
                result[dir_name] = sorted(files)
            else:
                result[dir_name] = []
        
        return result
    
    def organize_by_tags(self) -> Dict[str, List[str]]:
        """Organize notes by tags.
        
        Returns:
            Dictionary mapping tags to lists of note files
        """
        tag_map = {}
        
        for note_file in self.notes_dir.glob("*.md"):
            try:
                with open(note_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                note_data = self._parse_note_file(content)
                tags = note_data.get('tags', [])
                
                for tag in tags:
                    if tag not in tag_map:
                        tag_map[tag] = []
                    tag_map[tag].append(note_file.name)
                    
            except Exception as e:
                logger.error(f"Error organizing note file {note_file}: {e}")
        
        return tag_map
    
    def export_research_data(
        self,
        export_format: str = "zip",
        output_path: Optional[str] = None
    ) -> str:
        """Export all research data.
        
        Args:
            export_format: Export format (zip, tar, folder)
            output_path: Output path (optional)
            
        Returns:
            Path to exported data
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"research_export_{timestamp}"
        
        if export_format == "zip":
            import zipfile
            
            zip_path = f"{output_path}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.research_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.research_dir.parent)
                        zipf.write(file_path, arcname)
            
            logger.info(f"Exported research data to: {zip_path}")
            return zip_path
            
        elif export_format == "folder":
            output_dir = Path(output_path)
            shutil.copytree(self.research_dir, output_dir, dirs_exist_ok=True)
            
            logger.info(f"Exported research data to: {output_dir}")
            return str(output_dir)
            
        else:
            raise ValueError(f"Unsupported export format: {export_format}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove extra spaces and limit length
        filename = '_'.join(filename.split())
        filename = filename[:100]  # Limit length
        
        return filename
    
    def _summary_to_markdown(self, summary_data: Dict[str, Any]) -> str:
        """Convert summary data to markdown format.
        
        Args:
            summary_data: Summary data dictionary
            
        Returns:
            Markdown formatted string
        """
        lines = []
        
        # Title
        if 'title' in summary_data:
            lines.append(f"# {summary_data['title']}")
            lines.append("")
        
        # Metadata
        if 'authors' in summary_data:
            lines.append(f"**Authors:** {', '.join(summary_data['authors'])}")
        if 'published' in summary_data:
            lines.append(f"**Published:** {summary_data['published']}")
        if 'categories' in summary_data:
            lines.append(f"**Categories:** {', '.join(summary_data['categories'])}")
        
        lines.append("")
        
        # Main summary
        if 'summary' in summary_data:
            lines.append("## Summary")
            lines.append("")
            lines.append(summary_data['summary'])
            lines.append("")
        
        # Key points
        if 'key_points' in summary_data:
            lines.append("## Key Points")
            lines.append("")
            for point in summary_data['key_points']:
                lines.append(f"- {point}")
            lines.append("")
        
        # Other sections
        for key, value in summary_data.items():
            if key not in ['title', 'authors', 'published', 'categories', 'summary', 'key_points', 'created']:
                if isinstance(value, str) and value.strip():
                    lines.append(f"## {key.replace('_', ' ').title()}")
                    lines.append("")
                    lines.append(value)
                    lines.append("")
        
        return '\n'.join(lines)
    
    def _parse_note_file(self, content: str) -> Dict[str, Any]:
        """Parse note file with frontmatter.
        
        Args:
            content: File content
            
        Returns:
            Parsed note data
        """
        if content.startswith('---'):
            # Split frontmatter and content
            parts = content[3:].split('---', 1)
            if len(parts) == 2:
                frontmatter_str, note_content = parts
                
                # Parse frontmatter
                frontmatter = {}
                for line in frontmatter_str.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        try:
                            frontmatter[key] = json.loads(value)
                        except json.JSONDecodeError:
                            frontmatter[key] = value
                
                frontmatter['content'] = note_content.strip()
                return frontmatter
        
        # Fallback: treat entire content as note
        return {'content': content, 'title': 'Untitled'}
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            File information dictionary
        """
        path = Path(file_path)
        
        if not path.exists():
            return {"error": "File not found"}
        
        stat = path.stat()
        
        return {
            "name": path.name,
            "path": str(path),
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_file": path.is_file(),
            "is_directory": path.is_dir(),
            "extension": path.suffix
        }
