"""GitHub API client for repository management and collaboration."""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import base64
import os

from github import Github, GithubException
from github.Repository import Repository
from github.ContentFile import ContentFile

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for interacting with GitHub API for research collaboration."""
    
    def __init__(
        self,
        token: str,
        username: str,
        repo_name: str,
        create_if_not_exists: bool = True
    ):
        """Initialize GitHub client.
        
        Args:
            token: GitHub personal access token
            username: GitHub username
            repo_name: Repository name for research data
            create_if_not_exists: Create repository if it doesn't exist
        """
        self.github = Github(token)
        self.username = username
        self.repo_name = repo_name
        self.repo = None
        
        try:
            self.repo = self.github.get_repo(f"{username}/{repo_name}")
            logger.info(f"Connected to existing repository: {username}/{repo_name}")
        except GithubException:
            if create_if_not_exists:
                self.repo = self._create_repository()
            else:
                raise Exception(f"Repository {username}/{repo_name} not found and create_if_not_exists is False")
    
    def _create_repository(self) -> Repository:
        """Create a new GitHub repository for research data.
        
        Returns:
            Created repository object
        """
        try:
            user = self.github.get_user()
            repo = user.create_repo(
                name=self.repo_name,
                description="Research data and notes managed by MCP Research Assistant",
                private=False,  # Make public by default, can be changed
                auto_init=True,
                gitignore_template="Python"
            )
            
            logger.info(f"Created new repository: {self.username}/{self.repo_name}")
            return repo
            
        except GithubException as e:
            logger.error(f"Failed to create repository: {e}")
            raise
    
    def upload_file(
        self,
        file_path: str,
        github_path: str,
        commit_message: Optional[str] = None,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Upload a file to GitHub repository.
        
        Args:
            file_path: Local file path
            github_path: Path in GitHub repository
            commit_message: Commit message (auto-generated if None)
            branch: Target branch
            
        Returns:
            Upload result information
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if commit_message is None:
            commit_message = f"Upload {os.path.basename(file_path)} via MCP Research Assistant"
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Check if file already exists
            try:
                existing_file = self.repo.get_contents(github_path, ref=branch)
                # File exists, update it
                result = self.repo.update_file(
                    path=github_path,
                    message=commit_message,
                    content=content,
                    sha=existing_file.sha,
                    branch=branch
                )
                operation = "updated"
            except GithubException:
                # File doesn't exist, create it
                result = self.repo.create_file(
                    path=github_path,
                    message=commit_message,
                    content=content,
                    branch=branch
                )
                operation = "created"
            
            logger.info(f"Successfully {operation} file: {github_path}")
            
            return {
                "operation": operation,
                "github_path": github_path,
                "commit_sha": result["commit"].sha,
                "commit_message": commit_message,
                "html_url": result["content"].html_url
            }
            
        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise
    
    def upload_directory(
        self,
        local_dir: str,
        github_dir: str = "",
        commit_message: Optional[str] = None,
        branch: str = "main",
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Upload an entire directory to GitHub.
        
        Args:
            local_dir: Local directory path
            github_dir: Target directory in GitHub repository
            commit_message: Commit message
            branch: Target branch
            exclude_patterns: File patterns to exclude
            
        Returns:
            Upload summary
        """
        if exclude_patterns is None:
            exclude_patterns = [".git", "__pycache__", "*.pyc", ".env", ".DS_Store"]
        
        if commit_message is None:
            commit_message = f"Upload directory {os.path.basename(local_dir)} via MCP Research Assistant"
        
        local_path = Path(local_dir)
        if not local_path.exists():
            raise FileNotFoundError(f"Directory not found: {local_dir}")
        
        uploaded_files = []
        failed_files = []
        
        for file_path in local_path.rglob("*"):
            if file_path.is_file():
                # Check exclusion patterns
                relative_path = file_path.relative_to(local_path)
                if self._should_exclude(str(relative_path), exclude_patterns):
                    continue
                
                # Construct GitHub path
                if github_dir:
                    github_path = f"{github_dir}/{relative_path}".replace("\\", "/")
                else:
                    github_path = str(relative_path).replace("\\", "/")
                
                try:
                    result = self.upload_file(
                        str(file_path),
                        github_path,
                        f"{commit_message} - {file_path.name}",
                        branch
                    )
                    uploaded_files.append(result)
                except Exception as e:
                    failed_files.append({"file": str(file_path), "error": str(e)})
        
        return {
            "uploaded_count": len(uploaded_files),
            "failed_count": len(failed_files),
            "uploaded_files": uploaded_files,
            "failed_files": failed_files
        }
    
    def create_research_summary(
        self,
        title: str,
        content: str,
        path: str = "research_summaries",
        commit_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a research summary file in the repository.
        
        Args:
            title: Summary title
            content: Summary content
            path: Directory path in repository
            commit_message: Commit message
            
        Returns:
            Creation result
        """
        # Sanitize title for filename
        filename = self._sanitize_filename(title) + ".md"
        github_path = f"{path}/{filename}"
        
        if commit_message is None:
            commit_message = f"Add research summary: {title}"
        
        # Create markdown content with metadata
        timestamp = datetime.now().isoformat()
        md_content = f"""---
title: {title}
created: {timestamp}
type: research_summary
---

# {title}

{content}

---
*Generated by MCP Research Assistant on {timestamp}*
"""
        
        try:
            # Check if file exists
            try:
                existing_file = self.repo.get_contents(github_path)
                # File exists, update it
                result = self.repo.update_file(
                    path=github_path,
                    message=commit_message,
                    content=md_content.encode(),
                    sha=existing_file.sha
                )
                operation = "updated"
            except GithubException:
                # File doesn't exist, create it
                result = self.repo.create_file(
                    path=github_path,
                    message=commit_message,
                    content=md_content.encode()
                )
                operation = "created"
            
            return {
                "operation": operation,
                "github_path": github_path,
                "html_url": result["content"].html_url,
                "commit_sha": result["commit"].sha
            }
            
        except Exception as e:
            logger.error(f"Failed to create research summary: {e}")
            raise
    
    def list_repository_contents(
        self,
        path: str = "",
        branch: str = "main"
    ) -> List[Dict[str, Any]]:
        """List contents of repository directory.
        
        Args:
            path: Directory path in repository
            branch: Branch to list from
            
        Returns:
            List of file/directory information
        """
        try:
            contents = self.repo.get_contents(path, ref=branch)
            
            if isinstance(contents, list):
                result = []
                for item in contents:
                    result.append({
                        "name": item.name,
                        "path": item.path,
                        "type": item.type,
                        "size": item.size,
                        "download_url": item.download_url,
                        "html_url": item.html_url
                    })
                return result
            else:
                # Single file
                return [{
                    "name": contents.name,
                    "path": contents.path,
                    "type": contents.type,
                    "size": contents.size,
                    "download_url": contents.download_url,
                    "html_url": contents.html_url
                }]
                
        except GithubException as e:
            logger.error(f"Failed to list repository contents: {e}")
            return []
    
    def download_file(
        self,
        github_path: str,
        local_path: str,
        branch: str = "main"
    ) -> bool:
        """Download a file from GitHub repository.
        
        Args:
            github_path: Path in GitHub repository
            local_path: Local file path to save to
            branch: Source branch
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_content = self.repo.get_contents(github_path, ref=branch)
            
            # Create local directory if needed
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Decode and save content
            content = base64.b64decode(file_content.content)
            with open(local_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Downloaded file: {github_path} -> {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file {github_path}: {e}")
            return False
    
    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create an issue in the repository.
        
        Args:
            title: Issue title
            body: Issue body/description
            labels: List of label names
            
        Returns:
            Issue information
        """
        try:
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=labels or []
            )
            
            return {
                "number": issue.number,
                "title": issue.title,
                "html_url": issue.html_url,
                "state": issue.state
            }
            
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            raise
    
    def sync_local_directory(
        self,
        local_dir: str,
        github_dir: str = "",
        direction: str = "up"
    ) -> Dict[str, Any]:
        """Synchronize local directory with GitHub repository.
        
        Args:
            local_dir: Local directory path
            github_dir: GitHub directory path
            direction: Sync direction ('up' for local->GitHub, 'down' for GitHub->local)
            
        Returns:
            Synchronization result
        """
        if direction == "up":
            return self.upload_directory(local_dir, github_dir)
        elif direction == "down":
            # Download from GitHub to local
            return self._download_directory(github_dir, local_dir)
        else:
            raise ValueError("Direction must be 'up' or 'down'")
    
    def _download_directory(
        self,
        github_dir: str,
        local_dir: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Download directory from GitHub to local.
        
        Args:
            github_dir: GitHub directory path
            local_dir: Local directory path
            branch: Source branch
            
        Returns:
            Download result
        """
        downloaded_files = []
        failed_files = []
        
        try:
            contents = self.repo.get_contents(github_dir, ref=branch)
            
            if not isinstance(contents, list):
                contents = [contents]
            
            for item in contents:
                if item.type == "file":
                    local_path = os.path.join(local_dir, item.name)
                    if self.download_file(item.path, local_path, branch):
                        downloaded_files.append(local_path)
                    else:
                        failed_files.append(item.path)
                elif item.type == "dir":
                    # Recursively download subdirectory
                    subdir_result = self._download_directory(
                        item.path,
                        os.path.join(local_dir, item.name),
                        branch
                    )
                    downloaded_files.extend(subdir_result["downloaded_files"])
                    failed_files.extend(subdir_result["failed_files"])
            
            return {
                "downloaded_count": len(downloaded_files),
                "failed_count": len(failed_files),
                "downloaded_files": downloaded_files,
                "failed_files": failed_files
            }
            
        except Exception as e:
            logger.error(f"Failed to download directory {github_dir}: {e}")
            return {
                "downloaded_count": 0,
                "failed_count": 1,
                "downloaded_files": [],
                "failed_files": [github_dir]
            }
    
    def get_repository_info(self) -> Dict[str, Any]:
        """Get repository information.
        
        Returns:
            Repository metadata
        """
        if not self.repo:
            return {"error": "No repository connected"}
        
        return {
            "name": self.repo.name,
            "full_name": self.repo.full_name,
            "description": self.repo.description,
            "html_url": self.repo.html_url,
            "clone_url": self.repo.clone_url,
            "default_branch": self.repo.default_branch,
            "private": self.repo.private,
            "created_at": self.repo.created_at.isoformat(),
            "updated_at": self.repo.updated_at.isoformat(),
            "size": self.repo.size,
            "language": self.repo.language,
            "forks_count": self.repo.forks_count,
            "stargazers_count": self.repo.stargazers_count
        }
    
    def _should_exclude(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file should be excluded based on patterns.
        
        Args:
            file_path: File path to check
            patterns: Exclusion patterns
            
        Returns:
            True if file should be excluded
        """
        import fnmatch
        
        for pattern in patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
            if fnmatch.fnmatch(os.path.basename(file_path), pattern):
                return True
        
        return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for GitHub.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove invalid characters for GitHub
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        
        # Limit length
        return filename[:100]
