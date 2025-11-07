import httpx
import json
from typing import Dict, Any, List
from app.tools.base import ToolSpec

class GitHubIssuesTool(ToolSpec):
    
    def __init__(self):
        super().__init__()
        self.name = "github_issues"
        self.description = "Fetch GitHub issues from a repository"
    
    def _run(self, repo: str, state: str = "open", limit: int = 5) -> str:
        """Fetch GitHub issues for a repository"""
        try:
            # Validate repo format (owner/repo)
            if "/" not in repo:
                return f"Invalid repository format. Use 'owner/repo' format."
            
            url = f"https://api.github.com/repos/{repo}/issues"
            params = {
                "state": state,
                "per_page": limit,
                "sort": "updated"
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                issues = response.json()
                
                if not issues:
                    return f"No {state} issues found for repository: {repo}"
                
                result = f"Found {len(issues)} {state} issues for {repo}:\n\n"
                
                for i, issue in enumerate(issues, 1):
                    result += f"{i}. #{issue['number']}: {issue['title']}\n"
                    result += f"   State: {issue['state']} | Comments: {issue['comments']}\n"
                    result += f"   Created: {issue['created_at'][:10]}\n"
                    result += f"   URL: {issue['html_url']}\n"
                    
                    # Add labels if present
                    if issue.get('labels'):
                        labels = [label['name'] for label in issue['labels']]
                        result += f"   Labels: {', '.join(labels)}\n"
                    
                    result += "\n"
                
                return result
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Repository '{repo}' not found or is private."
            return f"HTTP error fetching issues: {e.response.status_code}"
        except Exception as e:
            return f"Error fetching GitHub issues: {str(e)}"