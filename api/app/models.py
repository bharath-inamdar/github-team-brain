from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    repositories = relationship(
        "Repository",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Repository(Base):
    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "owner",
            "name",
            name="uq_repository_user_owner_name",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)

    description = Column(Text, nullable=True)
    language = Column(String, nullable=True)

    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    open_issues = Column(Integer, default=0)

    default_branch = Column(String, nullable=False)

    user = relationship(
        "User",
        back_populates="repositories",
    )

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
    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "github_issue_number",
            name="uq_issue_repository_number",
        ),
    )

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
    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "github_pr_number",
            name="uq_pull_request_repository_number",
        ),
    )

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

    review_comments = relationship(
        "PullRequestReviewComment",
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


class PullRequestReviewComment(Base):
    __tablename__ = "pull_request_review_comments"

    id = Column(Integer, primary_key=True, index=True)

    pull_request_id = Column(
        Integer,
        ForeignKey("pull_requests.id"),
        nullable=False,
    )

    github_comment_id = Column(
        BigInteger,
        nullable=False,
        unique=True,
        index=True,
    )

    reviewer = Column(String, nullable=True)

    body = Column(Text, nullable=True)

    path = Column(String, nullable=True)

    line = Column(Integer, nullable=True)

    created_at = Column(DateTime, nullable=True)

    updated_at = Column(DateTime, nullable=True)

    pull_request = relationship(
        "PullRequest",
        back_populates="review_comments",
    )

class SyncState(Base):
    __tablename__ = "sync_state"

    id = Column(Integer, primary_key=True, index=True)

    last_review_sync = Column(
        DateTime,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )
