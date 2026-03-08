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
    """
    Run AI code review on a pull request.
    """
    print(f"[bold blue]Starting AI code review for PR #{pr} in repository '{repo}'...[/bold blue]")
    
    review_pipeline(repo, pr)

    print("[bold green]Review completed[/bold green]")

if __name__ == "__main__":
    app()