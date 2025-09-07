"""Utility functions for the MCP Research Assistant."""

import re
import hashlib
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import json
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def validate_arxiv_id(arxiv_id: str) -> bool:
    """Validate ArXiv ID format.
    
    Args:
        arxiv_id: ArXiv paper ID
        
    Returns:
        True if valid format, False otherwise
    """
    # Remove common prefixes
    clean_id = arxiv_id.replace("arXiv:", "").replace("http://arxiv.org/abs/", "")
    
    # New format (YYMM.NNNNN)
    new_format = re.match(r'^\d{4}\.\d{4,5}(v\d+)?$', clean_id)
    
    # Old format (subject-class/YYMMnnn)
    old_format = re.match(r'^[a-z-]+(\.[A-Z]{2})?/\d{7}(v\d+)?$', clean_id)
    
    return bool(new_format or old_format)


def clean_text(text: str) -> str:
    """Clean and normalize text content.
    
    Args:
        text: Raw text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Remove common artifacts
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
    
    return text.strip()


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text using simple frequency analysis.
    
    Args:
        text: Text to analyze
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Simple keyword extraction
    # Remove common stopwords
    stopwords = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
        'can', 'this', 'that', 'these', 'those', 'a', 'an', 'we', 'they', 'he',
        'she', 'it', 'i', 'you', 'me', 'him', 'her', 'us', 'them'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter stopwords and count frequency
    word_freq = {}
    for word in words:
        if word not in stopwords and len(word) > 2:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Hexadecimal hash string
    """
    hasher = hashlib.sha256()
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate hash for {file_path}: {e}")
        return ""


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"


