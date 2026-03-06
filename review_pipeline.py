import os
import json
import logging
from dotenv import load_dotenv
from app.services.github_services import GithubService

load_dotenv()
logger = logging.getLogger(__name__)

"""
event_path = os.getenv("GITHUB_EVENT_PATH")

event_data = None
with open(event_path, "r") as f:
    event_data = json.load(f)

repo_name = event_data.get("repository", {}).get("full_name")
pull_request_number = event_data.get("pull_request", {}).get("number")

print(f"Repository: {repo_name}")
print(f"Pull Request Number: {pull_request_number}")
"""

#example usage of GithubService to fetch files from a pull request
repo_name = "dhruv8315/empty-repo"
pr_number = 3

github_service = GithubService()

files = github_service.get_pr_files(repo_name, pr_number)

diff_text = github_service.combine_diffs(files)
logger.info(f"Combined diff for PR #{pr_number} in repository {repo_name}:\n{diff_text}")
print(diff_text)