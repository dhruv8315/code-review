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

from models import ReviewIssue, ReviewResult, Severity, ReviewSummary

severity_style: dict[str, str] = {
    "CRITICAL": "bold red",
    "HIGH": "bold orange1",
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
    Renders a ReviewResult to the terminal using rich.
    """
    def __init__(self,verdict: bool = False) -> None:
        self.console = Console()
        self.verbose = verdict
    
    def print_result(self,result:ReviewResult):
        self._print_header(result)
        self._print_summary_table(result)

        if not result.issues:
            self.console.print("\n[bold green]✅  No issues found![/bold green]\n")
            return
        
        # Group issues by file for a cleaner layout
        by_file: dict[str, list[ReviewIssue]] = {}
        for issue in result.issues:
            by_file.setdefault(issue.file_path, []).append(issue)
    
        for file_path, issues in by_file.items():
            self._print_file_issues(file_path, issues)
    
        self._print_verdict(result)

    def print_error(self, message: str) -> None:
        self.console.print(f"[bold red]Error:[/bold red] {message}")
    
    def print_info(self, message: str) -> None:
        self.console.print(f"[dim]ℹ  {message}[/dim]")
    
    def print_success(self, message: str) -> None:
        self.console.print(f"[bold green]✓[/bold green]  {message}")
    
    def exit_code(self, result: ReviewResult, fails_on:Severity) -> int:
        """
        Return 0 if no issues at or above fail_on severity, else 1.
        """
        severity_order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]
        threshold_index = severity_order.index(fails_on)
        
        for issue in result.issues:
            if severity_order.index(issue.severity) <= threshold_index:
                return 1
        return 0 
    
    # ------------------------------------------------------------------
    # Private rendering helpers
    # ------------------------------------------------------------------
 
    def _print_header(self, result: ReviewResult) -> None:
        self.console.print()
        self.console.print(Rule(
            f"[bold blue]🤖  AI Code Review — {result.repo_name} PR #{result.pr_number}[/bold blue]",
            style="blue"
        ))
        self.console.print()
 
    def _print_summary_table(self, result: ReviewResult) -> None:
        s = result.summary
        table = Table(
            title="Review Summary",
            box=box.ROUNDED,
            show_header=True,
            border_style="blue",
            header_style="bold blue"
        )
        
        table.add_column("Severity", style="bold", width=12)
        table.add_column("Count", justify="center", width=8)

        rows = [
            ("🔴 Critical", str(s.critical_count), "bold red"),
            ("🟠 High",     str(s.high_count),     "bold orange1"),
            ("🟡 Medium",   str(s.medium_count),   "bold yellow"),
            ("🔵 Low",      str(s.low_count),      "bold cyan"),
            ("⚪ Info",     str(s.info_count),     "dim"),
        ]

        for label, count, style in rows:
            table.add_row(label, Text(count, style=style if count != "0" else "dim"))

        table.add_section()
        table.add_row(
            "[bold]Total[/bold]",
            Text(str(s.total_issues), style="bold white"),
        )

        self.console.print(table)
        self.console.print(
            f"  Files reviewed: [bold]{s.files_reviewed}[/bold]  |  "
            f"Changes: [green]+{result.summary.total_issues}[/green]\n"
            if self.verbose else ""
        )

    def _print_file_issues(self, file_path: str, issues: list[ReviewIssue]) -> None:
        self.console.print(f"\n[bold white on blue]  📄 {file_path}  [/bold white on blue]")

        """
        In this lambda function search for i.severity on list of Severity and return the index number, and at the end return tuple with severity index and line number, this way we can sort first by severity and then by line number  
        """
        for issue in sorted(issues, key=lambda i: (list(Severity).index(i.severity), i.line_number)):
            severity_value = issue.severity.value
            emoji = severity_emoji[severity_value]
            style = severity_style[severity_value]
            category_value = issue.category.value

            #Issue title
            title_text = Text()
            title_text.append(f"\n {emoji} ", style=style)
            title_text.append(f"\n Line number: {issue.line_number} ", style="bold white")
            title_text.append(f" [{severity_value}] ", style=style)
            title_text.append(f" {category_value} ", style="bold magenta")
            title_text.append(f" -  {issue.title} ", style="bold")
            self.console.print(title_text)

            if self.verbose or severity_value in ["CRITICAL", "HIGH"]:
                #Issue description
                self.console.print(Panel(f"  [white]{issue.description}[/white]",
                                         title="[bold white]Description[/bold white]",
                                         border_style="white",
                                         padding=(0, 2),
                                         expand=False))
                #Suggestion
                self.console.print(Panel(f"  [green]{issue.suggestion}[/green]",
                                         title="[bold green]Suggestion[/bold green]",
                                         border_style="green",
                                         padding=(0, 2),
                                         expand=False))


    def _print_verdict(self, result: ReviewResult) -> None:
        verdict = result.summary.verdict
        emoji = verdict_emoji.get(verdict, "")
        style = verdict_style.get(verdict, "bold")

        messages = {
            "BLOCKED":  "Critical issues found. Merge is blocked until they are resolved.",
            "WARNINGS": "Warnings found. Please review before merging.",
            "APPROVED": "No blocking issues found. Good to merge!"
        }

        self.console.print()
        self.console.print(Panel(
            f"[{style}]{emoji}  {messages.get(verdict, '')}[/{style}]",
            title = f"[{style}]Verdict: {verdict}[/{style}]",
            border_style=style.replace("bold", ""),
            padding = (0,2)
        ))

        self.console.print()
#Example usage:
result = ReviewResult(
    repo_name="example/repo",
    pr_number=42,
    issues=[
        ReviewIssue(
            file_path="src/app.py",
            line_number=10,
            severity=Severity.HIGH,
            category="SECURITY",
            title="Use of eval()",
            description="The eval() function can execute arbitrary code and should be avoided.",
            suggestion="Consider using ast.literal_eval() for safer evaluation of literals."),
        ReviewIssue(
            file_path="src/utils.py",
            line_number=25,
            severity=Severity.MEDIUM,
            category="PERFORMANCE",
            title="Inefficient loop",
            description="This loop has O(n^2) complexity. Consider using a set for faster lookups.",
            suggestion="Refactor to use a set for O(1) lookups.")
    ],
    summary=ReviewSummary(
        total_issues=2,
        critical_count=0,
        high_count=1,
        medium_count=1,
        low_count=0,
        info_count=0,
        files_reviewed=5,
        verdict="WARNINGS",
        overall_comment="High severity issue found. Please address before merging."
    ),
    review_event="COMMENT",
    raw_ai_response='{"issues":[{"file_path":"src/app.py","line_number":10,"severity":"HIGH","category":"Security","title":"Use of eval()","description":"The eval() function can execute arbitrary code and should be avoided.","suggestion":"Consider using ast.literal_eval() for safer evaluation of literals."}],"summary":{"total_issues":1,"critical_count":0,"high_count":1,"medium_count":0,"low_count":0,"info_count":0,"files_reviewed":5,"verdict":"WARNINGS","overall_comment":"High severity issue found. Please address before merging."},"review_event":"COMMENT"}'
    )


reporter = Reporter(verdict=True)
reporter.print_result(result)
