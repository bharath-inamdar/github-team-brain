from fastapi import HTTPException

from app import models
from app.services import github_service, review_service


def test_review_service_skips_malformed_github_reviews(
    monkeypatch,
    db_session,
    make_user,
):
    user = make_user()
    repository = models.Repository(
        user_id=user.id,
        owner="octo-org",
        name="octo-repo",
        default_branch="main",
    )
    db_session.add(repository)
    db_session.commit()
    db_session.refresh(repository)

    pull_request = models.PullRequest(
        repository_id=repository.id,
        github_pr_number=12,
        title="Improve review import",
        body="",
        state="open",
        author="octocat",
    )
    db_session.add(pull_request)
    db_session.commit()
    db_session.refresh(pull_request)

    monkeypatch.setattr(
        github_service,
        "get_pull_request_review_details",
        lambda owner, repo, pull_request_number: [
            {
                "github_review_id": 2001,
                "reviewer": "reviewer",
                "state": "COMMENTED",
                "body": "This is a valid review comment that should import.",
                "submitted_at": None,
            },
            {
                "github_review_id": None,
                "reviewer": None,
                "state": "COMMENTED",
                "body": "Broken review payload",
                "submitted_at": None,
            },
        ],
    )

    imported_count = review_service.import_pull_request_reviews(
        "octo-org",
        "octo-repo",
        db_session,
    )

    assert imported_count == 1
    stored_reviews = db_session.query(models.PullRequestReview).all()
    assert len(stored_reviews) == 1
    assert stored_reviews[0].github_review_id == 2001


def test_review_service_rolls_back_on_upstream_failure(
    monkeypatch,
    db_session,
    make_user,
):
    user = make_user()
    repository = models.Repository(
        user_id=user.id,
        owner="octo-org",
        name="octo-repo",
        default_branch="main",
    )
    db_session.add(repository)
    db_session.commit()
    db_session.refresh(repository)

    pull_request = models.PullRequest(
        repository_id=repository.id,
        github_pr_number=12,
        title="Improve review import",
        body="",
        state="open",
        author="octocat",
    )
    db_session.add(pull_request)
    db_session.commit()

    monkeypatch.setattr(
        github_service,
        "get_pull_request_review_details",
        lambda owner, repo, pull_request_number: (_ for _ in ()).throw(
            HTTPException(status_code=502, detail="GitHub API request failed.")
        ),
    )

    try:
        review_service.import_pull_request_reviews(
            "octo-org",
            "octo-repo",
            db_session,
        )
    except HTTPException as exc:
        assert exc.status_code == 502
    else:
        raise AssertionError("Expected import_pull_request_reviews to raise HTTPException")

    assert db_session.query(models.PullRequestReview).count() == 0