from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Repository,
    Issue,
    PullRequest,
    PullRequestReview,
    PullRequestReviewComment,
)


def get_dashboard_overview(
    db: Session,
    user_id: int,
):
    repositories = (
        db.query(func.count(Repository.id))
        .filter(Repository.user_id == user_id)
        .scalar()
        or 0
    )
    issues = (
        db.query(func.count(Issue.id))
        .join(Issue.repository)
        .filter(Repository.user_id == user_id)
        .scalar()
        or 0
    )
    pull_requests = (
        db.query(func.count(PullRequest.id))
        .join(PullRequest.repository)
        .filter(Repository.user_id == user_id)
        .scalar()
        or 0
    )
    reviews = (
        db.query(func.count(PullRequestReview.id))
        .join(PullRequestReview.pull_request)
        .join(PullRequest.repository)
        .filter(Repository.user_id == user_id)
        .scalar()
        or 0
    )
    review_comments = (
        db.query(func.count(PullRequestReviewComment.id))
        .join(PullRequestReviewComment.pull_request)
        .join(PullRequest.repository)
        .filter(Repository.user_id == user_id)
        .scalar()
        or 0
    )

    return {
        "repositories": repositories,
        "issues": issues,
        "pull_requests": pull_requests,
        "reviews": reviews,
        "review_comments": review_comments,
        "summary_ready": review_comments > 0,
    }
