from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Text, Enum, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum


from .base import Base

from sqlalchemy.types import TypeEngine
try:
    # Use JSONB for PostgreSQL if available (recommended)
    from sqlalchemy.dialects.postgresql import JSONB as JSON_TYPE
except ImportError:
    try:
        # Fallback to standard JSON type
        from sqlalchemy.types import JSON as JSON_TYPE
    except ImportError:
        # Final fallback to Text (requires application-level JSON serialization/deserialization)
        JSON_TYPE = Text

class EventORM(Base):
    __tablename__ = 'events'

    # --- Core Identifiers ---
    # Primary Key - Every event needs a unique identifier
    event_id = Column(String, primary_key=True, index=True)

    # User ID - Who performed the action
    user_id = Column(String, nullable=False, index=True)

    # Event Type - What kind of action (e.g., "click", "purchase")
    type = Column(String, nullable=False, index=True)

    # 🎯 Contextual Link - Which experiment was the user assigned to AT THE TIME OF THE EVENT
    # This is crucial for filtering and analysis.
    experiment_id = Column(String, ForeignKey('experiments.experiment_id'), index=True, nullable=True)

    # --- Metadata ---
    # Timestamp - When the action occurred
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 🎯 Flexible Properties - The required JSON object for additional context
    # This stores the flexible data like {'product_id': 'X', 'price': 99.99}
    properties = Column(JSON_TYPE, default={}, nullable=False)

    # Relationship to Parent
    experiment = relationship("ExperimentORM", back_populates="events")
