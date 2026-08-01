import logging

from app.clients.github_client import (
    get_repository,
    get_repository_issues,
    get_repository_pull_requests,
    get_pull_request_review_comments,
    get_pull_request_reviews,
)
from app.services.datetime_utils import parse_github_datetime

logger = logging.getLogger(__name__)

def get_repository_details(
    owner: str,
    repo: str
):
    """
    Fetch a repository from GitHub and
    return only the fields our application needs.
    """

    repository = get_repository(
        owner,
        repo
    )

    return {
        "id": repository["id"],
        "name": repository["name"],
        "owner": repository["owner"]["login"],
        "description": repository["description"],
        "language": repository["language"],
        "stars": repository["stargazers_count"],
        "forks": repository["forks_count"],
        "open_issues": repository["open_issues_count"],
        "default_branch": repository["default_branch"],
    }

def get_repository_issue_details(
    owner: str,
    repo: str,
):
    """
    Fetch issues from GitHub and return only
    the fields our application needs.
    """

    issues = get_repository_issues(owner, repo)

    cleaned_issues = []

    for issue in issues:

        # GitHub returns pull requests in the issues endpoint.
        # Skip them because we'll import pull requests separately.
        if "pull_request" in issue:
            continue

        cleaned_issues.append(
            {
                "github_issue_number": issue["number"],
                "title": issue["title"],
                "body": issue["body"],
                "state": issue["state"],
                "author": issue["user"]["login"],
            }
        )

    return cleaned_issues


def get_repository_pull_request_details(owner: str, repo: str):
    """
    Fetch pull requests and keep only the fields
    needed by TeamBrain.
    """

    github_pull_requests = get_repository_pull_requests(owner, repo)

    cleaned_pull_requests = []

    for pr in github_pull_requests:
        cleaned_pull_requests.append(
            {
                "github_pr_number": pr["number"],
                "title": pr["title"],
                "body": pr["body"],
                "state": pr["state"],
                "author": pr["user"]["login"],
                "created_at": parse_github_datetime(pr["created_at"]),
                "merged_at": parse_github_datetime(pr["merged_at"]),
                "closed_at": parse_github_datetime(pr["closed_at"]),
            }
        )

    return cleaned_pull_requests



def get_pull_request_review_details(
    owner: str,
    repo: str,
    pull_request_number: int,
):
    """
    Fetch pull request reviews and keep only the
    fields needed by TeamBrain.
    """

    github_reviews = get_pull_request_reviews(
        owner,
        repo,
        pull_request_number,
    )

    cleaned_reviews = []

    for review in github_reviews:
        github_review_id = review.get("id")

        if github_review_id is None:
            logger.warning(
                "Skipping malformed GitHub review without an id",
                extra={
                    "owner": owner,
                    "repo": repo,
                    "pull_request_number": pull_request_number,
                },
            )
            continue

        reviewer = review.get("user") or {}

        cleaned_reviews.append(
            {
                "github_review_id": github_review_id,
                "reviewer": reviewer.get("login"),
                "state": review.get("state"),
                "body": review.get("body"),
                "submitted_at": parse_github_datetime(
                    review.get("submitted_at")
                ),
            }
        )

    return cleaned_reviews


def get_pull_request_review_comment_details(
    owner: str,
    repo: str,
    pull_request_number: int,
):
    """
    Fetch pull request review comments and keep only the
    fields needed by TeamBrain.
    """

    github_review_comments = get_pull_request_review_comments(
        owner,
        repo,
        pull_request_number,
    )

    cleaned_review_comments = []

    for review_comment in github_review_comments:
        github_comment_id = review_comment.get("id")

        if github_comment_id is None:
            logger.warning(
                "Skipping malformed GitHub review comment without an id",
                extra={
                    "owner": owner,
                    "repo": repo,
                    "pull_request_number": pull_request_number,
                },
            )
            continue

        reviewer = review_comment.get("user") or {}

        cleaned_review_comments.append(
            {
                "github_comment_id": github_comment_id,
                "reviewer": reviewer.get("login"),
                "body": review_comment.get("body"),
                "path": review_comment.get("path"),
                "line": review_comment.get("line"),
                "created_at": parse_github_datetime(
                    review_comment.get("created_at")
                ),
                "updated_at": parse_github_datetime(
                    review_comment.get("updated_at")
                ),
            }
        )

    return cleaned_review_comments
