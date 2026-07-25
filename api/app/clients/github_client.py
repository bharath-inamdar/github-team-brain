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