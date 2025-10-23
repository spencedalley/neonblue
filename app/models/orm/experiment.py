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


# Use Python Enum for constrained choices like Experiment Status
class ExperimentStatus(enum.Enum):
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

# --- Experiment Model ---
class ExperimentORM(Base):
    __tablename__ = 'experiments'

    # --- Core Identifiers ---
    experiment_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)

    # --- Lifecycle and Governance ---
    status = Column(Enum(ExperimentStatus), default=ExperimentStatus.DRAFT, nullable=False)

    # 🎯 NEW: Tracking who created and last updated the experiment
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Timing and Duration ---
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)

    # --- Analysis and Metrics ---
    # 🎯 NEW: Defines the goal of the experiment for reporting
    primary_metric_name = Column(String, nullable=False)
    # 🎯 NEW: Defines the minimum sample size or time needed to declare a winner
    target_duration_days = Column(Float, default=7.0)
    target_statistical_significance = Column(Float, default=0.95)  # 95% confidence

    # --- Relationship to Variants ---
    # One Experiment has Many VariantConfigs
    variants = relationship("VariantORM", back_populates="experiment")

    # One Experiment has Many Events
    events = relationship("EventORM", back_populates="experiment")

# --- Variant Configuration Model ---
class VariantORM(Base):
    __tablename__ = 'variants'

    variant_id = Column(String, primary_key=True)
    variant_name = Column(String, nullable=False)
    traffic_allocation_percent = Column(Float, nullable=False)
    is_control = Column(Boolean, default=False)

    # Additional configuration details (e.g., feature flag overrides)
    configuration_json = Column(JSON_TYPE, nullable=True)

    # 🎯 Foreign Key: This is the "many" side pointing to the "one" Experiment
    experiment_id = Column(String, ForeignKey('experiments.experiment_id'), nullable=False, index=True)

    # Relationship to Parent
    experiment = relationship("ExperimentORM", back_populates="variants")



