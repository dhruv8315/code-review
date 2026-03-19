"""
Github Client for interacting with the GitHub API.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from github import Github, GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository

from models import PRContext, FileDiff, ReviewResult, ReviewIssue, ReviewEvent

from dotenv import load_dotenv
import os
load_dotenv()

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
            print(repo)
            pr = self._get_pr(repo,pr_number)
            print(pr)
            changed_files: list[FileDiff] = []
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
        
    
    def get_raw_diff(self, repo_name: str, pr_number: int) -> str:
        try:
            import httpx
            url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
            headers = {
                "Authorizations": f"Bearer {self._token}",
                "Accept": "application/vnd.github.v3.diff"
            }

            response = httpx.get(url,headers=headers,follow_redirects=True)
            response.raise_for_status()
            return response.text

        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            raise ValueError(f"Failed to fetch raw diff: {e}")
        
    """
    Commenting on PRs
    """
    def post_review(self,repo_name: str, pr_number: int, Result:ReviewResult) -> None:
        """
        Post structure PR review
        """
        repo = self._get_repo(repo_name)
        pr = self._get_pr(repo, pr_number)
        commit = list(pr.get_commits())[-1]

        inline_comments = []
        for issue in Result.issues:
            comment_body = self._format_inline_comment(issue)
            inline_comments.append({
                "path": issue.file_path,
                "line_number": issue.line_number,
                "side": "RIGHT",
                "body": comment_body
            })
        summary_body = self._format_summary_comment(Result)
        event = Result.review_event.value
        
        try:
            pr.create_review(
                commit=commit,
                body=summary_body,
                event=event,
                comments=inline_comments
            )
            logger.info(
                "Posted review to PR #%d: %s with %d inline comments",
                pr_number, event, len(inline_comments)
            )
        except GithubException as e:
            logger.error("Failed to post review: %s", e)
            raise

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
    
    """
    Formatting
    """
    severity_emoji: dict[str, str] = {
    "CRITICAL": "🔴",
    "HIGH": "🟠",
    "MEDIUM": "🟡",
    "LOW": "🔵",
    "INFO": "⚪️"
    }

    verdict_emoji: dict[str, str] = {
    "BLOCKED": "🔴 **BLOCKED** — Critical issues must be resolved before merge.",
    "WARNINGS": "🟡 **WARNINGS** — Review findings below, consider addressing before merge.",
    "APPROVED": "🟢 **APPROVED** — No significant issues found."
    }

    def _format_inline_comment(self, issue: ReviewIssue) -> str:
        emoji = self.severity_emoji.get(issue.severity.value, "⚪️")
        lines = [
            f"{emoji} **[{issue.severity.value}] {issue.category.value}** - {issue.title}",
            "",
            issue.description,
            f"**Suggestion:** {issue.suggestion}"
        ]
        if issue.code_block:
            lines += [
                "",
                "```",
                issue.code_block,
                "```"
            ]
        return "\n".join(lines)
    
    def _format_summary_comment(self, result: ReviewResult) -> str:
        s = result.summary
        verdict_line = self.verdict_emoji.get(s.verdict, "")

        lines = [
            f"# AI Code Review Summary for PR #{result.pr_number}",
            "",
            verdict_line,
            "",
           "| Severity | Count |",
            "|----------|-------|",
            f"| 🔴 Critical | {s.critical_count} |",
            f"| 🟠 High     | {s.high_count} |",
            f"| 🟡 Medium   | {s.medium_count} |",
            f"| 🔵 Low      | {s.low_count} |",
            f"| ⚪ Info     | {s.info_count} |",
            f"| **Total**   | **{s.total_issues}** |",
            "",
            f"Files reviewed: **{s.files_reviewed}**"
        ]

        if s.overall_comment:
            lines += [
                "",
                "## Overall Comments",
                "",
                s.overall_comment
            ]
        return "\n".join(lines)



github_client = GitHubClient(token=os.getenv("GITHUB_TOKEN"))
print(github_client.get_pr_context("dhruv8315/empty-repo", 3))
