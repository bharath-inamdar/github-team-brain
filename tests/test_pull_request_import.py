from datetime import datetime

import pytest
from fastapi import HTTPException

from app import models
from app.services import pull_request_service


def test_import_pull_requests_uses_mocked_github_data(
    db_session,
    monkeypatch,
):
    repository = models.Repository(
        owner="octo-org",
        name="octo-repo",
        default_branch="main",
    )
    db_session.add(repository)
    db_session.commit()
    db_session.refresh(repository)

    created_at = datetime(2026, 1, 1)

    monkeypatch.setattr(
        pull_request_service,
        "get_repository_pull_request_details",
        lambda owner, repo: [
            {
                "github_pr_number": 1,
                "title": "Improve ingestion",
                "body": "Adds better import behavior",
                "state": "closed",
                "author": "octocat",
                "created_at": created_at,
                "merged_at": None,
                "closed_at": None,
            }
        ],
    )

    imported_count = pull_request_service.import_repository_pull_requests(
        "octo-org",
        "octo-repo",
        db_session,
    )

    assert imported_count == 1
    pull_request = db_session.query(models.PullRequest).one()
    assert pull_request.github_pr_number == 1
    assert pull_request.created_at == created_at

    second_import_count = pull_request_service.import_repository_pull_requests(
        "octo-org",
        "octo-repo",
        db_session,
    )
    assert second_import_count == 0


def test_import_pull_requests_returns_404_for_missing_repository(db_session):
    with pytest.raises(HTTPException) as exc_info:
        pull_request_service.import_repository_pull_requests(
            "missing",
            "repo",
            db_session,
        )

    assert exc_info.value.status_code == 404
