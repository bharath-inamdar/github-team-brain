from datetime import datetime


def parse_github_datetime(value: str | None) -> datetime | None:
    """
    Convert GitHub ISO 8601 timestamps into Python datetime objects.
    """

    if value is None:
        return None

    return datetime.fromisoformat(value.replace("Z", "+00:00"))
