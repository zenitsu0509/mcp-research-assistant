# MCP Research Assistant

A custom Model Context Protocol (MCP) Server that enables AI assistants to perform comprehensive research tasks. This server provides seamless integration with ArXiv for paper discovery, Groq API for intelligent summarization, local file system for organization, and GitHub for collaboration.

## Features

### 🔬 Research Capabilities
- **ArXiv Integration**: Search and fetch research papers from ArXiv
- **Intelligent Summarization**: Leverage Groq API for high-quality paper summaries
- **Reference Management**: Organize and track research references
- **Citation Generation**: Generate proper citations for papers

### 📁 File System Management
- **Note Organization**: Create and manage research notes
- **Summary Storage**: Save paper summaries in structured formats
- **Reference Library**: Build a local library of research materials
- **Export Options**: Export research data in various formats

### 🔗 GitHub Integration
- **Repository Management**: Push research notes and reports to GitHub
- **Collaboration**: Share research findings with team members
- **Version Control**: Track changes in research documentation
- **Automated Commits**: Automatic organization of research materials

### 🚀 MCP Tools
All capabilities are exposed as MCP tools for seamless AI integration:
- `search_arxiv`: Search ArXiv for research papers
- `fetch_paper`: Download and parse paper content
- `summarize_paper`: Generate AI-powered summaries using Groq
- `save_notes`: Save research notes locally
- `create_summary`: Create structured research summaries
- `organize_references`: Manage reference collections
- `push_to_github`: Upload research materials to GitHub
- `search_local_notes`: Find existing research notes
- `generate_citation`: Create proper citations
- `export_research`: Export research in various formats

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/mcp-research-assistant.git
cd mcp-research-assistant
```

2. Install dependencies:
```bash
pip install -e .
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

Create a `.env` file with the following variables:

```env
# Groq API for summarization
GROQ_API_KEY=your_groq_api_key_here

# GitHub API for repository integration
GITHUB_TOKEN=your_github_token_here
GITHUB_USERNAME=your_github_username
GITHUB_REPO=your_research_repo_name

# Local paths
RESEARCH_DIR=./research_data
NOTES_DIR=./research_data/notes
SUMMARIES_DIR=./research_data/summaries
REFERENCES_DIR=./research_data/references
```

## Usage

### Running the MCP Server

Start the server:
```bash
python -m mcp_research_assistant.server
```

Or use the installed command:
```bash
mcp-research-assistant
```

### MCP Client Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "research-assistant": {
      "command": "mcp-research-assistant",
      "args": []
    }
  }
}
```

### Example Workflows

1. **Research a Topic**:
   - Search ArXiv for relevant papers
   - Fetch interesting papers
   - Generate summaries using Groq
   - Save organized notes
   - Push findings to GitHub

2. **Literature Review**:
   - Search multiple topics
   - Collect and summarize papers
   - Organize references by theme
   - Export comprehensive review

3. **Collaborative Research**:
   - Share notes via GitHub
   - Track research progress
   - Maintain version history

## API Reference

### ArXiv Tools
- `search_arxiv(query, max_results)`: Search ArXiv database
- `fetch_paper(arxiv_id)`: Download paper content
- `get_paper_metadata(arxiv_id)`: Get paper information

### Summarization Tools
- `summarize_paper(content, style)`: Groq-powered summarization
- `generate_key_points(content)`: Extract key insights
- `create_abstract_summary(content)`: Generate abstracts

### File System Tools
- `save_notes(title, content, tags)`: Save research notes
- `search_local_notes(query)`: Find existing notes
- `organize_files(structure)`: Organize research files
- `export_research(format, filter)`: Export research data

### GitHub Tools
- `push_to_github(files, commit_message)`: Upload to repository
- `create_research_branch(name)`: Create feature branch
- `sync_research_repo()`: Synchronize with remote

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Format code
black .
isort .

# Type checking
mypy src/
```

### Project Structure

```
mcp-research-assistant/
├── src/mcp_research_assistant/
│   ├── __init__.py
│   ├── server.py              # Main MCP server
│   ├── arxiv_client.py        # ArXiv API integration
│   ├── groq_client.py         # Groq API integration
│   ├── file_manager.py        # Local file system management
│   ├── github_client.py       # GitHub API integration
│   ├── research_tools.py      # MCP tool implementations
│   └── utils.py               # Utility functions
├── tests/
├── examples/
├── README.md
├── pyproject.toml
└── .env.example
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review example workflows

---

Built with ❤️ for the research community
