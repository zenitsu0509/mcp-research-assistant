"""
Example usage of the MCP Research Assistant.

This script demonstrates how to use the research assistant tools
to perform various research tasks.
"""

import asyncio
import json
import os
from pathlib import Path

# Add the src directory to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_research_assistant.research_tools import ResearchTools
from mcp_research_assistant.utils import setup_logging


async def main():
    """Demonstrate research assistant functionality."""
    
    # Set up logging
    setup_logging("INFO")
    
    # Load configuration (you should set these in your .env file)
    config = {
        "groq_api_key": os.getenv("GROQ_API_KEY"),
        "github_token": os.getenv("GITHUB_TOKEN"),
        "github_username": os.getenv("GITHUB_USERNAME"),
        "github_repo": os.getenv("GITHUB_REPO"),
        "research_dir": "./example_research_data",
        "arxiv_max_results": 5,
        "arxiv_delay_seconds": 1.0
    }
    
    # Initialize research tools
    print("🔬 Initializing Research Assistant...")
    research_tools = ResearchTools(config)
    
    # Example 1: Search ArXiv for papers
    print("\n📚 Searching ArXiv for machine learning papers...")
    search_result = await research_tools.call_tool("search_arxiv", {
        "query": "machine learning transformers",
        "max_results": 3
    })
    
    search_data = json.loads(search_result.content[0].text)
    print(f"Found {search_data['total_results']} papers")
    
    if search_data["papers"]:
        first_paper = search_data["papers"][0]
        print(f"First paper: {first_paper['title']}")
        paper_id = first_paper['id']
        
        # Example 2: Fetch detailed paper information
        print(f"\n📄 Fetching details for paper {paper_id}...")
        paper_result = await research_tools.call_tool("fetch_paper", {
            "arxiv_id": paper_id
        })
        paper_data = json.loads(paper_result.content[0].text)
        
        # Example 3: Download paper content
        print(f"\n⬇️ Downloading content for paper {paper_id}...")
        content_result = await research_tools.call_tool("download_paper_content", {
            "arxiv_id": paper_id
        })
        paper_content = content_result.content[0].text
        print(f"Downloaded {len(paper_content)} characters of content")
        
        # Example 4: Summarize paper (if Groq API is available)
        if config.get("groq_api_key"):
            print(f"\n🤖 Generating AI summary for paper {paper_id}...")
            summary_result = await research_tools.call_tool("summarize_paper", {
                "content": paper_content,
                "style": "academic",
                "arxiv_id": paper_id
            })
            summary_data = json.loads(summary_result.content[0].text)
            print(f"Generated summary: {summary_data.get('summary', 'N/A')[:200]}...")
            
            # Example 5: Extract key points
            print(f"\n🔑 Extracting key points...")
            keypoints_result = await research_tools.call_tool("extract_key_points", {
                "content": paper_content,
                "num_points": 3
            })
            keypoints_data = json.loads(keypoints_result.content[0].text)
            print("Key points:")
            for i, point in enumerate(keypoints_data.get("key_points", []), 1):
                print(f"  {i}. {point}")
        
        # Example 6: Save notes about the paper
        print(f"\n📝 Saving research notes...")
        notes_result = await research_tools.call_tool("save_notes", {
            "title": f"Notes on {paper_data.get('title', 'Unknown Paper')}",
            "content": f"This paper discusses {paper_data.get('title', 'research topics')}.\n\nMain authors: {', '.join(paper_data.get('authors', []))}\n\nKey findings: [Add your analysis here]",
            "tags": ["arxiv", "ml", "research"],
            "metadata": {
                "arxiv_id": paper_id,
                "source": "arxiv_search"
            }
        })
        notes_data = json.loads(notes_result.content[0].text)
        print(f"Saved notes to: {notes_data.get('file_path')}")
        
        # Example 7: Save paper summary
        if config.get("groq_api_key") and 'summary_data' in locals():
            print(f"\n💾 Saving paper summary...")
            save_summary_result = await research_tools.call_tool("save_summary", {
                "paper_id": paper_id,
                "summary_data": {
                    **paper_data,
                    **summary_data
                },
                "format": "json"
            })
            save_data = json.loads(save_summary_result.content[0].text)
            print(f"Saved summary to: {save_data.get('file_path')}")
        
        # Example 8: Save reference data
        print(f"\n📚 Saving reference data...")
        ref_result = await research_tools.call_tool("save_reference", {
            "paper_id": paper_id,
            "reference_data": paper_data
        })
        ref_data = json.loads(ref_result.content[0].text)
        print(f"Saved reference to: {ref_data.get('file_path')}")
    
    # Example 9: Search local notes
    print(f"\n🔍 Searching local notes...")
    search_notes_result = await research_tools.call_tool("search_local_notes", {
        "query": "machine learning"
    })
    search_notes_data = json.loads(search_notes_result.content[0].text)
    print(f"Found {search_notes_data.get('results_count', 0)} matching notes")
    
    # Example 10: List research files
    print(f"\n📂 Listing research files...")
    list_files_result = await research_tools.call_tool("list_research_files", {
        "directory": "all"
    })
    files_data = json.loads(list_files_result.content[0].text)
    print(f"Notes: {len(files_data.get('notes', []))}")
    print(f"Summaries: {len(files_data.get('summaries', []))}")
    print(f"References: {len(files_data.get('references', []))}")
    
    # Example 11: Create research index
    print(f"\n📊 Creating research index...")
    index_result = await research_tools.call_tool("create_research_index", {})
    index_data = json.loads(index_result.content[0].text)
    print(f"Total files indexed: {index_data.get('total_files', 0)}")
    print(f"Unique tags: {len(index_data.get('tags', []))}")
    print(f"Categories: {len(index_data.get('categories', []))}")
    
    # Example 12: Export research data
    print(f"\n📦 Exporting research data...")
    export_result = await research_tools.call_tool("export_research_data", {
        "format": "zip",
        "output_path": "research_backup"
    })
    export_data = json.loads(export_result.content[0].text)
    print(f"Exported to: {export_data.get('export_path')}")
    
    # Example 13: GitHub integration (if configured)
    if config.get("github_token") and config.get("github_username") and config.get("github_repo"):
        print(f"\n🐙 GitHub integration examples...")
        
        # Get repository info
        repo_info_result = await research_tools.call_tool("get_repository_info", {})
        repo_data = json.loads(repo_info_result.content[0].text)
        print(f"Connected to repository: {repo_data.get('full_name')}")
        
        # Create a research summary on GitHub
        github_summary_result = await research_tools.call_tool("create_github_summary", {
            "title": "Research Summary - Machine Learning Papers",
            "content": f"## Research Summary\n\nThis is an automated summary of research conducted on {len(search_data.get('papers', []))} machine learning papers.\n\n### Key Findings\n- Analyzed papers from ArXiv\n- Generated AI-powered summaries\n- Organized research notes\n\n*Generated by MCP Research Assistant*"
        })
        github_data = json.loads(github_summary_result.content[0].text)
        print(f"Created GitHub summary: {github_data.get('html_url')}")
    
    print("\n✅ Research assistant demo completed!")
    print(f"Check your research directory: {config['research_dir']}")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the example
    asyncio.run(main())
