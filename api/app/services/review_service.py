import logging

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models
from app.services import github_service

logger = logging.getLogger(__name__)


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
        raise HTTPException(
            status_code=404,
            detail="Repository not found. Import the repository first.",
        )

    pull_requests = (
        db.query(models.PullRequest)
        .filter(
            models.PullRequest.repository_id == repository.id
        )
        .all()
    )

    imported_count = 0

    try:
        for pull_request in pull_requests:

            reviews = github_service.get_pull_request_review_details(
                owner,
                repo,
                pull_request.github_pr_number,
            )

            for review in reviews:

                github_review_id = review.get("github_review_id")

                if github_review_id is None:
                    logger.warning(
                        "Skipping malformed review without a GitHub review id",
                        extra={
                            "owner": owner,
                            "repo": repo,
                            "pull_request_number": pull_request.github_pr_number,
                        },
                    )
                    continue

                existing_review = (
                    db.query(models.PullRequestReview)
                    .filter(
                        models.PullRequestReview.github_review_id
                        == github_review_id
                    )
                    .first()
                )

                if existing_review:
                    continue

                new_review = models.PullRequestReview(
                    pull_request_id=pull_request.id,
                    github_review_id=github_review_id,
                    reviewer=review.get("reviewer"),
                    state=review.get("state"),
                    body=review.get("body"),
                    submitted_at=review.get("submitted_at"),
                )

                db.add(new_review)
                imported_count += 1

            db.commit()

        logger.info(
            "Imported pull request reviews",
            extra={"imported_count": imported_count},
        )

        return imported_count

    except HTTPException:
        db.rollback()
        logger.exception(
            "Review import failed while calling an upstream dependency",
            extra={
                "owner": owner,
                "repo": repo,
                "imported_count": imported_count,
            },
        )
        raise

    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(
            "Database error while importing pull request reviews",
            extra={
                "owner": owner,
                "repo": repo,
                "imported_count": imported_count,
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to import pull request reviews due to a database error.",
        ) from exc

    except Exception as exc:
        db.rollback()
        logger.exception(
            "Unexpected error while importing pull request reviews",
            extra={
                "owner": owner,
                "repo": repo,
                "imported_count": imported_count,
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while importing pull request reviews.",
        ) from exc


def import_pull_request_review_comments(
    owner: str,
    repo: str,
    db: Session,
):
    """
    Import review comments for all pull requests
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
        raise HTTPException(
            status_code=404,
            detail="Repository not found. Import the repository first.",
        )

    pull_requests = (
        db.query(models.PullRequest)
        .filter(
            models.PullRequest.repository_id == repository.id
        )
        .all()
    )

    imported_count = 0

    try:
        for pull_request in pull_requests:

            review_comments = github_service.get_pull_request_review_comment_details(
                owner,
                repo,
                pull_request.github_pr_number,
            )

            for review_comment in review_comments:

                github_comment_id = review_comment.get("github_comment_id")

                if github_comment_id is None:
                    logger.warning(
                        "Skipping malformed review comment without a GitHub comment id",
                        extra={
                            "owner": owner,
                            "repo": repo,
                            "pull_request_number": pull_request.github_pr_number,
                        },
                    )
                    continue

                existing_review_comment = (
                    db.query(models.PullRequestReviewComment)
                    .filter(
                        models.PullRequestReviewComment.github_comment_id
                        == github_comment_id
                    )
                    .first()
                )

                if existing_review_comment:
                    continue

                new_review_comment = models.PullRequestReviewComment(
                    pull_request_id=pull_request.id,
                    github_comment_id=github_comment_id,
                    reviewer=review_comment.get("reviewer"),
                    body=review_comment.get("body"),
                    path=review_comment.get("path"),
                    line=review_comment.get("line"),
                    created_at=review_comment.get("created_at"),
                    updated_at=review_comment.get("updated_at"),
                )

                db.add(new_review_comment)
                imported_count += 1

            db.commit()

        logger.info(
            "Imported pull request review comments",
            extra={"imported_count": imported_count},
        )

        return imported_count

    except HTTPException:
        db.rollback()
        logger.exception(
            "Review comment import failed while calling an upstream dependency",
            extra={
                "owner": owner,
                "repo": repo,
                "imported_count": imported_count,
            },
        )
        raise

    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(
            "Database error while importing pull request review comments",
            extra={
                "owner": owner,
                "repo": repo,
                "imported_count": imported_count,
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to import pull request review comments due to a database error.",
        ) from exc

    except Exception as exc:
        db.rollback()
        logger.exception(
            "Unexpected error while importing pull request review comments",
            extra={
                "owner": owner,
                "repo": repo,
                "imported_count": imported_count,
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while importing pull request review comments.",
        ) from exc
