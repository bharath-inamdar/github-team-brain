from sqlalchemy.orm import Session

from app import models
from app.services.github_service import (
    get_pull_request_review_details,
)


def import_pull_request_reviews(
    owner: str,
    repo: str,
    db: Session,
):
    """
    Import reviews for all pull requests
    belonging to a repository.
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

    pull_requests = (
        db.query(models.PullRequest)
        .filter(
            models.PullRequest.repository_id == repository.id
        )
        .all()
    )

    imported_count = 0

    for pull_request in pull_requests:

        reviews = get_pull_request_review_details(
            owner,
            repo,
            pull_request.github_pr_number,
        )

        for review in reviews:

            existing_review = (
                db.query(models.PullRequestReview)
                .filter(
                    models.PullRequestReview.github_review_id
                    == review["github_review_id"]
                )
                .first()
            )

            if existing_review:
                continue

            new_review = models.PullRequestReview(
                pull_request_id=pull_request.id,
                github_review_id=review["github_review_id"],
                reviewer=review["reviewer"],
                state=review["state"],
                body=review["body"],
                submitted_at=review["submitted_at"],
            )

            db.add(new_review)
            imported_count += 1

    db.commit()

    print(f"Imported {imported_count} reviews")

    return imported_count