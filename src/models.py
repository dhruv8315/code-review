from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


"""
Enums
"""
class Severity(str,Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"
    INFO     = "INFO"

class IssueCategory(str, Enum):
    """Category of the review issue."""
    SECURITY        = "SECURITY"
    PERFORMANCE     = "PERFORMANCE"
    ERROR_HANDLING  = "ERROR_HANDLING"
    TEST_COVERAGE   = "TEST_COVERAGE"
    LOGIC_BUG       = "LOGIC_BUG"
    CODE_QUALITY    = "CODE_QUALITY"

class ReviewEvent(str, Enum):
    """GitHub PR review event type."""
    APPROVE          = "APPROVE"
    REQUEST_CHANGES  = "REQUEST_CHANGES"
    COMMENT          = "COMMENT"

"""
Diff classes to represent content

"""
class LineChange(BaseModel):
    # Represents a single line change in a diff hunk.
    line_number: int = Field(..., description="Line number in the file.")
    old_line_number: Optional[int] = Field(None, description="Original line number before changes.")
    content: str = Field(..., description="Raw content of the line without (+/-).")
    type_of_change: str = Field(...,description="Type of change: 'added', 'removed', or 'context'.")

class DiffHunk(BaseModel):
    # Block representing a contiguous set of line changes in a file.
    old_start: int = Field(..., description="Starting line of OLD file.")
    old_count: int = Field(..., description="Number of lines in OLD file hunk.")
    new_start: int = Field(..., description="Starting line of NEW file.")
    new_count: int = Field(..., description="Number of lines in NEW file hunk.")
    header: str = Field(..., description="Raw hunk header (e.g., '@@ -1,5 +1,6 @@').")
    lines: list[LineChange] = Field(default_factory=list, description="List of line changes in this hunk.")

class FileDiff(BaseModel):
    # All diff information for a single file in PR.
    old_file_path: Optional[str] = Field(None, description='Path relative to repository root before changes. None if new file.')
    file_path: str = Field(...,description='Path relative to repository root.')
    language: str = Field(default='unknown', description='Detected programming language.')
    change_type: str = Field(..., description='modified, added, deleted, renamed')
    hunks: list[DiffHunk] = Field(default_factory=list, description="List of diff hunks in this file.")
    additions: int = Field(default=0, description="Number of lines added in this file.")
    deletions: int = Field(default=0, description="Number of lines deleted in this file.")

class PRContext(BaseModel):
    # overall context of the PR, including metadata and file diffs.
    repo_name: str = Field(..., description='Repository name in the format "owner/repo".')
    pr_number: int = Field(..., description='Pull request number.')
    pr_title: str = Field(..., description='Title of the pull request.')
    pr_description: Optional[str] = Field(default='')
    base_branch: str = Field(default='')
    head_branch: str = Field(default='')
    author: str = Field(default='')
    changed_files: list[FileDiff] = Field(default_factory=list, description="List of files changed in this PR.")
    total_additions: int = Field(default=0)
    total_deletions: int = Field(default=0)

"""
Review Output models
"""
class ReviewIssue(BaseModel):
    file_path: str = Field(..., description="Path of the file with the issue.")
    line_number: int = Field(..., description="Line nunber in new file")
    severity: Severity = Field(..., description="Severity level of the issue.")
    category: IssueCategory = Field(..., description="Category of the issue.")
    title: str = Field(..., description="Short title summarizing the issue.")
    description: str = Field(..., description="Detailed description of the issue.")
    suggestion: str = Field(None, description="Suggested code change or improvement.")
    code_block: Optional[str] = Field(None, description="Optional code block illustrating the issue or suggestion.")

class ReviewSummary(BaseModel):
    """Aggregate statistics for a full PR review."""
    total_issues: int         = Field(default=0)
    critical_count: int       = Field(default=0)
    high_count: int           = Field(default=0)
    medium_count: int         = Field(default=0)
    low_count: int            = Field(default=0)
    info_count: int           = Field(default=0)
    files_reviewed: int       = Field(default=0)
    verdict: str              = Field(default="APPROVED")   # BLOCKED / WARNINGS / APPROVED
    overall_comment: str      = Field(default="")

class ReviewResult(BaseModel):
    """Complete review result for a PR."""
    repo_name : str = Field(..., description="Repository name in the format 'owner/repo'.")
    pr_number : int = Field(..., description="Pull request number.")
    issues: list[ReviewIssue] = Field(default_factory=list, description="List of identified issues in the PR.")
    summary: ReviewSummary = Field(default_factory=ReviewSummary, description="Aggregate summary of the review findings.")
    review_event: ReviewEvent = Field(..., description="GitHub review event type (APPROVE, REQUEST_CHANGES, COMMENT).")
    raw_ai_response: Optional[str] = Field(None, description="Raw JSON response from the AI model for debugging and transparency.")

    def compute_summary(self):

        counts = {s:0 for s in Severity}
        for issue in self.issues:
            counts[issue.severity] += 1
            
        self.summary.total_issues = len(self.issues)
        self.summary.critical_count = counts[Severity.CRITICAL]
        self.summary.high_count = counts[Severity.HIGH]
        self.summary.medium_count = counts[Severity.MEDIUM]
        self.summary.low_count = counts[Severity.LOW]
        self.summary.info_count = counts[Severity.INFO]

        if self.summary.critical_count > 0:
            self.summary.verdict = "BLOCKED"
            self.review_event = ReviewEvent.REQUEST_CHANGES
        elif self.summary.high_count > 0:
            self.summary.verdict = "WARNINGS"
            self.review_event = ReviewEvent.COMMENT
        else:
            self.summary.verdict = "APPROVED"
            self.review_event = ReviewEvent.APPROVE

"""
Config model
"""
class ReviewConfig(BaseModel):
    github_token: str = Field(..., description="GitHub API token with repo access.")
    anthropic_api_key: str = Field(..., description="Anthropic API key for AI model access.")
    model: str = Field(default="claude-sonnet-4")
    max_tokens: int = Field(default=4096)
    fail_on_severity: Severity = Field(default=Severity.HIGH, description="Exit with non-zero code if issues at this severity or above are found")
    post_comments: bool = Field(default=True, description="Post inline comments to GitHub PR")
    context_lines: int = Field(default=10, description="Number of lines of context to include around each issue in the review comments.")
    verbose: bool = Field(default=False)