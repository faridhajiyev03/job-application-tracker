"""add application user

Revision ID: 20d656c51d77
Revises: bb8dad464641
Create Date: 2026-09-23 19:25:18.469536

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20d656c51d77'
down_revision: Union[str, Sequence[str], None] = 'bb8dad464641'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "applications",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_applications_user_id_users",
        "applications",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_applications_user_id_users",
        "applications",
        type_="foreignkey",
    )

    op.drop_column("applications", "user_id")
