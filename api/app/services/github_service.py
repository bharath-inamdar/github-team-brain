from app.clients.github_client import get_repository


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