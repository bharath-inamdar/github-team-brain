from google.genai import errors

import pytest

from app.services.ai_service import AIService, RateLimitError


class _FakeGenerateResponse:
    text = "Generated answer"


class _FakeEmbedding:
    values = [0.1, 0.2, 0.3]


class _FakeEmbedResponse:
    embeddings = [_FakeEmbedding()]


class _FakeModels:
    def generate_content(self, model, contents, config):
        self.last_generate_call = {
            "model": model,
            "contents": contents,
            "config": config,
        }
        return _FakeGenerateResponse()

    def embed_content(self, model, contents):
        self.last_embed_call = {
            "model": model,
            "contents": contents,
        }
        return _FakeEmbedResponse()


class _FakeClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.models = _FakeModels()


def test_ai_service_generates_text_with_mocked_gemini(monkeypatch):
    monkeypatch.setattr("app.services.ai_service.genai.Client", _FakeClient)
    monkeypatch.setattr("app.services.ai_service.settings.gemini_model", "test-model")

    service = AIService()

    assert service.generate_text("Summarize this") == "Generated answer"
    assert service.client.models.last_generate_call["model"] == "test-model"


def test_ai_service_generates_embedding_with_mocked_gemini(monkeypatch):
    monkeypatch.setattr("app.services.ai_service.genai.Client", _FakeClient)
    monkeypatch.setattr(
        "app.services.ai_service.settings.gemini_embedding_model",
        "test-embedding-model",
    )

    service = AIService()

    assert service.generate_embedding("review text") == [0.1, 0.2, 0.3]
    assert (
        service.client.models.last_embed_call["model"]
        == "test-embedding-model"
    )


class _RateLimitedEmbedModels:
    def embed_content(self, model, contents):
        raise errors.ClientError(
            429,
            {
                "error": {
                    "code": 429,
                    "status": "RESOURCE_EXHAUSTED",
                    "details": [
                        {
                            "@type": (
                                "type.googleapis.com/"
                                "google.rpc.RetryInfo"
                            ),
                            "retryDelay": "60s",
                        }
                    ],
                }
            },
            None,
        )

    def generate_content(self, model, contents, config):
        raise AssertionError("generate_content should not be reached")


class _RateLimitedEmbedClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.models = _RateLimitedEmbedModels()


def test_embedding_429_maps_to_rate_limit_error(monkeypatch):
    monkeypatch.setattr(
        "app.services.ai_service.genai.Client",
        _RateLimitedEmbedClient,
    )

    service = AIService()

    with pytest.raises(RateLimitError) as exc_info:
        service.generate_embedding("review text")

    assert exc_info.value.retry_after_seconds == 60


class _RateLimitedGenerateModels:
    def embed_content(self, model, contents):
        raise AssertionError("embed_content should not be reached")

    def generate_content(self, model, contents, config):
        raise errors.ClientError(
            429,
            {
                "error": {
                    "code": 429,
                    "status": "RESOURCE_EXHAUSTED",
                    "details": [
                        {
                            "@type": (
                                "type.googleapis.com/"
                                "google.rpc.RetryInfo"
                            ),
                            "retryDelay": "90s",
                        }
                    ],
                }
            },
            None,
        )


class _RateLimitedGenerateClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.models = _RateLimitedGenerateModels()


def test_generate_text_429_maps_to_rate_limit_error(monkeypatch):
    monkeypatch.setattr(
        "app.services.ai_service.genai.Client",
        _RateLimitedGenerateClient,
    )

    service = AIService()

    with pytest.raises(RateLimitError) as exc_info:
        service.generate_text("Summarize this")

    assert exc_info.value.retry_after_seconds == 90


class _BadRequestModels:
    def embed_content(self, model, contents):
        raise errors.ClientError(
            400,
            {"error": {"code": 400, "message": "Bad request"}},
            None,
        )


class _BadRequestClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.models = _BadRequestModels()


def test_non_429_client_error_propagates_unchanged(monkeypatch):
    monkeypatch.setattr(
        "app.services.ai_service.genai.Client",
        _BadRequestClient,
    )

    service = AIService()

    with pytest.raises(errors.ClientError):
        service.generate_embedding("review text")
