from app.clients import github_client


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_get_all_pages_uses_timeout_and_pagination(monkeypatch):
    calls = []

    def fake_get(url, headers, params, timeout):
        calls.append(
            {
                "url": url,
                "headers": headers,
                "params": params,
                "timeout": timeout,
            }
        )

        if params["page"] == 1:
            return _FakeResponse([{"id": 1}])
        if params["page"] == 2:
            return _FakeResponse([{"id": 2}])
        return _FakeResponse([])

    monkeypatch.setattr(github_client.requests, "get", fake_get)
    monkeypatch.setattr(
        github_client.settings,
        "github_request_timeout_seconds",
        3.5,
    )

    issues = github_client.get_repository_issues("octo-org", "octo-repo")

    assert issues == [{"id": 1}, {"id": 2}]
    assert [call["params"]["page"] for call in calls] == [1, 2, 3]
    assert all(call["timeout"] == 3.5 for call in calls)
    assert all(call["params"]["per_page"] == 100 for call in calls)
