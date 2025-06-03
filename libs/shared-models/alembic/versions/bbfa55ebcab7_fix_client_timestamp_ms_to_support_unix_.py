"""Fix client_timestamp_ms to support unix timestamps

Revision ID: bbfa55ebcab7
Revises: 7fa95b5a0eb7
Create Date: 2025-06-03 17:46:14.974351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbfa55ebcab7'
down_revision: Union[str, None] = '7fa95b5a0eb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Change client_timestamp_ms from INTEGER to BIGINT to support Unix timestamps in milliseconds
    op.alter_column('speaker_events', 'client_timestamp_ms',
                    type_=sa.BigInteger(),
                    existing_type=sa.Integer(),
                    existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert client_timestamp_ms from BIGINT back to INTEGER
    op.alter_column('speaker_events', 'client_timestamp_ms',
                    type_=sa.Integer(),
                    existing_type=sa.BigInteger(),
                    existing_nullable=False)
