from sqlalchemy.orm import Session

from app import models
from app.services.github_service import (
    get_repository_pull_request_details,
)


def import_repository_pull_requests(
    owner: str,
    repo: str,
    db: Session,
):
    """
    Import GitHub pull requests into the database.
    """

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

    github_pull_requests = (
        get_repository_pull_request_details(
            owner,
            repo,
        )
    )

    print(f"Found {len(github_pull_requests)} pull requests")

    imported_count = 0

    for pr in github_pull_requests:

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

    db.commit()

    print(f"Imported {imported_count} pull requests")

    return imported_count