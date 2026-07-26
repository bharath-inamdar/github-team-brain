import requests
from app.core.config import settings

GITHUB_API_BASE_URL = "https://api.github.com"



def get_headers():
    """
    Return headers for GitHub API requests.
    """

    headers = {
        "Accept": "application/vnd.github+json",
    }

    if settings.github_token:
        headers["Authorization"] = (
            f"Bearer {settings.github_token}"
        )

    return headers


def get_repository(owner: str, repo: str):
    """
    Fetch repository information from GitHub.
    """

    url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}"

    response = requests.get(
        url,
        headers=get_headers(),
    )

    response.raise_for_status()

    return response.json()


def get_repository_issues(
    owner: str,
    repo: str,
):
    """
    Fetch all issues for a GitHub repository.
    """

    url = (
        f"{GITHUB_API_BASE_URL}"
        f"/repos/{owner}/{repo}/issues"
        "?per_page=100"
    )

    response = requests.get(
        url,
        headers=get_headers(),
    )

    response.raise_for_status()

    return response.json()


def get_repository_pull_requests(
    owner: str,
    repo: str,
):
    """
    Fetch all pull requests for a GitHub repository.
    """

    url = (
        f"{GITHUB_API_BASE_URL}"
        f"/repos/{owner}/{repo}/pulls"
        "?state=all&per_page=100"
    )

    response = requests.get(
        url,
        headers=get_headers(),
    )

    response.raise_for_status()

    return response.json()


def get_pull_request_reviews(
    owner: str,
    repo: str,
    pull_request_number: int,
):
    """
    Fetch reviews for a pull request.
    """

    url = (
        f"{GITHUB_API_BASE_URL}"
        f"/repos/{owner}/{repo}"
        f"/pulls/{pull_request_number}/reviews"
    )

    response = requests.get(
        url,
        headers=get_headers(),
    )

    response.raise_for_status()

    return response.json()