import requests

GITHUB_API_BASE_URL = "https://api.github.com"


def get_repository(owner: str, repo: str):
    """
    Fetch repository information from GitHub.
    """

    url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}"

    response = requests.get(url)

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

    response = requests.get(url)
    response.raise_for_status()

    return response.json()