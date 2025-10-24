from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime


#  event posting flow


class EventCreateModel(BaseModel):
    """Schema for creating a new Event (API Input)."""

    user_id: str
    type: str = Field(..., description="e.g., 'click', 'purchase', 'signup'")
    # We allow the timestamp to be optional in the API input; the server can set it if missing.
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    properties: Dict = Field(default_factory=dict, description="Flexible JSON object.")

    # TODO: thinking of making this required
    experiment_id: Optional[str] = None


class EventResponseModel(BaseModel):
    event_id: str
    experiment_id: Optional[str] = None
