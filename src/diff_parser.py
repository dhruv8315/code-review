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

    Phase 1: Basic line-counting and hunk detection.
    Phase 2: Will add tree-sitter AST context enrichment.

    Usage:
        parser = DiffParser(context_lines=10)
        parser.parse_pr_context(pr_context)   # mutates pr_context in-place
    """

    def __init__(self,context_lines: int = 10):
        self.context_lines = context_lines
    
    def parse_pr_context(self, pr_context: PRContext) -> None:
        
"""import re

class DiffParser:
    def __init__(self):
        pass

    def diff_parser(self, diff_text: list):
        
        #Parses the diff text and extracts file changes, including line numbers, change types (added or removed), and content
        files=[]
        current_file=None
        new_line_number=0

        #Iterating through each item in the diff_text(list)
        for item in diff_text:
            #Iterating through each key-value pair in the item(dictionary)
            for key, value in item.items():

                if key == 'filename':
                    if current_file:
                        files.append(current_file)
                    current_file = {
                        "File": value,
                        "changes": []
                    }
                
                else:
                    if key == 'patch' and value.startswith("@@"):
                        match = re.search(r"\+(\d+)", value)

                        if match:
                            new_line_number = int(match.group(1))
                        
                        for t in value.splitlines():
                            if not t.endswith('@@'):
                                if t.startswith("+"):
                                    current_file["changes"].append({
                                        "line_number": new_line_number,
                                        "change_type": "added",
                                        "content": t[1:]
                                    })
                                    new_line_number += 1
                                
                                elif t.startswith("-"):
                                    current_file["changes"].append({
                                        "line_number": new_line_number,
                                        "change_type": "removed",
                                        "content": t[1:]
                                    })
                    else:
                        if isinstance(value, str) and not value.startswith("\\"):
                            new_line_number += 1

        if current_file:
            files.append(current_file)
        
        return files
   """