"""
Terminal reporter.
"""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.text import Text
from rich.rule import Rule

from .models import ReviewIssue, ReviewResult, Severity

severity_style: dict[str, str] = {
    "CRITICAL": "bold red",
    "HIGH": "bold orange",
    "MEDIUM": "bold yellow",
    "LOW": "bold cyan",
    "INFO": "dim white"
}

severity_emoji: dict[str, str] = {
    "CRITICAL": "🔴",
    "HIGH": "🟠",
    "MEDIUM": "🟡",
    "LOW": "🔵",
    "INFO": "⚪️"
}

verdict_style: dict[str, str] = {
    "BLOCKED": "bold red",
    "WARNINGS": "bold yellow",
    "APPROVED": "bold green"
}

verdict_emoji: dict[str, str] = {
    "BLOCKED": "🔴",
    "WARNINGS": "🟡",
    "APPROVED": "🟢"
}


class Reporter:
    """
    
    """
    def __init__(self,verdict: bool = False) -> None:
        self.console = Console()
        self.verbose = verdict