import logging
import time

import requests
from fastapi import HTTPException

from app.core.config import settings

GITHUB_API_BASE_URL = "https://api.github.com"
logger = logging.getLogger(__name__)
MAX_GITHUB_REQUEST_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {429, 502, 503, 504}


def _truncate(value: str, limit: int = 500) -> str:
    if len(value) <= limit:
        return value

    return f"{value[:limit]}..."


def _response_error_detail(response: requests.Response) -> str:
    response_text = getattr(response, "text", "").strip()

    if not response_text:
        return ""

    return f" Response body: {_truncate(response_text)}"


def _is_secondary_rate_limit(response: requests.Response) -> bool:
    response_text = getattr(response, "text", "").lower()
    headers = getattr(response, "headers", {})

    return (
        getattr(response, "status_code", 200) == 403
        and (
            "secondary rate limit" in response_text
            or "abuse detection" in response_text
            or headers.get("Retry-After") is not None
        )
    )


def get_headers():
    """
    Return headers for GitHub API requests.
    """

    headers = {
        "Accept": "application/vnd.github+json",
    }

    if settings.github_token:
        headers["Authorization"] = (
            f"Bearer {settings.github_token}"
        )

    return headers


def _get_json(url: str, params: dict | None = None):
    last_exception: Exception | None = None

    for attempt in range(1, MAX_GITHUB_REQUEST_ATTEMPTS + 1):
        try:
            response = requests.get(
                url,
                headers=get_headers(),
                params=params,
                timeout=settings.github_request_timeout_seconds,
            )

            status_code = getattr(response, "status_code", 200)

            if (
                status_code in RETRYABLE_STATUS_CODES
                and attempt < MAX_GITHUB_REQUEST_ATTEMPTS
            ):
                logger.warning(
                    "GitHub API returned a transient status code; retrying",
                    extra={
                        "url": url,
                        "status_code": status_code,
                        "attempt": attempt,
                    },
                )
                time.sleep(2 ** (attempt - 1))
                continue

            if (
                _is_secondary_rate_limit(response)
                and attempt < MAX_GITHUB_REQUEST_ATTEMPTS
            ):
                headers = getattr(response, "headers", {})
                retry_after = headers.get("Retry-After")
                sleep_seconds = (
                    float(retry_after)
                    if retry_after is not None and retry_after.isdigit()
                    else 2 ** (attempt - 1)
                )

                logger.warning(
                    "GitHub API hit a secondary rate limit; retrying",
                    extra={
                        "url": url,
                        "status_code": status_code,
                        "attempt": attempt,
                        "sleep_seconds": sleep_seconds,
                    },
                )
                time.sleep(sleep_seconds)
                continue

            response.raise_for_status()
            return response.json()

        except requests.Timeout as exc:
            last_exception = exc
            logger.warning(
                "GitHub API request timed out",
                extra={"url": url, "attempt": attempt},
            )

            if attempt < MAX_GITHUB_REQUEST_ATTEMPTS:
                time.sleep(2 ** (attempt - 1))
                continue

            raise HTTPException(
                status_code=504,
                detail="GitHub API request timed out.",
            ) from exc

        except requests.HTTPError as exc:
            response = exc.response
            status_code = response.status_code if response is not None else 502
            detail = "GitHub API request failed."

            if response is not None:
                detail = (
                    f"GitHub API request failed with status {status_code}."
                    f"{_response_error_detail(response)}"
                )

            logger.exception(
                "GitHub API request failed",
                extra={
                    "url": url,
                    "status_code": status_code,
                    "attempt": attempt,
                },
            )

            raise HTTPException(
                status_code=status_code,
                detail=detail,
            ) from exc

        except requests.RequestException as exc:
            last_exception = exc
            logger.warning(
                "GitHub API request failed before receiving a response",
                extra={"url": url, "attempt": attempt},
            )

            if attempt < MAX_GITHUB_REQUEST_ATTEMPTS:
                time.sleep(2 ** (attempt - 1))
                continue

            raise HTTPException(
                status_code=502,
                detail="GitHub API request failed.",
            ) from exc

    if last_exception is not None:
        raise HTTPException(
            status_code=502,
            detail="GitHub API request failed.",
        ) from last_exception

    raise HTTPException(
        status_code=502,
        detail="GitHub API request failed.",
    )


def _get_all_pages(path: str, params: dict | None = None):
    """
    Fetch all GitHub REST pages for list endpoints.
    """

    page = 1
    results = []

    while True:
        page_params = {
            **(params or {}),
            "per_page": 100,
            "page": page,
        }
        url = f"{GITHUB_API_BASE_URL}{path}"
        page_results = _get_json(url, params=page_params)

        if not page_results:
            break

        results.extend(page_results)
        page += 1

    return results


def get_repository(owner: str, repo: str):
    """
    Fetch repository information from GitHub.
    """

    url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}"

    return _get_json(url)


def get_repository_issues(
    owner: str,
    repo: str,
):
    """
    Fetch all issues for a GitHub repository.
    """

    return _get_all_pages(
        f"/repos/{owner}/{repo}/issues",
    )


def get_repository_pull_requests(
    owner: str,
    repo: str,
):
    """
    Fetch all pull requests for a GitHub repository.
    """

    return _get_all_pages(
        f"/repos/{owner}/{repo}/pulls",
        params={"state": "all"},
    )


def get_pull_request_reviews(
    owner: str,
    repo: str,
    pull_request_number: int,
):
    """
    Fetch reviews for a pull request.
    """

    return _get_all_pages(
        (
            f"/repos/{owner}/{repo}"
            f"/pulls/{pull_request_number}/reviews"
        ),
    )


def get_pull_request_review_comments(
    owner: str,
    repo: str,
    pull_request_number: int,
):
    """
    Fetch review comments for a pull request.
    """

    return _get_all_pages(
        (
            f"/repos/{owner}/{repo}"
            f"/pulls/{pull_request_number}/comments"
        ),
    )
