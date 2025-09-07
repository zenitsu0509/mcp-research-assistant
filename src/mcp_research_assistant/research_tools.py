"""MCP tools implementation for research assistant functionality."""

import logging
from typing import Dict, List, Any, Optional, Union
import json
import os
from datetime import datetime

from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    CallToolResult
)

from .arxiv_client import ArXivClient
from .groq_client import GroqClient
from .file_manager import FileManager
from .github_client import GitHubClient
from .utils import (
    validate_arxiv_id,
    clean_text,
    extract_keywords,
    create_citation_apa,
    create_research_index
)

logger = logging.getLogger(__name__)


class ResearchTools:
    """Implementation of MCP tools for research assistant."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize research tools with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Initialize clients
        self.arxiv_client = ArXivClient(
            delay_seconds=config.get('arxiv_delay_seconds', 1.0),
            max_results=config.get('arxiv_max_results', 10)
        )
        
        if config.get('groq_api_key'):
            self.groq_client = GroqClient(
                api_key=config['groq_api_key'],
                model=config.get('groq_model', 'llama-3.1-70b-versatile')
            )
        else:
            self.groq_client = None
            logger.warning("Groq API key not provided, summarization features will be unavailable")
        
        self.file_manager = FileManager(
            research_dir=config.get('research_dir', './research_data'),
            notes_dir=config.get('notes_dir'),
            summaries_dir=config.get('summaries_dir'),
            references_dir=config.get('references_dir')
        )
        
        if config.get('github_token') and config.get('github_username') and config.get('github_repo'):
            self.github_client = GitHubClient(
                token=config['github_token'],
                username=config['github_username'],
                repo_name=config['github_repo']
            )
        else:
            self.github_client = None
            logger.warning("GitHub configuration incomplete, GitHub features will be unavailable")
    
    def get_tools(self) -> List[Tool]:
        """Get list of available MCP tools.
        
        Returns:
            List of Tool objects
        """
        tools = [
            Tool(
                name="search_arxiv",
                description="Search ArXiv for research papers using various criteria",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (can include field prefixes like ti:, au:, abs:)"
                        },
                        "max_results": {
                            "type": "integer", 
                            "description": "Maximum number of results (default: 10)",
                            "default": 10,
                            "minimum": 1
                        },
                        "sort_by": {
                            "type": "string",
                            "description": "Sort criteria",
                            "enum": ["relevance", "lastUpdatedDate", "submittedDate"],
                            "default": "relevance"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="fetch_paper",
                description="Fetch detailed information about a specific ArXiv paper",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {
                            "type": "string",
                            "description": "ArXiv paper ID (e.g., '2301.12345')"
                        }
                    },
                    "required": ["arxiv_id"]
                }
            ),
            Tool(
                name="download_paper_content",
                description="Download paper content (abstract and metadata) for analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {
                            "type": "string",
                            "description": "ArXiv paper ID"
                        }
                    },
                    "required": ["arxiv_id"]
                }
            ),
        ]
        
        # Add Groq-powered tools if available
        if self.groq_client:
            tools.extend([
                Tool(
                    name="summarize_paper",
                    description="Generate AI-powered summary of a research paper using Groq",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Paper content to summarize"
                            },
                            "style": {
                                "type": "string",
                                "description": "Summary style",
                                "enum": ["academic", "casual", "technical", "brief", "detailed"],
                                "default": "academic"
                            },
                            "arxiv_id": {
                                "type": "string",
                                "description": "ArXiv ID for the paper (optional)"
                            }
                        },
                        "required": ["content"]
                    }
                ),
                Tool(
                    name="extract_key_points",
                    description="Extract key points from a research paper",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Paper content to analyze"
                            },
                            "num_points": {
                                "type": "integer",
                                "description": "Number of key points to extract (default: 5)",
                                "default": 5,
                                "minimum": 1
                            }
                        },
                        "required": ["content"]
                    }
                ),
                Tool(
                    name="create_structured_summary",
                    description="Create a structured summary with specific sections",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Paper content to summarize"
                            },
                            "sections": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Sections to include in summary",
                                "default": ["main_contribution", "methodology", "key_findings", "limitations", "future_work"]
                            }
                        },
                        "required": ["content"]
                    }
                ),
                Tool(
                    name="generate_citation",
                    description="Generate formatted citation for a paper",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "paper_metadata": {
                                "type": "object",
                                "description": "Paper metadata dictionary"
                            },
                            "style": {
                                "type": "string",
                                "description": "Citation style",
                                "enum": ["apa", "mla", "chicago", "ieee"],
                                "default": "apa"
                            }
                        },
                        "required": ["paper_metadata"]
                    }
                ),
                Tool(
                    name="compare_papers",
                    description="Compare multiple research papers",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "papers_content": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of paper contents to compare"
                            },
                            "comparison_aspects": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Aspects to compare",
                                "default": ["methodology", "findings", "strengths", "limitations", "novelty"]
                            }
                        },
                        "required": ["papers_content"]
                    }
                )
            ])
        
        # File management tools
        tools.extend([
            Tool(
                name="save_notes",
                description="Save research notes to local file system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Note title"
                        },
                        "content": {
                            "type": "string",
                            "description": "Note content"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for categorization"
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional metadata"
                        }
                    },
                    "required": ["title", "content"]
                }
            ),
            Tool(
                name="save_summary",
                description="Save paper summary to local file system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "paper_id": {
                            "type": "string",
                            "description": "Paper identifier (e.g., ArXiv ID)"
                        },
                        "summary_data": {
                            "type": "object",
                            "description": "Summary data dictionary"
                        },
                        "format": {
                            "type": "string",
                            "description": "Output format",
                            "enum": ["json", "markdown"],
                            "default": "json"
                        }
                    },
                    "required": ["paper_id", "summary_data"]
                }
            ),
            Tool(
                name="save_reference",
                description="Save paper reference data",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "paper_id": {
                            "type": "string",
                            "description": "Paper identifier"
                        },
                        "reference_data": {
                            "type": "object",
                            "description": "Reference metadata"
                        }
                    },
                    "required": ["paper_id", "reference_data"]
                }
            ),
            Tool(
                name="search_local_notes",
                description="Search through saved research notes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "search_content": {
                            "type": "boolean",
                            "description": "Search in note content",
                            "default": True
                        },
                        "search_tags": {
                            "type": "boolean",
                            "description": "Search in tags",
                            "default": True
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="list_research_files",
                description="List files in research directories",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory to list",
                            "enum": ["all", "notes", "summaries", "references"],
                            "default": "all"
                        }
                    }
                }
            ),
            Tool(
                name="organize_by_tags",
                description="Organize notes by tags",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="export_research_data", 
                description="Export all research data",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "description": "Export format",
                            "enum": ["zip", "folder"],
                            "default": "zip"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Output path (optional)"
                        }
                    }
                }
            ),
            Tool(
                name="create_research_index",
                description="Create an index of all research files",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ])
        
        # GitHub tools (if available)
        if self.github_client:
            tools.extend([
                Tool(
                    name="upload_to_github",
                    description="Upload file to GitHub repository",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Local file path"
                            },
                            "github_path": {
                                "type": "string",
                                "description": "Path in GitHub repository"
                            },
                            "commit_message": {
                                "type": "string",
                                "description": "Commit message (optional)"
                            }
                        },
                        "required": ["file_path", "github_path"]
                    }
                ),
                Tool(
                    name="upload_directory_to_github",
                    description="Upload entire directory to GitHub",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "local_dir": {
                                "type": "string",
                                "description": "Local directory path"
                            },
                            "github_dir": {
                                "type": "string",
                                "description": "Target directory in GitHub (optional)",
                                "default": ""
                            },
                            "commit_message": {
                                "type": "string",
                                "description": "Commit message (optional)"
                            }
                        },
                        "required": ["local_dir"]
                    }
                ),
                Tool(
                    name="create_github_summary",
                    description="Create research summary in GitHub repository",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Summary title"
                            },
                            "content": {
                                "type": "string",
                                "description": "Summary content"
                            },
                            "path": {
                                "type": "string",
                                "description": "Directory path in repository",
                                "default": "research_summaries"
                            }
                        },
                        "required": ["title", "content"]
                    }
                ),
                Tool(
                    name="sync_with_github",
                    description="Synchronize local research data with GitHub",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "direction": {
                                "type": "string",
                                "description": "Sync direction",
                                "enum": ["up", "down"],
                                "default": "up"
                            }
                        }
                    }
                ),
                Tool(
                    name="list_github_contents",
                    description="List contents of GitHub repository",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Repository path",
                                "default": ""
                            }
                        }
                    }
                ),
                Tool(
                    name="get_repository_info",
                    description="Get GitHub repository information",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ])
        
        return tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Call a specific tool with arguments.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        try:
            # ArXiv tools
            if name == "search_arxiv":
                return await self._search_arxiv(arguments)
            elif name == "fetch_paper":
                return await self._fetch_paper(arguments)
            elif name == "download_paper_content":
                return await self._download_paper_content(arguments)
            
            # Groq tools
            elif name == "summarize_paper":
                return await self._summarize_paper(arguments)
            elif name == "extract_key_points":
                return await self._extract_key_points(arguments)
            elif name == "create_structured_summary":
                return await self._create_structured_summary(arguments)
            elif name == "generate_citation":
                return await self._generate_citation(arguments)
            elif name == "compare_papers":
                return await self._compare_papers(arguments)
            
            # File management tools
            elif name == "save_notes":
                return await self._save_notes(arguments)
            elif name == "save_summary":
                return await self._save_summary(arguments)
            elif name == "save_reference":
                return await self._save_reference(arguments)
            elif name == "search_local_notes":
                return await self._search_local_notes(arguments)
            elif name == "list_research_files":
                return await self._list_research_files(arguments)
            elif name == "organize_by_tags":
                return await self._organize_by_tags(arguments)
            elif name == "export_research_data":
                return await self._export_research_data(arguments)
            elif name == "create_research_index":
                return await self._create_research_index(arguments)
            
            # GitHub tools
            elif name == "upload_to_github":
                return await self._upload_to_github(arguments)
            elif name == "upload_directory_to_github":
                return await self._upload_directory_to_github(arguments)
            elif name == "create_github_summary":
                return await self._create_github_summary(arguments)
            elif name == "sync_with_github":
                return await self._sync_with_github(arguments)
            elif name == "list_github_contents":
                return await self._list_github_contents(arguments)
            elif name == "get_repository_info":
                return await self._get_repository_info(arguments)
            
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")]
                )
                
        except Exception as e:
            logger.error(f"Tool execution failed for {name}: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error executing {name}: {str(e)}")]
            )
    
    # ArXiv tool implementations
    async def _search_arxiv(self, args: Dict[str, Any]) -> CallToolResult:
        """Search ArXiv implementation."""
        query = args["query"]
        max_results = args.get("max_results", 10)
        sort_by = args.get("sort_by", "relevance")
        
        papers = self.arxiv_client.search_papers(query, max_results, sort_by)
        
        result = {
            "query": query,
            "total_results": len(papers),
            "papers": papers
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _fetch_paper(self, args: Dict[str, Any]) -> CallToolResult:
        """Fetch paper implementation."""
        arxiv_id = args["arxiv_id"]
        
        if not validate_arxiv_id(arxiv_id):
            return CallToolResult(
                content=[TextContent(type="text", text=f"Invalid ArXiv ID format: {arxiv_id}")]
            )
        
        paper = self.arxiv_client.get_paper_by_id(arxiv_id)
        
        if not paper:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Paper not found: {arxiv_id}")]
            )
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(paper, indent=2))]
        )
    
    async def _download_paper_content(self, args: Dict[str, Any]) -> CallToolResult:
        """Download paper content implementation."""
        arxiv_id = args["arxiv_id"]
        
        content = self.arxiv_client.download_paper_content(arxiv_id)
        
        if not content:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Failed to download content for: {arxiv_id}")]
            )
        
        return CallToolResult(
            content=[TextContent(type="text", text=content)]
        )
    
    # Groq tool implementations
    async def _summarize_paper(self, args: Dict[str, Any]) -> CallToolResult:
        """Summarize paper implementation."""
        if not self.groq_client:
            return CallToolResult(
                content=[TextContent(type="text", text="Groq client not available. Please configure GROQ_API_KEY.")]
            )
        
        content = args["content"]
        style = args.get("style", "academic")
        arxiv_id = args.get("arxiv_id")
        
        summary = self.groq_client.summarize_paper(content, style)
        
        # Add arxiv_id to summary if provided
        if arxiv_id:
            summary["arxiv_id"] = arxiv_id
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(summary, indent=2))]
        )
    
    async def _extract_key_points(self, args: Dict[str, Any]) -> CallToolResult:
        """Extract key points implementation."""
        if not self.groq_client:
            return CallToolResult(
                content=[TextContent(type="text", text="Groq client not available. Please configure GROQ_API_KEY.")]
            )
        
        content = args["content"]
        num_points = args.get("num_points", 5)
        
        key_points = self.groq_client.generate_key_points(content, num_points)
        
        result = {
            "key_points": key_points,
            "count": len(key_points)
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _create_structured_summary(self, args: Dict[str, Any]) -> CallToolResult:
        """Create structured summary implementation."""
        if not self.groq_client:
            return CallToolResult(
                content=[TextContent(type="text", text="Groq client not available. Please configure GROQ_API_KEY.")]
            )
        
        content = args["content"]
        sections = args.get("sections")
        
        summary = self.groq_client.create_structured_summary(content, sections)
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(summary, indent=2))]
        )
    
    async def _generate_citation(self, args: Dict[str, Any]) -> CallToolResult:
        """Generate citation implementation."""
        paper_metadata = args["paper_metadata"]
        style = args.get("style", "apa")
        
        if self.groq_client:
            citation = self.groq_client.generate_citation(paper_metadata, style)
        else:
            # Fallback to local implementation for APA
            if style == "apa":
                citation = create_citation_apa(paper_metadata)
            else:
                citation = f"Citation generation requires Groq API for {style} style"
        
        result = {
            "citation": citation,
            "style": style,
            "paper_id": paper_metadata.get("id", "")
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _compare_papers(self, args: Dict[str, Any]) -> CallToolResult:
        """Compare papers implementation."""
        if not self.groq_client:
            return CallToolResult(
                content=[TextContent(type="text", text="Groq client not available. Please configure GROQ_API_KEY.")]
            )
        
        papers_content = args["papers_content"]
        comparison_aspects = args.get("comparison_aspects")
        
        comparison = self.groq_client.compare_papers(papers_content, comparison_aspects)
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(comparison, indent=2))]
        )
    
    # File management tool implementations
    async def _save_notes(self, args: Dict[str, Any]) -> CallToolResult:
        """Save notes implementation."""
        title = args["title"]
        content = args["content"]
        tags = args.get("tags", [])
        metadata = args.get("metadata", {})
        
        file_path = self.file_manager.save_notes(title, content, tags, metadata)
        
        result = {
            "saved": True,
            "file_path": file_path,
            "title": title,
            "tags": tags
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _save_summary(self, args: Dict[str, Any]) -> CallToolResult:
        """Save summary implementation."""
        paper_id = args["paper_id"]
        summary_data = args["summary_data"]
        format_type = args.get("format", "json")
        
        file_path = self.file_manager.save_summary(paper_id, summary_data, format_type)
        
        result = {
            "saved": True,
            "file_path": file_path,
            "paper_id": paper_id,
            "format": format_type
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _save_reference(self, args: Dict[str, Any]) -> CallToolResult:
        """Save reference implementation."""
        paper_id = args["paper_id"]
        reference_data = args["reference_data"]
        
        file_path = self.file_manager.save_reference(paper_id, reference_data)
        
        result = {
            "saved": True,
            "file_path": file_path,
            "paper_id": paper_id
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _search_local_notes(self, args: Dict[str, Any]) -> CallToolResult:
        """Search local notes implementation."""
        query = args["query"]
        search_content = args.get("search_content", True)
        search_tags = args.get("search_tags", True)
        
        results = self.file_manager.search_notes(query, search_content, search_tags)
        
        result = {
            "query": query,
            "results_count": len(results),
            "results": results
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _list_research_files(self, args: Dict[str, Any]) -> CallToolResult:
        """List research files implementation."""
        directory = args.get("directory", "all")
        
        files = self.file_manager.list_files(directory)
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(files, indent=2))]
        )
    
    async def _organize_by_tags(self, args: Dict[str, Any]) -> CallToolResult:
        """Organize by tags implementation."""
        tag_map = self.file_manager.organize_by_tags()
        
        result = {
            "total_tags": len(tag_map),
            "tag_organization": tag_map
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _export_research_data(self, args: Dict[str, Any]) -> CallToolResult:
        """Export research data implementation."""
        format_type = args.get("format", "zip")
        output_path = args.get("output_path")
        
        export_path = self.file_manager.export_research_data(format_type, output_path)
        
        result = {
            "exported": True,
            "export_path": export_path,
            "format": format_type
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _create_research_index(self, args: Dict[str, Any]) -> CallToolResult:
        """Create research index implementation."""
        index = create_research_index(self.file_manager.research_dir)
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(index, indent=2))]
        )
    
    # GitHub tool implementations
    async def _upload_to_github(self, args: Dict[str, Any]) -> CallToolResult:
        """Upload to GitHub implementation."""
        if not self.github_client:
            return CallToolResult(
                content=[TextContent(type="text", text="GitHub client not available. Please configure GitHub settings.")]
            )
        
        file_path = args["file_path"]
        github_path = args["github_path"]
        commit_message = args.get("commit_message")
        
        result = self.github_client.upload_file(file_path, github_path, commit_message)
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _upload_directory_to_github(self, args: Dict[str, Any]) -> CallToolResult:
        """Upload directory to GitHub implementation."""
        if not self.github_client:
            return CallToolResult(
                content=[TextContent(type="text", text="GitHub client not available. Please configure GitHub settings.")]
            )
        
        local_dir = args["local_dir"]
        github_dir = args.get("github_dir", "")
        commit_message = args.get("commit_message")
        
        result = self.github_client.upload_directory(local_dir, github_dir, commit_message)
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _create_github_summary(self, args: Dict[str, Any]) -> CallToolResult:
        """Create GitHub summary implementation."""
        if not self.github_client:
            return CallToolResult(
                content=[TextContent(type="text", text="GitHub client not available. Please configure GitHub settings.")]
            )
        
        title = args["title"]
        content = args["content"]
        path = args.get("path", "research_summaries")
        
        result = self.github_client.create_research_summary(title, content, path)
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _sync_with_github(self, args: Dict[str, Any]) -> CallToolResult:
        """Sync with GitHub implementation."""
        if not self.github_client:
            return CallToolResult(
                content=[TextContent(type="text", text="GitHub client not available. Please configure GitHub settings.")]
            )
        
        direction = args.get("direction", "up")
        
        result = self.github_client.sync_local_directory(
            str(self.file_manager.research_dir),
            "research_data",
            direction
        )
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _list_github_contents(self, args: Dict[str, Any]) -> CallToolResult:
        """List GitHub contents implementation."""
        if not self.github_client:
            return CallToolResult(
                content=[TextContent(type="text", text="GitHub client not available. Please configure GitHub settings.")]
            )
        
        path = args.get("path", "")
        
        contents = self.github_client.list_repository_contents(path)
        
        result = {
            "path": path,
            "contents": contents
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _get_repository_info(self, args: Dict[str, Any]) -> CallToolResult:
        """Get repository info implementation."""
        if not self.github_client:
            return CallToolResult(
                content=[TextContent(type="text", text="GitHub client not available. Please configure GitHub settings.")]
            )
        
        info = self.github_client.get_repository_info()
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(info, indent=2))]
        )
