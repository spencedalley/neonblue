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



class AssignmentORM(Base):
    __tablename__ = 'assignments'

    # --- Core Identifiers ---

    # 🎯 Primary Key: The combination of user_id and experiment_id ensures
    # a user has only one assignment per experiment (idempotency).
    user_id = Column(String, nullable=False, index=True)

    # Include experiment_id to define the assignment context,
    # even though it's technically redundant via the variant_id FK.
    # We keep it for better indexing and querying simplicity.
    experiment_id = Column(String, ForeignKey('experiments.experiment_id'), nullable=False, index=True)

    # 🎯 Foreign Key: Links to the specific Variant (which itself links to the experiment)
    variant_id = Column(String, ForeignKey('variants.variant_id'), nullable=False)

    # --- Metadata ---
    assignment_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


    # Define the composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'experiment_id', name='assignment_pk'),
    )

    # --- Relationships ---

    # Many Assignments belong to One Variant
    variant = relationship("VariantORM")

    # Many Assignments belong to One Experiment
    experiment = relationship("ExperimentORM")

