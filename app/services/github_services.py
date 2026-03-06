import os
import logging
from dotenv import load_dotenv
from github import Github
from github import Auth

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the GitHub client with authentication
github = Github(auth=Auth.Token(os.getenv("GITHUB_TOKEN")))

class GithubService:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        if not self.github_token:
            logger.error(f"File: {__file__} | GITHUB_TOKEN is not set in environment variables.")
            raise ValueError("GITHUB_TOKEN is not set in environment variables.")
        
        self.client = Github(auth=Auth.Token(self.github_token))
        
    
    def get_pull_request(self, repo_name: str, pr_number: int):
        """
        Fetches a pull request from the specified repository.
        """
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)

            logger.info(f"File: {__file__} | Successfully fetched pull request #{pr_number} from repository {repo_name}.")
            
            return pr
        
        except Exception as e:
            logger.error(f"File: {__file__} | Error fetching pull request: {e}")
            return None
        
    
    def get_pr_files(self, repo_name: str, pr_number: int):
        """
        Fetches the list of files changed in the pull request along with diff patches.
        """
        
        try:
            pr = self.get_pull_request(repo_name, pr_number)
            files_data=[]

            for file in pr.get_files():
                files_data.append({
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch
                })

            return files_data

        except Exception as e:
            logger.error(f"File: {__file__} | Error fetching pull request files: {e}")
            return None

    def combine_diffs(files):
        """
        Combine the diffs of all files in a pull request into a single string for easier processing.
        """
        try:
            combined_diff = ""
            
            for file in files:
                combined_diff += f"Filename: {file['filename']}\n"
                combined_diff += f"Patch:\n{file['patch']}\n\n"
            
            return combined_diff
        
        except Exception as e:
            
            logger.error(f"File: {__file__} | Error combining diffs: {e}")
            return None

    def post_comment(self, repo_name: str, pr_number: int, message: str):
        """
        Posts a comment on the specified pull request.
        """
        try:
            
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            pr.create_issue_comment(message)
            logger.info(f"File: {__file__} | Comment posted successfully.")

        except Exception as e:
            logger.error(f"File: {__file__} | Error posting comment: {e}")