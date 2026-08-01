"""Initial TeamBrain schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-01
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("stars", sa.Integer(), nullable=True),
        sa.Column("forks", sa.Integer(), nullable=True),
        sa.Column("open_issues", sa.Integer(), nullable=True),
        sa.Column("default_branch", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner",
            "name",
            name="uq_repository_owner_name",
        ),
    )
    op.create_index(
        op.f("ix_repositories_id"),
        "repositories",
        ["id"],
        unique=False,
    )

    op.create_table(
        "sync_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("last_review_sync", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_sync_state_id"),
        "sync_state",
        ["id"],
        unique=False,
    )

    op.create_table(
        "issues",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("github_issue_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("author", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "repository_id",
            "github_issue_number",
            name="uq_issue_repository_number",
        ),
    )
    op.create_index(op.f("ix_issues_id"), "issues", ["id"], unique=False)

    op.create_table(
        "pull_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("github_pr_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("author", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("merged_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "repository_id",
            "github_pr_number",
            name="uq_pull_request_repository_number",
        ),
    )
    op.create_index(
        op.f("ix_pull_requests_id"),
        "pull_requests",
        ["id"],
        unique=False,
    )

    op.create_table(
        "pull_request_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pull_request_id", sa.Integer(), nullable=False),
        sa.Column("github_review_id", sa.BigInteger(), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["pull_request_id"], ["pull_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_review_id"),
    )
    op.create_index(
        op.f("ix_pull_request_reviews_id"),
        "pull_request_reviews",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_pull_request_reviews_id"),
        table_name="pull_request_reviews",
    )
    op.drop_table("pull_request_reviews")
    op.drop_index(op.f("ix_pull_requests_id"), table_name="pull_requests")
    op.drop_table("pull_requests")
    op.drop_index(op.f("ix_issues_id"), table_name="issues")
    op.drop_table("issues")
    op.drop_index(op.f("ix_sync_state_id"), table_name="sync_state")
    op.drop_table("sync_state")
    op.drop_index(op.f("ix_repositories_id"), table_name="repositories")
    op.drop_table("repositories")
