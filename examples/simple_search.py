"""
Simple example: Search and summarize a paper.

This is a minimal example showing how to search for a paper,
download its content, and generate a summary.
"""

import asyncio
import json
import os
from pathlib import Path

# Add the src directory to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_research_assistant.research_tools import ResearchTools


async def search_and_summarize():
    """Simple workflow: search, fetch, and summarize."""
    
    # Configuration
    config = {
        "groq_api_key": os.getenv("GROQ_API_KEY"),
        "groq_model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        "research_dir": "./simple_research",
        "arxiv_max_results": 1
    }
    
    # Initialize tools
    tools = ResearchTools(config)
    
    print("🔍 Searching for a paper on 'attention mechanisms'...")
    
    # Search for papers
    search_result = await tools.call_tool("search_arxiv", {
        "query": "attention mechanisms neural networks",
        "max_results": 1
    })
    
    search_data = json.loads(search_result.content[0].text)
    
    if not search_data["papers"]:
        print("❌ No papers found")
        return
    
    paper = search_data["papers"][0]
    paper_id = paper["id"]
    
    print(f"📄 Found paper: {paper['title']}")
    print(f"   ID: {paper_id}")
    print(f"   Authors: {', '.join(paper['authors'][:3])}...")
    
    # Download content
    print("\n⬇️ Downloading paper content...")
    content_result = await tools.call_tool("download_paper_content", {
        "arxiv_id": paper_id
    })
    
    content = content_result.content[0].text
    print(f"✅ Downloaded {len(content)} characters")
    
    # Generate summary (if Groq API is available)
    if config.get("groq_api_key"):
        print("\n🤖 Generating AI summary...")
        summary_result = await tools.call_tool("summarize_paper", {
            "content": content,
            "style": "brief"
        })
        
        result_text = summary_result.content[0].text
        
        # Check if the result is an error message
        if result_text.startswith("Error"):
            print(f"\n⚠️ AI summarization failed: {result_text}")
            print("The paper content is still available for manual review.")
        else:
            summary_data = json.loads(result_text)
            print("\n📋 Summary:")
            print("=" * 50)
            print(summary_data.get("summary", "No summary generated"))
            print("=" * 50)
            
            # Save the summary
            save_result = await tools.call_tool("save_summary", {
                "paper_id": paper_id,
                "summary_data": {
                    **paper,
                    **summary_data
                }
            })
            
            save_data = json.loads(save_result.content[0].text)
            print(f"\n💾 Summary saved to: {save_data['file_path']}")
    
    else:
        print("⚠️ Groq API key not configured - skipping AI summary")
        print("Set GROQ_API_KEY environment variable to enable AI features")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the example
    asyncio.run(search_and_summarize())
