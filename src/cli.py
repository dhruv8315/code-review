"""
CLI entry point.

Defines the `code-reviewer` command with its subcommands:
  code-reviewer review   — run a review on a PR
  code-reviewer config   — print current configuration (with secrets masked)
  code-reviewer version  — print the tool version
"""

from __future__ import annotations

import sys
import json
import logging

import click
from rich.console import Console, console
from rich.table import Table
from rich import box

from .config import get_settings
from .reporter import Reporter
from .models import Severity, ReviewConfig

"""
Logging configuration
"""

def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )


"""
Main group
"""
@click.group()
@click.version_option(version="0.1.0", prog_name="Code Reviewer")
def main() -> None:
        """
    🤖  AI Code Reviewer — context-aware PR reviews powered by Claude.

    Reads your pull request diff, sends it through an AI pipeline, and
    posts structured, line-level review comments back to GitHub.

    \b
    Quick start:
      export GITHUB_TOKEN=ghp_...
      export ANTHROPIC_API_KEY=sk-ant-...
      code-reviewer review --repo owner/repo --pr 42
    """
        
"""
Review command
"""
@main.command()
@click.option(
      "--repo",
      '-r', 
      required=True,
      help="GitHub repository in the format 'owner/repo' eg, 'octocat/Hello-World'"
      )
@click.option(
      "--pr",
      '-p',
      required=True,
      type=int,
      help="Pull request number to review. eg., 42"
      )
@click.option(
      "--fail-on",
      default='CRITICAL',
      type=click.Choice([s.value for s in Severity],
      case_sensitive=True), 
      help="Minimum severity level to fail the review"
      )
