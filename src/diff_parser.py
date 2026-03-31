"""
diff_parser.py

Diff parser 

This module will parse unified diff format into structured DiffHunk /
LineChange objects and enrich them with AST context.

"""

from __future__ import annotations

import re
import logging

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