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
    from sqlalchemy.dialects.postgresql import JSONB as JSON_TYPE
except ImportError:
    try:
        from sqlalchemy.types import JSON as JSON_TYPE
    except ImportError:
        JSON_TYPE = Text


class AssignmentORM(Base):
    __tablename__ = "assignments"

    user_id = Column(String, nullable=False, index=True)
    experiment_id = Column(
        String, ForeignKey("experiments.experiment_id"), nullable=False, index=True
    )
    variant_id = Column(String, ForeignKey("variants.variant_id"), nullable=False)

    assignment_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("user_id", "experiment_id", name="assignment_pk"),
    )

    variant = relationship("VariantORM")

    experiment = relationship("ExperimentORM")
