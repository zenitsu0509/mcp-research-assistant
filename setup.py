#!/usr/bin/env python3
"""
Quick setup script for MCP Research Assistant.

This script helps users set up the research assistant with
interactive configuration.
"""

import os
import sys
from pathlib import Path


def create_env_file():
    """Create .env file with user input."""
    env_path = Path(".env")
    
    if env_path.exists():
        print("📄 .env file already exists")
        return
    
    print("🔧 Setting up environment configuration...")
    print("\nPlease provide the following information (press Enter to skip optional items):")
    
    # Groq API Key
    groq_key = input("\n🤖 Groq API Key (for AI summarization): ").strip()
    
    # GitHub settings
    print("\n🐙 GitHub Integration (optional):")
    github_token = input("   GitHub Token: ").strip()
    github_username = input("   GitHub Username: ").strip()
    github_repo = input("   GitHub Repository: ").strip()
    
    # Research directory
    research_dir = input("\n📁 Research Directory (default: ./research_data): ").strip()
    if not research_dir:
        research_dir = "./research_data"
    
    # Create .env content
    env_content = [
        "# MCP Research Assistant Configuration",
        "",
        "# Groq API for AI-powered summarization",
        f"GROQ_API_KEY={groq_key}",
        "",
        "# GitHub integration (optional)",
        f"GITHUB_TOKEN={github_token}",
        f"GITHUB_USERNAME={github_username}",
        f"GITHUB_REPO={github_repo}",
        "",
        "# Local paths",
        f"RESEARCH_DIR={research_dir}",
        "",
        "# Optional: ArXiv settings",
        "ARXIV_MAX_RESULTS=10",
        "ARXIV_DELAY_SECONDS=1",
        "",
        "# Optional: Groq model settings",
        "GROQ_MODEL=llama-3.1-8b-instant",
        "GROQ_MAX_TOKENS=2048",
        "GROQ_TEMPERATURE=0.1",
        ""
    ]
    
    with open(env_path, 'w') as f:
        f.write('\n'.join(env_content))
    
    print(f"✅ Created .env file at {env_path.absolute()}")


def create_claude_config():
    """Create Claude Desktop configuration."""
    print("\n📋 Claude Desktop Configuration:")
    print("Add this to your Claude Desktop config file:")
    print("(usually at ~/.config/claude-desktop/claude_desktop_config.json)")
    
    config = '''
{
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
    '''.strip()
    
    print(config)
    
    # Save to file
    config_path = Path("claude_config_example.json")
    with open(config_path, 'w') as f:
        f.write(config)
    
    print(f"\n💾 Saved example config to: {config_path.absolute()}")


def test_installation():
    """Test the installation."""
    print("\n🧪 Testing installation...")
    
    try:
        # Test imports
        from mcp_research_assistant.arxiv_client import ArXivClient
        from mcp_research_assistant.research_tools import ResearchTools
        print("   ✅ Python imports working")
        
        # Test ArXiv client
        client = ArXivClient(delay_seconds=0.5, max_results=1)
        papers = client.search_papers("test", max_results=1)
        print(f"   ✅ ArXiv integration working (found {len(papers)} papers)")
        
        # Test research tools initialization
        config = {"research_dir": "./test_setup", "arxiv_max_results": 1}
        tools = ResearchTools(config)
        available_tools = tools.get_tools()
        print(f"   ✅ Research tools working ({len(available_tools)} tools available)")
        
        print("\n🎉 Installation test passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🔬 MCP Research Assistant Setup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Please run this script from the mcp-research-assistant directory")
        sys.exit(1)
    
    # Install package if not already installed
    print("📦 Checking installation...")
    try:
        import mcp_research_assistant
        print("   ✅ Package already installed")
    except ImportError:
        print("   📥 Installing package...")
        os.system(f"{sys.executable} -m pip install -e .")
    
    # Create environment configuration
    create_env_file()
    
    # Create Claude config example
    create_claude_config()
    
    # Test installation
    if test_installation():
        print("\n🚀 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your API keys")
        print("2. Add the Claude config to your Claude Desktop")
        print("3. Restart Claude Desktop")
        print("4. Try: 'Search ArXiv for papers about machine learning'")
        
        print(f"\n📖 Documentation: README.md")
        print(f"🧪 Run examples: python examples/simple_search.py")
    else:
        print("\n❌ Setup encountered issues. Please check the error messages above.")


if __name__ == "__main__":
    main()
