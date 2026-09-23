"""create applications table

Revision ID: 8def1b5bac06
Revises: 
Create Date: 2026-09-23 13:47:15.145562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8def1b5bac06'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company", sa.String(length=100), nullable=False),
        sa.Column("position", sa.String(length=100), nullable=False),
        sa.Column("vacancy_url", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("applications")
