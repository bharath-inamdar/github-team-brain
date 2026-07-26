from sqlalchemy import (
    BigInteger,
    Column,
    Integer,
    String,
    ForeignKey,
    Text,
    DateTime,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)

    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)

    description = Column(Text, nullable=True)
    language = Column(String, nullable=True)

    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    open_issues = Column(Integer, default=0)

    default_branch = Column(String, nullable=False)

    # One repository can have many issues
    issues = relationship(
        "Issue",
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    pull_requests = relationship(
        "PullRequest",
        back_populates="repository",
        cascade="all, delete-orphan",
    )


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)

    repository_id = Column(
        Integer,
        ForeignKey("repositories.id"),
        nullable=False,
    )

    github_issue_number = Column(Integer, nullable=False)

    title = Column(String, nullable=False)

    body = Column(Text, nullable=True)

    state = Column(String, nullable=False)

    author = Column(String, nullable=False)

    repository = relationship(
        "Repository",
        back_populates="issues",
    )


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)

    repository_id = Column(
        Integer,
        ForeignKey("repositories.id"),
        nullable=False,
    )

    github_pr_number = Column(Integer, nullable=False)

    title = Column(String, nullable=False)

    body = Column(Text)

    state = Column(String, nullable=False)

    author = Column(String)

    created_at = Column(DateTime)

    merged_at = Column(DateTime)

    closed_at = Column(DateTime)

    reviews = relationship(
    "PullRequestReview",
    back_populates="pull_request",
    cascade="all, delete-orphan",
    )

    repository = relationship(
        "Repository",
        back_populates="pull_requests",
    )


class PullRequestReview(Base):
    __tablename__ = "pull_request_reviews"

    id = Column(Integer, primary_key=True, index=True)

    pull_request_id = Column(
        Integer,
        ForeignKey("pull_requests.id"),
        nullable=False,
    )

    github_review_id = Column(
        BigInteger,
        nullable=False,
        unique=True,
    )

    reviewer = Column(String)

    state = Column(String)

    body = Column(Text)

    submitted_at = Column(DateTime)

    pull_request = relationship(
        "PullRequest",
        back_populates="reviews",
    )