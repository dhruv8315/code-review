from rich import print
from dotenv import load_dotenv
from app.integration.github_client import GithubService
from app.reviewer.diff_parser import DiffParser
from app.utils.logger_config import setup_logger

load_dotenv()
logger = setup_logger()

def review_pipeline(repo_name, pr_number):
    """
    Main pipeline that ochestrates the AI code review.
    """

    print(f"[yellow]Step 1: Fetching pull request details...[/yellow]\n")

    github_service = GithubService()
    pr_files = github_service.get_pr_files(repo_name, pr_number)
    print(pr_files)

    print(f"[yellow]Step 2: Parsing the diff...[/yellow]\n")

    parser = DiffParser()
    parsed_diff = parser.diff_parser(pr_files)
    print(parsed_diff)

    print(f"[yellow]Step 3: Running analysis...[/yellow]\n")

    print(f"[yellow]Step 4: Running AI analysis...[/yellow]\n")

    print(f"[yellow]Step 5: Generating review comments...[/yellow]\n")



    