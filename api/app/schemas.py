from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel


class RepositoryCreate(BaseModel):
    """
    Schema used when creating a new repository.
    """

    owner: str
    name: str

    description: str | None = None
    language: str | None = None

    stars: int = 0
    forks: int = 0
    open_issues: int = 0

    default_branch: str

class RepositoryUpdate(BaseModel):
    owner: str
    name: str

    description: str | None = None
    language: str | None = None

    stars: int = 0
    forks: int = 0
    open_issues: int = 0

    default_branch: str

    
class RepositoryResponse(BaseModel):
    """
    Schema used when returning repository data to the client.
    """

    id: int

    owner: str
    name: str

    description: str | None
    language: str | None

    stars: int
    forks: int
    open_issues: int

    default_branch: str

    model_config = ConfigDict(from_attributes=True)


class RepositoryImportRequest(BaseModel):
    url: str = Field(min_length=1, max_length=300)


class RepositoryImportResponse(BaseModel):
    success: bool
    message: str
    repository: RepositoryResponse


class IssueCreate(BaseModel):
    repository_id: int

    github_issue_number: int

    title: str

    body: str | None = None

    state: str

    author: str


class IssueResponse(BaseModel):
    id: int

    repository_id: int

    github_issue_number: int

    title: str

    body: str | None

    state: str

    author: str

    model_config = ConfigDict(from_attributes=True)


class AIEmbeddingTestResponse(BaseModel):
    dimensions: int
    first_10_values: list[float]


class AIChromaTestResponse(BaseModel):
    collection_name: str
    document_count: int
    status: str


class AIMessageResponse(BaseModel):
    message: str


class AIIndexAllReviewsResponse(BaseModel):
    total_reviews: int
    total_review_comments: int = 0
    indexed: int
    indexed_reviews: int = 0
    indexed_review_comments: int = 0
    skipped_empty: int
    skipped_short: int
    skipped_bot: int
    skipped_existing: int


class AISearchReviewsResponse(RootModel[dict[str, Any]]):
    pass


class AISourceCitation(BaseModel):
    citation_id: int
    text: str
    source_type: str
    reviewer: str | None = None
    state: str | None = None
    path: str | None = None
    line: int | None = None
    pull_request_id: int | None = None
    repository_id: int | None = None


class AIAskRepositoryResponse(BaseModel):
    question: str
    answer: str
    sources: list[AISourceCitation]


class AIRepositorySummaryResponse(BaseModel):
    total_reviews: int
    summary: str
