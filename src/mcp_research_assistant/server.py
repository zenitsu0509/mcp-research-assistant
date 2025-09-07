"""Main MCP server for research assistant functionality."""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional
import json

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from dotenv import load_dotenv

from .research_tools import ResearchTools
from .utils import setup_logging, validate_environment

# Load environment variables
load_dotenv()

# Set up logging
setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


class ResearchAssistantServer:
    """MCP Server for research assistant functionality."""
    
    def __init__(self):
        """Initialize the research assistant server."""
        self.server = Server("mcp-research-assistant")
        self.research_tools = None
        
        # Load configuration
        self.config = self._load_config()
        
        # Validate environment
        validation = validate_environment()
        missing_config = [key for key, valid in validation.items() if not valid]
        
        if missing_config:
            logger.warning(f"Missing configuration: {missing_config}")
            logger.warning("Some features may be unavailable")
        
        # Initialize research tools
        try:
            self.research_tools = ResearchTools(self.config)
            logger.info("Research tools initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize research tools: {e}")
            raise
        
        # Register handlers
        self._register_handlers()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables.
        
        Returns:
            Configuration dictionary
        """
        config = {
            # Groq API settings
            "groq_api_key": os.getenv("GROQ_API_KEY"),
            "groq_model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            "groq_max_tokens": int(os.getenv("GROQ_MAX_TOKENS", "2048")),
            "groq_temperature": float(os.getenv("GROQ_TEMPERATURE", "0.1")),
            
            # GitHub settings
            "github_token": os.getenv("GITHUB_TOKEN"),
            "github_username": os.getenv("GITHUB_USERNAME"),
            "github_repo": os.getenv("GITHUB_REPO"),
            
            # Local file paths
            "research_dir": os.getenv("RESEARCH_DIR", "./research_data"),
            "notes_dir": os.getenv("NOTES_DIR"),
            "summaries_dir": os.getenv("SUMMARIES_DIR"),
            "references_dir": os.getenv("REFERENCES_DIR"),
            
            # ArXiv settings
            "arxiv_max_results": int(os.getenv("ARXIV_MAX_RESULTS", "10")),
            "arxiv_delay_seconds": float(os.getenv("ARXIV_DELAY_SECONDS", "1.0"))
        }
        
        # Remove None values
        config = {k: v for k, v in config.items() if v is not None}
        
        logger.info(f"Loaded configuration with {len(config)} settings")
        return config
    
    def _register_handlers(self):
        """Register MCP server handlers."""
        
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """List available resources."""
            resources = [
                Resource(
                    uri="research://config",
                    name="Research Assistant Configuration",
                    description="Current configuration and status of the research assistant",
                    mimeType="application/json"
                ),
                Resource(
                    uri="research://index",
                    name="Research Data Index",
                    description="Index of all research files and metadata",
                    mimeType="application/json"
                )
            ]
            
            if self.research_tools and self.research_tools.github_client:
                resources.append(
                    Resource(
                        uri="research://github/repo",
                        name="GitHub Repository Info",
                        description="Information about the connected GitHub repository",
                        mimeType="application/json"
                    )
                )
            
            return resources
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content."""
            if uri == "research://config":
                status = {
                    "config": self.config,
                    "features": {
                        "arxiv_search": True,
                        "groq_summarization": bool(self.config.get("groq_api_key")),
                        "github_integration": bool(
                            self.config.get("github_token") and 
                            self.config.get("github_username") and 
                            self.config.get("github_repo")
                        ),
                        "local_file_management": True
                    },
                    "validation": validate_environment()
                }
                return json.dumps(status, indent=2)
            
            elif uri == "research://index":
                if self.research_tools:
                    from .utils import create_research_index
                    index = create_research_index(self.research_tools.file_manager.research_dir)
                    return json.dumps(index, indent=2)
                else:
                    return json.dumps({"error": "Research tools not initialized"})
            
            elif uri == "research://github/repo":
                if self.research_tools and self.research_tools.github_client:
                    repo_info = self.research_tools.github_client.get_repository_info()
                    return json.dumps(repo_info, indent=2)
                else:
                    return json.dumps({"error": "GitHub client not available"})
            
            else:
                raise ValueError(f"Unknown resource: {uri}")
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            if not self.research_tools:
                return []
            
            try:
                tools = self.research_tools.get_tools()
                logger.info(f"Listed {len(tools)} available tools")
                return tools
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                return []
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
            """Call a tool with given arguments."""
            if not self.research_tools:
                return [TextContent(type="text", text="Research tools not initialized")]
            
            logger.info(f"Calling tool: {name} with arguments: {arguments}")
            
            try:
                result = await self.research_tools.call_tool(name, arguments)
                return result.content
            except Exception as e:
                logger.error(f"Tool call failed for {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def run(self):
        """Run the MCP server."""
        logger.info("Starting MCP Research Assistant Server")
        
        # Log startup information (don't print to stdout as it interferes with MCP protocol)
        logger.info("MCP Research Assistant Server Starting")
        logger.info("=" * 50)
        logger.info(f"Groq API: {'OK' if self.config.get('groq_api_key') else 'NOT_SET'}")
        logger.info(f"GitHub: {'OK' if self.config.get('github_token') else 'NOT_SET'}")
        logger.info(f"Research Dir: {self.config.get('research_dir', './research_data')}")
        logger.info("=" * 50)
        
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Main entry point for the server."""
    try:
        server = ResearchAssistantServer()
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
