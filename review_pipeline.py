import os
import sys
import json
import logging
from dotenv import load_dotenv
from app.services.github_services import GithubService
from app.reviewer.logger_config import setup_logger

load_dotenv()
logger = setup_logger()


"""
event_path = os.getenv('GITHUB_EVENT_PATH')

event_data = None
with open(event_path, 'r') as f:
    event_data = json.load(f)

repo_name = event_data['repository']['full_name']
pull_request_number = event_data['pull_request']['number']

print(f"Repository: {repo_name}")
print(f"Pull Request Number: {pull_request_number}")
"""

repo_name = "dhruv8315/empty-repo"
pull_request_number = 3

github_service = GithubService()

files = github_service.get_pr_files(repo_name, pull_request_number)

diff_text = github_service.combine_diffs(files)

print(diff_text)