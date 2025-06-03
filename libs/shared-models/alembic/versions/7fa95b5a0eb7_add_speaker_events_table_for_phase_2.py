"""Add speaker_events table for Phase 2

Revision ID: 7fa95b5a0eb7
Revises: 
Create Date: 2025-06-03 17:19:11.945871

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fa95b5a0eb7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type for speaker event types
    speaker_event_type = sa.Enum('SPEAKER_START', 'SPEAKER_END', name='speakereventtype')
    speaker_event_type.create(op.get_bind(), checkfirst=True)
    
    # Create speaker_events table
    op.create_table('speaker_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meeting_id', sa.Integer(), nullable=False),
        sa.Column('session_uid', sa.String(), nullable=False),
        sa.Column('participant_name', sa.String(length=255), nullable=False),
        sa.Column('participant_id_meet', sa.String(length=255), nullable=False),
        sa.Column('event_type', speaker_event_type, nullable=False),
        sa.Column('client_timestamp_ms', sa.BigInteger(), nullable=False),
        sa.Column('server_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('absolute_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_speaker_event_meeting_absolute_time', 'speaker_events', ['meeting_id', 'absolute_timestamp'])
    op.create_index('ix_speaker_event_participant_meeting', 'speaker_events', ['meeting_id', 'participant_id_meet', 'absolute_timestamp'])
    op.create_index('ix_speaker_event_session_time', 'speaker_events', ['session_uid', 'client_timestamp_ms'])
    op.create_index(op.f('ix_speaker_events_event_type'), 'speaker_events', ['event_type'])
    op.create_index(op.f('ix_speaker_events_id'), 'speaker_events', ['id'])
    op.create_index(op.f('ix_speaker_events_meeting_id'), 'speaker_events', ['meeting_id'])
    op.create_index(op.f('ix_speaker_events_participant_id_meet'), 'speaker_events', ['participant_id_meet'])
    op.create_index(op.f('ix_speaker_events_session_uid'), 'speaker_events', ['session_uid'])
    op.create_index(op.f('ix_speaker_events_absolute_timestamp'), 'speaker_events', ['absolute_timestamp'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f('ix_speaker_events_absolute_timestamp'), table_name='speaker_events')
    op.drop_index(op.f('ix_speaker_events_session_uid'), table_name='speaker_events')
    op.drop_index(op.f('ix_speaker_events_participant_id_meet'), table_name='speaker_events')
    op.drop_index(op.f('ix_speaker_events_meeting_id'), table_name='speaker_events')
    op.drop_index(op.f('ix_speaker_events_id'), table_name='speaker_events')
    op.drop_index(op.f('ix_speaker_events_event_type'), table_name='speaker_events')
    op.drop_index('ix_speaker_event_session_time', table_name='speaker_events')
    op.drop_index('ix_speaker_event_participant_meeting', table_name='speaker_events')
    op.drop_index('ix_speaker_event_meeting_absolute_time', table_name='speaker_events')
    
    # Drop table
    op.drop_table('speaker_events')
    
    # Drop enum type
    sa.Enum(name='speakereventtype').drop(op.get_bind(), checkfirst=True)