def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse various date string formats.
    
    Args:
        date_str: Date string
        
    Returns:
        Parsed datetime or None if parsing fails
    """
    if not date_str:
        return None
    
    # Common date formats
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%d %b %Y',
        '%B %d, %Y',
        '%m/%d/%Y',
        '%d/%m/%Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date string: {date_str}")
    return None


def create_citation_apa(paper_metadata: Dict[str, Any]) -> str:
    """Create APA style citation.
    
    Args:
        paper_metadata: Paper metadata dictionary
        
    Returns:
        APA formatted citation
    """
    authors = paper_metadata.get('authors', [])
    title = paper_metadata.get('title', 'Untitled')
    year = None
    
    # Extract year from date
    if paper_metadata.get('published'):
        date_obj = parse_date_string(paper_metadata['published'])
        if date_obj:
            year = date_obj.year
    
    # Format authors
    if not authors:
        author_str = "Unknown Author"
    elif len(authors) == 1:
        author_str = authors[0]
    elif len(authors) <= 7:
        author_str = ", ".join(authors[:-1]) + ", & " + authors[-1]
    else:
        author_str = ", ".join(authors[:6]) + ", ... " + authors[-1]
    
    # Build citation
    citation_parts = [author_str]
    
    if year:
        citation_parts.append(f"({year})")
    
    citation_parts.append(f"{title}.")
    
    if paper_metadata.get('journal_ref'):
        citation_parts.append(f"{paper_metadata['journal_ref']}.")
    else:
        citation_parts.append("arXiv preprint.")
    
    if paper_metadata.get('arxiv_url'):
        citation_parts.append(f"Retrieved from {paper_metadata['arxiv_url']}")
    
    return " ".join(citation_parts)


def create_research_index(research_dir: str) -> Dict[str, Any]:
    """Create an index of all research files.
    
    Args:
        research_dir: Research directory path
        
    Returns:
        Research index dictionary
    """
    index = {
        "created": datetime.now().isoformat(),
        "total_files": 0,
        "notes": [],
        "summaries": [],
        "references": [],
        "tags": set(),
        "categories": set()
    }
    
    research_path = Path(research_dir)
    if not research_path.exists():
        return index
    
    # Index notes
    notes_dir = research_path / "notes"
    if notes_dir.exists():
        for note_file in notes_dir.glob("*.md"):
            try:
                with open(note_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract metadata if present
                metadata = extract_frontmatter(content)
                
                note_info = {
                    "file": note_file.name,
                    "path": str(note_file),
                    "title": metadata.get('title', note_file.stem),
                    "tags": metadata.get('tags', []),
                    "created": metadata.get('created', ''),
                    "size": note_file.stat().st_size
                }
                
                index["notes"].append(note_info)
                index["tags"].update(note_info["tags"])
                
            except Exception as e:
                logger.error(f"Error indexing note {note_file}: {e}")
    
    # Index summaries
    summaries_dir = research_path / "summaries"
    if summaries_dir.exists():
        for summary_file in summaries_dir.glob("*.json"):
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary_data = json.load(f)
                
                summary_info = {
                    "file": summary_file.name,
                    "path": str(summary_file),
                    "title": summary_data.get('title', summary_file.stem),
                    "paper_id": summary_data.get('id', ''),
                    "created": summary_data.get('created', ''),
                    "size": summary_file.stat().st_size
                }
                
                index["summaries"].append(summary_info)
                
                # Extract categories
                if 'categories' in summary_data:
                    index["categories"].update(summary_data['categories'])
                
            except Exception as e:
                logger.error(f"Error indexing summary {summary_file}: {e}")
    
    # Index references
    references_dir = research_path / "references"
    if references_dir.exists():
        for ref_file in references_dir.glob("*.json"):
            try:
                with open(ref_file, 'r', encoding='utf-8') as f:
                    ref_data = json.load(f)
                
                ref_info = {
                    "file": ref_file.name,
                    "path": str(ref_file),
                    "title": ref_data.get('title', ref_file.stem),
                    "authors": ref_data.get('authors', []),
                    "paper_id": ref_data.get('id', ''),
                    "saved": ref_data.get('saved', ''),
                    "size": ref_file.stat().st_size
                }
                
                index["references"].append(ref_info)
                
            except Exception as e:
                logger.error(f"Error indexing reference {ref_file}: {e}")
    
    # Convert sets to lists for JSON serialization
    index["tags"] = list(index["tags"])
    index["categories"] = list(index["categories"])
    
    # Calculate total files
    index["total_files"] = len(index["notes"]) + len(index["summaries"]) + len(index["references"])
    
    return index


def extract_frontmatter(content: str) -> Dict[str, Any]:
    """Extract YAML frontmatter from markdown content.
    
    Args:
        content: Markdown content with potential frontmatter
        
    Returns:
        Frontmatter dictionary
    """
    if not content.startswith('---'):
        return {}
    
    try:
        # Split content
        parts = content[3:].split('---', 1)
        if len(parts) < 2:
            return {}
        
        frontmatter_str = parts[0].strip()
        
        # Parse frontmatter (simple key: value format)
        frontmatter = {}
        for line in frontmatter_str.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Try to parse as JSON (for lists and complex values)
                try:
                    frontmatter[key] = json.loads(value)
                except json.JSONDecodeError:
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    frontmatter[key] = value
        
        return frontmatter
        
    except Exception as e:
        logger.error(f"Error parsing frontmatter: {e}")
        return {}


def create_backup(source_dir: str, backup_dir: str) -> str:
    """Create a backup of research directory.
    
    Args:
        source_dir: Source directory to backup
        backup_dir: Backup directory
        
    Returns:
        Path to created backup
    """
    import shutil
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"research_backup_{timestamp}"
    backup_path = Path(backup_dir) / backup_name
    
    try:
        shutil.copytree(source_dir, backup_path)
        logger.info(f"Created backup at: {backup_path}")
        return str(backup_path)
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise


def merge_metadata(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Merge metadata dictionaries.
    
    Args:
        existing: Existing metadata
        new: New metadata to merge
        
    Returns:
        Merged metadata
    """
    merged = existing.copy()
    
    for key, value in new.items():
        if key in merged:
            if isinstance(merged[key], list) and isinstance(value, list):
                # Merge lists, removing duplicates
                merged[key] = list(set(merged[key] + value))
            elif isinstance(merged[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                merged[key] = merge_metadata(merged[key], value)
            else:
                # Overwrite with new value
                merged[key] = value
        else:
            merged[key] = value
    
    return merged


def validate_environment() -> Dict[str, bool]:
    """Validate environment setup.
    
    Returns:
        Dictionary of validation results
    """
    validation = {
        "groq_api_key": bool(os.getenv("GROQ_API_KEY")),
        "github_token": bool(os.getenv("GITHUB_TOKEN")),
        "research_dir": True,  # Will be created if not exists
        "python_version": True  # Assuming compatible if running
    }
    
    # Check if directories can be created
    try:
        import tempfile
        test_dir = tempfile.mkdtemp()
        os.rmdir(test_dir)
        validation["filesystem_writable"] = True
    except Exception:
        validation["filesystem_writable"] = False
    
    return validation


def generate_research_report(index: Dict[str, Any]) -> str:
    """Generate a summary report of research data.
    
    Args:
        index: Research index dictionary
        
    Returns:
        Formatted report string
    """
    report_lines = [
        "# Research Data Report",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        f"- Total files: {index['total_files']}",
        f"- Notes: {len(index['notes'])}",
        f"- Summaries: {len(index['summaries'])}",
        f"- References: {len(index['references'])}",
        f"- Unique tags: {len(index['tags'])}",
        f"- Categories: {len(index['categories'])}",
        ""
    ]
    
    if index['tags']:
        report_lines.extend([
            "## Tags",
            ", ".join(sorted(index['tags'])),
            ""
        ])
    
    if index['categories']:
        report_lines.extend([
            "## Categories", 
            ", ".join(sorted(index['categories'])),
            ""
        ])
    
    if index['notes']:
        report_lines.extend([
            "## Recent Notes",
            ""
        ])
        for note in index['notes'][-5:]:  # Last 5 notes
            report_lines.append(f"- {note['title']} ({note['file']})")
        report_lines.append("")
    
    if index['summaries']:
        report_lines.extend([
            "## Recent Summaries",
            ""
        ])
        for summary in index['summaries'][-5:]:  # Last 5 summaries
            report_lines.append(f"- {summary['title']} ({summary['file']})")
        report_lines.append("")
    
    return "\n".join(report_lines)


# Import os at the top level for environment validation
import os
