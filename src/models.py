from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


"""

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
    language: str = Field(..., default='unknown', description='Detected programming language.')
    change_type: str = Field(..., description='modified, added, deleted, renamed')
    hunks: list[DiffHunk] = Field(default_factory=list, description="List of diff hunks in this file.")
    additions: int = Field(default=0, description="Number of lines added in this file.")
    deletions: int = Field(default=0, description="Number of lines deleted in this file.")

class PRContext(BaseModel):
    # overall context of the PR, including metadata and file diffs.
    repo_name: str = Field(..., description='Repository name in the format "owner/repo".')
    pr_number: int = Field(..., description='Pull request number.')
    pr_title: str = Field(..., description='Title of the pull request.')
    pr_description: str = Field(default='')
    base_branch: str = Field(default='')
    head_branch: str = Field(default='')
    author: str = Field(default='')
    changed_files: list[FileDiff] = Field(default_factory=list, description="List of files changed in this PR.")
    total_additions: int = Field(default=0)
    total_deletions: int = Field(default=0)

"""
Review Output models
"""