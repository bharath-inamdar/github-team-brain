from app.services.ingestion_service import IngestionService


def test_is_useful_review_filters_empty_short_and_bot_text():
    service = IngestionService.__new__(IngestionService)

    assert service._is_useful_review("") is False
    assert service._is_useful_review("LGTM") is False
    assert service._is_useful_review("Dependabot updated a dependency") is False
    assert service._is_useful_review("Approved, looks good to me overall") is False


def test_is_useful_review_allows_meaningful_feedback():
    service = IngestionService.__new__(IngestionService)

    review = (
        "This query should be indexed by repository_id because otherwise "
        "search results can mix unrelated repositories."
    )

    assert service._is_useful_review(review) is True
