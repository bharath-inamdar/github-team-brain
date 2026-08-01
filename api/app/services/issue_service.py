import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import models
from app.services.github_service import (
    get_repository_issue_details,
)

logger = logging.getLogger(__name__)


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
        raise HTTPException(
            status_code=404,
            detail="Repository not found. Import the repository first.",
        )

    # Fetch issues from GitHub
    github_issues = get_repository_issue_details(owner, repo)

    logger.info(
        "Fetched issues from GitHub",
        extra={"count": len(github_issues)},
    )

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

    logger.info(
        "Imported issues",
        extra={"imported_count": imported_count},
    )

    return imported_count
