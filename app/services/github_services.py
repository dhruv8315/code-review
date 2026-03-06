import os
from dotenv import load_dotenv
from github import Github
from github import Auth

load_dotenv()

# Initialize the GitHub client with authentication
github = Github(auth=Auth.Token(os.getenv("GITHUB_TOKEN")))

class GithubService:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN is not set in environment variables.")
        
        self.client = Github(auth=Auth.Token(self.github_token))
        
    
    def get_pull_request(self, repo_name: str, pr_number: int):
        """
        Fetches a pull request from the specified repository.
        """
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            return pr
        
        except Exception as e:
            print(f"Error fetching pull request: {e}")
            return None
        
    
    def get_pr_files(self, repo_name: str, pr_number: int):
        """
        Fetches the list of files changed in the pull request along with diff patches.
        """
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
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
            print(f"Error fetching pull request files: {e}")
            return None
        

print("GithubService initialized successfully.")

repo = GithubService().get_pr_files("dhruv8315/empty-repo", 2)

print(repo)