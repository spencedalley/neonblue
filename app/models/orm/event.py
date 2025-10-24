from sqlalchemy import (
    Column,
    String,
    Float,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
    Enum,
    PrimaryKeyConstraint,
)
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
    __tablename__ = "events"

    event_id = Column(String, primary_key=True, index=True)

    user_id = Column(String, nullable=False, index=True)

    type = Column(String, nullable=False, index=True)

    experiment_id = Column(
        String, ForeignKey("experiments.experiment_id"), index=True, nullable=True
    )

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    properties = Column(JSON_TYPE, default={}, nullable=False)

    experiment = relationship("ExperimentORM", back_populates="events")
