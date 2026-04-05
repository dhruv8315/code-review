"""
diff_parser.py

Diff parser 

This module will parse unified diff format into structured DiffHunk /
LineChange objects and enrich them with AST context.

"""

from __future__ import annotations

import re
import logging
from models import DiffHunk, FileDiff, LineChange, PRContext

logger = logging.getLogger(__name__)

# Regex to match unified diff hunk headers: @@ -10,5 +12,7 @@ optional_func_name
HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)")

class DiffParser:
    """
    Parses raw unified diff patches into structured objects.
    """

    def __init__(self,context_lines: int = 10):
        self.context_lines = context_lines
    
    def parse_pr_context(self, pr_context: PRContext) -> None:
        """
        Parses the raw patches of every file in PRContext
        """
        print(pr_context.changed_files) #temporary debug statement to check if changed_files is populated
        for file_diff in pr_context.changed_files:
            for hunk in file_diff.hunks:
                raw_patch = getattr(hunk, 'header', None)
                print(raw_patch)#temporary debug statement to check if _raw_patch is populated
                if raw_patch:
                    print(hunk.lines) #temporary debug statement to check if hunk.lines is populated
                    file_diff.hunks = self._parse_patch(raw_patch, hunk.lines)
                    logger.debug("Parsed %d hunks for %s", len(file_diff.hunks), file_diff.file_path)
                    
    """
    Helper Function
    """
    def _parse_patch(self, patch: str, lines: list[LineChange]) -> list[DiffHunk]:
        """
        Parse a single file's unified diff patch into a list of DiffHunk objects.
        """
        hunks: list[DiffHunk] = []
        current_hunk: DiffHunk | None = None
        new_line_num = 0

        for raw_line in patch.splitlines():
            hunk_match = HUNK_HEADER_RE.match(raw_line)
            if hunk_match:
                old_start = int(hunk_match.group(1))
                old_count = int(hunk_match.group(2) or '1')
                new_start = int(hunk_match.group(3))
                new_count = int(hunk_match.group(4) or '1')

                current_hunk = DiffHunk(
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                    header=raw_line,
                    lines=[]
                )
                hunks.append(current_hunk)
                new_line_num = new_start
                continue
            if current_hunk is None:
                continue

            if raw_line.startswith('+') and not raw_line.startswith('+++'):
                current_hunk.lines.append(
                    LineChange(
                        line_number=new_line_num,
                        content=raw_line[1:],
                        type_of_change='added'
                        ))
                new_line_num += 1
            elif raw_line.startswith('-') and not raw_line.startswith('---'):
                current_hunk.lines.append(LineChange(
                    line_number=new_line_num,  # This is the line number in the new file where the change would be applied
                    content=raw_line[1:],
                    type_of_change='removed'
                ))
                # Note: We do not increment new_line_num for removed lines since they do not exist in the new file.
            else:
                content = raw_line[1:] if raw_line.startswith(' ') else raw_line
                current_hunk.lines.append(LineChange(
                    line_number=new_line_num,
                    content=content,
                    type_of_change='context'
                ))
                new_line_num += 1
        print(hunks)
        return hunks
    

print("DiffParser module loaded successfully.")
pr_context = PRContext(
    repo_name="example/repo",
    pr_number=123,
    pr_title="Example PR",
    pr_description="An example pull request for testing.",
    base_branch="main",
    head_branch="feature-branch",
    author="contributor",
    changed_files=[
        FileDiff(
            file_path="src/example.py",
            language="python",
            change_type="modified",
            hunks=[
                DiffHunk(
                    old_start=1,
                    old_count=3,
                    new_start=1,
                    new_count=3,
                    header="@@ -1,3 +1,3 @@",
                    lines=[
                        LineChange(line_number=1, content="def example():", type_of_change="context"),
                        LineChange(line_number=2, content="    print('Hello, world!')", type_of_change="removed"),
                        LineChange(line_number=2, content="    print('Hello, universe!')", type_of_change="added"),
                        LineChange(line_number=3, content="    return True", type_of_change="context")
                    ])
            ],
            additions=1,
            deletions=1
        )],
    total_additions=1,
    total_deletions=1
    )

parser = DiffParser()
print(parser.parse_pr_context(pr_context))