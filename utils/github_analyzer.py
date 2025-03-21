import os
import re
import base64
import requests
from github import Github
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Tuple, Optional

class GitHubRepoAnalyzer:
    """Analyzes GitHub repositories for specific characteristics"""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize with optional GitHub token for API access"""
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github_client = Github(self.github_token) if self.github_token else None
        
    def extract_repo_info(self, repo_url: str) -> Dict[str, Any]:
        """Extract basic information about a GitHub repository"""
        # Parse the URL to get owner and repo name
        url_parts = repo_url.rstrip('/').split('/')
        if 'github.com' not in url_parts:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
            
        owner_idx = url_parts.index('github.com') + 1
        if owner_idx >= len(url_parts):
            raise ValueError(f"Invalid GitHub URL format: {repo_url}")
            
        owner = url_parts[owner_idx]
        repo_name = url_parts[owner_idx + 1] if owner_idx + 1 < len(url_parts) else None
        
        if not repo_name:
            raise ValueError(f"Could not parse repository name from URL: {repo_url}")
        
        return {
            "url": repo_url,
            "owner": owner,
            "name": repo_name,
            "files": self.get_repo_files(owner, repo_name),
            "readme": self.get_readme_content(owner, repo_name),
            "architecture_diagrams": self.find_architecture_diagrams(owner, repo_name)
        }
    
    def get_repo_files(self, owner: str, repo_name: str) -> List[Dict[str, str]]:
        """Get key files from the repository"""
        files = []
        
        if self.github_client:
            # Use GitHub API if token is available
            try:
                repo = self.github_client.get_repo(f"{owner}/{repo_name}")
                contents = repo.get_contents("")
                
                while contents:
                    file_content = contents.pop(0)
                    if file_content.type == "dir":
                        contents.extend(repo.get_contents(file_content.path))
                    else:
                        if self._is_relevant_file(file_content.name):
                            try:
                                decoded_content = base64.b64decode(file_content.content).decode('utf-8')
                                files.append({
                                    "name": file_content.name,
                                    "path": file_content.path,
                                    "content": decoded_content
                                })
                            except:
                                # Skip binary files or encoding issues
                                pass
            except Exception as e:
                print(f"Error accessing GitHub API: {str(e)}")
                # Fall back to web scraping if API fails
                return self._scrape_repo_files(owner, repo_name)
        else:
            # Fall back to web scraping if no token
            return self._scrape_repo_files(owner, repo_name)
        
        return files
    
    def _is_relevant_file(self, filename: str) -> bool:
        """Check if a file is relevant for analysis"""
        relevant_extensions = [
            '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml', 
            '.bicep', '.arm', '.tf', '.html', '.ipynb', '.sh'
        ]
        relevant_names = [
            'readme', 'dockerfile', 'license', 'requirements.txt',
            'package.json', 'config', 'setup', 'deploy'
        ]
        
        extension = os.path.splitext(filename.lower())[1]
        name_lower = filename.lower()
        
        return (extension in relevant_extensions or 
                any(relevant_name in name_lower for relevant_name in relevant_names))
    
    def _scrape_repo_files(self, owner: str, repo_name: str) -> List[Dict[str, str]]:
        """Scrape repository files from GitHub web interface"""
        # This is a simplified version - in practice, you'd need more robust scraping
        files = []
        base_url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/main/"
        
        # Try to get some common important files
        common_files = ["README.md", "DEPLOYMENT.md", "ARCHITECTURE.md", "deployment/README.md"]
        
        for file_path in common_files:
            try:
                response = requests.get(base_url + file_path)
                if response.status_code == 200:
                    files.append({
                        "name": os.path.basename(file_path),
                        "path": file_path,
                        "content": response.text
                    })
            except:
                continue
                
        return files
    
    def get_readme_content(self, owner: str, repo_name: str) -> str:
        """Get the README.md content from the repo"""
        try:
            if self.github_client:
                repo = self.github_client.get_repo(f"{owner}/{repo_name}")
                readme = repo.get_readme()
                return base64.b64decode(readme.content).decode('utf-8')
            else:
                response = requests.get(f"https://raw.githubusercontent.com/{owner}/{repo_name}/main/README.md")
                if response.status_code == 200:
                    return response.text
                
                # Try uppercase README.md if lowercase fails
                response = requests.get(f"https://raw.githubusercontent.com/{owner}/{repo_name}/main/README.MD")
                if response.status_code == 200:
                    return response.text
                    
                # Try master branch if main fails
                response = requests.get(f"https://raw.githubusercontent.com/{owner}/{repo_name}/master/README.md")
                if response.status_code == 200:
                    return response.text
        except Exception as e:
            print(f"Error getting README: {str(e)}")
        
        return ""
    
    def find_architecture_diagrams(self, owner: str, repo_name: str) -> List[str]:
        """Find architecture diagrams in the repository"""
        diagrams = []
        
        # Look for images in common locations
        image_patterns = [
            "architecture.png", "architecture.jpg", "architecture.svg",
            "diagram.png", "diagram.jpg", "diagram.svg",
            "overview.png", "overview.jpg", "overview.svg",
            "design.png", "design.jpg", "design.svg"
        ]
        
        common_folders = ["", "images/", "docs/", "assets/", "media/"]
        
        for folder in common_folders:
            for pattern in image_patterns:
                image_url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/main/{folder}{pattern}"
                try:
                    response = requests.head(image_url)
                    if response.status_code == 200:
                        diagrams.append(image_url)
                except:
                    continue
                    
                # Try master branch if main fails
                image_url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/master/{folder}{pattern}"
                try:
                    response = requests.head(image_url)
                    if response.status_code == 200:
                        diagrams.append(image_url)
                except:
                    continue
        
        return diagrams
