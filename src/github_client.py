"""
Github Client for interacting with the GitHub API.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from github import Github, GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository

from .models import PRContext, FileDiff, ReviewResult, ReviewEvent

logger = logging.getLogger(__name__)

#Language detection using laguage extension
Extension_to_language: dict[str, str] = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.jsx': 'javascript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.go': 'go',
    '.rb': 'ruby',
    '.php': 'php',
    '.cpp': 'cpp',
    '.c': 'c',
    '.cs': 'csharp',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.rs': 'rust',
    'yml': 'yaml',
    '.yaml': 'yaml',
    'json': 'json',
    '.sql': 'sql',
    '.html': 'html',
    '.css': 'css',
    '.tf': 'terraform',
    '.sh': 'shell',
}

def detect_language(file_path: str) -> str:
    for ex , lang in Extension_to_language.items():
        if file_path.endswith(ex):
            return lang
    return 'unknown'


class GitHubClient:
    def __init__(self,token: str):
        self._gh = Github(token)
        self._token = token
    # Fetching PR data
    def get_pr_context(self, repo_name: str, pr_number: int) -> PRContext:
        
        try:
            repo = self._get_repo(repo_name)
            pr = self._get_pr(repo, pr_number)
            changed_files = list[FileDiff] = []
            total_additions = 0
            total_deletions = 0

            for file in pr.get_files():

                if file.changes > 2000:
                    """
                    Perform chunking for large files
                    """
                if file.patch is None:
                    logger.warning(f"Skipping {file.filename} - No patch data for file in PR #{pr_number}")
                    continue

                file_diff = FileDiff(
                    file_path=file.filename,
                    language=detect_language(file.filename),
                    change_type=file.status,
                    hunks=[],
                    additions=file.additions,
                    deletions=file.deletions
                )
                """
                add the patch of data here
                """

                changed_files.append(file_diff)
                total_additions += file.additions
                total_deletions += file.deletions
            
            return PRContext(
                repo_name=repo,
                pr_number=pr,
                pr_title=pr.title,
                pr_description=pr.body,
                base_branch=pr.base.ref,
                head_branch=pr.head.label,
                author=pr.user.login,
                changed_files=changed_files,
                total_additions=total_additions,
                total_deletions=total_deletions
            )
        
        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            raise ValueError(f"Failed to fetch PR context: {e}")
        
    
    
    """
    Helper Functions
    """
    def _get_repo(self, repo_name: str) -> Repository:
        try:
            return self._gh.get_repo(repo_name)
        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            raise ValueError(f"Failed to fetch repository: {e}")
    
    def _get_pr(self, repo_name: Repository, pr_number: int) -> PullRequest:
        try:
            return repo_name.get_pull(pr_number)
        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            raise ValueError(f"Failed to fetch pull request: {e}")