# migrations/versions/<generated_hash>_add_conversation_document_context.py
"""add scratchpad_notes and active_document_ids to conversations

Revision ID: a1b2c3d4e5f6
Revises: 546422ce6f2a
Create Date: 2026-08-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '546422ce6f2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('scratchpad_notes', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('active_document_ids', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.drop_column('active_document_ids')
        batch_op.drop_column('scratchpad_notes')