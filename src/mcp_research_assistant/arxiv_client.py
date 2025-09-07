"""ArXiv API client for fetching research papers."""

import logging
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode, quote_plus
import xml.etree.ElementTree as ET
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class ArXivClient:
    """Client for interacting with the ArXiv API."""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def __init__(self, delay_seconds: float = 1.0, max_results: int = 5):
        """Initialize ArXiv client.
        
        Args:
            delay_seconds: Delay between API calls to respect rate limits
            max_results: Default maximum results per query
        """
        self.delay_seconds = delay_seconds
        self.max_results = max_results
        self._last_request_time = 0
    
    def _rate_limit(self) -> None:
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.delay_seconds:
            time.sleep(self.delay_seconds - time_since_last)
        self._last_request_time = time.time()
    
    def search_papers(
        self,
        query: str,
        max_results: Optional[int] = None,
        sort_by: str = "relevance",
        sort_order: str = "descending",
        start: int = 0
    ) -> List[Dict[str, Any]]:
        """Search ArXiv for papers.
        
        Args:
            query: Search query (can include field prefixes like ti:, au:, abs:)
            max_results: Maximum number of results to return
            sort_by: Sort criteria (relevance, lastUpdatedDate, submittedDate)
            sort_order: Sort order (ascending, descending)
            start: Starting index for pagination
            
        Returns:
            List of paper dictionaries with metadata
        """
        if max_results is None:
            max_results = self.max_results
            
        self._rate_limit()
        
        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            return self._parse_response(response.text)
        except requests.RequestException as e:
            logger.error(f"ArXiv API request failed: {e}")
            raise
    
    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific paper by ArXiv ID.
        
        Args:
            arxiv_id: ArXiv paper ID (e.g., "2301.12345" or "cs.AI/0601001")
            
        Returns:
            Paper dictionary or None if not found
        """
        # Clean up the ArXiv ID
        arxiv_id = arxiv_id.replace("arXiv:", "").replace("v1", "").replace("v2", "").replace("v3", "")
        
        papers = self.search_papers(f"id:{arxiv_id}", max_results=1)
        return papers[0] if papers else None
    
    def _parse_response(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse ArXiv API XML response.
        
        Args:
            xml_content: Raw XML response from ArXiv API
            
        Returns:
            List of parsed paper dictionaries
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Handle namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            papers = []
            entries = root.findall('atom:entry', namespaces)
            
            for entry in entries:
                paper = self._parse_entry(entry, namespaces)
                if paper:
                    papers.append(paper)
            
            return papers
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse ArXiv response: {e}")
            return []
    
    def _parse_entry(self, entry: ET.Element, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Parse a single paper entry from ArXiv XML.
        
        Args:
            entry: XML entry element
            namespaces: XML namespaces
            
        Returns:
            Paper dictionary
        """
        def get_text(element_path: str, default: str = "") -> str:
            element = entry.find(element_path, namespaces)
            return element.text.strip() if element is not None and element.text else default
        
        def get_date(element_path: str) -> Optional[str]:
            date_str = get_text(element_path)
            if date_str:
                try:
                    # Parse ISO format and return just the date
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    return date_str
            return None
        
        # Extract ArXiv ID from the URL
        arxiv_url = get_text('atom:id')
        arxiv_id = arxiv_url.split('/')[-1] if arxiv_url else ""
        
        # Extract authors
        authors = []
        author_elements = entry.findall('atom:author', namespaces)
        for author in author_elements:
            name_elem = author.find('atom:name', namespaces)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text.strip())
        
        # Extract categories
        categories = []
        category_elements = entry.findall('atom:category', namespaces)
        for category in category_elements:
            term = category.get('term')
            if term:
                categories.append(term)
        
        # Extract links
        pdf_url = ""
        abs_url = ""
        link_elements = entry.findall('atom:link', namespaces)
        for link in link_elements:
            rel = link.get('rel', '')
            href = link.get('href', '')
            if rel == 'alternate' and href:
                abs_url = href
            elif rel == 'related' and 'pdf' in href:
                pdf_url = href
        
        # Extract summary
        summary = get_text('atom:summary')
        
        # Clean and format the summary
        if summary:
            # Remove excessive whitespace and normalize
            summary = ' '.join(summary.split())
        
        return {
            'id': arxiv_id,
            'title': get_text('atom:title'),
            'authors': authors,
            'summary': summary,
            'published': get_date('atom:published'),
            'updated': get_date('atom:updated'),
            'categories': categories,
            'primary_category': categories[0] if categories else "",
            'pdf_url': pdf_url,
            'abs_url': abs_url,
            'arxiv_url': arxiv_url,
            'comment': get_text('arxiv:comment'),
            'journal_ref': get_text('arxiv:journal_ref'),
            'doi': get_text('arxiv:doi')
        }
    
    def download_paper_content(self, arxiv_id: str) -> Optional[str]:
        """Download paper content (abstract and metadata).
        
        Note: This returns the abstract and metadata. For full PDF content,
        you would need additional PDF parsing libraries.
        
        Args:
            arxiv_id: ArXiv paper ID
            
        Returns:
            Paper content as string or None if failed
        """
        paper = self.get_paper_by_id(arxiv_id)
        if not paper:
            return None
        
        content_parts = []
        
        # Add title
        if paper.get('title'):
            content_parts.append(f"Title: {paper['title']}")
        
        # Add authors
        if paper.get('authors'):
            authors_str = ", ".join(paper['authors'])
            content_parts.append(f"Authors: {authors_str}")
        
        # Add metadata
        if paper.get('published'):
            content_parts.append(f"Published: {paper['published']}")
        
        if paper.get('categories'):
            categories_str = ", ".join(paper['categories'])
            content_parts.append(f"Categories: {categories_str}")
        
        if paper.get('journal_ref'):
            content_parts.append(f"Journal: {paper['journal_ref']}")
        
        if paper.get('doi'):
            content_parts.append(f"DOI: {paper['doi']}")
        
        # Add abstract
        if paper.get('summary'):
            content_parts.append(f"\nAbstract:\n{paper['summary']}")
        
        return "\n".join(content_parts)
    
    def build_search_query(
        self,
        title: Optional[str] = None,
        author: Optional[str] = None,
        abstract: Optional[str] = None,
        category: Optional[str] = None,
        all_fields: Optional[str] = None
    ) -> str:
        """Build a structured search query for ArXiv.
        
        Args:
            title: Search in title field
            author: Search in author field
            abstract: Search in abstract field
            category: Search in category field
            all_fields: Search in all fields
            
        Returns:
            Formatted query string
        """
        query_parts = []
        
        if title:
            query_parts.append(f'ti:"{title}"')
        if author:
            query_parts.append(f'au:"{author}"')
        if abstract:
            query_parts.append(f'abs:"{abstract}"')
        if category:
            query_parts.append(f'cat:{category}')
        if all_fields:
            query_parts.append(f'all:"{all_fields}"')
        
        return " AND ".join(query_parts) if query_parts else ""
