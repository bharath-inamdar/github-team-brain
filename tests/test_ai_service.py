from app.services.ai_service import AIService


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
