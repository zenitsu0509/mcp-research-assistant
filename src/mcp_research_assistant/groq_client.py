"""Groq API client for AI-powered text summarization."""

import logging
from typing import Dict, List, Optional, Any
import json
from groq import Groq

logger = logging.getLogger(__name__)


class GroqClient:
    """Client for interacting with Groq API for summarization."""
    
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        """Initialize Groq client.
        
        Args:
            api_key: Groq API key
            model: Model to use for completion
        """
        self.client = Groq(api_key=api_key)
        self.model = model
    
    def summarize_paper(
        self,
        paper_content: str,
        style: str = "academic",
        max_tokens: int = 2048,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """Summarize a research paper using Groq.
        
        Args:
            paper_content: Full paper content or abstract
            style: Summary style (academic, casual, technical, brief)
            max_tokens: Maximum tokens in response
            temperature: Creativity level (0.0-1.0)
            
        Returns:
            Dictionary containing summary and metadata
        """
        try:
            prompt = self._build_summary_prompt(paper_content, style)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert research assistant specializing in academic paper analysis and summarization."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON if it's structured
            try:
                summary_data = json.loads(content)
                if isinstance(summary_data, dict):
                    return summary_data
            except json.JSONDecodeError:
                pass
            
            # If not JSON, return as plain summary
            return {
                "summary": content,
                "style": style,
                "model": self.model,
                "tokens_used": response.usage.total_tokens if response.usage else None
            }
            
        except Exception as e:
            logger.error(f"Groq summarization failed: {e}")
            raise
    
    def generate_key_points(
        self,
        paper_content: str,
        num_points: int = 5,
        max_tokens: int = 1024
    ) -> List[str]:
        """Extract key points from a research paper.
        
        Args:
            paper_content: Paper content to analyze
            num_points: Number of key points to extract
            max_tokens: Maximum tokens in response
            
        Returns:
            List of key points
        """
        prompt = f"""
        Extract the {num_points} most important key points from this research paper.
        Return them as a JSON array of strings, with each point being concise but informative.
        
        Paper content:
        {paper_content[:8000]}  # Limit content to avoid token limits
        
        Format your response as:
        ["Key point 1", "Key point 2", ...]
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at extracting key insights from research papers."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                key_points = json.loads(content)
                if isinstance(key_points, list):
                    return key_points
            except json.JSONDecodeError:
                pass
            
            # Fallback: split by lines and clean up
            lines = content.strip().split('\n')
            key_points = []
            for line in lines:
                line = line.strip()
                # Remove bullet points and numbering
                line = line.lstrip('-*123456789. ')
                if line:
                    key_points.append(line)
            
            return key_points[:num_points]
            
        except Exception as e:
            logger.error(f"Key points extraction failed: {e}")
            return []
    
    def create_structured_summary(
        self,
        paper_content: str,
        include_sections: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a structured summary with specific sections.
        
        Args:
            paper_content: Paper content to summarize
            include_sections: Sections to include in summary
            
        Returns:
            Structured summary dictionary
        """
        if include_sections is None:
            include_sections = [
                "main_contribution",
                "methodology",
                "key_findings", 
                "limitations",
                "future_work"
            ]
        
        sections_str = ", ".join(include_sections)
        
        prompt = f"""
        Create a structured summary of this research paper with the following sections:
        {sections_str}
        
        Return the summary as a JSON object with these exact keys. Make each section concise but informative.
        
        Paper content:
        {paper_content[:10000]}  # Limit content
        
        Format your response as valid JSON:
        {{
            "main_contribution": "...",
            "methodology": "...",
            "key_findings": "...",
            "limitations": "...",
            "future_work": "..."
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert research analyst who creates structured academic summaries."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2048,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            try:
                summary = json.loads(content)
                return summary
            except json.JSONDecodeError:
                # Fallback: create basic structure
                return {
                    "summary": content,
                    "error": "Could not parse structured response"
                }
                
        except Exception as e:
            logger.error(f"Structured summary failed: {e}")
            return {"error": str(e)}
    
    def _build_summary_prompt(self, paper_content: str, style: str) -> str:
        """Build the prompt for paper summarization.
        
        Args:
            paper_content: Content to summarize
            style: Summary style
            
        Returns:
            Formatted prompt string
        """
        style_instructions = {
            "academic": "Write in formal academic language suitable for researchers and scholars.",
            "casual": "Write in accessible language that a general audience can understand.",
            "technical": "Focus on technical details, methods, and implementation specifics.",
            "brief": "Provide a concise overview highlighting only the most essential points.",
            "detailed": "Provide a comprehensive analysis covering all major aspects of the paper."
        }
        
        instruction = style_instructions.get(
            style, 
            "Write a clear and informative summary suitable for researchers."
        )
        
        # Limit content to avoid token limits
        content_preview = paper_content[:12000]
        
        return f"""
        Summarize this research paper in {style} style. {instruction}

        Include the following in your summary:
        1. Main research question or problem addressed
        2. Key methodology or approach used
        3. Major findings and results
        4. Significance and implications
        5. Any notable limitations

        Paper content:
        {content_preview}

        Provide a well-structured summary that captures the essence of this research.
        """
    
    def generate_citation(
        self,
        paper_metadata: Dict[str, Any],
        style: str = "apa"
    ) -> str:
        """Generate a formatted citation for a paper.
        
        Args:
            paper_metadata: Paper metadata dictionary
            style: Citation style (apa, mla, chicago, ieee)
            
        Returns:
            Formatted citation string
        """
        prompt = f"""
        Generate a {style.upper()} style citation for this research paper.
        
        Paper metadata:
        {json.dumps(paper_metadata, indent=2)}
        
        Return only the properly formatted citation.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert in academic citation formatting, specifically {style.upper()} style."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=512,
                temperature=0.0
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Citation generation failed: {e}")
            return f"Error generating citation: {e}"
    
    def compare_papers(
        self,
        papers_content: List[str],
        comparison_aspects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare multiple research papers.
        
        Args:
            papers_content: List of paper contents to compare
            comparison_aspects: Specific aspects to compare
            
        Returns:
            Comparison analysis
        """
        if comparison_aspects is None:
            comparison_aspects = [
                "methodology",
                "findings",
                "strengths",
                "limitations",
                "novelty"
            ]
        
        # Limit content for each paper
        limited_papers = [content[:5000] for content in papers_content]
        
        aspects_str = ", ".join(comparison_aspects)
        papers_str = "\n\n---PAPER SEPARATOR---\n\n".join(limited_papers)
        
        prompt = f"""
        Compare these research papers focusing on: {aspects_str}
        
        Provide a structured comparison that highlights similarities, differences, and relative strengths.
        
        Papers to compare:
        {papers_str}
        
        Format your response as a JSON object with comparison insights.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert research analyst specializing in comparative analysis of academic papers."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3072,
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"comparison": content}
                
        except Exception as e:
            logger.error(f"Paper comparison failed: {e}")
            return {"error": str(e)}
