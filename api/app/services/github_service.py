from app.clients.github_client import (
    get_repository,
    get_repository_issues,
)

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