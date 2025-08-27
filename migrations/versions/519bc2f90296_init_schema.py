"""init schema

Revision ID: 519bc2f90296
Revises: 42c73fe3c7ad
Create Date: 2025-08-27 17:11:18.360540

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '519bc2f90296'
down_revision: Union[str, Sequence[str], None] = '42c73fe3c7ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
