from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class VariantConfig(BaseModel):
    """Configuration for a single variant in an experiment."""

    variant_name: str
    traffic_allocation_percent: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of traffic allocated to this variant.",
    )
    # Optional: could add configuration specific to the variant (e.g., feature flags, content IDs)
    configuration_json: Optional[Dict] = None
    is_control: Optional[bool] = None


class ExperimentModel(BaseModel):
    """Data model for a persistent experiment record."""

    experiment_id: str = Field(..., description="Unique ID for the experiment.")
    name: str
    description: Optional[str] = None
    status: str = Field(
        ..., description="e.g., 'DRAFT', 'RUNNING', 'PAUSED', 'COMPLETED'"
    )
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    variants: List[VariantConfig]
    total_traffic_allocation: float = Field(
        ...,
        description="Sum of all variant traffic_allocation_percent, should be 100.0.",
    )
    primary_metric_name: str = Field(..., description="Primary metric name")


class ExperimentCreateModel(BaseModel):
    """Data model for a persistent experiment record."""

    name: str
    description: Optional[str] = None
    status: str = Field(
        ..., description="e.g., 'DRAFT', 'RUNNING', 'PAUSED', 'COMPLETED'"
    )
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    variants: List[VariantConfig]
    primary_metric_name: str = Field(..., description="Primary metric name")

    class Config:
        # Example validation check for total allocation (would be better in a root_validator)
        # For simplicity in this model-only response, we rely on total_traffic_allocation field
        pass


class ExperimentVariantConfigResponseModel(BaseModel):
    variant_id: str
    variant_name: str
    traffic_allocation_percent: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of traffic allocated to this variant.",
    )


class ExperimentResponseModel(ExperimentModel):
    experiment_id: str = Field(..., description="Unique ID for the experiment.")
    name: str
    description: Optional[str] = None
    status: str = Field(
        ..., description="e.g., 'DRAFT', 'RUNNING', 'PAUSED', 'COMPLETED'"
    )
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    variants_ids: List[ExperimentVariantConfigResponseModel]
    primary_metric_name: str = Field(..., description="Primary metric name")
    total_traffic_allocation: float = Field(
        ...,
        description="Sum of all variant traffic_allocation_percent, should be 100.0.",
    )


# --- User Assignment ---


class AssignmentModel(BaseModel):
    """Data model for a persistent user assignment record."""

    experiment_id: str
    user_id: str
    variant_id: str = Field(
        ..., description="The name of the variant the user was assigned."
    )
    assignment_timestamp: datetime = Field(default_factory=datetime.utcnow)
    # Could be indexed by (experiment_id, user_id) for quick lookups

    model_config = ConfigDict(from_attributes=True)


# --- Event Tracking ---
class EventModel(BaseModel):
    """Data model for a persistent event record (e.g., from POST /events)."""

    event_id: str = Field(..., description="Unique ID for the event.")
    user_id: str
    experiment_id: Optional[str] = Field(
        None,
        description="Optional: ID of the experiment the user is currently participating in (at event time).",
    )
    type: str = Field(..., description="e.g., 'click', 'purchase', 'signup'")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    properties: Dict = Field(
        default_factory=dict,
        description="Flexible JSON object for additional context (e.g., 'product_id', 'purchase_amount').",
    )


# --- Reporting and Analytics ---


class VariantMetric(BaseModel):
    """Core structure for a single metric result."""

    metric_name: str = Field(
        ..., description="e.g., 'conversion_rate', 'total_revenue', 'user_count'"
    )
    value: float
    unit: str = Field(..., description="e.g., '%', '$', 'count'")
    # For statistical significance
    confidence_interval_low: Optional[float] = None
    confidence_interval_high: Optional[float] = None


class VariantResult(BaseModel):
    """Metrics aggregated for a single variant."""

    variant_name: str
    assignment_count: int = Field(
        ...,
        description="Total users assigned to this variant *before* the reporting period end.",
    )
    active_user_count: int = Field(
        ...,
        description="Users who recorded relevant events during the reporting period.",
    )
    metrics: List[VariantMetric]
