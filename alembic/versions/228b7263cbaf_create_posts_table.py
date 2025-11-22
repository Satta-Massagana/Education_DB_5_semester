"""create posts table

Revision ID: 228b7263cbaf
Revises: 10b55bd07c9a
Create Date: 2025-11-22 15:28:44.778027

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '228b7263cbaf'
down_revision: Union[str, Sequence[str], None] = '10b55bd07c9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
