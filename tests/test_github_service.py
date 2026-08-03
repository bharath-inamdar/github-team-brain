from datetime import datetime, timezone

from app.services import github_service


def test_pull_request_details_parse_github_timestamps(monkeypatch):
    monkeypatch.setattr(
        github_service,
        "get_repository_pull_requests",
        lambda owner, repo: [
            {
                "number": 12,
                "title": "Add docs",
                "body": "Adds README",
                "state": "closed",
                "user": {"login": "octocat"},
                "created_at": "2026-01-01T00:00:00Z",
                "merged_at": None,
                "closed_at": "2026-01-02T00:00:00Z",
            }
        ],
    )

    pull_requests = github_service.get_repository_pull_request_details(
        "octo-org",
        "octo-repo",
    )

    assert pull_requests[0]["created_at"] == datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )
    assert pull_requests[0]["merged_at"] is None


def test_review_details_parse_github_timestamps(monkeypatch):
    monkeypatch.setattr(
        github_service,
        "get_pull_request_reviews",
        lambda owner, repo, pull_request_number: [
            {
                "id": 1001,
                "user": {"login": "reviewer"},
                "state": "COMMENTED",
                "body": "Consider extracting this helper.",
                "submitted_at": "2026-01-03T10:30:00Z",
            }
        ],
    )

    reviews = github_service.get_pull_request_review_details(
        "octo-org",
        "octo-repo",
        12,
    )

    assert reviews[0]["submitted_at"] == datetime(
        2026,
        1,
        3,
        10,
        30,
        tzinfo=timezone.utc,
    )
