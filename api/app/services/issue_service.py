from sqlalchemy.orm import Session

from app import models
from app.services.github_service import (
    get_repository_issue_details,
    get_repository_pull_request_details,
)


def import_repository_issues(
    owner: str,
    repo: str,
    db: Session,
):
    """
    Import GitHub issues into the database.
    """

    # Find the repository in our database
    repository = (
        db.query(models.Repository)
        .filter(
            models.Repository.owner == owner,
            models.Repository.name == repo,
        )
        .first()
    )

    if repository is None:
        raise ValueError(
            "Repository not found. Import the repository first."
        )

    # Fetch issues from GitHub
    github_issues = get_repository_issue_details(owner, repo)

    print(f"Found {len(github_issues)} issues")

    imported_count = 0

    # Import each issue
    for issue in github_issues:

        # Skip if this issue already exists
        existing_issue = (
            db.query(models.Issue)
            .filter(
                models.Issue.repository_id == repository.id,
                models.Issue.github_issue_number
                == issue["github_issue_number"],
            )
            .first()
        )

        if existing_issue:
            continue

        # Create a new Issue ORM object
        new_issue = models.Issue(
            repository_id=repository.id,
            github_issue_number=issue["github_issue_number"],
            title=issue["title"],
            body=issue["body"],
            state=issue["state"],
            author=issue["author"],
        )

        db.add(new_issue)
        imported_count += 1

    # Save all new issues in one transaction
    db.commit()

    print(f"Imported {imported_count} new issues")

    return imported_count


def import_repository_pull_requests(
    owner: str,
    repo: str,
    db: Session,
):
    """
    Import GitHub pull requests into the database.
    """

    # Find the repository in our database
    repository = (
        db.query(models.Repository)
        .filter(
            models.Repository.owner == owner,
            models.Repository.name == repo,
        )
        .first()
    )

    if repository is None:
        raise ValueError(
            "Repository not found. Import the repository first."
        )

    # Fetch pull requests from GitHub
    github_pull_requests = get_repository_pull_request_details(
        owner,
        repo,
    )

    print(f"Found {len(github_pull_requests)} pull requests")

    imported_count = 0

    # Import each pull request
    for pr in github_pull_requests:

        # Skip if this pull request already exists
        existing_pr = (
            db.query(models.PullRequest)
            .filter(
                models.PullRequest.repository_id == repository.id,
                models.PullRequest.github_pr_number
                == pr["github_pr_number"],
            )
            .first()
        )

        if existing_pr:
            continue

        # Create a new PullRequest ORM object
        new_pr = models.PullRequest(
            repository_id=repository.id,
            github_pr_number=pr["github_pr_number"],
            title=pr["title"],
            body=pr["body"],
            state=pr["state"],
            author=pr["author"],
            created_at=pr["created_at"],
            merged_at=pr["merged_at"],
            closed_at=pr["closed_at"],
        )

        db.add(new_pr)
        imported_count += 1

    # Save all new pull requests in one transaction
    db.commit()

    print(f"Imported {imported_count} pull requests")

    return imported_count