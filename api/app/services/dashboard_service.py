from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Repository,
    Issue,
    PullRequest,
    PullRequestReview,
    PullRequestReviewComment,
)


def get_dashboard_overview(db: Session):
    repositories = db.query(func.count(Repository.id)).scalar() or 0
    issues = db.query(func.count(Issue.id)).scalar() or 0
    pull_requests = db.query(func.count(PullRequest.id)).scalar() or 0
    reviews = db.query(func.count(PullRequestReview.id)).scalar() or 0
    review_comments = (
        db.query(func.count(PullRequestReviewComment.id)).scalar() or 0
    )

    return {
        "repositories": repositories,
        "issues": issues,
        "pull_requests": pull_requests,
        "reviews": reviews,
        "review_comments": review_comments,
        "summary_ready": review_comments > 0,
    }