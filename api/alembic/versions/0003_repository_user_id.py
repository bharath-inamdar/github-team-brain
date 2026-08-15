"""Add user ownership to repositories.

Backfills existing repositories to the bootstrap admin account so that no
pre-existing data is lost when the user_id column becomes required.

Revision ID: 0003_repository_user_id
Revises: 0002_users
Create Date: 2026-08-15
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003_repository_user_id"
down_revision: str | None = "0002_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Default bootstrap admin email, matching app.core.config. Not a secret.
BOOTSTRAP_ADMIN_EMAIL = "admin@teambrain.local"


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column(
        "repositories",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )

    bootstrap_user_id = bind.execute(
        sa.text(
            "SELECT id FROM users WHERE email = :email"
        ),
        {"email": BOOTSTRAP_ADMIN_EMAIL},
    ).scalar()

    if bootstrap_user_id is None:
        # The placeholder password cannot authenticate a login. The real
        # password is set from the BOOTSTRAP_ADMIN_PASSWORD environment
        # variable on the first application startup; it is never stored in
        # source code or migrations.
        bind.execute(
            sa.text(
                "INSERT INTO users "
                "(email, hashed_password, is_active, created_at) "
                "VALUES (:email, :hashed_password, :is_active, "
                "CURRENT_TIMESTAMP)"
            ),
            {
                "email": BOOTSTRAP_ADMIN_EMAIL,
                "hashed_password": "bootstrap-unset",
                "is_active": True,
            },
        )

        bootstrap_user_id = bind.execute(
            sa.text(
                "SELECT id FROM users WHERE email = :email"
            ),
            {"email": BOOTSTRAP_ADMIN_EMAIL},
        ).scalar()

    bind.execute(
        sa.text("UPDATE repositories SET user_id = :user_id"),
        {"user_id": bootstrap_user_id},
    )

    # Batch mode keeps this migration runnable on SQLite (which cannot
    # ALTER constraints or NOT NULL in place) and PostgreSQL alike.
    with op.batch_alter_table("repositories") as batch_op:
        batch_op.alter_column(
            "user_id",
            nullable=False,
        )

        batch_op.drop_constraint(
            "uq_repository_owner_name",
            type_="unique",
        )
        batch_op.create_unique_constraint(
            "uq_repository_user_owner_name",
            ["user_id", "owner", "name"],
        )
        batch_op.create_index(
            op.f("ix_repositories_user_id"),
            ["user_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("repositories") as batch_op:
        batch_op.drop_index(
            op.f("ix_repositories_user_id"),
        )
        batch_op.drop_constraint(
            "uq_repository_user_owner_name",
            type_="unique",
        )
        batch_op.create_unique_constraint(
            "uq_repository_owner_name",
            ["owner", "name"],
        )
        batch_op.alter_column(
            "user_id",
            nullable=True,
        )
        batch_op.drop_column(
            "user_id",
        )
