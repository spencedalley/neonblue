# services/event_service.py

from sqlalchemy.orm import Session
from app.repositories.event_repo import EventRepository
from app.models.schemas.event import EventCreateModel, EventResponseModel
from app.models.orm.event import EventORM
from app.repositories.assignment_repo import AssignmentRepository  # Assuming an Assignment Repository exists


class EventService:
    def __init__(self, db: Session):
        """Initializes the service with repositories it needs."""
        self.event_repo = EventRepository(db)
        # We need the AssignmentRepo to look up the user's experiment context
        self.assignment_repo = AssignmentRepository(db)

    def record_event(self, event_data: EventCreateModel) -> EventResponseModel:
        """
        Handles the business logic for recording an event.
        1. Finds the active experiment assignment for the user.
        2. Records the event with the correct experiment context.
        """
        # --- Repository Call ---
        # Pass the enriched data (including resolved experiment context) to the repository
        recorded_event = self.event_repo.create_event(
            event_data=event_data
        )

        return EventResponseModel(event_id=recorded_event.event_id, experiment_id=recorded_event.experiment_id)