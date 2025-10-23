from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AssignmentModel(BaseModel):
    """Data model for a persistent user assignment record."""
    experiment_id: str
    user_id: str
    variant_id: str = Field(..., description="The name of the variant the user was assigned.")
    assignment_timestamp: datetime = Field(default_factory=datetime.utcnow)
    # Could be indexed by (experiment_id, user_id) for quick lookups

