import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import models
from app.services.github_service import (
    get_repository_pull_request_details,
)

logger = logging.getLogger(__name__)


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
        raise HTTPException(
            status_code=404,
            detail="Repository not found. Import the repository first.",
        )

    github_pull_requests = (
        get_repository_pull_request_details(
            owner,
            repo,
        )
    )

    logger.info(
        "Fetched pull requests from GitHub",
        extra={"count": len(github_pull_requests)},
    )

    existing_pull_request_numbers = {
        pull_request_number
        for (pull_request_number,) in (
            db.query(models.PullRequest.github_pr_number)
            .filter(
                models.PullRequest.repository_id == repository.id,
            )
            .all()
        )
    }

    imported_count = 0

    for pr in github_pull_requests:

        if pr["github_pr_number"] in existing_pull_request_numbers:
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
        existing_pull_request_numbers.add(pr["github_pr_number"])
        imported_count += 1

    db.commit()

    logger.info(
        "Imported pull requests",
        extra={"imported_count": imported_count},
    )

    return imported_count
