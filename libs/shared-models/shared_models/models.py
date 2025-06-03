import sqlalchemy
from sqlalchemy import (Column, String, Text, Integer, DateTime, Float, ForeignKey, Index, UniqueConstraint, Enum)
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime # Needed for Transcription model default
from shared_models.schemas import Platform # Import Platform for the static method
from typing import Optional # Added for the return type hint in constructed_meeting_url
import enum # Add enum import for speaker event types

# Define the base class for declarative models
Base = declarative_base()

# Add enum for speaker event types
class SpeakerEventType(enum.Enum):
    """Enum for speaker activity event types"""
    SPEAKER_START = "SPEAKER_START"
    SPEAKER_END = "SPEAKER_END"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True) # Added index=True
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100))
    image_url = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    max_concurrent_bots = Column(Integer, nullable=False, server_default='1', default=1) # Added field
    
    meetings = relationship("Meeting", back_populates="user")
    api_tokens = relationship("APIToken", back_populates="user")

class APIToken(Base):
    __tablename__ = "api_tokens"
    id = Column(Integer, primary_key=True, index=True) # Added index=True
    token = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="api_tokens")

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(100), nullable=False) # e.g., 'google_meet', 'zoom'
    # Database column name is platform_specific_id but we use native_meeting_id in the code
    platform_specific_id = Column(String(255), index=True, nullable=True)
    status = Column(String(50), nullable=False, default='requested', index=True)
    bot_container_id = Column(String(255), nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="meetings")
    transcriptions = relationship("Transcription", back_populates="meeting")
    sessions = relationship("MeetingSession", back_populates="meeting", cascade="all, delete-orphan")
    speaker_events = relationship("SpeakerEvent", back_populates="meeting", cascade="all, delete-orphan")

    # Add composite index for efficient lookup by user, platform, and native ID, including created_at for sorting
    __table_args__ = (
        Index(
            'ix_meeting_user_platform_native_id_created_at',
            'user_id',
            'platform',
            'platform_specific_id',
            'created_at' # Include created_at because the query orders by it
        ),
        # Optional: Unique constraint (uncomment if needed, ensure native_meeting_id cannot be NULL if unique)
        # UniqueConstraint('user_id', 'platform', 'platform_specific_id', name='_user_platform_native_id_uc'),
    )

    # Add property getters/setters for compatibility
    @property
    def native_meeting_id(self):
        return self.platform_specific_id
        
    @native_meeting_id.setter
    def native_meeting_id(self, value):
        self.platform_specific_id = value
        
    @property
    def constructed_meeting_url(self) -> Optional[str]: # Added return type hint
        # Calculate the URL on demand using the static method from schemas.py
        if self.platform and self.platform_specific_id:
             return Platform.construct_meeting_url(self.platform, self.platform_specific_id)
        return None

class Transcription(Base):
    __tablename__ = "transcriptions"
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True) # Changed nullable to False, should always link
    # Removed redundant platform, meeting_url, token, client_uid, server_id as they belong to the Meeting
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    speaker = Column(String(255), nullable=True) # Speaker identifier
    language = Column(String(10), nullable=True) # e.g., 'en', 'es'
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="transcriptions")
    
    session_uid = Column(String, nullable=True, index=True) # Link to the specific bot session

    # Index for efficient querying by meeting_id and start_time
    __table_args__ = (Index('ix_transcription_meeting_start', 'meeting_id', 'start_time'),)

# New table to store session start times
class MeetingSession(Base):
    __tablename__ = 'meeting_sessions'
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id'), nullable=False, index=True)
    session_uid = Column(String, nullable=False, index=True) # Stores the 'uid' (based on connectionId)
    # Store timezone-aware timestamp to avoid ambiguity
    session_start_time = Column(sqlalchemy.DateTime(timezone=True), nullable=False, server_default=func.now())

    meeting = relationship("Meeting", back_populates="sessions") # Define relationship

    __table_args__ = (UniqueConstraint('meeting_id', 'session_uid', name='_meeting_session_uc'),) # Ensure unique session per meeting

# New table to store speaker events for Phase 2
class SpeakerEvent(Base):
    """
    Table to store individual speaker activity events (SPEAKER_START/SPEAKER_END)
    for detailed timeline reconstruction and transcription-speaker correlation.
    """
    __tablename__ = 'speaker_events'
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id'), nullable=False, index=True)
    session_uid = Column(String, nullable=False, index=True)  # Links to MeetingSession
    
    # Speaker information
    participant_name = Column(String(255), nullable=False)  # Display name from the meeting
    participant_id_meet = Column(String(255), nullable=False, index=True)  # Platform-specific participant ID
    
    # Event details
    event_type = Column(Enum(SpeakerEventType), nullable=False, index=True)  # SPEAKER_START or SPEAKER_END
    
    # Timestamps
    client_timestamp_ms = Column(sqlalchemy.BigInteger, nullable=False)  # Original timestamp from bot (milliseconds since epoch)
    server_timestamp = Column(sqlalchemy.DateTime(timezone=True), nullable=False, server_default=func.now())  # When event was processed
    
    # Calculated absolute timestamp (will be populated by correlation logic)
    absolute_timestamp = Column(sqlalchemy.DateTime(timezone=True), nullable=True, index=True)  # Correlated with session start time
    
    # Relationships
    meeting = relationship("Meeting", back_populates="speaker_events")
    
    # Indexes for efficient querying
    __table_args__ = (
        # Index for timeline queries (by meeting and absolute time)
        Index('ix_speaker_event_meeting_absolute_time', 'meeting_id', 'absolute_timestamp'),
        # Index for participant activity queries  
        Index('ix_speaker_event_participant_meeting', 'meeting_id', 'participant_id_meet', 'absolute_timestamp'),
        # Index for session correlation
        Index('ix_speaker_event_session_time', 'session_uid', 'client_timestamp_ms'),
    )
