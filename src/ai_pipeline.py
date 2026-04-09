"""
AI Review Pipeline.

Sends the enriched PR diff to the Anthropic Claude API and parses the
structured JSON response into ReviewResult objects.

"""

from __future__ import annotations

import json
import logging
from typing import Any
import openai
import anthropic
from dotenv import load_dotenv
import os
load_dotenv()
from models import (
    PRContext, FileDiff, DiffHunk,
    ReviewResult, ReviewIssue, ReviewSummary,
    Severity, IssueCategory, ReviewConfig, LineChange
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a senior software engineer performing a thorough code review.
Analyse the provided pull request diff and identify concrete, actionable issues.

Review for these categories in priority order:
1. SECURITY       — SQL injection, XSS, hardcoded secrets, insecure deserialization,
                    path traversal, missing auth/authz checks, use of eval()
2. LOGIC_BUG      — null dereference, off-by-one errors, incorrect boolean logic,
                    race conditions, unintended mutation, wrong algorithm
3. PERFORMANCE    — N+1 queries, O(n²) or worse loops in hot paths, unnecessary
                    allocations, synchronous I/O in async code, missing indexes
4. ERROR_HANDLING — bare except clauses, swallowed exceptions, missing finally
                    blocks, no timeout on network calls, ignored return values
5. TEST_COVERAGE  — new functions with no tests, changed logic with no test update,
                    missing edge-case coverage, no negative tests
6. CODE_QUALITY   — excessive complexity, misleading names, violation of SOLID,
                    duplication, overly long functions

RULES:
- Only report issues in CHANGED lines (lines marked + in the diff).
  You may reference unchanged context lines in your description.
- Always include the EXACT new-file line number.
- Severity must be one of: CRITICAL, HIGH, MEDIUM, LOW, INFO.
  CRITICAL = data breach / data loss / crashes in prod.
  HIGH     = wrong behavior under normal conditions.
  MEDIUM   = wrong behavior under edge conditions.
  LOW      = code quality / maintainability.
  INFO     = suggestions / minor style.
- Provide a concrete fix suggestion. Show corrected code when it helps.
- Do NOT report issues about lines that were NOT changed in this PR.
- Return ONLY the JSON object described in the user prompt. No prose, no markdown.
"""


def build_user_prompt(pr_context: PRContext) -> str:
    """Build the user message from a PRContext."""
    lines: list[str] = [
        f"## Pull Request: {pr_context.pr_title}",
        f"Repository: {pr_context.repo_name}",
        f"PR #{pr_context.pr_number} by @{pr_context.author}",
        f"Branch: {pr_context.head_branch} → {pr_context.base_branch}",
        "",
    ]
    if pr_context.pr_description:
        lines += [
            "### PR Description",
            pr_context.pr_description.strip(),
            "",
        ]

    lines += [
        "### Changed Files",
        f"Total: +{pr_context.total_additions} / -{pr_context.total_deletions}",
        "",
    ]

    for file_diff in pr_context.changed_files:
        lines += _format_file_diff(file_diff)

    lines += [
        "",
        "---",
        "Return ONLY a JSON object with this exact schema (no markdown wrapper):",
        "",
        json.dumps({
            "issues": [
                {
                    "file_path":    "string — relative path from repo root",
                    "line_number":  "integer — line number in the NEW file",
                    "end_line_number": "integer or null — end line for multi-line issues",
                    "category":     "SECURITY | LOGIC_BUG | PERFORMANCE | ERROR_HANDLING | TEST_COVERAGE | CODE_QUALITY",
                    "severity":     "CRITICAL | HIGH | MEDIUM | LOW | INFO",
                    "title":        "string — short one-line summary",
                    "description":  "string — detailed explanation of the problem",
                    "suggestion":   "string — concrete fix, include corrected code if helpful",
                    "code_snippet": "string or null — the problematic code fragment",
                }
            ],
            "overall_comment": "string — 2-3 sentence high-level assessment of the PR",
        }, indent=2),
    ]
    return "\n".join(lines)


def _format_file_diff(file_diff: FileDiff) -> list[str]:
    """Render a single FileDiff as a human-readable diff block."""
    lines = [
        f"#### {file_diff.file_path}  [{file_diff.language}]  {file_diff.change_type}",
        f"Changes: +{file_diff.additions} / -{file_diff.deletions}",
        "```diff",
    ]
    for hunk in file_diff.hunks:
        lines.append(hunk.header)
        for lc in hunk.lines:
            prefix = {"added": "+", "removed": "-", "context": " "}[lc.type_of_change]
            # Annotate added lines with their line number so the model can reference them
            annotation = f"  // line {lc.line_number}" if lc.type_of_change == "added" else ""
            lines.append(f"{prefix}{lc.content}{annotation}")
    lines += ["```", ""]
    return lines


# ---------------------------------------------------------------------------
# Pipeline class
# ---------------------------------------------------------------------------

class AIPipeline:
    """
    Sends PR context to Claude and parses structured review output.

    Usage:
        pipeline = AIPipeline(config=config)
        result = pipeline.review(pr_context)
    """

    def __init__(self, config: ReviewConfig) -> None:
        self._config = config
        self._client = anthropic.Anthropic(
            api_key=config.anthropic_api_key,
            max_retries=3,
        )

    def review(self, pr_context: PRContext) -> ReviewResult:
        """
        Run the full AI review pipeline.

        Returns a ReviewResult with issues and summary populated.
        """
        user_prompt = build_user_prompt(pr_context)
        logger.debug("Sending prompt (%d chars) to %s", len(user_prompt), self._config.model)

        raw_response = self._call_api(user_prompt)
        logger.debug("Received response (%d chars)", len(raw_response))

        issues = self._parse_issues(raw_response, pr_context)
        overall_comment = self._extract_overall_comment(raw_response)

        result = ReviewResult(
            pr_number=pr_context.pr_number,
            repo_name=pr_context.repo_name,
            issues=issues,
            raw_ai_response=raw_response if self._config.verbose else None,
        )
        result.summary.files_reviewed = len(pr_context.changed_files)
        result.summary.overall_comment = overall_comment
        result.compute_summary()

        return result

    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------

    def _call_api(self, user_prompt: str) -> str:
        """Call the Anthropic messages API and return the text content."""
        message = self._client.messages.create(
            model=self._config.model,
            max_tokens=self._config.max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        # Extract the text from the response content blocks
        text_blocks = [block.text for block in message.content if hasattr(block, "text")]
        return "\n".join(text_blocks)

    def _parse_issues(self, raw: str, pr_context: PRContext) -> list[ReviewIssue]:
        """
        Parse the raw JSON string from the AI into a list of ReviewIssue objects.

        Handles:
        - Markdown code fences (```json ... ```)
        - Partial JSON (trims to the last complete object)
        - Validation via Pydantic
        """
        cleaned = self._strip_fences(raw)
        try:
            data: dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.warning("JSON parse error: %s — attempting recovery", exc)
            data = self._recover_json(cleaned)

        raw_issues: list[dict[str, Any]] = data.get("issues", [])
        issues: list[ReviewIssue] = []

        # Build a quick lookup: file_path → set of valid new-file line numbers
        valid_lines: dict[str, set[int]] = {}
        for fd in pr_context.changed_files:
            valid_lines[fd.file_path] = {
                lc.line_number
                for hunk in fd.hunks
                for lc in hunk.lines
                if lc.type_of_change == "added"
            }

        for raw_issue in raw_issues:
            try:
                issue = ReviewIssue(**raw_issue)
            except Exception as exc:
                logger.warning("Skipping malformed issue: %s — %s", raw_issue, exc)
                continue

            # Sanity-check: only keep issues on lines that actually changed
            allowed = valid_lines.get(issue.file_path, set())
            if allowed and issue.line_number not in allowed:
                logger.debug(
                    "Discarding issue at %s:%d — not an added line",
                    issue.file_path, issue.line_number
                )
                continue

            issues.append(issue)

        return issues

    def _extract_overall_comment(self, raw: str) -> str:
        cleaned = self._strip_fences(raw)
        try:
            data = json.loads(cleaned)
            return data.get("overall_comment", "")
        except Exception:
            return ""

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Remove ```json ... ``` fences if present."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            # Remove first and last fence lines
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            return "\n".join(lines).strip()
        return text

    @staticmethod
    def _recover_json(text: str) -> dict[str, Any]:
        """Last-resort: find the outermost {...} block and try to parse it."""
        start = text.find("{")
        end   = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        logger.error("Could not recover JSON from AI response")
        return {"issues": [], "overall_comment": ""}

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

config = ReviewConfig()
ai = AIPipeline(config)
print(ai.review(pr_context))