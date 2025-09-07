"""
Example MCP client configuration for Claude or other MCP-enabled clients.

Add this configuration to your MCP client to connect to the research assistant server.
"""

# Claude Desktop Configuration
# Add to your Claude Desktop config file (usually at ~/.config/claude-desktop/claude_desktop_config.json)

CLAUDE_DESKTOP_CONFIG = {
    "mcpServers": {
        "research-assistant": {
            "command": "python",
            "args": [
                "-m", "mcp_research_assistant.server"
            ],
            "env": {
                "GROQ_API_KEY": "your_groq_api_key_here",
                "GITHUB_TOKEN": "your_github_token_here", 
                "GITHUB_USERNAME": "your_github_username",
                "GITHUB_REPO": "your_research_repo_name",
                "RESEARCH_DIR": "./research_data"
            }
        }
    }
}

# Alternative: Using the installed command
CLAUDE_DESKTOP_CONFIG_ALT = {
    "mcpServers": {
        "research-assistant": {
            "command": "mcp-research-assistant",
            "env": {
                "GROQ_API_KEY": "your_groq_api_key_here",
                "GITHUB_TOKEN": "your_github_token_here",
                "GITHUB_USERNAME": "your_github_username", 
                "GITHUB_REPO": "your_research_repo_name"
            }
        }
    }
}

# Example usage prompts for Claude

EXAMPLE_PROMPTS = [
    # Basic search
    "Search ArXiv for papers about 'transformer architecture' and summarize the top 3 results",
    
    # Detailed analysis
    "Find papers on 'few-shot learning', download the content of the most recent one, generate a structured summary, and save it to my research notes",
    
    # Literature review
    "Search for papers on 'graph neural networks' from the last year, create summaries for each, organize them by methodology, and push the results to my GitHub repository",
    
    # Research organization
    "List all my saved research notes, organize them by tags, and create an index of my research library",
    
    # Comparison study
    "Find 3 papers on 'attention mechanisms', compare their approaches and findings, and create a comparative analysis document",
    
    # Citation management
    "Generate APA citations for all papers in my references directory and create a bibliography file",
    
    # Research export
    "Export all my research data as a zip file and create a summary report of my research progress"
]

# Example workflow description
WORKFLOW_EXAMPLE = """
Example Research Workflow with MCP Research Assistant:

1. **Discovery Phase**
   - Use search_arxiv to find relevant papers
   - Filter by publication date, authors, or categories
   - Save interesting papers to reference library

2. **Analysis Phase**  
   - Download paper content for detailed analysis
   - Generate AI-powered summaries using Groq
   - Extract key points and contributions
   - Create structured summaries with specific sections

3. **Organization Phase**
   - Save research notes with tags and metadata
   - Organize papers by topic or methodology
   - Create cross-references between related work

4. **Collaboration Phase**
   - Push research notes to GitHub repository
   - Create research summaries for team sharing
   - Sync findings across different projects

5. **Documentation Phase**
   - Generate citations in various formats
   - Create research indexes and bibliographies
   - Export research data for backup or sharing

The MCP Research Assistant handles all the technical details while you focus on the research content and insights.
"""

if __name__ == "__main__":
    import json
    
    print("MCP Research Assistant Configuration Examples")
    print("=" * 50)
    
    print("\n1. Claude Desktop Configuration:")
    print(json.dumps(CLAUDE_DESKTOP_CONFIG, indent=2))
    
    print("\n2. Example Usage Prompts:")
    for i, prompt in enumerate(EXAMPLE_PROMPTS, 1):
        print(f"{i}. {prompt}")
    
    print(f"\n3. Workflow Overview:")
    print(WORKFLOW_EXAMPLE)
