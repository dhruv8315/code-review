"""
Github Client for interacting with the GitHub API.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from github import Github, GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository

from .models import PRContext, FileDiff, ReviewResult, ReviewEvent