@click.option(
      "--no-post",
      is_flag=True,
      default=False,
      help="Dry-run mode: print the review but do NOT post comments to GitHub"
)
@click.option(
      "--output",
      type=click.Choice(['json','terminal','Markdown']),
      default='terminal',
      show_default=True,
      help="Output format"
)
@click.option(
      "--verbose",
      '-v',
      is_flag=True,
      default=False,
      help="Show detailed output"
)
def review(repo: str, pr: int, fail_on: str, no_post: bool, output: str, verbose: bool) -> None:
    """
    Review a pull request and post structured feedback.

    \b
    Examples:
      code-reviewer review --repo acme/api --pr 123
      code-reviewer review --repo acme/api --pr 123 --no-post --output json
      code-reviewer review --repo acme/api --pr 123 --fail-on HIGH
    """
    _setup_logging(verbose)
    report = Reporter(verbose)

    #Load configuration
    try:
         settings = get_settings()
    except Exception as e:
         print(f"[bold red]Error loading configuration: {e}[/bold red]")
         sys.exit(1)
    
    config = ReviewConfig(
        github_token=settings.github_token,
        anthropic_api_key=settings.anthropic_api_key,
        model=settings.model,
        max_tokens=settings.max_tokens,
        fail_on_severity=Severity(fail_on),
        post_comments=not no_post,
        context_lines=settings.context_lines,
        verbose=verbose,
    )


    #Import pipeline
    from .github_client import GitHubClient
    from .ai_pipeline import AIPipeline
    from .diff_parser import DiffParser

    try:
        #Step1: Fetch PR diff
        gh_client = GitHubClient(token=config.github_token)
        pr_context = gh_client._get_pr_context(repo, pr)

        #Step2: Parse diff into structured format
        parser = DiffParser(context_lines=config.context_lines)
        parser.parse_pr_context(pr_context)

        #Step 3: Run AI pipeline
        pipeline = AIPipeline(config)
        review_result = pipeline.review(pr_context)

        #Step 4: Output results
        if output == 'json':
            click.echo(review_result.json(indent=2))
        elif output == 'Markdown':
            click.echo(review_result.to_markdown())
        elif output == 'terminal':
            reporter.print_result(review_result)

        #Step 5: Post comments to GitHub (if not in no-post mode)
        if config.post_comments:
            gh_client.post_review_comments(repo, pr, review_result)
        else:
            reporter.print_info("--no-post flag enabled: skipping posting comments to GitHub")
                                
        exit_code = reporter.exit_code(review_result, fail_on=config.fail_on_severity)
        sys.exit(exit_code)
    except ValueError as exc:
        reporter.print_error(str(exc))
        sys.exit(1)
    except Exception as exc:
        reporter.print_error(f"Unexpected error: {exc}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

"""
config command
"""
@main.command()
@click.option("--verbose", is_flag=True, default=False, help="Show detailed output")
def config(verbose: bool) -> None:
    """
    Print current configuration with secrets masked.
    \b
    Checks for settings in this order:
      1. Environment variables
      2. .env file in the current or parent directories
      3. Built-in defaults
    """
    _setup_logging(verbose)
    report = Reporter(verbose)

    try:
        settings = get_settings()

    except Exception as exc:
        console.print(f"[bold red]Config error:[/bold red] {exc}")
        console.print("[dim]Set GITHUB_TOKEN and ANTHROPIC_API_KEY in your environment or .env file.[/dim]")
        sys.exit(2)
    
    def mask(value: str) -> str:
        if not value:
            return "[red]Not set[/red]"
        if len(value) <= 8:
            return value[0] + "****" + value[-1]
        return value[:4] + "****" + value[-4:]

    table = Table(title="AI Reviwer Configuration", box=box.ROUNDED)

    table.add_column("Setting",       style="bold")
    table.add_column("Value",         style="cyan")
    table.add_column("Source",        style="dim")

    for name, value, source in rows:
        table.add_row(name, value, source)

    console.print(table)

    rows = [
        ("github_token",      mask(settings.github_token),      "env / .env"),
        ("anthropic_api_key", mask(settings.anthropic_api_key), "env / .env"),
        ("model",             settings.model,                   "env / default"),
        ("max_tokens",        str(settings.max_tokens),         "env / default"),
        ("fail_on_severity",  settings.fail_on_severity.value,  "env / default"),
        ("post_comments",     str(settings.post_comments),      "env / default"),
        ("context_lines",     str(settings.context_lines),      "env / default"),
    ]

"""
version command
"""
@main.command()
def version() -> None:
    """
    Print the tool version.
    """
    console.print("[bold blue]Code Reviewer CLI v0.1.0[/bold blue]")



"""
Helper
"""
def _to_markdown(result) -> str:
    lines = [
        f"# AI Code Review — PR #{result.pr_number}",
        "",
        f"**Verdict:** {result.summary.verdict}  ",
        f"**Issues:** {result.summary.total_issues} "
        f"(🔴{result.summary.critical_count} "
        f"🟠{result.summary.high_count} "
        f"🟡{result.summary.medium_count} "
        f"🔵{result.summary.low_count})",
        "",
        "## Issues",
        "",
    ]
    for issue in result.issues:
        lines += [
            f"### `{issue.file_path}` line {issue.line_number} — {issue.title}",
            f"**Severity:** {issue.severity.value}  **Category:** {issue.category.value}",
            "",
            issue.description,
            "",
            f"**Suggestion:** {issue.suggestion}",
            "",
            "---",
            "",
        ]
    return "\n".join(lines)


if __name__ == "__main__":


    main()


"""
import typer
from typing import Annotated
from rich import print
from review_pipeline import review_pipeline

app = typer.Typer()

#Additional command to see the list of commands
@app.command()
def version():
    print("AI Code Review CLI v1.0")

@app.command()
def review_pr(
    repo: Annotated[str, typer.Option(help="GitHub repository name in the format 'owner/repo'")],
    pr: Annotated[int, typer.Option(help="Pull request number to review")]
    ):

    #Run AI code review on a pull request.
  
    print(f"[bold blue]Starting AI code review for PR #{pr} in repository '{repo}'...[/bold blue]")
    
    review_pipeline(repo, pr)

    print("[bold green]Review completed[/bold green]")

if __name__ == "__main__":
    app()
"""